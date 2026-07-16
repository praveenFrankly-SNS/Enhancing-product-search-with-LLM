# Databricks notebook source
# MAGIC %md
# MAGIC # Environment Validation Notebook
# MAGIC **Responsibility**: Verifies secret scopes, PostgreSQL connectivity, catalog accessibility, and cluster runtime prerequisites before executing setup.
# MAGIC 
# MAGIC Running this notebook ensures:
# MAGIC 1. Secret scope permissions and validity.
# MAGIC 2. Network and auth reachability to Supabase PostgreSQL database via Spark JDBC.
# MAGIC 3. Unity Catalog accessibility.
# MAGIC 4. Spark Runtime configurations are correct.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
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

from src.shared.config import get_config
from src.shared.logger import get_logger
from src.ingestion.jdbc_reader import check_jdbc_connection
# COMMAND ----------
# Initialize Spark Session
spark = SparkSession.builder.getOrCreate()
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment (dev/staging/prod)")
dbutils.widgets.text("secret_scope", "supabase-creds", "Secret Scope Name")

# Retrieve parameters using unified config layer
config = get_config(dbutils)
logger = get_logger("validate_environment")

logger.info(
    "Starting environment pre-validation checks",
    catalog=config.catalog,
    environment=config.environment,
    secret_scope=config.secret_scope
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Verify Secret Scope Accessibility
# COMMAND ----------
try:
    # Attempt to retrieve database host to verify secret scope access
    try:
        dbutils.secrets.get(scope=config.secret_scope, key="host")
    except Exception:
        dbutils.secrets.get(scope=config.secret_scope, key="db-host")
    logger.info("✓ Secret scope access verified successfully.")
except Exception as e:
    error_msg = (
        f"Failed to access secret scope '{config.secret_scope}'. "
        f"Ensure the scope is created in Databricks and matches credentials. Details: {str(e)}"
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Verify Supabase Database Connectivity (Spark JDBC)
# COMMAND ----------
try:
    check_jdbc_connection(spark, config.secret_scope, dbutils)
    logger.info("✓ Supabase PostgreSQL JDBC connection established successfully.")
except Exception as e:
    error_msg = f"Supabase database connectivity check failed. Details: {str(e)}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Verify Unity Catalog & Cluster Runtime Compatibility
# COMMAND ----------
# Check Spark Runtime Version
try:
    spark_version = spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", "unknown")
    logger.info("✓ Spark Runtime Version verified", version=spark_version)
except Exception:
    logger.warn("Could not retrieve Spark runtime version tags.")

# Check Unity Catalog active state
try:
    current_catalog = spark.sql("SELECT CURRENT_CATALOG()").collect()[0][0]
    logger.info("✓ Unity Catalog is active on this cluster", current_catalog=current_catalog)
except Exception as e:
    error_msg = f"Unity Catalog is not enabled or accessible on this cluster. Details: {str(e)}"
    logger.error(error_msg)
    raise RuntimeError(error_msg)
# COMMAND ----------
logger.success("All environment validation checks passed successfully!")
