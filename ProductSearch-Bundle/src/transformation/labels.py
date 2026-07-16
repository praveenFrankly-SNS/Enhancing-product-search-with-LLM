# =====================================================================
# Product Search — Ingestion: Labels Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_labels(df: DataFrame) -> DataFrame:
    """
    Trims and standardizes relevance labels.
    """
    return df.withColumn(
        "label", F.initcap(F.trim(F.col("label")))
    )

def validate_labels(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates label unique combinations and strict value restrictions.
    """
    violations = []
    
    # 1. Deduplicate on query_id and product_id
    df_dedup, duplicate_count = remove_duplicates(df, ["query_id", "product_id"])
    
    # 2. Key null validations
    null_filter = F.col("id").isNull() | F.col("query_id").isNull() | F.col("product_id").isNull()
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "label",
                "rule_name": "null_keys",
                "violation_reason": "id, query_id or product_id key is null",
                "record_key": str(row["id"]) if row["id"] else "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Label value checks: Exact, Partial, Irrelevant
    valid_labels = ["Exact", "Partial", "Irrelevant"]
    label_filter = ~F.col("label").isin(valid_labels)
    invalid_labels = current_df.filter(label_filter)
    current_df = current_df.filter(~label_filter)
    
    label_cnt = invalid_labels.count()
    if label_cnt > 0:
        for row in invalid_labels.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "label",
                "rule_name": "invalid_label_value",
                "violation_reason": f"label value '{row['label']}' is not one of {valid_labels}",
                "record_key": str(row["id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
