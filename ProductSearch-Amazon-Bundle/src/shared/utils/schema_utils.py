# =====================================================================
# Product Search Amazon — Dynamic Schema Adapter & Column Resolver
# =====================================================================
# Handles variable CSV columns, header name variations, missing fields,
# dynamic numeric parsing, and automatic search document synthesis.
# =====================================================================

from typing import Dict, List, Optional
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from pyspark.sql.types import StringType, DoubleType, IntegerType, DataType

# Comprehensive alias map for column normalization
COLUMN_ALIASES: Dict[str, List[str]] = {
    "product_id": ["product_id", "id", "asin", "item_id", "prod_id"],
    "product_name": ["product_name", "title", "name", "item_name", "product_title"],
    "category": ["category", "categories", "category_formatted", "subcategory", "catalog_category"],
    "discounted_price": ["discounted_price", "price", "sale_price", "discount_price", "current_price", "offer_price"],
    "actual_price": ["actual_price", "list_price", "original_price", "mrp", "regular_price"],
    "discount_percentage": ["discount_percentage", "discount_percent", "discount", "savings_percentage"],
    "rating": ["rating", "rating_score", "score", "stars", "avg_rating"],
    "rating_count": ["rating_count", "ratings_count", "num_ratings", "review_count", "total_reviews"],
    "about_product": ["about_product", "description", "product_description", "overview", "details", "summary"],
    "user_id": ["user_id", "customer_id", "reviewer_id", "author_id"],
    "user_name": ["user_name", "customer_name", "reviewer_name", "author_name"],
    "review_id": ["review_id", "review_pk", "comment_id"],
    "review_title": ["review_title", "review_summary", "headline", "subject"],
    "review_content": ["review_content", "review_body", "review_text", "comment", "feedback"],
    "img_link": ["img_link", "image", "image_url", "img_url", "product_image", "thumbnail"],
    "product_link": ["product_link", "url", "product_url", "link", "web_url"]
}

# Standard default data types for standard columns
COLUMN_TYPES: Dict[str, DataType] = {
    "product_id": StringType(),
    "product_name": StringType(),
    "category": StringType(),
    "discounted_price": DoubleType(),
    "actual_price": DoubleType(),
    "discount_percentage": StringType(),
    "rating": DoubleType(),
    "rating_count": IntegerType(),
    "about_product": StringType(),
    "user_id": StringType(),
    "user_name": StringType(),
    "review_id": StringType(),
    "review_title": StringType(),
    "review_content": StringType(),
    "img_link": StringType(),
    "product_link": StringType(),
}


def normalize_column_name(name: str) -> str:
    """Standardizes column string to lowercase snake_case."""
    return name.strip().lower().replace(" ", "_").replace("-", "_")


def resolve_dynamic_schema(df: DataFrame, alias_map: Optional[Dict[str, List[str]]] = None) -> DataFrame:
    """
    Dynamically maps input DataFrame columns to standard target column names.
    If expected columns are missing, populates them with lit(None) of appropriate type.
    Extra non-standard columns are preserved.
    """
    alias_map = alias_map or COLUMN_ALIASES
    existing_cols = {normalize_column_name(c): c for c in df.columns}
    
    select_exprs = []
    mapped_source_cols = set()

    for target_col, aliases in alias_map.items():
        matched_col = None
        for alias in aliases:
            norm_alias = normalize_column_name(alias)
            if norm_alias in existing_cols:
                matched_col = existing_cols[norm_alias]
                mapped_source_cols.add(matched_col)
                break
        
        if matched_col:
            select_exprs.append(F.col(f"`{matched_col}`").alias(target_col))
        else:
            # Fallback for missing target column
            target_type = COLUMN_TYPES.get(target_col, StringType())
            select_exprs.append(F.lit(None).cast(target_type).alias(target_col))

    # Keep any additional unknown columns that were not mapped
    for norm_c, orig_c in existing_cols.items():
        if orig_c not in mapped_source_cols and norm_c not in alias_map:
            select_exprs.append(F.col(f"`{orig_c}`"))

    return df.select(select_exprs)


def clean_numeric_fields(df: DataFrame) -> DataFrame:
    """
    Cleans currency characters (₹, $, €), commas, non-numeric ratings,
    and returns sanitized numeric columns using safe CAST operations with NULL fallback.
    """
    res = df
    if "discounted_price" in res.columns:
        res = res.withColumn(
            "_dp_clean", F.regexp_replace(F.col("discounted_price").cast("string"), "[₹$€,]", "")
        ).withColumn(
            "discounted_price", 
            F.when(
                F.col("_dp_clean").rlike("^[0-9]*\\.?[0-9]+$"),
                F.col("_dp_clean").cast(DoubleType())
            ).otherwise(F.lit(None).cast(DoubleType()))
        ).drop("_dp_clean")

    if "actual_price" in res.columns:
        res = res.withColumn(
            "_ap_clean", F.regexp_replace(F.col("actual_price").cast("string"), "[₹$€,]", "")
        ).withColumn(
            "actual_price",
            F.when(
                F.col("_ap_clean").rlike("^[0-9]*\\.?[0-9]+$"),
                F.col("_ap_clean").cast(DoubleType())
            ).otherwise(F.lit(None).cast(DoubleType()))
        ).drop("_ap_clean")

    if "rating" in res.columns:
        res = res.withColumn(
            "_rt_clean", F.regexp_replace(F.col("rating").cast("string"), "[^0-9.]", "")
        ).withColumn(
            "rating",
            F.when(
                (F.col("_rt_clean") != "") & F.col("_rt_clean").rlike("^[0-9]*\\.?[0-9]+$"),
                F.col("_rt_clean").cast(DoubleType())
            ).otherwise(F.lit(None).cast(DoubleType()))
        ).drop("_rt_clean")

    if "rating_count" in res.columns:
        res = res.withColumn(
            "_rc_clean", F.regexp_replace(F.col("rating_count").cast("string"), "[,]", "")
        ).withColumn(
            "rating_count",
            F.when(
                (F.col("_rc_clean") != "") & F.col("_rc_clean").rlike("^[0-9]+$"),
                F.col("_rc_clean").cast(IntegerType())
            ).otherwise(F.lit(None).cast(IntegerType()))
        ).drop("_rc_clean")

    if "category" in res.columns:
        res = res.withColumn(
            "category",
            F.regexp_replace(F.col("category"), "[|]", " > ")
        )
    return res


def build_dynamic_search_document(df: DataFrame) -> DataFrame:
    """
    Dynamically constructs rich 'search_document' combining all available
    textual fields in the DataFrame (title, category, product description, reviews).
    """
    candidate_text_cols = [
        ("Title", "product_name"),
        ("Category", "category"),
        ("Description", "about_product"),
        ("Review Title", "review_title"),
        ("Review", "review_content")
    ]
    
    concat_parts = []
    for label, col_name in candidate_text_cols:
        if col_name in df.columns:
            concat_parts.append(
                F.when(
                    F.col(col_name).isNotNull() & (F.trim(F.col(col_name)) != ""),
                    F.concat(F.lit(f"{label}: "), F.col(col_name))
                )
            )

    if not concat_parts:
        # Fallback to simple product name if available or empty string
        search_doc_expr = F.coalesce(F.col("product_name"), F.lit(""))
    else:
        search_doc_expr = F.concat_ws(" | ", *concat_parts)

    return df.withColumn("search_document", search_doc_expr)
