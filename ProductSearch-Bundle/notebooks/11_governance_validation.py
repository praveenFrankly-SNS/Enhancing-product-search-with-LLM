# Databricks notebook source
# MAGIC %md
# MAGIC # Enterprise Governance & Security Validation
# MAGIC **Responsibility**: Performs pre-execution/scheduled security validation checks across configs, secrets, Unity Catalog schemas, and platform dependencies. Logs validations history to audit tables and outputs a formatted status report.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import uuid
import time
from datetime import datetime, timezone
from pathlib import Path

from pyspark.sql import SparkSession
import mlflow

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
from src.shared.constants import OPERATIONS, SECURITY_VALIDATION, AUDIT_LOG
from src.shared.logger import get_logger

# Import governance package utilities
from src.governance import (
    validate_pipeline_config,
    validate_environment,
    verify_secrets_prerequisites,
    verify_catalog_prerequisites,
    record_security_validation,
    record_pipeline_audit
)
# COMMAND ----------
spark = SparkSession.builder.getOrCreate()
logger = get_logger("governance_validation")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",          "product_search_dev",          "Catalog Name")
dbutils.widgets.text("environment",      "dev",                         "Environment (dev/staging/prod)")

config = get_config(dbutils)
catalog = config.catalog
environment = config.environment
run_id = str(uuid.uuid4())

logger.info(f"Starting Enterprise Governance Validation (Run ID: {run_id}) on catalog: {catalog}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Run Governance Validation Steps
# COMMAND ----------
validation_summary = []

# A. Configuration Validation
config_val = validate_pipeline_config(config.yaml_config)
c_res = "PASSED" if config_val["valid"] else "FAILED"
c_details = "All required pipeline config fields are present." if config_val["valid"] else "; ".join(config_val["errors"])
validation_summary.append(("Configuration Validation", "Pipeline Config", c_res, c_details))

# B. Runtime Environment Validation
env_val = validate_environment(spark)
e_res = "PASSED" if env_val["valid"] else "FAILED"
e_details = f"Spark runtime version: {env_val.get('spark_version', 'Unknown')}" if env_val["valid"] else "; ".join(env_val["errors"])
validation_summary.append(("Environment Validation", "Spark Connect Runtime", e_res, e_details))

# C. Secret Scope & Required Keys Validation
governance_config = config.yaml_config.get("governance", {})
secrets_config = governance_config.get("secrets", {})
secret_scope = secrets_config.get("scope", config.yaml_config.get("pipeline", {}).get("secret_scope", ""))
required_secrets = secrets_config.get("required", [])

secrets_val = verify_secrets_prerequisites(dbutils, secret_scope, required_secrets)
s_res = "PASSED" if secrets_val["scope_exists"] and not secrets_val["missing_keys"] else "FAILED"
s_details = f"Scope '{secret_scope}' verified. Available: {len(secrets_val['available_keys'])} secrets."
if secrets_val["missing_keys"]:
    s_details += f" Missing required: {', '.join(secrets_val['missing_keys'])}"
if secrets_val["errors"] and not secrets_val["scope_exists"]:
    s_details = secrets_val["errors"][0]
validation_summary.append(("Secrets Validation", f"Secret Scope: {secret_scope}", s_res, s_details))

# D. Unity Catalog Schemas and Read/Write Permissions Validation
catalog_val = verify_catalog_prerequisites(spark, catalog)
cat_res = "PASSED" if catalog_val["catalog_exists"] and not catalog_val["errors"] else "FAILED"
cat_details = f"Catalog '{catalog}' active. All schemas and required tables permissions validated successfully."
if catalog_val["errors"]:
    cat_details = "; ".join(catalog_val["errors"])
validation_summary.append(("Unity Catalog Validation", f"UC Catalog: {catalog}", cat_res, cat_details))

# E. Dependency Validation (MLflow & Vector Search checks)
# MLflow experiment accessibility check
mlflow_cfg = config.yaml_config.get("mlflow", {})
if mlflow_cfg.get("enabled", True):
    exp_path = mlflow_cfg.get("experiment_path", "/Shared/Product_Search_ML")
    try:
        # Pre-set tracking URIs to bypass connect lookup errors
        mlflow.set_tracking_uri("databricks")
        mlflow.set_registry_uri("databricks-uc")
        
        active_exp = mlflow.get_experiment_by_name(exp_path)
        mlflow_res = "PASSED"
        mlflow_details = f"MLflow Experiment '{exp_path}' is accessible."
    except Exception as e:
        mlflow_res = "WARNING"
        mlflow_details = f"MLflow Experiment '{exp_path}' inaccessible. Detail: {str(e)}"
    validation_summary.append(("Dependency Validation", "MLflow Service", mlflow_res, mlflow_details))

# Vector Search index existence check (if evaluation is enabled)
eval_cfg = config.yaml_config.get("evaluation", {})
if eval_cfg.get("enabled", True):
    index_name = f"{catalog}.gold.product_search_catalog_index"
    try:
        index_exists = spark.catalog.tableExists(index_name)
        vs_res = "PASSED" if index_exists else "FAILED"
        vs_details = f"Vector Search Delta Sync Index '{index_name}' exists." if index_exists else f"Index '{index_name}' is missing."
    except Exception as e:
        vs_res = "FAILED"
        vs_details = f"Vector Search Index access error. Detail: {str(e)}"
    validation_summary.append(("Dependency Validation", "Vector Search Index", vs_res, vs_details))
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Write Security Validation Logs to Operations
# COMMAND ----------
# Record validation checks to Operations Security Validation log table
for val_type, component, result, details in validation_summary:
    record_security_validation(spark, catalog, val_type, component, result, details)

# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Health Summary Status Report & Audit Log
# COMMAND ----------
print("=" * 110)
print("                           ENTERPRISE GOVERNANCE & SECURITY HEALTH REPORT")
print("=" * 110)
print(f"{'Validation Type':<30} | {'Component':<35} | {'Result':<10} | {'Details'}")
print("-" * 110)
for val_type, component, result, details in validation_summary:
    # Truncate details if too long for display
    disp_details = details[:40] + "..." if len(details) > 40 else details
    print(f"{val_type:<30} | {component:<35} | {result:<10} | {disp_details}")
print("=" * 110)

# Determine final execution status
has_failed = any(r[2] == "FAILED" for r in validation_summary)
final_status = "FAILED" if has_failed else "SUCCESS"
final_msg = "Enterprise governance prerequisites validation completed successfully." if not has_failed else "One or more governance checks failed."

record_pipeline_audit(spark, catalog, run_id, "Governance", "governance_run_audit", final_status, final_msg)

if has_failed:
    logger.error("CRITICAL governance verification failed! Check details in operations.security_validation.")
    raise RuntimeError("Governance validation check failed. Halting execution pipeline.")
else:
    logger.success("All enterprise governance prerequisites verified successfully.")
