# Databricks notebook source
# MAGIC %md
# MAGIC # 01. Setup Platform — Amazon Product Search Accelerator
# MAGIC Provisions Unity Catalog catalog, schemas (`bronze`, `silver`, `gold`, `operations`), and operational logging tables.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment")

catalog = dbutils.widgets.get("catalog").strip()

def resolve_and_add_root():
    try:
        ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        nb_path = ctx.notebookPath().get()
        full_ws_path = nb_path if nb_path.startswith("/Workspace") else f"/Workspace{nb_path}"
        if "/notebooks" in full_ws_path:
            base_dir = full_ws_path.split("/notebooks")[0]
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
    except Exception:
        pass

resolve_and_add_root()

from pyspark.sql import SparkSession
from src.governance.catalog import ensure_catalog_and_schemas
from src.shared.logger import EXEC_LOG_SCHEMA

spark = SparkSession.builder.getOrCreate()

print(f"⚙️ Initializing platform assets for catalog: '{catalog}'...")
ensure_catalog_and_schemas(spark, catalog)

# Create operational logging table
ops_table = f"`{catalog}`.operations.pipeline_execution_log"
spark.createDataFrame([], schema=EXEC_LOG_SCHEMA).write.mode("ignore").format("delta").saveAsTable(ops_table)
print(f"✅ Verified operational logging table: {ops_table}")

# Create rejected records table
rejected_table = f"`{catalog}`.operations.rejected_records"
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {rejected_table} (
        product_id STRING,
        product_name STRING,
        rejection_reason STRING,
        rejected_at TIMESTAMP
    ) USING DELTA
""")
print(f"✅ Verified rejected records table: {rejected_table}")

print("🎉 Platform setup completed successfully.")
