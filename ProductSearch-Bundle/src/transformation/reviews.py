# =====================================================================
# Product Search — Ingestion: Reviews Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_reviews(df: DataFrame) -> DataFrame:
    """
    Fills empty review fields with fallback messages.
    """
    return df.withColumn(
        "review_summary", F.coalesce(F.trim(F.col("review_summary")), F.lit("No summary available."))
    ).withColumn(
        "search_review_text", F.coalesce(F.trim(F.col("search_review_text")), F.lit("No customer feedback available yet."))
    )

def validate_reviews(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates review ID formats and reviews sentiment score constraints.
    """
    violations = []
    
    # 1. Deduplicate on product_id
    df_dedup, duplicate_count = remove_duplicates(df, ["product_id"])
    
    # 2. Key null validations
    null_filter = F.col("review_summary_id").isNull() | F.col("product_id").isNull()
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_review_summary",
                "rule_name": "null_keys",
                "violation_reason": "review_summary_id or product_id key is null",
                "record_key": str(row["review_summary_id"]) if row["review_summary_id"] else "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Audit sentiment_score range
    sentiment_filter = (F.col("sentiment_score") < -1) | (F.col("sentiment_score") > 1)
    invalid_sentiments = current_df.filter(sentiment_filter)
    current_df = current_df.filter(~sentiment_filter)
    
    sent_cnt = invalid_sentiments.count()
    if sent_cnt > 0:
        for row in invalid_sentiments.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_review_summary",
                "rule_name": "invalid_sentiment_score",
                "violation_reason": f"sentiment_score ({row['sentiment_score']}) is out of valid bounds [-1, 1]",
                "record_key": str(row["review_summary_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
