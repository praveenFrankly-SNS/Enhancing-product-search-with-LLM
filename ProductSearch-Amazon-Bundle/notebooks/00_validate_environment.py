# Databricks notebook source
# MAGIC %md
# MAGIC # 00. Environment Validation (Amazon Dataset Variant)
# MAGIC Checks Unity Catalog access, active compute cluster runtime, and dependencies.

# COMMAND ----------
# MAGIC %pip install pyyaml databricks-vectorsearch
# COMMAND ----------
import sys
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment", "dev", "Environment Target")

catalog = dbutils.widgets.get("catalog")
env = dbutils.widgets.get("environment")

print(f"✅ Spark Session initialized: {spark.version}")
print(f"✅ Target Catalog: {catalog}")
print(f"✅ Target Environment: {env}")

# Validate Unity Catalog
spark.sql(f"CREATE CATALOG IF NOT EXISTS `{catalog}`")
spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{catalog}`.gold")
print(f"✅ Unity Catalog Schema Verified: {catalog}.gold")
