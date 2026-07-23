# =====================================================================
# Product Search Amazon — Embeddings: Document Preparation
# =====================================================================

from typing import Dict, List, Optional
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def prepare_embedding_documents(
    df: DataFrame,
    text_columns: Optional[List[str]] = None,
    separator: str = " | ",
    max_length: int = 8192
) -> DataFrame:
    """
    Prepares a DataFrame for embedding by constructing a consolidated
    search document from available text columns. Truncates to max_length
    to respect model input limits.

    Args:
        df: Input DataFrame (typically gold catalog)
        text_columns: Ordered list of column names to concatenate.
                      If None, uses standard Amazon columns.
        separator: Separator between document sections.
        max_length: Maximum character length for the document.

    Returns:
        DataFrame with 'embedding_document' column added/updated.
    """
    if text_columns is None:
        text_columns = ["product_name", "category", "about_product", "review_title", "review_content"]

    # Filter to only columns that exist
    available_cols = [c for c in text_columns if c in df.columns]

    if not available_cols:
        # Fallback: use product_name or empty
        if "product_name" in df.columns:
            return df.withColumn("embedding_document", F.col("product_name"))
        return df.withColumn("embedding_document", F.lit(""))

    # Build concatenated document
    concat_parts = []
    for col in available_cols:
        concat_parts.append(
            F.when(
                F.col(col).isNotNull() & (F.trim(F.col(col)) != ""),
                F.col(col)
            ).otherwise(F.lit(""))
        )

    doc_expr = F.concat_ws(separator, *concat_parts)

    # Truncate to max_length
    doc_expr = F.substring(doc_expr, 1, max_length)

    return df.withColumn("embedding_document", doc_expr)


def validate_embedding_readiness(df: DataFrame, doc_column: str = "embedding_document") -> Dict:
    """
    Validates that the DataFrame is ready for embedding generation.

    Returns:
        Dict with total_docs, empty_docs, sample_empty, ready (bool)
    """
    total = df.count()
    empty = df.filter(
        F.col(doc_column).isNull() | (F.trim(F.col(doc_column)) == "")
    ).count()

    sample_empty = []
    if empty > 0:
        sample_empty = (
            df.filter(F.col(doc_column).isNull() | (F.trim(F.col(doc_column)) == ""))
            .select("product_id", "product_name")
            .limit(5)
            .collect()
        )
        sample_empty = [row.asDict() for row in sample_empty]

    return {
        "total_documents": total,
        "empty_documents": empty,
        "sample_empty_records": sample_empty,
        "ready": empty == 0 and total > 0,
    }