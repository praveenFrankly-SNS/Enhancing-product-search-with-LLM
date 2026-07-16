# =====================================================================
# Product Search — Ingestion: Pricing Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_pricing(df: DataFrame) -> DataFrame:
    """
    Standardizes currency and buckets.
    """
    return df.withColumn(
        "currency", F.coalesce(F.trim(F.col("currency")), F.lit("INR"))
    ).withColumn(
        "price_bucket", F.coalesce(F.trim(F.col("price_bucket")), F.lit("Mid-range"))
    )

def validate_pricing(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates logical bounds, duplicates, and keys.
    """
    violations = []
    
    # 1. Deduplicate on product_id and effective_from
    df_dedup, duplicate_count = remove_duplicates(df, ["product_id", "effective_from"])
    
    # 2. Key null validations
    null_filter = F.col("price_id").isNull() | F.col("product_id").isNull()
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_pricing",
                "rule_name": "null_keys",
                "violation_reason": "price_id or product_id key is null",
                "record_key": str(row["price_id"]) if row["price_id"] else "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Check selling_price <= list_price
    price_filter = (F.col("selling_price") < 0) | (F.col("list_price") < 0) | (F.col("selling_price") > F.col("list_price"))
    invalid_prices = current_df.filter(price_filter)
    current_df = current_df.filter(~price_filter)
    
    price_cnt = invalid_prices.count()
    if price_cnt > 0:
        for row in invalid_prices.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_pricing",
                "rule_name": "invalid_prices",
                "violation_reason": f"selling_price ({row['selling_price']}) > list_price ({row['list_price']}) or negative value",
                "record_key": str(row["price_id"]),
                "created_at": datetime.now(timezone.utc)
            })

    # 4. Check currency is INR
    currency_filter = F.col("currency") != "INR"
    invalid_currencies = current_df.filter(currency_filter)
    current_df = current_df.filter(~currency_filter)
    
    curr_cnt = invalid_currencies.count()
    if curr_cnt > 0:
        for row in invalid_currencies.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_pricing",
                "rule_name": "invalid_currency",
                "violation_reason": f"currency '{row['currency']}' is not INR",
                "record_key": str(row["price_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
