# =====================================================================
# Product Search Amazon — Shared: Contract Validation
# =====================================================================

from typing import List, Dict, Any
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def validate_dataframe_schema(df: DataFrame, required_cols: List[str]) -> Dict[str, Any]:
    """Validates presence of required columns in a DataFrame."""
    missing_cols = [c for c in required_cols if c not in df.columns]
    is_valid = len(missing_cols) == 0
    return {
        "valid": is_valid,
        "missing_columns": missing_cols,
        "existing_columns": df.columns
    }


def validate_non_empty(df: DataFrame, table_name: str) -> int:
    """Ensures a DataFrame or Table is non-empty."""
    cnt = df.count()
    if cnt == 0:
        raise ValueError(f"Validation failure: Table '{table_name}' has 0 records!")
    return cnt
