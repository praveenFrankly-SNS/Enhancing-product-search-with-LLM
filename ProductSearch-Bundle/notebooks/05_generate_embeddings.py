# Databricks notebook source
# MAGIC %md
# MAGIC # Gold Catalog — Indexing Readiness Prep
# MAGIC **Responsibility**: Final preparation step before Vector Search indexing.
# MAGIC
# MAGIC This notebook:
# MAGIC 1. Enables **Change Data Feed (CDF)** on `gold.product_search_catalog` — required for the Delta Sync index to track incremental product changes.
# MAGIC 2. Validates `searchable_text` coverage (non-null, non-empty) across the full catalog.
# MAGIC 3. Logs a readiness summary to the operations execution log.
# MAGIC
# MAGIC **Pipeline position (Offline — Product Indexing Pipeline):**
# MAGIC ```
# MAGIC PostgreSQL → Bronze → Silver → Gold → [THIS NOTEBOOK] → Vector Search Index
# MAGIC ```
# MAGIC
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import time
import uuid
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# Add project root to sys.path for imports
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
from src.shared.constants import GOLD, OPERATIONS
from src.shared.logger import get_logger

# Import MLflow tracking helpers
from src.mlflow.experiment import start_mlflow_run, end_mlflow_run
from src.mlflow.logger import log_parameters, log_metrics, log_execution_time
from src.mlflow.artifacts import log_file_artifact

# Import governance package utilities
from src.governance import (
    validate_pipeline_config,
    verify_secrets_prerequisites,
    verify_catalog_prerequisites,
    record_pipeline_audit
)

spark = SparkSession.builder.getOrCreate()
logger = get_logger("indexing_prep")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",     "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev",                "Environment (dev/staging/prod)")

config  = get_config(dbutils)
catalog = config.catalog
run_id  = str(uuid.uuid4())

logger.info(f"Starting indexing readiness prep (Run ID: {run_id}) for catalog: {catalog}")

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
record_pipeline_audit(spark, catalog, run_id, "Embedding Prep", "pre_execution_governance_validation", "SUCCESS", "All governance prerequisites verified successfully.")

# Start MLflow run context
start_mlflow_run(config.yaml_config, run_name="Embedding Generation", stage="Embedding Prep")

# Log execution parameters
log_parameters({
    "catalog": catalog,
    "environment": config.environment,
    "run_id": run_id,
    "pipeline_stage": "Embedding Prep",
    "embedding_model": "databricks-bge-large-en"
})

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Enable Change Data Feed on Gold Product Search Catalog
# MAGIC
# MAGIC CDF is required for the Databricks Vector Search Delta Sync index to track
# MAGIC incremental product changes and stay in sync as the catalog is refreshed.
# COMMAND ----------
catalog_table = f"{catalog}.{GOLD}.product_search_catalog"

logger.info(f"Enabling Change Data Feed on: {catalog_table}")
spark.sql(f"""
    ALTER TABLE {catalog_table}
    SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
""")
logger.info(f"CDF enabled on {catalog_table}.")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Validate searchable_text Coverage
# MAGIC
# MAGIC Every product must have a non-null, non-empty `searchable_text` field
# MAGIC before it can be indexed. Rows failing this check are logged as warnings.
# COMMAND ----------
t_start = time.time()
catalog_df = spark.table(catalog_table)
total_count = catalog_df.count()

valid_filter = (
    F.col("searchable_text").isNotNull() &
    (F.length(F.trim(F.col("searchable_text"))) > 0)
)
invalid_count = catalog_df.filter(~valid_filter).count()
valid_count   = total_count - invalid_count

logger.info(f"Catalog: {total_count} total products | {valid_count} with valid searchable_text | {invalid_count} invalid")

if invalid_count > 0:
    logger.warn(
        f"{invalid_count} products have null or empty searchable_text — "
        f"they will be excluded from embedding by the Vector Search index."
    )
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Validate Required Columns for Vector Search Index
# MAGIC
# MAGIC The Delta Sync index requires: `product_id` (primary key), `searchable_text` (embedding source),
# MAGIC and the metadata columns used for filtering pushdown.
# COMMAND ----------
required_columns = [
    "product_id", "product_name", "category_path", "brand_name",
    "selling_price", "average_rating", "review_count",
    "attribute_summary", "searchable_text",
]

actual_columns = catalog_df.columns
missing = [col for col in required_columns if col not in actual_columns]

if missing:
    raise ValueError(
        f"Gold product_search_catalog is missing required columns for indexing: {missing}"
    )

logger.info(f"All {len(required_columns)} required columns present. Ready for Vector Search indexing.")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 4. Readiness Summary
# COMMAND ----------
duration = time.time() - t_start

logger.log_execution(
    spark=spark,
    catalog=catalog,
    task_name="indexing_prep",
    table_name="gold.product_search_catalog",
    status="SUCCESS" if invalid_count == 0 else "WARN",
    rows_processed=valid_count,
    duration_seconds=duration,
    message=(
        f"CDF enabled. {valid_count}/{total_count} products ready for indexing. "
        f"{invalid_count} products with empty searchable_text."
    ),
)

# Preview the searchable_text for spot-checking
display(
    catalog_df
    .select("product_id", "product_name", "searchable_text")
    .orderBy(F.length("searchable_text").desc())
    .limit(5)
)

# Log metrics to MLflow
log_metrics({
    "total_products_count": float(total_count),
    "valid_products_count": float(valid_count),
    "invalid_products_count": float(invalid_count)
})

# Log execution time
log_execution_time(duration, "embedding_prep")

try:
    config_path = project_root + "/config/pipeline.yml"
    log_file_artifact(config_path, "config")
except Exception as e:
    logger.warn(f"Failed to upload config file artifact: {str(e)}")

# End MLflow run context
end_mlflow_run()
# COMMAND ----------
# Record audit log
record_pipeline_audit(spark, catalog, run_id, "Embedding Prep", "indexing_prep_pipeline", "SUCCESS", f"CDF preparation completed. Ready to index: {valid_count} products.")
logger.success(
    f"Indexing readiness prep complete. "
    f"{valid_count} products ready for Vector Search Delta Sync indexing."
)


