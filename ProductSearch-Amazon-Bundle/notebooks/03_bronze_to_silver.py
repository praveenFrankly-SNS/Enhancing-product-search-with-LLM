# Databricks notebook source
# MAGIC %md
# MAGIC # 03. Bronze to Silver Transformation (Dynamic Column Normalization)
# MAGIC Transforms `bronze.amazon_products_raw` to `silver.amazon_products_clean`.
# MAGIC Handles changing input columns dynamically, cleans price/rating numbers, and generates dynamic search documents.

# COMMAND ----------
import sys
import os
import time

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
from src.transformation.amazon_transformer import transform_raw_to_silver
from src.transformation.quality import filter_valid_products
from src.transformation.deduplication import deduplicate_products
from src.shared.logger import PipelineLogger

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

try:
    bronze_table = f"`{catalog}`.bronze.amazon_products_raw"
    silver_table = f"`{catalog}`.silver.amazon_products_clean"
    rejected_table = f"`{catalog}`.operations.rejected_records"

    print(f"📖 Reading raw Bronze data from: {bronze_table}")
    raw_df = spark.table(bronze_table)
    records_in = raw_df.count()

    # 1. Transform with dynamic column mapping and field cleaning
    silver_df = transform_raw_to_silver(raw_df)

    # 2. Quality validation split
    valid_df, rejected_df = filter_valid_products(silver_df)
    
    if rejected_df.count() > 0:
        rejected_df.write.mode("append").format("delta").saveAsTable(rejected_table)

    # 3. Deduplication
    clean_df = deduplicate_products(valid_df, "product_id")
    records_out = clean_df.count()

    # 4. Save to Silver Table
    clean_df.write.mode("overwrite").option("mergeSchema", "true").format("delta").saveAsTable(silver_table)

    duration = time.time() - start_time
    logger.log_execution("Silver_Transformation", "clean_products", "SUCCESS", records_in, records_out, duration)
    print(f"✅ Successfully wrote {records_out} cleaned products to {silver_table}")

except Exception as e:
    duration = time.time() - start_time
    logger.log_execution("Silver_Transformation", "clean_products", "FAILED", 0, 0, duration, str(e))
    raise e
