# Databricks notebook source
# MAGIC %md
# MAGIC # 04. Feature Engineering (Gold Product Catalog)
# MAGIC Builds `gold.amazon_product_catalog` table from clean Silver data.
# MAGIC Enriches features with price tiers, rating buckets, search document metadata,
# MAGIC discount analysis, and price-to-rating relationship features.

# COMMAND ----------
import sys
import os
import time
import json

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
from src.feature_engineering.amazon_features import build_amazon_gold_catalog
from src.shared.logger import PipelineLogger
from src.utils.spark import enable_change_data_feed
from src.utils.validation import check_data_quality

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

try:
    silver_table = f"`{catalog}`.silver.amazon_products_clean"
    gold_table = f"`{catalog}`.gold.amazon_product_catalog"

    print(f"📖 Reading Silver dataset from: {silver_table}")
    silver_df = spark.table(silver_table)
    records_in = silver_df.count()
    print(f"📊 Input records: {records_in}")

    # ── Stage 1: Generate Gold Catalog features ──
    print("\n🔧 Building Gold catalog features...")
    gold_df = build_amazon_gold_catalog(silver_df)
    records_out = gold_df.count()

    # ── Stage 2: Feature distribution analysis ──
    print("\n📊 Feature distribution analysis:")

    # Price tier distribution
    if "price_tier" in gold_df.columns:
        price_tiers = gold_df.groupBy("price_tier").agg(
            F.count("*").alias("count"),
            F.round(F.avg(F.col("discounted_price")), 2).alias("avg_price")
        ).orderBy("price_tier").collect()
        print(f"\n💰 Price tier distribution:")
        for row in price_tiers:
            pct = round(100.0 * row["count"] / records_out, 1)
            print(f"  • {row['price_tier']}: {row['count']} ({pct}%), avg price ₹{row['avg_price']}")

    # Rating tier distribution
    if "rating_tier" in gold_df.columns:
        rating_tiers = gold_df.groupBy("rating_tier").agg(
            F.count("*").alias("count")
        ).orderBy("rating_tier").collect()
        print(f"\n⭐ Rating tier distribution:")
        for row in rating_tiers:
            pct = round(100.0 * row["count"] / records_out, 1)
            print(f"  • {row['rating_tier']}: {row['count']} ({pct}%)")

    # Discount analysis
    if "discount_percentage" in gold_df.columns:
        discount_stats = gold_df.agg(
            F.count(F.col("discount_percentage")).alias("with_discount"),
            F.avg(F.col("discount_percentage").cast("double")).alias("avg_discount_pct"),
            F.min(F.col("discount_percentage").cast("double")).alias("min_discount"),
            F.max(F.col("discount_percentage").cast("double")).alias("max_discount")
        ).collect()[0]
        print(f"\n🏷️ Discount analysis:")
        print(f"  • Products with discount info: {discount_stats['with_discount']}")
        print(f"  • Avg discount: {round(discount_stats['avg_discount_pct'] or 0, 1)}%")
        print(f"  • Discount range: {discount_stats['min_discount'] or 0}% - {discount_stats['max_discount'] or 0}%")

        # High discount products
        high_discount = gold_df.filter(
            F.col("discount_percentage").cast("double") > 50
        ).count()
        print(f"  • Products with >50% discount: {high_discount}")

    # Search document length analysis
    if "search_doc_length" in gold_df.columns:
        doc_stats = gold_df.agg(
            F.avg(F.col("search_doc_length")).alias("avg_doc_length"),
            F.min(F.col("search_doc_length")).alias("min_doc_length"),
            F.max(F.col("search_doc_length")).alias("max_doc_length")
        ).collect()[0]
        print(f"\n📝 Search document length:")
        print(f"  • Avg length: {round(doc_stats['avg_doc_length'] or 0, 0)} chars")
        print(f"  • Min: {doc_stats['min_doc_length'] or 0}, Max: {doc_stats['max_doc_length'] or 0}")

    # ── Stage 3: Price vs Rating correlation ──
    if all(c in gold_df.columns for c in ["discounted_price", "rating"]):
        price_rating = gold_df.filter(
            F.col("discounted_price").isNotNull() & F.col("rating").isNotNull()
        ).select(
            F.corr("discounted_price", "rating").alias("price_rating_corr")
        ).collect()[0]["price_rating_corr"]
        print(f"\n📈 Price-Rating correlation: {round(price_rating or 0, 4)}")

    # ── Stage 4: Write to Gold Delta Table ──
    print(f"\n💾 Writing {records_out} records to Gold table: {gold_table}")
    gold_df.write \
        .mode("overwrite") \
        .option("mergeSchema", "true") \
        .option("delta.enableChangeDataFeed", "true") \
        .format("delta") \
        .saveAsTable(gold_table)

    # ── Stage 5: Enable Change Data Feed for Vector Search sync ──
    cdf_enabled = enable_change_data_feed(spark, gold_table)
    if cdf_enabled:
        print("✅ Change Data Feed enabled for Vector Search auto-sync")
    else:
        print("⚠️  CDF may already be enabled")

    # ── Stage 6: Quality check ──
    quality = check_data_quality(
        spark.table(gold_table),
        table_name=gold_table,
        pk_column="product_id",
        not_null_columns=["product_id", "product_name", "price_tier", "rating_tier"]
    )
    print(f"\n✅ Gold table quality score: {quality.get('quality_score', 1.0):.2f}")

    duration = time.time() - start_time
    logger.log_execution("Gold_Feature_Engineering", "build_gold_catalog", "SUCCESS", records_in, records_out, duration)
    print(f"\n✅ Gold catalog built: {records_out} products, {len(gold_df.columns)} feature columns")
    print(f"⏱️  Duration: {duration:.2f}s")
    
    # Show sample
    display(spark.sql(f"SELECT product_id, product_name, discounted_price, price_tier, rating_tier FROM {gold_table} LIMIT 10"))

except Exception as e:
    duration = time.time() - start_time
    logger.log_execution("Gold_Feature_Engineering", "build_gold_catalog", "FAILED", 0, 0, duration, str(e))
    print(f"❌ Error: {str(e)}")
    raise e