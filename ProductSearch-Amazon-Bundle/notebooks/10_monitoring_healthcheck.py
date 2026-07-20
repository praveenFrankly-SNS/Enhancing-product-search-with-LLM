# Databricks notebook source
# MAGIC %md
# MAGIC # 10. Monitoring & Healthcheck
# MAGIC Audits health across `bronze`, `silver`, `gold`, and `operations` tables.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
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
from src.monitoring.health import check_table_health

spark = SparkSession.builder.getOrCreate()

tables_to_check = [
    ("bronze", "amazon_products_raw"),
    ("silver", "amazon_products_clean"),
    ("gold", "amazon_product_catalog"),
    ("operations", "pipeline_execution_log")
]

print(f"🏥 SYSTEM HEALTH REPORT FOR CATALOG: '{catalog}'")
print("=" * 60)
for schema, tbl in tables_to_check:
    res = check_table_health(spark, catalog, schema, tbl)
    status_icon = "✅" if res["status"] == "HEALTHY" else "❌"
    print(f"{status_icon} {schema}.{tbl:<25} Status: {res['status']:<10} Records: {res['record_count']:<8} Cols: {res['column_count']}")
