# =====================================================================
# Product Search — Ingestion: Attributes Transformation
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame
from pyspark.sql import functions as F
from src.transformation.deduplication import remove_duplicates

def transform_attributes(df: DataFrame) -> DataFrame:
    """
    Standardizes attribute names to a controlled vocabulary.
    """
    standard_map = F.when(
        F.lower(F.col("attribute_name")).isin(["color", "primarycolor"]), F.lit("Color")
    ).when(
        F.lower(F.col("attribute_name")).isin(["material", "primarymaterial", "framematerial"]), F.lit("Material")
    ).when(
        F.lower(F.col("attribute_name")) == "size", F.lit("Size")
    ).when(
        F.lower(F.col("attribute_name")) == "weight", F.lit("Weight")
    ).when(
        F.lower(F.col("attribute_name")) == "capacity", F.lit("Capacity")
    ).when(
        F.lower(F.col("attribute_name")) == "dimensions", F.lit("Dimensions")
    ).when(
        F.lower(F.col("attribute_name")) == "length", F.lit("Length")
    ).when(
        F.lower(F.col("attribute_name")) == "depth", F.lit("Depth")
    ).when(
        F.lower(F.col("attribute_name")) == "width", F.lit("Width")
    ).when(
        F.lower(F.col("attribute_name")) == "height", F.lit("Height")
    ).otherwise(F.initcap(F.col("attribute_name")))
    
    return df.withColumn("attribute_name", standard_map)

def validate_attributes(df: DataFrame, run_id: str) -> Tuple[DataFrame, List[Dict], int]:
    """
    Validates attributes table keys, duplicates, and empty strings.
    """
    violations = []
    
    # 1. Deduplicate on product_id and attribute_name
    df_dedup, duplicate_count = remove_duplicates(df, ["product_id", "attribute_name"])
    
    # 2. Key null validations
    null_filter = F.col("attribute_id").isNull() | F.col("product_id").isNull()
    invalid_nulls = df_dedup.filter(null_filter)
    current_df = df_dedup.filter(~null_filter)
    
    null_cnt = invalid_nulls.count()
    if null_cnt > 0:
        for row in invalid_nulls.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_attributes",
                "rule_name": "null_keys",
                "violation_reason": "attribute_id or product_id key is null",
                "record_key": str(row["attribute_id"]) if row["attribute_id"] else "(unknown)",
                "created_at": datetime.now(timezone.utc)
            })

    # 3. Check for empty values or names
    empty_val_filter = (F.trim(F.col("attribute_name")) == "") | (F.trim(F.col("attribute_value")) == "")
    invalid_vals = current_df.filter(empty_val_filter)
    current_df = current_df.filter(~empty_val_filter)
    
    val_cnt = invalid_vals.count()
    if val_cnt > 0:
        for row in invalid_vals.limit(100).collect():
            violations.append({
                "rejection_id": str(uuid.uuid4()),
                "run_id": run_id,
                "run_date": datetime.now(timezone.utc).date(),
                "source_table": "product_attributes",
                "rule_name": "empty_attribute_specs",
                "violation_reason": "attribute_name or attribute_value is empty",
                "record_key": str(row["attribute_id"]),
                "created_at": datetime.now(timezone.utc)
            })
            
    return current_df, violations, duplicate_count
