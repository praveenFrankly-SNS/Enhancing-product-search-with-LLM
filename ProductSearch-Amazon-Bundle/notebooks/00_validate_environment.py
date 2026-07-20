# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Validate Environment — Amazon Product Search Accelerator
# MAGIC Validates cluster setup, Python packages, project root pathing, and PySpark session.

# COMMAND ----------
import sys
import os

# Add project root to sys.path
def resolve_and_add_root():
    try:
        ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        nb_path = ctx.notebookPath().get()
        full_ws_path = nb_path if nb_path.startswith("/Workspace") else f"/Workspace{nb_path}"
        if "/notebooks" in full_ws_path:
            base_dir = full_ws_path.split("/notebooks")[0]
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
                print(f"✅ Added project root: {base_dir}")
    except Exception as e:
        print(f"Notice setting root path: {e}")

resolve_and_add_root()

# COMMAND ----------
from pyspark.sql import SparkSession
spark = SparkSession.builder.getOrCreate()
print(f"⚡ Spark Version: {spark.version}")
print(f"🐍 Python Version: {sys.version.split()[0]}")

# Test imports from src
try:
    from src.shared.config import get_config
    from src.shared.utils.schema_utils import COLUMN_ALIASES
    print(f"✅ Successfully loaded Amazon Product Search source package ('src').")
    print(f"  └─ Configured dynamic column aliases for {len(COLUMN_ALIASES)} fields.")
except Exception as e:
    print(f"❌ Error loading src module: {e}")

print("🎉 Environment Validation Complete.")
