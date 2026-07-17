# =====================================================================
# Product Search — MLflow: Metrics Builders & Calculators
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def build_pipeline_metrics(catalog_count: int, query_count: int, label_count: int) -> dict:
    """
    Constructs a conformed dictionary of pipeline counts.
    """
    return {
        "products_engineered": float(catalog_count),
        "queries_loaded": float(query_count),
        "labels_loaded": float(label_count)
    }

def calculate_searchable_text_stats(catalog_df: DataFrame) -> dict:
    """
    Calculates statistics on the assembled searchable_text column.
    """
    try:
        avg_len = catalog_df.select(F.avg(F.length(F.col("searchable_text")))).collect()[0][0]
        max_len = catalog_df.select(F.max(F.length(F.col("searchable_text")))).collect()[0][0]
        min_len = catalog_df.select(F.min(F.length(F.col("searchable_text")))).collect()[0][0]
        return {
            "searchable_text_avg_length": float(avg_len) if avg_len else 0.0,
            "searchable_text_max_length": float(max_len) if max_len else 0.0,
            "searchable_text_min_length": float(min_len) if min_len else 0.0,
        }
    except Exception:
        return {
            "searchable_text_avg_length": 0.0,
            "searchable_text_max_length": 0.0,
            "searchable_text_min_length": 0.0,
        }
