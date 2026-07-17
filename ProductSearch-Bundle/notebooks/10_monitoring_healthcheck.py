# Databricks notebook source
# MAGIC %md
# MAGIC # Centralized Monitoring Health Check
# MAGIC **Responsibility**: Periodically runs health audits on Unity Catalog schemas, secret scopes, Vector Search endpoints, and model serving endpoints. Evaluates operational metrics thresholds and writes status logs and alerts to Operations tables.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, TimestampType

# Add project root to sys.path for package imports
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
from src.shared.constants import OPERATIONS, HEALTH_STATUS, MONITORING_METRICS, EXECUTION_LOG
from src.shared.logger import get_logger

# Import health check functions
from src.monitoring.health import (
    check_unity_catalog,
    check_secret_scope,
    check_vector_search_endpoint,
    check_embedding_endpoint
)
from src.monitoring.alerts import check_and_log_alert, evaluate_metric_thresholds

# Import governance package utilities
from src.governance import (
    validate_pipeline_config,
    verify_secrets_prerequisites,
    verify_catalog_prerequisites,
    record_pipeline_audit
)

# COMMAND ----------
spark = SparkSession.builder.getOrCreate()
logger = get_logger("monitoring_healthcheck")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",          "product_search_dev",          "Catalog Name")
dbutils.widgets.text("environment",      "dev",                         "Environment (dev/staging/prod)")
dbutils.widgets.text("secret_scope",     "supabase-creds",              "Secret Scope")
dbutils.widgets.text("endpoint_name",    "product_search_ep",           "Vector Search Endpoint")
dbutils.widgets.text("embedding_model",  "databricks-bge-large-en",     "Embedding Serving Endpoint")

config = get_config(dbutils)
catalog = config.catalog
secret_scope = dbutils.widgets.get("secret_scope")
endpoint_name = dbutils.widgets.get("endpoint_name")
embedding_model = dbutils.widgets.get("embedding_model")
run_id = str(uuid.uuid4())

# ── Enterprise Governance pre-execution validation checks ──────────────
# 1. Run config validation
config_check = validate_pipeline_config(config.yaml_config)
if not config_check["valid"]:
    raise RuntimeError(f"Governance Configuration check failed: {'; '.join(config_check['errors'])}")

# 2. Run secrets validation (this stage does not require database connection secrets)
governance_cfg = config.yaml_config.get("governance", {})
secrets_cfg = governance_cfg.get("secrets", {})
required_secrets = []
secrets_check = verify_secrets_prerequisites(dbutils, secret_scope, required_secrets)
if not secrets_check["scope_exists"] or secrets_check["missing_keys"]:
    raise RuntimeError(f"Governance Secrets check failed in scope '{secret_scope}': {'; '.join(secrets_check['errors'])}")


# 3. Run catalog validation
catalog_check = verify_catalog_prerequisites(spark, catalog)
if not catalog_check["catalog_exists"] or catalog_check["errors"]:
    raise RuntimeError(f"Governance Catalog check failed on '{catalog}': {'; '.join(catalog_check['errors'])}")

# 4. Log successful validation
record_pipeline_audit(spark, catalog, run_id, "Monitoring", "pre_execution_governance_validation", "SUCCESS", "All governance prerequisites verified successfully.")

# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Run Workspace Component Health Checks
# COMMAND ----------
health_results = []

# A. Unity Catalog & Medallion Schemas Check
uc_status, uc_msg = check_unity_catalog(spark, catalog)
health_results.append(("Unity Catalog", uc_status, uc_msg))

# B. Secret Scope Availability Check
secrets_status, secrets_msg = check_secret_scope(dbutils, secret_scope)
health_results.append(("Secret Scope", secrets_status, secrets_msg))

# C. Vector Search Endpoint Status Check
vs_status, vs_msg = check_vector_search_endpoint(endpoint_name)
health_results.append(("Vector Search", vs_status, vs_msg))

# D. Embedding Model Serving Endpoint Availability Check
embed_status, embed_msg = check_embedding_endpoint(embedding_model)
health_results.append(("Embedding Service", embed_status, embed_msg))
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Write Component Health Status to Operations
# COMMAND ----------
now = datetime.now(timezone.utc)
HEALTH_SCHEMA = StructType([
    StructField("component",  StringType(),    False),
    StructField("status",     StringType(),    False),
    StructField("checked_at", TimestampType(), False),
    StructField("message",    StringType(),    True),
])

health_rows = [(r[0], r[1], now, r[2]) for r in health_results]
health_df = spark.createDataFrame(health_rows, HEALTH_SCHEMA)

target_health_table = f"{catalog}.{OPERATIONS}.{HEALTH_STATUS}"
try:
    health_df.write.format("delta").mode("append").saveAsTable(target_health_table)
    logger.info(f"Successfully recorded component statuses in operations log.")
except Exception as e:
    logger.warn(f"Failed to write health log to database. Error: {str(e)}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Evaluate Thresholds and Trigger Alerts
# COMMAND ----------
monitoring_config = config.yaml_config.get("monitoring", {})
alert_thresholds = monitoring_config.get("alert_thresholds", {})

# A. Evaluate health alert logs
for component, status, message in health_results:
    if status == "Critical":
        check_and_log_alert(spark, catalog, "CRITICAL", component, "service_unreachable", message)
    elif status == "Warning":
        check_and_log_alert(spark, catalog, "WARNING", component, "service_degraded", message)

# B. Evaluate pipeline failures alert threshold
try:
    failures_df = spark.table(f"{catalog}.{OPERATIONS}.{EXECUTION_LOG}").filter(F.col("status") == "FAILED")
    failures_count = failures_df.count()
    
    thresholds = alert_thresholds.get("pipeline_failure_rate", {})
    warning_t = thresholds.get("warning", 2)
    critical_t = thresholds.get("critical", 5)
    
    if failures_count >= critical_t:
        msg = f"Accumulated {failures_count} pipeline failures. Breached CRITICAL threshold ({critical_t})."
        check_and_log_alert(spark, catalog, "CRITICAL", "Data Pipeline", "pipeline_failures_exceeded", msg)
    elif failures_count >= warning_t:
        msg = f"Accumulated {failures_count} pipeline failures. Breached WARNING threshold ({warning_t})."
        check_and_log_alert(spark, catalog, "WARNING", "Data Pipeline", "pipeline_failures_exceeded", msg)
except Exception as e:
    logger.warn(f"Could not audit pipeline failure counts. Detail: {str(e)}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 4. Health Summary Status Report
# MAGIC 
# MAGIC Display conformed status mapping.
# COMMAND ----------
print("=" * 70)
print("                    CENTRALIZED HEALTH STATUS REPORT")
print("=" * 70)
print(f"{'Component':<20} | {'Status':<10} | {'Message'}")
print("-" * 70)
for component, status, message in health_results:
    print(f"{component:<20} | {status:<10} | {message}")
print("=" * 70)

# Determine final status code
status_hierarchy = {"Critical": 3, "Warning": 2, "Healthy": 1}
max_severity = max(status_hierarchy.get(r[1], 1) for r in health_results)
final_status = "Healthy"
if max_severity == 3:
    final_status = "Critical"
elif max_severity == 2:
    final_status = "Warning"

if final_status == "Healthy":
    record_pipeline_audit(spark, catalog, run_id, "Monitoring", "monitoring_healthcheck_pipeline", "SUCCESS", "Observability health check completed. All components healthy.")
    logger.success("All systems healthy. Product Search observability framework active.")
elif final_status == "Warning":
    record_pipeline_audit(spark, catalog, run_id, "Monitoring", "monitoring_healthcheck_pipeline", "SUCCESS", "Observability health check completed. Some components have warnings.")
    logger.warn("Some workspace services have warnings. Check operations.alert_log.")
else:
    record_pipeline_audit(spark, catalog, run_id, "Monitoring", "monitoring_healthcheck_pipeline", "FAILED", "CRITICAL operational health check validation failed!")
    logger.error("CRITICAL operational check failed! Check database logs immediately.")

