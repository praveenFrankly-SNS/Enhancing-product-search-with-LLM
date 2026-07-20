# Databricks notebook source
# MAGIC %md
# MAGIC # 04. Feature Engineering (Gold Product Catalog)
# MAGIC Builds `gold.amazon_product_catalog` table from clean Silver data.
# MAGIC Enriches features with price tiers, rating buckets, and search document metadata.

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
from src.feature_engineering.amazon_features import build_amazon_gold_catalog
from src.shared.logger import PipelineLogger

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

try:
    silver_table = f"`{catalog}`.silver.amazon_products_clean"
    gold_table = f"`{catalog}`.gold.amazon_product_catalog"

    print(f"📖 Reading Silver dataset from: {silver_table}")
    silver_df = spark.table(silver_table)
    records_in = silver_df.count()

    # Generate Gold Catalog features
    gold_df = build_amazon_gold_catalog(silver_df)
    records_out = gold_df.count()

    # Write to Gold Delta Table with Change Data Feed enabled for Vector Search
    gold_df.write \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .option("delta.enableChangeDataFeed", "true") \
        .format("delta") \
        .saveAsTable(gold_table)

    duration = time.time() - start_time
    logger.log_execution("Gold_Feature_Engineering", "build_gold_catalog", "SUCCESS", records_in, records_out, duration)
    print(f"✅ Successfully written {records_out} products to Gold Catalog table: {gold_table}")
    display(spark.sql(f"SELECT product_id, product_name, category, discounted_price, price_tier, rating_tier FROM {gold_table} LIMIT 5"))

except Exception as e:
    duration = time.time() - start_time
    logger.log_execution("Gold_Feature_Engineering", "build_gold_catalog", "FAILED", 0, 0, duration, str(e))
    raise e
