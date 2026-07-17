# Databricks notebook source
# MAGIC %md
# MAGIC # Platform Setup
# MAGIC **Responsibility**: Creates the Unity Catalog database schemas and operational metadata tables required before running any pipelines.
# MAGIC 
# MAGIC Running this notebook sets up:
# MAGIC 1. Target Catalog
# MAGIC 2. Bronze Schema (for raw WANDS and extension tables)
# MAGIC 3. Silver Schema (for cleaned and validated tables)
# MAGIC 4. Gold Schema (for final search-optimized tables)
# MAGIC 5. Operations Schema (for pipeline logs, metrics, and quarantined records)
# MAGIC 6. Metadata tables: `pipeline_execution_log`, `data_ingestion_audit`, `rejected_records`, and `data_quality_report`
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    DoubleType, DateType, TimestampType
)

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
from src.shared.constants import BRONZE, SILVER, GOLD, OPERATIONS, EXECUTION_LOG, DATA_INGESTION_AUDIT, REJECTED_RECORDS, DATA_QUALITY_REPORT, MONITORING_METRICS, HEALTH_STATUS, ALERT_LOG, AUDIT_LOG, SECURITY_VALIDATION
# COMMAND ----------
# Initialize Spark Session
spark = SparkSession.builder.getOrCreate()
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment (dev/staging/prod)")

config = get_config(dbutils)

print(f"Configuring workspace environment:")
print(f"  - Environment: {config.environment}")
print(f"  - Catalog: {config.catalog}")
print(f"  - Bronze Schema: {config.catalog}.{BRONZE}")
print(f"  - Operations Schema: {config.catalog}.{OPERATIONS}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Create Unity Catalog Database & Medallion Schemas
# COMMAND ----------
# Create Catalog
spark.sql(f"CREATE CATALOG IF NOT EXISTS {config.catalog}")
print(f"✓ Catalog '{config.catalog}' ready.")

# Create Schemas
for schema_name in [BRONZE, SILVER, GOLD, OPERATIONS]:
    spark.sql(f"CREATE SCHEMA IF NOT EXISTS {config.catalog}.{schema_name}")
    print(f"✓ Schema '{config.catalog}.{schema_name}' ready.")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Initialize Operational Metadata Logs
# COMMAND ----------
# A. Define schema for Pipeline Execution Log
PIPELINE_EXECUTION_LOG_SCHEMA = StructType([
    StructField("log_id",             StringType(),    False),
    StructField("run_id",             StringType(),    False),
    StructField("run_date",           DateType(),      True),
    StructField("task_name",          StringType(),    True),
    StructField("table_name",         StringType(),    True),
    StructField("status",             StringType(),    True),   # SUCCESS | WARN | FAILED
    StructField("rows_processed",     LongType(),      True),
    StructField("duration_seconds",   DoubleType(),    True),
    StructField("message",            StringType(),    True),
    StructField("created_at",         TimestampType(), True),
])

full_log_table = f"{config.catalog}.{OPERATIONS}.{EXECUTION_LOG}"
print(f"Initializing operational execution table: {full_log_table}...")
(
    spark.createDataFrame([], PIPELINE_EXECUTION_LOG_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_log_table)
)
print(f"✓ Operational table '{full_log_table}' ready.")

# B. Define schema for Data Ingestion Audit
DATA_INGESTION_AUDIT_SCHEMA = StructType([
    StructField("audit_id",         StringType(),    False),
    StructField("run_id",           StringType(),    False),
    StructField("table_name",       StringType(),    True),
    StructField("source_table",     StringType(),    True),
    StructField("status",           StringType(),    True),   # SUCCESS | FAILED
    StructField("rows_read",        LongType(),      True),
    StructField("rows_written",     LongType(),      True),
    StructField("duration_seconds", DoubleType(),    True),
    StructField("message",          StringType(),    True),
    StructField("created_at",       TimestampType(), True),
])

full_audit_table = f"{config.catalog}.{OPERATIONS}.{DATA_INGESTION_AUDIT}"
print(f"Initializing operational ingestion audit table: {full_audit_table}...")
(
    spark.createDataFrame([], DATA_INGESTION_AUDIT_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_audit_table)
)
print(f"✓ Ingestion audit table '{full_audit_table}' ready.")

# C. Define schema for Quarantine (rejected_records)
REJECTED_RECORDS_SCHEMA = StructType([
    StructField("rejection_id",     StringType(),    False),
    StructField("run_id",           StringType(),    False),
    StructField("run_date",         DateType(),      True),
    StructField("source_table",     StringType(),    True),
    StructField("rule_name",        StringType(),    True),
    StructField("violation_reason", StringType(),    True),
    StructField("record_key",       StringType(),    True),
    StructField("created_at",       TimestampType(), True),
])

full_rejected_table = f"{config.catalog}.{OPERATIONS}.{REJECTED_RECORDS}"
print(f"Initializing quarantine table: {full_rejected_table}...")
(
    spark.createDataFrame([], REJECTED_RECORDS_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_rejected_table)
)
print(f"✓ Quarantine table '{full_rejected_table}' ready.")

# D. Define schema for Data Quality Report
DATA_QUALITY_REPORT_SCHEMA = StructType([
    StructField("report_id",        StringType(),    False),
    StructField("run_id",           StringType(),    False),
    StructField("run_date",         DateType(),      True),
    StructField("table_name",       StringType(),    True),
    StructField("stage",            StringType(),    True),   # silver | gold
    StructField("execution_time",   TimestampType(), True),
    StructField("status",           StringType(),    True),   # SUCCESS | WARN | FAILED
    StructField("records_read",     LongType(),      True),
    StructField("records_written",  LongType(),      True),
    StructField("duplicates",       LongType(),      True),
    StructField("invalid_records",  LongType(),      True),
    StructField("quality_score",    DoubleType(),    True),
    StructField("error_message",    StringType(),    True),
    StructField("created_at",       TimestampType(), True),
])

full_dq_table = f"{config.catalog}.{OPERATIONS}.{DATA_QUALITY_REPORT}"
print(f"Initializing quality report table: {full_dq_table}...")
(
    spark.createDataFrame([], DATA_QUALITY_REPORT_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_dq_table)
)
print(f"✓ Quality report table '{full_dq_table}' ready.")

# E. Define schema for Monitoring Metrics
MONITORING_METRICS_SCHEMA = StructType([
    StructField("timestamp",      TimestampType(), False),
    StructField("pipeline_stage", StringType(),    True),
    StructField("metric_name",    StringType(),    False),
    StructField("metric_value",   DoubleType(),    False),
    StructField("unit",           StringType(),    True),
    StructField("status",         StringType(),    True),
])

full_metrics_table = f"{config.catalog}.{OPERATIONS}.{MONITORING_METRICS}"
print(f"Initializing monitoring metrics table: {full_metrics_table}...")
(
    spark.createDataFrame([], MONITORING_METRICS_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_metrics_table)
)
print(f"✓ Monitoring metrics table '{full_metrics_table}' ready.")

# F. Define schema for Health Status
HEALTH_STATUS_SCHEMA = StructType([
    StructField("component",  StringType(),    False),
    StructField("status",     StringType(),    False),
    StructField("checked_at", TimestampType(), False),
    StructField("message",    StringType(),    True),
])

full_health_table = f"{config.catalog}.{OPERATIONS}.{HEALTH_STATUS}"
print(f"Initializing health status table: {full_health_table}...")
(
    spark.createDataFrame([], HEALTH_STATUS_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_health_table)
)
print(f"✓ Health status table '{full_health_table}' ready.")

# G. Define schema for Alert Log
ALERT_LOG_SCHEMA = StructType([
    StructField("severity",   StringType(),    False),
    StructField("component",  StringType(),    False),
    StructField("alert_type", StringType(),    False),
    StructField("message",    StringType(),    True),
    StructField("timestamp",  TimestampType(), False),
    StructField("resolved",   StringType(),    True),
])

full_alert_table = f"{config.catalog}.{OPERATIONS}.{ALERT_LOG}"
print(f"Initializing alert log table: {full_alert_table}...")
(
    spark.createDataFrame([], ALERT_LOG_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_alert_table)
)
print(f"✓ Alert log table '{full_alert_table}' ready.")

# H. Define schema for Audit Log
AUDIT_LOG_SCHEMA = StructType([
    StructField("timestamp",      TimestampType(), False),
    StructField("run_id",         StringType(),    False),
    StructField("pipeline_stage", StringType(),    True),
    StructField("action",         StringType(),    False),
    StructField("status",         StringType(),    False),   # SUCCESS | WARNING | FAILED
    StructField("message",        StringType(),    True),
])

full_audit_log_table = f"{config.catalog}.{OPERATIONS}.{AUDIT_LOG}"
print(f"Initializing governance audit log table: {full_audit_log_table}...")
(
    spark.createDataFrame([], AUDIT_LOG_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_audit_log_table)
)
print(f"✓ Governance audit log table '{full_audit_log_table}' ready.")

# I. Define schema for Security Validation Log
SECURITY_VALIDATION_SCHEMA = StructType([
    StructField("validation_type", StringType(),    False),
    StructField("component",       StringType(),    False),
    StructField("result",          StringType(),    False),   # PASSED | WARNING | FAILED
    StructField("details",         StringType(),    True),
    StructField("checked_at",      TimestampType(), False),
])

full_sec_table = f"{config.catalog}.{OPERATIONS}.{SECURITY_VALIDATION}"
print(f"Initializing security validation table: {full_sec_table}...")
(
    spark.createDataFrame([], SECURITY_VALIDATION_SCHEMA)
    .write
    .format("delta")
    .mode("ignore")
    .saveAsTable(full_sec_table)
)
print(f"✓ Security validation table '{full_sec_table}' ready.")

# COMMAND ----------
print("Platform setup completed successfully for all medallion schemas, telemetry, and governance log tables!")


