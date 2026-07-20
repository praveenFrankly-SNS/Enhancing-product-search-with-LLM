# Databricks notebook source
# MAGIC %md
# MAGIC # 02. Ingest Amazon CSV (Bronze Ingestion)
# MAGIC Ingests `Amazon.csv` dataset into `bronze.amazon_products_raw` table with raw string types and ingest timestamp metadata.

# COMMAND ----------
import sys
import os
import time

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("csv_path", "", "Custom CSV Path (Optional)")

catalog = dbutils.widgets.get("catalog").strip()
custom_csv = dbutils.widgets.get("csv_path").strip()

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
from src.ingestion.csv_reader import resolve_amazon_csv_path, read_amazon_csv
from src.shared.logger import PipelineLogger

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

try:
    csv_file_path = resolve_amazon_csv_path(dbutils, custom_csv)
    print(f"📥 Reading Amazon CSV dataset from path: {csv_file_path}")

    raw_df = read_amazon_csv(spark, csv_file_path)
    raw_count = raw_df.count()
    print(f"📊 Raw Rows Read: {raw_count}")

    # Add ingestion metadata
    bronze_df = raw_df.withColumn("ingested_at", F.current_timestamp())

    # Write to Bronze Delta Table with mergeSchema support
    bronze_table = f"`{catalog}`.bronze.amazon_products_raw"
    bronze_df.write.mode("overwrite").option("mergeSchema", "true").format("delta").saveAsTable(bronze_table)

    duration = time.time() - start_time
    logger.log_execution("Bronze_Ingestion", "ingest_csv", "SUCCESS", raw_count, raw_count, duration)
    print(f"✅ Successfully wrote {raw_count} products to {bronze_table}")

except Exception as e:
    duration = time.time() - start_time
    logger.log_execution("Bronze_Ingestion", "ingest_csv", "FAILED", 0, 0, duration, str(e))
    raise e
