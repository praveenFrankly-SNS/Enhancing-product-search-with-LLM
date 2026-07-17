# =====================================================================
# Product Search — Gold: Feature Engineering Helpers
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql import functions as F

def calculate_attribute_summary(attributes_df: DataFrame) -> DataFrame:
    """
    Groups attributes per product and rolls them up into a single string
    (e.g., 'Material: Wood, Color: Black, Width: 32 in').
    """
    # Build 'AttributeName: AttributeValue [Unit]'
    attr_expr = F.concat(
        F.col("attribute_name"),
        F.lit(": "),
        F.col("attribute_value"),
        F.when(
            (F.col("attribute_unit").isNotNull()) & (F.trim(F.col("attribute_unit")) != ""), 
            F.concat(F.lit(" "), F.col("attribute_unit"))
        ).otherwise(F.lit(""))
    )
    
    return attributes_df.groupBy("product_id").agg(
        F.concat_ws(", ", F.collect_list(attr_expr)).alias("attribute_summary")
    )

def map_label_scores(labels_df: DataFrame) -> DataFrame:
    """
    Appends a numeric label_score column to the Silver labels table
    (Exact = 1.0, Partial = 0.75, Irrelevant = 0.0) while preserving original label.
    """
    score_expr = F.when(
        F.lower(F.col("label")) == "exact", F.lit(1.0)
    ).when(
        F.lower(F.col("label")) == "partial", F.lit(0.75)
    ).otherwise(F.lit(0.0))
    
    return labels_df.withColumn("label_score", score_expr)

def assemble_product_search_catalog(
    products_df: DataFrame,
    pricing_df: DataFrame,
    master_df: DataFrame,
    brands_df: DataFrame,
    attributes_summary_df: DataFrame,
    reviews_df: DataFrame
) -> DataFrame:
    """
    Joins Silver dimensions and rolls them up into the single Gold search catalog.
    Computes brand names, category paths, and compiles the canonical searchable_text.
    """
    # 1. Start from base product master and join references
    joined_df = master_df.join(products_df, "product_id", "inner")
    
    # 2. Join brands
    joined_df = joined_df.join(
        brands_df.select("brand_id", "brand_name"),
        "brand_id",
        "left"
    ).withColumn(
        "brand_name", F.coalesce(F.col("brand_name"), F.lit("Generic"))
    )
    
    # 3. Join pricing
    # Select the active selling_price
    joined_df = joined_df.join(
        pricing_df.select("product_id", "selling_price"),
        "product_id",
        "left"
    )
    
    # 4. Join attributes summary roll-up
    joined_df = joined_df.join(
        attributes_summary_df,
        "product_id",
        "left"
    ).withColumn(
        "attribute_summary", F.coalesce(F.col("attribute_summary"), F.lit(""))
    )
    
    # 5. Join reviews and derive review_summary text (renaming rating columns to avoid ambiguity with base product ratings)
    joined_df = joined_df.join(
        reviews_df.select(
            "product_id",
            F.col("average_rating").alias("reviews_average_rating"),
            F.col("rating_count").alias("reviews_rating_count"),
            "sentiment_score"
        ),
        "product_id",
        "left"
    ).withColumn(
        "review_summary",
        F.when(
            F.col("reviews_rating_count") > 0,
            F.concat(
                F.lit("Average rating: "), F.col("reviews_average_rating"), F.lit(" out of 5 stars based on "), F.col("reviews_rating_count"), F.lit(" reviews. Customer sentiment score is "), F.col("sentiment_score"), F.lit(".")
            )
        ).otherwise(F.lit("No reviews yet."))
    )


    
    # 6. Build category_path
    # E.g. 'Furniture > Living Room Furniture > Sofas'
    category_path_expr = F.regexp_replace(F.col("category_hierarchy"), "\\s+/\\s+", " › ")
    joined_df = joined_df.withColumn("category_path", category_path_expr)
    
    # 7. Assemble canonical searchable_text (excluding empty components dynamically via concat_ws)
    # Form: product_name + description + features + category_path + attributes + reviews
    searchable_text_expr = F.concat_ws(
        " \n ",
        F.col("normalized_name"),
        F.col("normalized_description"),
        F.col("product_features"),
        F.col("category_path"),
        F.col("attribute_summary"),
        F.col("review_summary")
    )
    
    catalog_df = joined_df.withColumn("searchable_text", searchable_text_expr)

    # 8. Cast all columns to Databricks Vector Search-compatible physical types.
    # JDBC sources (PostgreSQL) map numeric types to DECIMAL and strings to VARCHAR,
    # both of which are rejected by Vector Search. Cast explicitly here so the
    # physical Delta schema is always stamped with supported types.
    catalog_df = (
        catalog_df
        .withColumn("product_id",    F.col("product_id").cast("string"))
        .withColumn("selling_price", F.col("selling_price").cast("double"))
        .withColumn("average_rating",F.col("average_rating").cast("double"))
        .withColumn("review_count",  F.col("review_count").cast("int"))
    )

    # 9. Select required Gold columns
    final_cols = [
        "product_id",
        "product_name",
        "category_path",
        "attribute_summary",
        "review_summary",
        "searchable_text",
        "brand_name",
        "selling_price",
        "average_rating",
        "review_count"
    ]

    return catalog_df.select(*final_cols)

def validate_search_catalog(df: DataFrame) -> DataFrame:
    """
    Enforces sanity bounds on final catalog (searchable_text must not be null/empty).
    """
    valid_filter = F.col("searchable_text").isNotNull() & (F.length(F.trim(F.col("searchable_text"))) > 0)
    invalid_count = df.filter(~valid_filter).count()
    if invalid_count > 0:
        raise ValueError(
            f"Validation failed: Gold product_search_catalog contains {invalid_count} records with empty searchable_text."
        )
    return df
