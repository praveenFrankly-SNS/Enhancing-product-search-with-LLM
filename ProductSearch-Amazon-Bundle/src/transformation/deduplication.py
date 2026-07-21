# =====================================================================
# Product Search Amazon — Transformation: Deduplication
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql.window import Window
from pyspark.sql import functions as F


def deduplicate_products(df: DataFrame, primary_key: str = "product_id") -> DataFrame:
    """
    Deduplicates products by primary key, keeping the record with maximum rating/info.
    """
    if primary_key not in df.columns:
        return df.dropDuplicates()

    order_cols = []
    if "updated_at" in df.columns:
        order_cols.append(F.col("updated_at").desc())
    if "rating" in df.columns:
        order_cols.append(F.col("rating").desc_nulls_last())

    if not order_cols:
        return df.dropDuplicates([primary_key])

    window_spec = Window.partitionBy(primary_key).orderBy(*order_cols)
    return (
        df.withColumn("row_num", F.row_number().over(window_spec))
        .filter(F.col("row_num") == 1)
        .drop("row_num")
    )
