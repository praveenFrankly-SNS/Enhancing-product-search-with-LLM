# Databricks notebook source
# MAGIC %md
# MAGIC # JDBC Ingestion Pipeline (Bronze Layer)
# MAGIC **Responsibility**: Connects to Supabase PostgreSQL and loads raw WANDS benchmark and extension tables into the Bronze Delta layer.
# MAGIC 
# MAGIC This notebook connects to Supabase, reads PostgreSQL tables in parallel, runs basic data sanity checks,
# MAGIC and writes the resulting data as Delta tables inside the unified Unity Catalog catalog.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import time
from pathlib import Path
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

import uuid
from src.shared.config import get_config
from src.shared.logger import get_logger
from src.shared.validation import validate_dataframe_not_empty, check_null_keys, check_duplicate_keys
from src.ingestion.jdbc_reader import read_jdbc_table

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
# Initialize Spark Session
spark = SparkSession.builder.getOrCreate()
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration & Input Parameters
# COMMAND ----------
dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("schema", "bronze", "Bronze Schema")
dbutils.widgets.text("environment", "dev", "Environment (dev/staging/prod)")
dbutils.widgets.text("secret_scope", "supabase-creds", "Secret Scope")
dbutils.widgets.text("num_partitions", "4", "Parallel Read Partitions")
dbutils.widgets.text("full_refresh", "true", "Full Overwrite Refresh (true/false)")

# Resolve Unified Config and Logger
config = get_config(dbutils)
logger = get_logger("jdbc_ingest")
run_id = str(uuid.uuid4())

# ── Enterprise Governance pre-execution validation checks ──────────────
# 1. Run config validation
config_check = validate_pipeline_config(config.yaml_config)
if not config_check["valid"]:
    raise RuntimeError(f"Governance Configuration check failed: {'; '.join(config_check['errors'])}")

# 2. Run secrets validation
governance_cfg = config.yaml_config.get("governance", {})
secrets_cfg = governance_cfg.get("secrets", {})
secret_scope = secrets_cfg.get("scope", config.yaml_config.get("pipeline", {}).get("secret_scope", ""))
required_secrets = secrets_cfg.get("required", [])
secrets_check = verify_secrets_prerequisites(dbutils, secret_scope, required_secrets)
if not secrets_check["scope_exists"] or secrets_check["missing_keys"]:
    raise RuntimeError(f"Governance Secrets check failed in scope '{secret_scope}': {'; '.join(secrets_check['errors'])}")

# 3. Run catalog validation
catalog = config.catalog
catalog_check = verify_catalog_prerequisites(spark, catalog)
# We enforce catalog existence, but schema/table missing during platform setup is expected (will be created below).
# If the catalog itself is missing/inaccessible, fail-fast.
if not catalog_check["catalog_exists"]:
    raise RuntimeError(f"Governance Catalog check failed on '{catalog}': {'; '.join(catalog_check['errors'])}")

# 4. Log successful validation
record_pipeline_audit(spark, catalog, run_id, "Bronze", "pre_execution_governance_validation", "SUCCESS", "All governance prerequisites verified successfully.")

logger.info(
    "JDBC Ingestion started",
    catalog=config.catalog,
    env=config.environment,
    full_refresh=config.full_refresh
)

# COMMAND ----------
# MAGIC %md
# MAGIC ### Ensure Target Schemas Exist
# COMMAND ----------
try:
    # Auto-create schemas if they don't exist to ensure ingestion runs cleanly
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.catalog}.{config.bronze_schema}")
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.catalog}.{config.ops_schema}")
    logger.info("✓ Verified target schemas exist.", catalog=config.catalog)
except Exception as e:
    logger.warn(f"Could not verify or create target schemas: {e}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Execute Table Ingestion
# COMMAND ----------
failed_tables = []

# Select write mode based on full_refresh widget
write_mode = "overwrite" if config.full_refresh else "append"

for entry in config.tables:
    src_table = entry["source"]
    tgt_table = entry["target"]
    primary_key = entry.get("primary_key")
    full_target = f"{config.catalog}.{config.bronze_schema}.{tgt_table}"
    
    logger.info("Ingesting table", source=src_table, target=full_target, write_mode=write_mode)
    t0 = time.time()
    
    try:
        # 1. Read table from database in parallel via Spark JDBC
        df = read_jdbc_table(
            spark=spark,
            secret_scope=config.secret_scope,
            source_table=src_table,
            num_partitions=config.num_partitions,
            dbutils=dbutils
        )
        
        # 2. Extract input count
        rows_read = df.count()
        
        # 3. Basic pre-write validation
        validate_dataframe_not_empty(df, src_table)
        if primary_key:
            check_null_keys(df, primary_key, src_table)
            check_duplicate_keys(df, primary_key, src_table)
            
        # 4. Write to Bronze Delta table
        (
            df.write
            .format("delta")
            .mode(write_mode)
            .option("overwriteSchema", "true" if write_mode == "overwrite" else "false")
            .saveAsTable(full_target)
        )
        
        # 5. Extract written count and duration
        rows_written = spark.table(full_target).count()
        duration = time.time() - t0
        
        # 6. Log success to stdout and direct Delta operations audit logs
        logger.log_ingestion_audit(
            spark=spark,
            catalog=config.catalog,
            source_table=src_table,
            target_table=full_target,
            status="SUCCESS",
            rows_read=rows_read,
            rows_written=rows_written,
            duration_seconds=duration
        )
        
        # Log telemetry operational metrics
        record_metric(spark, config.catalog, "Bronze", f"{src_table}_ingestion_duration", duration, "seconds", "SUCCESS")
        record_metric(spark, config.catalog, "Bronze", f"{src_table}_rows_read", rows_read, "rows", "SUCCESS")
        record_metric(spark, config.catalog, "Bronze", f"{src_table}_rows_written", rows_written, "rows", "SUCCESS")
        
        logger.success(
            "Ingestion successful",
            target=full_target,
            rows=rows_written,
            duration_s=round(duration, 2)
        )
        
    except Exception as e:
        duration = time.time() - t0
        logger.log_ingestion_audit(
            spark=spark,
            catalog=config.catalog,
            source_table=src_table,
            target_table=full_target,
            status="FAILED",
            rows_read=0,
            rows_written=0,
            duration_seconds=duration,
            message=str(e)
        )
        
        # Log telemetry failure metrics
        record_metric(spark, config.catalog, "Bronze", f"{src_table}_ingestion_duration", duration, "seconds", "FAILED")
        record_metric(spark, config.catalog, "Bronze", f"{src_table}_rows_read", 0, "rows", "FAILED")
        record_metric(spark, config.catalog, "Bronze", f"{src_table}_rows_written", 0, "rows", "FAILED")
        
        logger.error("Ingestion failed", source=src_table, error=str(e))
        failed_tables.append(src_table)

# COMMAND ----------
# MAGIC %md
# MAGIC ### Ingestion Completion Summary
# COMMAND ----------
if failed_tables:
    error_msg = f"JDBC Ingestion failed for tables: {failed_tables}"
    record_pipeline_audit(spark, config.catalog, run_id, "Bronze", "jdbc_ingestion_pipeline", "FAILED", error_msg)
    logger.error(error_msg)
    raise RuntimeError(error_msg)
else:
    record_pipeline_audit(spark, config.catalog, run_id, "Bronze", "jdbc_ingestion_pipeline", "SUCCESS", "All tables ingested successfully to Bronze layer.")
    logger.success("JDBC Ingestion Pipeline completed successfully for all tables!")

