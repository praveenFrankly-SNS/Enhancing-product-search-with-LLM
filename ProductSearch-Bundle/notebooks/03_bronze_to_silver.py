# Databricks notebook source
# MAGIC %md
# MAGIC # Silver Data Transformation Pipeline (Cleaning & Preprocessing)
# MAGIC **Responsibility**: Loads raw WANDS and extension tables from Bronze, runs deduplication and value validations, audits cross-table integrity, and saves clean Silver tables.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import uuid
import time
from pathlib import Path
from datetime import datetime, timezone

from pyspark.sql import SparkSession

# Add project root to sys.path to allow imports when run in Databricks context
try:
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    project_root = "/Workspace" + notebook_path.split("/notebooks/")[0]
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    except NameError:
        pass

from src.shared.config import get_config
from src.shared.constants import BRONZE, SILVER, OPERATIONS
from src.shared.logger import get_logger

# Import Transformation modules
from src.transformation.products import transform_products, validate_products
from src.transformation.brand import transform_brand, validate_brand
from src.transformation.category import transform_category, validate_category
from src.transformation.pricing import transform_pricing, validate_pricing
from src.transformation.attributes import transform_attributes, validate_attributes
from src.transformation.reviews import transform_reviews, validate_reviews
from src.transformation.queries import transform_queries, validate_queries
from src.transformation.labels import transform_labels, validate_labels
from src.transformation.deduplication import remove_duplicates
from src.transformation.referential import validate_referential_integrity
from src.transformation.quality import log_dq_report, write_violations_to_quarantine

# Import MLflow tracking helpers
from src.mlflow.experiment import start_mlflow_run, end_mlflow_run
from src.mlflow.logger import log_parameters, log_metrics, log_table_statistics, log_execution_time
from src.mlflow.artifacts import log_file_artifact

# Import monitoring telemetry
from src.monitoring.telemetry import record_metric

# Import governance package utilities
from src.governance import (
    validate_pipeline_config,
    verify_secrets_prerequisites,
    verify_catalog_prerequisites,
    record_pipeline_audit
)



# COMMAND ----------
# Initialize Spark
spark = SparkSession.builder.getOrCreate()
logger = get_logger("bronze_to_silver")
# COMMAND ----------
# Setup widgets
dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment (dev/staging/prod)")

config = get_config(dbutils)
catalog = config.catalog
run_id = str(uuid.uuid4())
start_time = time.time()

logger.info(f"Starting Silver Data Transformation pipeline (Run ID: {run_id})")

# ── Enterprise Governance pre-execution validation checks ──────────────
# 1. Run config validation
config_check = validate_pipeline_config(config.yaml_config)
if not config_check["valid"]:
    raise RuntimeError(f"Governance Configuration check failed: {'; '.join(config_check['errors'])}")

# 2. Run secrets validation (this stage does not require database connection secrets)
governance_cfg = config.yaml_config.get("governance", {})
secrets_cfg = governance_cfg.get("secrets", {})
secret_scope = secrets_cfg.get("scope", config.yaml_config.get("pipeline", {}).get("secret_scope", ""))
required_secrets = []
secrets_check = verify_secrets_prerequisites(dbutils, secret_scope, required_secrets)
if not secrets_check["scope_exists"] or secrets_check["missing_keys"]:
    raise RuntimeError(f"Governance Secrets check failed in scope '{secret_scope}': {'; '.join(secrets_check['errors'])}")


# 3. Run catalog validation
catalog_check = verify_catalog_prerequisites(spark, catalog)
if not catalog_check["catalog_exists"] or catalog_check["errors"]:
    raise RuntimeError(f"Governance Catalog check failed on '{catalog}': {'; '.join(catalog_check['errors'])}")

# 4. Log successful validation
record_pipeline_audit(spark, catalog, run_id, "Silver", "pre_execution_governance_validation", "SUCCESS", "All governance prerequisites verified successfully.")

# Start MLflow run context
start_mlflow_run(config.yaml_config, run_name="Silver Transformation", stage="Silver")

# Log execution parameters
log_parameters({
    "catalog": catalog,
    "environment": config.environment,
    "run_id": run_id,
    "full_refresh": "true"
})
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Read Bronze tables and apply Entity validations
# COMMAND ----------
# Setup mappings

entities = [
    {"name": "product",                 "transform_fn": transform_products,           "validate_fn": validate_products},
    {"name": "query",                   "transform_fn": transform_queries,            "validate_fn": validate_queries},
    {"name": "label",                   "transform_fn": transform_labels,             "validate_fn": validate_labels},
    {"name": "brand",                   "transform_fn": transform_brand,              "validate_fn": validate_brand},
    {"name": "category",                "transform_fn": transform_category,           "validate_fn": validate_category},
    {"name": "product_pricing",         "transform_fn": transform_pricing,            "validate_fn": validate_pricing},
    {"name": "product_attributes",      "transform_fn": transform_attributes,         "validate_fn": validate_attributes},
    {"name": "product_review_summary",  "transform_fn": transform_reviews,            "validate_fn": validate_reviews},
]

entity_dfs = {}
all_violations = []

# Validate standard entities first
for ent in entities:
    name = ent["name"]
    logger.info(f"Reading and transforming entity: {name}...")
    
    bronze_df = spark.table(f"{catalog}.{BRONZE}.{name}")
    records_read = bronze_df.count()
    
    # Apply cleaning and preprocessing transformations
    transformed_df = ent["transform_fn"](bronze_df)
    
    # Run structural data quality and value bounds checks
    conformed_df, violations, dup_count = ent["validate_fn"](transformed_df, run_id)
    records_written = conformed_df.count()
    invalid_records = records_read - records_written - dup_count
    
    # Collect violations
    all_violations.extend(violations)
    entity_dfs[name] = conformed_df
    
    # Log individual entity validation results
    log_dq_report(
        spark=spark, catalog=catalog, ops_schema=OPERATIONS, run_id=run_id,
        table_name=name, stage="silver", records_read=records_read,
        records_written=records_written, duplicates=dup_count,
        invalid_records=invalid_records, status="SUCCESS"
    )
    
    # Log conformed table stats to MLflow
    log_table_statistics(name, records_read, records_written, dup_count, invalid_records)


# Handle product_master separately (simple validation)
logger.info("Reading and transforming product_master...")
master_bronze = spark.table(f"{catalog}.{BRONZE}.product_master")
master_read = master_bronze.count()
master_dedup, master_dup = remove_duplicates(master_bronze, ["product_id"])

# Null key check on product_id
master_invalid = master_dedup.filter(master_dedup.product_id.isNull() | (master_dedup.product_id == ""))
master_conformed = master_dedup.filter(master_dedup.product_id.isNotNull() & (master_dedup.product_id != ""))

master_invalid_cnt = master_invalid.count()
if master_invalid_cnt > 0:
    for row in master_invalid.limit(100).collect():
        all_violations.append({
            "rejection_id": str(uuid.uuid4()), "run_id": run_id, "run_date": datetime.now(timezone.utc).date(),
            "source_table": "product_master", "rule_name": "null_product_id",
            "violation_reason": "product_id is null in product_master", "record_key": "(unknown)",
            "created_at": datetime.now(timezone.utc)
        })

entity_dfs["product_master"] = master_conformed
log_dq_report(
    spark=spark, catalog=catalog, ops_schema=OPERATIONS, run_id=run_id,
    table_name="product_master", stage="silver", records_read=master_read,
    records_written=master_conformed.count(), duplicates=master_dup,
    invalid_records=master_invalid_cnt, status="SUCCESS"
)

# Log conformed table stats to MLflow
log_table_statistics("product_master", master_read, master_conformed.count(), master_dup, master_invalid_cnt)

# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Run cross-table Referential Integrity audits
# COMMAND ----------
logger.info("Starting cross-table referential integrity validations...")
conformed_tables, ref_violations = validate_referential_integrity(entity_dfs, run_id)
all_violations.extend(ref_violations)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Quarantine violations and write Silver tables
# COMMAND ----------
# Save all structural and referential violations to quarantine table
if all_violations:
    logger.warn(f"Quarantining {len(all_violations)} records to operations schema.")
    write_violations_to_quarantine(spark, all_violations, catalog, OPERATIONS)

# Save conformed DataFrames to Silver Medallion schema
for name, df in conformed_tables.items():
    target_table = f"{catalog}.{SILVER}.{name}"
    logger.info(f"Writing conformed table {target_table}...")
    df.write.format("delta").mode("overwrite").option("overwriteSchema", "true").saveAsTable(target_table)

# Log final metrics & upload config artifact
duration = time.time() - start_time
log_execution_time(duration, "silver_transformation")
log_metrics({"quarantined_violations_total": float(len(all_violations))})

# Log telemetry operational metrics
record_metric(spark, catalog, "Silver", "silver_transformation_duration", duration, "seconds", "SUCCESS")
record_metric(spark, catalog, "Silver", "quarantined_violations_count", len(all_violations), "violations", "SUCCESS")


try:
    config_path = project_root + "/config/pipeline.yml"
    log_file_artifact(config_path, "config")
except Exception as e:
    logger.warn(f"Failed to upload config file artifact: {str(e)}")

# End MLflow run context
end_mlflow_run()
# COMMAND ----------
# Record audit log
record_pipeline_audit(spark, catalog, run_id, "Silver", "silver_transformation_pipeline", "SUCCESS", f"Silver layer transformation completed. {len(all_violations)} violations quarantined.")
logger.success("Silver Data Transformation pipeline completed successfully for all tables!")


