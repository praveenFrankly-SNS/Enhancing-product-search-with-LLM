# =====================================================================
# Product Search Amazon — Transformation: Quality Checks
# =====================================================================

from typing import Tuple
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def filter_valid_products(df: DataFrame) -> Tuple[DataFrame, DataFrame]:
    """
    Splits DataFrame into valid products vs invalid/rejected records.
    Quality rules:
    - product_id must not be null or empty
    - product_name must not be null or empty
    """
    valid_cond = (
        F.col("product_id").isNotNull() & (F.trim(F.col("product_id")) != "") &
        F.col("product_name").isNotNull() & (F.trim(F.col("product_name")) != "")
    )
    
    valid_df = df.filter(valid_cond)
    rejected_df = df.filter(~valid_cond).withColumn("rejection_reason", F.lit("Missing product_id or product_name"))
    
    return valid_df, rejected_df
