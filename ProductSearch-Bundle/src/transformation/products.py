# =====================================================================
# Product Search — Ingestion: Products Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_products(df: DataFrame) -> DataFrame:
    """
    Standardizes categories, handles nulls, and normalizes product names/descriptions.
    """
    # 1. Fill missing values according to cleaning rules (Table 3.1)
    df_filled = df.withColumn(
        "product_name", F.coalesce(F.trim(F.col("product_name")), F.lit(""))
    ).withColumn(
        "product_description", 
        F.coalesce(F.col("product_description"), F.col("product_name"))
    ).withColumn(
        "product_features", F.coalesce(F.col("product_features"), F.lit(""))
    ).withColumn(
        "rating_count", F.coalesce(F.col("rating_count").cast("long"), F.lit(0))
    ).withColumn(
        "average_rating", 
        F.when(F.col("rating_count") > 0, F.col("average_rating").cast("double")).otherwise(F.lit(None))
    ).withColumn(
        "review_count", F.coalesce(F.col("review_count").cast("long"), F.lit(0))
    ).withColumn(
        "category_hierarchy", 
        F.when(F.trim(F.col("category_hierarchy")) != "", F.col("category_hierarchy")).otherwise(F.lit("Unknown"))
    ).withColumn(
        "product_class", 
        F.when(F.trim(F.col("product_class")) != "", F.col("product_class")).otherwise(F.lit("Unknown"))
    )

    # 2. Extract explicit parent-child levels from category path hierarchy
    split_col = F.split(F.col("category_hierarchy"), "\\s+/\\s+")
    df_levels = df_filled.withColumn(
        "level_1", F.coalesce(split_col.getItem(0), F.lit("Unknown"))
    ).withColumn(
        "level_2", F.coalesce(split_col.getItem(1), F.lit("Unknown"))
    ).withColumn(
        "level_3", F.coalesce(split_col.getItem(2), F.lit("Unknown"))
    )

    # 3. Clean spacing and decode basic HTML entities
    def clean_text_expr(col_name):
        c = F.col(col_name)
        c = F.regexp_replace(c, "&amp;", "&")
        c = F.regexp_replace(c, "&quot;", "\"")
        c = F.regexp_replace(c, "&apos;", "'")
        c = F.regexp_replace(c, "&lt;", "<")
        c = F.regexp_replace(c, "&gt;", ">")
        c = F.regexp_replace(c, "\\s+", " ")
        return F.trim(c)

    df_normalized = df_levels.withColumn(
        "normalized_name", clean_text_expr("product_name")
    ).withColumn(
        "normalized_description", clean_text_expr("product_description")
    )
    
    return df_normalized

def validate_products(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates product data quality bounds (ID/name existence and rating constraints).
    """
    violations = []
    
    # 1. Deduplicate
    df_dedup, duplicate_count = remove_duplicates(df, ["product_id"])
    
    # 2. Validate product_id key
    null_filter = F.col("product_id").isNull() | (F.trim(F.col("product_id")) == "")
    invalid_nulls = df_dedup.filter(null_filter)
    valid_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product",
                "rule_name": "null_product_id",
                "violation_reason": "product_id is null or empty",
                "record_key": "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Validate product_name presence
    empty_name_filter = F.col("product_name").isNull() | (F.trim(F.col("product_name")) == "")
    invalid_names = valid_df.filter(empty_name_filter)
    current_df = valid_df.filter(~empty_name_filter)
    
    name_cnt = invalid_names.count()
    if name_cnt > 0:
        for row in invalid_names.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product",
                "rule_name": "empty_product_name",
                "violation_reason": "product_name is null or empty",
                "record_key": str(row["product_id"]),
                "created_at": datetime.now(timezone.utc)
            })

    # 4. Audit ratings range
    rating_filter = (F.col("rating_count") < 0) | (F.col("average_rating") < 0) | (F.col("average_rating") > 5)
    invalid_ratings = current_df.filter(rating_filter)
    current_df = current_df.filter(~rating_filter)
    
    rating_cnt = invalid_ratings.count()
    if rating_cnt > 0:
        for row in invalid_ratings.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product",
                "rule_name": "invalid_ratings_bounds",
                "violation_reason": f"average_rating ({row['average_rating']}) or rating_count ({row['rating_count']}) out of valid bounds",
                "record_key": str(row["product_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
