# =====================================================================
# Product Search Amazon — Transformation: Amazon Transformer
# =====================================================================
# Executes medallion transformation from raw Bronze DataFrame to Silver clean dataset.
# Employs dynamic column resolution and resilient field cleaning.
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.shared.utils.schema_utils import (
    resolve_dynamic_schema,
    clean_numeric_fields,
    build_dynamic_search_document
)


def transform_raw_to_silver(raw_df: DataFrame) -> DataFrame:
    """
    Transforms raw bronze DataFrame into clean silver DataFrame.
    
    Steps:
    1. Dynamic column mapping & schema alignment (resolves variable column names).
    2. Resilient numeric field cleaning (price symbols, non-numeric ratings).
    3. Dynamic search document synthesis.
    4. Metadata timestamp enrichment.
    """
    # Step 1: Align dynamic schema
    aligned_df = resolve_dynamic_schema(raw_df)

    # Step 2: Clean numeric fields & format categories
    cleaned_df = clean_numeric_fields(aligned_df)

    # Step 3: Synthesize dynamic search document
    search_doc_df = build_dynamic_search_document(cleaned_df)

    # Step 4: Enrich with ingestion metadata
    final_df = (
        search_doc_df
        .withColumn("processed_at", F.current_timestamp())
        .withColumn("updated_at", F.current_timestamp())
    )

    return final_df
