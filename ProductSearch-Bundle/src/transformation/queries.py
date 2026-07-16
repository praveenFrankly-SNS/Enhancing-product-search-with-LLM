# =====================================================================
# Product Search — Ingestion: Queries Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_queries(df: DataFrame) -> DataFrame:
    """
    Standardizes queries by trimming spacing and lowercasing to create normalized_query.
    Original raw query is preserved byte-for-byte.
    """
    clean_expr = F.trim(F.regexp_replace(F.col("query"), "\\s+", " "))
    return df.withColumn("normalized_query", F.lower(clean_expr))

def validate_queries(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates query primary keys and verifies query text presence.
    """
    violations = []
    
    # 1. Deduplicate on query_id
    df_dedup, duplicate_count = remove_duplicates(df, ["query_id"])
    
    # 2. Key null validations
    null_filter = F.col("query_id").isNull() | (F.trim(F.col("query_id")) == "")
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "query",
                "rule_name": "null_query_id",
                "violation_reason": "query_id is null or empty",
                "record_key": "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Drop records with empty query text
    empty_query_filter = F.col("query").isNull() | (F.trim(F.col("query")) == "")
    invalid_queries = current_df.filter(empty_query_filter)
    current_df = current_df.filter(~empty_query_filter)
    
    empty_cnt = invalid_queries.count()
    if empty_cnt > 0:
        for row in invalid_queries.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "query",
                "rule_name": "empty_query_string",
                "violation_reason": "query string is empty or null",
                "record_key": str(row["query_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
