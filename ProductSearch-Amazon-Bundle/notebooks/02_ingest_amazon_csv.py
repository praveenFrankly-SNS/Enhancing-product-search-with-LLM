# Databricks notebook source
# MAGIC %md
# MAGIC # 02. Ingest Amazon CSV (Bronze Ingestion)
# MAGIC Ingests `Amazon.csv` dataset into `bronze.amazon_products_raw` table with raw string types and ingest timestamp metadata.
# MAGIC Performs data profiling, column validation, and duplicate detection at the bronze level.

# COMMAND ----------
import sys
import os
import time
import json

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("csv_path", "", "Custom CSV Path (Optional)")
dbutils.widgets.text("full_refresh", "true", "Full Refresh Mode (true/false)")

catalog = dbutils.widgets.get("catalog").strip()
custom_csv = dbutils.widgets.get("csv_path").strip()
full_refresh = dbutils.widgets.get("full_refresh").strip().lower() in ["true", "yes", "1"]

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
from pyspark.sql.types import StringType
from src.ingestion.csv_reader import resolve_amazon_csv_path, read_amazon_csv
from src.shared.logger import PipelineLogger
from src.utils.validation import validate_dataframe, check_data_quality

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

try:
    csv_file_path = resolve_amazon_csv_path(dbutils, custom_csv)
    print(f"📥 Reading Amazon CSV dataset from path: {csv_file_path}")

    # ── Stage 1: Read raw CSV ──
    raw_df = read_amazon_csv(spark, csv_file_path)
    raw_count = raw_df.count()
    num_columns = len(raw_df.columns)
    print(f"📊 Raw rows read: {raw_count}")
    print(f"📊 Raw columns: {num_columns}")
    print(f"📊 Column names: {raw_df.columns}")

    # ── Stage 2: Column profiling ──
    print("\n🔬 Column profiling results:")
    profile_stats = []
    for col_name in raw_df.columns:
        null_count = raw_df.filter(F.col(col_name).isNull() | (F.trim(F.col(col_name)) == "")).count()
        non_null_count = raw_count - null_count
        null_pct = round(100.0 * null_count / max(raw_count, 1), 2)
        distinct_count = raw_df.select(col_name).distinct().count()
        profile_stats.append({
            "column": col_name,
            "non_null": non_null_count,
            "null_count": null_count,
            "null_pct": null_pct,
            "distinct_values": distinct_count,
            "sample": raw_df.select(col_name).limit(3).collect()[0][col_name] if raw_count > 0 else "N/A"
        })
        print(f"  • {col_name}: {non_null_count}/{raw_count} non-null ({null_pct}% null), {distinct_count} distinct")

    # ── Stage 3: Detect duplicate product_ids early ──
    if "product_id" in raw_df.columns or any("id" in c.lower() or "asin" in c.lower() for c in raw_df.columns):
        id_col = "product_id" if "product_id" in raw_df.columns else \
                 ("asin" if "asin" in raw_df.columns else 
                  [c for c in raw_df.columns if "id" in c.lower()][0] if [c for c in raw_df.columns if "id" in c.lower()] else None)
        if id_col:
            total = raw_df.count()
            distinct = raw_df.select(id_col).distinct().count()
            duplicates = total - distinct
            print(f"\n⚠️  Duplicate analysis on '{id_col}': {duplicates} duplicates out of {total} records")
            if duplicates > 0:
                dup_examples = (
                    raw_df.groupBy(id_col).agg(F.count("*").alias("cnt"))
                    .filter(F.col("cnt") > 1)
                    .orderBy(F.col("cnt").desc())
                    .limit(5)
                    .collect()
                )
                for row in dup_examples:
                    print(f"     '{row[id_col]}' appears {row['cnt']} times")

    # ── Stage 4: Attach ingestion metadata ──
    bronze_df = (raw_df
        .withColumn("ingested_at", F.current_timestamp())
        .withColumn("ingestion_batch_id", F.lit(f"batch_{int(time.time())}"))
        .withColumn("source_file", F.lit(os.path.basename(csv_file_path)))
    )

    # ── Stage 5: Write to Bronze Delta Table ──
    bronze_table = f"`{catalog}`.bronze.amazon_products_raw"
    write_mode = "overwrite" if full_refresh else "append"
    
    bronze_df.write \
        .mode(write_mode) \
        .option("mergeSchema", "true") \
        .format("delta") \
        .saveAsTable(bronze_table)

    # ── Stage 6: Verify write ──
    written_count = spark.table(bronze_table).count()
    
    # ── Stage 7: Run data quality check ──
    quality_result = check_data_quality(
        spark.table(bronze_table),
        table_name=bronze_table,
        pk_column="product_id" if "product_id" in bronze_df.columns else None,
        not_null_columns=["product_id", "product_name"] if all(c in bronze_df.columns for c in ["product_id", "product_name"]) else []
    )
    print(f"\n✅ Data quality score: {quality_result.get('quality_score', 1.0):.2f}")
    if quality_result.get("not_null_violations"):
        print(f"⚠️  Null violations found: {quality_result['not_null_violations']}")

    duration = time.time() - start_time
    logger.log_execution("Bronze_Ingestion", "ingest_csv", "SUCCESS", raw_count, written_count, duration)
    print(f"\n✅ Successfully wrote {written_count} products to {bronze_table}")
    print(f"⏱️  Duration: {duration:.2f}s")

except Exception as e:
    duration = time.time() - start_time
    logger.log_execution("Bronze_Ingestion", "ingest_csv", "FAILED", 0, 0, duration, str(e))
    print(f"❌ Error: {str(e)}")
    raise e