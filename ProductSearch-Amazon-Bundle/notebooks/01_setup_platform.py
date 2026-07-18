# Databricks notebook source
# MAGIC %md
# MAGIC # 01. Platform & Table Setup (Amazon Dataset Variant)
# MAGIC Creates the Gold Delta Table schema for `product_search_dev.gold.amazon_product_catalog`.

# COMMAND ----------
import sys
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
catalog = dbutils.widgets.get("catalog")

table_name = f"`{catalog}`.gold.amazon_product_catalog"

# COMMAND ----------
print(f"Creating Gold Table for Amazon Dataset: {table_name}")

create_sql = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
    product_id STRING NOT NULL,
    product_name STRING,
    category STRING,
    discounted_price DOUBLE,
    actual_price DOUBLE,
    discount_percentage STRING,
    rating DOUBLE,
    rating_count INT,
    about_product STRING,
    user_id STRING,
    user_name STRING,
    review_id STRING,
    review_title STRING,
    review_content STRING,
    img_link STRING,
    product_link STRING,
    search_document STRING,
    updated_at TIMESTAMP
)
USING DELTA
TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.minReaderVersion' = '1',
    'delta.minWriterVersion' = '2'
)
"""

spark.sql(create_sql)
print(f"✅ Successfully initialized table: {table_name}")
