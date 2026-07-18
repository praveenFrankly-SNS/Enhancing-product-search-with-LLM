# Databricks notebook source
# MAGIC %md
# MAGIC # 02. Ingest Amazon CSV Dataset & Feature Engineering
# MAGIC Ingests `Amazon.csv` (1,465 items), cleans price and rating fields, builds the rich `search_document`, and populates `gold.amazon_product_catalog`.

# COMMAND ----------
import os
import sys
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.getOrCreate()

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("csv_path", "", "Custom CSV Path (Optional)")

catalog = dbutils.widgets.get("catalog")
custom_csv = dbutils.widgets.get("csv_path").strip()

# Locate Amazon.csv in Workspace or Volume
candidate_paths = [
    custom_csv,
    "/Workspace/Users/praveen.v.ihub@snsgroups.com/bundle/product-search/dev/dataset/V2/Amazon.csv",
    "/Workspace/Users/praveen.v.ihub@snsgroups.com/Product-Search/dataset/V2/Amazon.csv",
    "/Workspace/dataset/V2/Amazon.csv",
    "dbfs:/FileStore/Amazon.csv",
]

csv_file_path = None
for p in candidate_paths:
    if p and (os.path.exists(p) or p.startswith("dbfs:")):
        csv_file_path = p
        break

if not csv_file_path:
    # Default to current workspace relative path if available
    try:
        notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
        ws_root = "/Workspace" + notebook_path.split("/ProductSearch-Amazon-Bundle")[0]
        csv_file_path = f"{ws_root}/dataset/V2/Amazon.csv"
    except Exception:
        csv_file_path = "/Workspace/dataset/V2/Amazon.csv"

print(f"📥 Loading Amazon.csv from: {csv_file_path}")

# COMMAND ----------
# Read CSV using Spark
raw_df = (
    spark.read.option("header", "true")
    .option("quote", '"')
    .option("escape", '"')
    .csv(csv_file_path)
)

print(f"📊 Raw Rows Read: {raw_df.count()}")

# COMMAND ----------
# Clean price, rating, and rating_count fields
cleaned_df = (
    raw_df
    # Clean discounted_price (strip ₹ and commas)
    .withColumn("discounted_price", F.regexp_replace(F.col("discounted_price"), "[₹,]", "").cast("double"))
    # Clean actual_price
    .withColumn("actual_price", F.regexp_replace(F.col("actual_price"), "[₹,]", "").cast("double"))
    # Clean rating (cast to double, handle non-numeric)
    .withColumn("rating", F.regexp_replace(F.col("rating"), "[^0-9.]", "").cast("double"))
    # Clean rating_count (strip commas)
    .withColumn("rating_count", F.regexp_replace(F.col("rating_count"), "[,]", "").cast("int"))
    # Format category replacing '|' with ' > ' for standard breadcrumb readability
    .withColumn("category_formatted", F.regexp_replace(F.col("category"), "[|]", " > "))
    # Construct rich search document combining name, category, about_product, review_title, review_content
    .withColumn(
        "search_document",
        F.concat_ws(
            " | ",
            F.coalesce(F.col("product_name"), F.lit("")),
            F.concat(F.lit("Category: "), F.coalesce(F.col("category_formatted"), F.lit(""))),
            F.concat(F.lit("Description: "), F.coalesce(F.col("about_product"), F.lit(""))),
            F.concat(F.lit("Review: "), F.coalesce(F.col("review_title"), F.lit("")), F.lit(" - "), F.coalesce(F.col("review_content"), F.lit("")))
        )
    )
    .withColumn("updated_at", F.current_timestamp())
    .select(
        F.col("product_id"),
        F.col("product_name"),
        F.col("category_formatted").alias("category"),
        F.col("discounted_price"),
        F.col("actual_price"),
        F.col("discount_percentage"),
        F.col("rating"),
        F.col("rating_count"),
        F.col("about_product"),
        F.col("user_id"),
        F.col("user_name"),
        F.col("review_id"),
        F.col("review_title"),
        F.col("review_content"),
        F.col("img_link"),
        F.col("product_link"),
        F.col("search_document"),
        F.col("updated_at")
    )
)

# COMMAND ----------
# Save to Gold Table
gold_table = f"`{catalog}`.gold.amazon_product_catalog"
cleaned_df.write.mode("overwrite").format("delta").saveAsTable(gold_table)

print(f"✅ Successfully wrote {cleaned_df.count()} products to {gold_table}")
display(spark.sql(f"SELECT product_id, product_name, category, discounted_price, rating, img_link FROM {gold_table} LIMIT 5"))
