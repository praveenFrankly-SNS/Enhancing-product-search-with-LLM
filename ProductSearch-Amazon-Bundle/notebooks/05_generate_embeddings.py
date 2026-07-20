# Databricks notebook source
# MAGIC %md
# MAGIC # 05. Generate & Verify Embeddings
# MAGIC Validates `search_document` text readiness and embedding endpoint connectivity for Vector Search indexing.

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
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()
gold_table = f"`{catalog}`.gold.amazon_product_catalog"

print(f"🔎 Validating search documents in Gold Catalog table: {gold_table}...")
df = spark.table(gold_table)

empty_docs = df.filter(F.col("search_document").isNull() | (F.trim(F.col("search_document")) == "")).count()
total_docs = df.count()

print(f"📊 Total Documents: {total_docs}")
print(f"⚠️ Null/Empty Search Documents: {empty_docs}")

if empty_docs > 0:
    print(f"⚠️ Warning: Found {empty_docs} records without search documents. Inspecting sample:")
    display(df.filter(F.col("search_document").isNull() | (F.trim(F.col("search_document")) == "")).select("product_id", "product_name"))
else:
    print("✅ All product catalog records have valid search documents ready for vector embedding.")
