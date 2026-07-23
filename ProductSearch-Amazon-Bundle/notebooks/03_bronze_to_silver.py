# Databricks notebook source
# MAGIC %md
# MAGIC # 03. Bronze to Silver Transformation (Dynamic Column Normalization)
# MAGIC Transforms `bronze.amazon_products_raw` to `silver.amazon_products_clean`.
# MAGIC Handles changing input columns dynamically, cleans price/rating numbers, generates dynamic search documents,
# MAGIC and produces a detailed data quality report with record-level statistics.

# COMMAND ----------
import sys
import os
import time
import json

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("quality_threshold", "0.8", "Minimum quality score (0-1)")
catalog = dbutils.widgets.get("catalog").strip()
quality_threshold = float(dbutils.widgets.get("quality_threshold").strip())

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
from src.transformation.amazon_transformer import transform_raw_to_silver
from src.transformation.quality import filter_valid_products
from src.transformation.deduplication import deduplicate_products
from src.shared.logger import PipelineLogger
from src.utils.validation import check_data_quality

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
    print(f"📊 Input records: {records_in}")

    # ── Stage 1: Transform with dynamic column mapping ──
    print("\n🔧 Applying dynamic column transformation...")
    silver_df = transform_raw_to_silver(raw_df)
    print(f"📊 Transformed columns: {silver_df.columns}")

    # ── Stage 2: Price field statistics after cleaning ──
    if "discounted_price" in silver_df.columns:
        price_stats = silver_df.agg(
            F.count(F.col("discounted_price")).alias("count"),
            F.round(F.avg(F.col("discounted_price")), 2).alias("avg_price"),
            F.round(F.min(F.col("discounted_price")), 2).alias("min_price"),
            F.round(F.max(F.col("discounted_price")), 2).alias("max_price"),
            F.round(F.stddev(F.col("discounted_price")), 2).alias("std_price")
        ).collect()[0]
        print(f"\n💰 Price statistics:")
        print(f"  • Records with price: {price_stats['count']}")
        print(f"  • Avg price: ₹{price_stats['avg_price']}")
        print(f"  • Min price: ₹{price_stats['min_price']}")
        print(f"  • Max price: ₹{price_stats['max_price']}")
        print(f"  • Std dev: ₹{price_stats['std_price']}")

    # ── Stage 3: Rating distribution ──
    if "rating" in silver_df.columns:
        rating_buckets = silver_df.withColumn(
            "rating_bucket",
            F.when(F.col("rating").isNull(), F.lit("No Rating"))
             .when(F.col("rating") >= 4.5, F.lit("4.5-5.0 (Excellent)"))
             .when(F.col("rating") >= 4.0, F.lit("4.0-4.5 (Good)"))
             .when(F.col("rating") >= 3.0, F.lit("3.0-4.0 (Average)"))
             .otherwise(F.lit("Below 3.0"))
        ).groupBy("rating_bucket").agg(
            F.count("*").alias("count"),
            F.round(F.avg(F.col("discounted_price")), 2).alias("avg_price")
        ).orderBy("rating_bucket").collect()
        print(f"\n⭐ Rating distribution:")
        for row in rating_buckets:
            print(f"  • {row['rating_bucket']}: {row['count']} products, avg price ₹{row['avg_price']}")

    # ── Stage 4: Category distribution ──
    if "category" in silver_df.columns:
        top_categories = silver_df.groupBy("category").agg(
            F.count("*").alias("count")
        ).orderBy(F.col("count").desc()).limit(10).collect()
        print(f"\n📂 Top categories:")
        for i, row in enumerate(top_categories, 1):
            print(f"  {i}. {row['category']}: {row['count']} products")

    # ── Stage 5: Quality validation split ──
    print("\n🔍 Running quality validation...")
    valid_df, rejected_df = filter_valid_products(silver_df)
    rejected_count = rejected_df.count()
    valid_count = valid_df.count()
    
    if rejected_count > 0:
        rejected_df.write.mode("append").format("delta").saveAsTable(rejected_table)
        print(f"⚠️  Rejected {rejected_count} records (missing product_id or product_name)")
        # Show sample of rejected records
        rejected_samples = rejected_df.select("product_name", "product_id", "rejection_reason").limit(5).collect()
        for row in rejected_samples:
            print(f"     Rejected: id='{row['product_id']}', name='{row['product_name']}', reason={row['rejection_reason']}")

    # ── Stage 6: Deduplication ──
    print("\n🧹 Deduplicating products...")
    clean_df = deduplicate_products(valid_df, "product_id")
    records_out = clean_df.count()
    dedup_removed = valid_count - records_out
    print(f"  • Removed {dedup_removed} duplicate records")

    # ── Stage 7: Data quality assessment ──
    quality_report = check_data_quality(
        clean_df,
        table_name=silver_table,
        pk_column="product_id",
        not_null_columns=["product_id", "product_name"]
    )
    print(f"\n📋 Silver quality score: {quality_report.get('quality_score', 1.0):.2f}")
    print(f"  • Row count: {quality_report['row_count']}")
    print(f"  • Column count: {quality_report['column_count']}")
    
    # Abort if quality below threshold
    if quality_report.get("quality_score", 1.0) < quality_threshold:
        error_msg = f"Data quality score {quality_report.get('quality_score', 0):.2f} below threshold {quality_threshold}"
        logger.log_execution("Silver_Transformation", "clean_products", "FAILED", records_in, 0, time.time() - start_time, error_msg)
        raise ValueError(error_msg)

    # ── Stage 8: Save to Silver Table ──
    print(f"\n💾 Writing {records_out} clean products to {silver_table}...")
    clean_df.write \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .format("delta") \
        .saveAsTable(silver_table)

    # Verify
    final_count = spark.table(silver_table).count()
    print(f"✅ Verified {final_count} records in silver table")

    duration = time.time() - start_time
    logger.log_execution("Silver_Transformation", "clean_products", "SUCCESS", records_in, records_out, duration)
    print(f"\n✅ Transformation complete. {records_in} → {records_out} records ({round(100*records_out/max(records_in,1),1)}% survival)")
    print(f"⏱️  Duration: {duration:.2f}s")

except Exception as e:
    duration = time.time() - start_time
    logger.log_execution("Silver_Transformation", "clean_products", "FAILED", 0, 0, duration, str(e))
    print(f"❌ Error: {str(e)}")
    raise e