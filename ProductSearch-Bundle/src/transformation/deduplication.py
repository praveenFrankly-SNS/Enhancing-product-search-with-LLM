# =====================================================================
# Product Search — Shared: Deduplication Helper
# =====================================================================

from typing import Tuple
from pyspark.sql import DataFrame

def remove_duplicates(df: DataFrame, dedup_cols: list) -> Tuple[DataFrame, int]:
    """
    Deduplicates a DataFrame based on a subset of columns.
    Returns: (deduplicated_df, duplicate_count)
    """
    if not dedup_cols:
        return df, 0
        
    initial_count = df.count()
    deduped_df = df.dropDuplicates(dedup_cols)
    after_count = deduped_df.count()
    duplicate_count = initial_count - after_count
    return deduped_df, duplicate_count
