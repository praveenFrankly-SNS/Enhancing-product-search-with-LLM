# =====================================================================
# Product Search Amazon — Feature Engineering: Amazon Catalog Builder
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def build_amazon_gold_catalog(silver_df: DataFrame) -> DataFrame:
    """
    Constructs the Gold `amazon_product_catalog` feature table from silver cleaned data.
    Enriches with price tiers, rating tiers, search document length, and metadata.
    """
    gold_df = (
        silver_df
        # Add price tier classification
        .withColumn(
            "price_tier",
            F.when(F.col("discounted_price") < 500, F.lit("Budget"))
             .when((F.col("discounted_price") >= 500) & (F.col("discounted_price") < 2000), F.lit("Mid-Range"))
             .when(F.col("discounted_price") >= 2000, F.lit("Premium"))
             .otherwise(F.lit("Unknown"))
        )
        # Add rating tier classification
        .withColumn(
            "rating_tier",
            F.when(F.col("rating") >= 4.5, F.lit("Top Rated"))
             .when((F.col("rating") >= 4.0) & (F.col("rating") < 4.5), F.lit("Highly Rated"))
             .when((F.col("rating") >= 3.0) & (F.col("rating") < 4.0), F.lit("Average"))
             .otherwise(F.lit("Low Rating"))
        )
        # Add search document character count feature
        .withColumn("search_doc_length", F.length(F.col("search_document")))
        .withColumn("created_at", F.current_timestamp())
    )

    return gold_df
