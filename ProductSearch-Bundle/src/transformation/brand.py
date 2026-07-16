# =====================================================================
# Product Search — Ingestion: Brand Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_brand(df: DataFrame) -> DataFrame:
    """
    Trims brand name fields.
    """
    return df.withColumn(
        "brand_name", F.coalesce(F.trim(F.col("brand_name")), F.lit("Generic"))
    )

def validate_brand(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates brand primary keys and drops records with blank brand names.
    """
    violations = []
    
    # 1. Deduplicate on brand_id
    df_dedup, duplicate_count = remove_duplicates(df, ["brand_id"])
    
    # 2. Key null validations
    null_filter = F.col("brand_id").isNull()
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "brand",
                "rule_name": "null_keys",
                "violation_reason": "brand_id key is null",
                "record_key": "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Drop records with blank brand_name
    blank_filter = F.col("brand_name").isNull() | (F.trim(F.col("brand_name")) == "")
    invalid_brands = current_df.filter(blank_filter)
    current_df = current_df.filter(~blank_filter)
    
    blank_cnt = invalid_brands.count()
    if blank_cnt > 0:
        for row in invalid_brands.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "brand",
                "rule_name": "blank_brand_name",
                "violation_reason": "brand_name is blank or empty",
                "record_key": str(row["brand_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
