# =====================================================================
# Product Search — Ingestion: Category Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_category(df: DataFrame) -> DataFrame:
    """
    Trims category fields.
    """
    return df.withColumn(
        "category_name", F.coalesce(F.trim(F.col("category_name")), F.lit("Unknown"))
    )

def validate_category(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates category primary keys and drops records with blank category names.
    """
    violations = []
    
    # 1. Deduplicate on category_id
    df_dedup, duplicate_count = remove_duplicates(df, ["category_id"])
    
    # 2. Key null validations
    null_filter = F.col("category_id").isNull()
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "category",
                "rule_name": "null_keys",
                "violation_reason": "category_id key is null",
                "record_key": "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Drop records with blank category_name
    blank_filter = F.col("category_name").isNull() | (F.trim(F.col("category_name")) == "")
    invalid_cats = current_df.filter(blank_filter)
    current_df = current_df.filter(~blank_filter)
    
    blank_cnt = invalid_cats.count()
    if blank_cnt > 0:
        for row in invalid_cats.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "category",
                "rule_name": "blank_category_name",
                "violation_reason": "category_name is blank or empty",
                "record_key": str(row["category_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
