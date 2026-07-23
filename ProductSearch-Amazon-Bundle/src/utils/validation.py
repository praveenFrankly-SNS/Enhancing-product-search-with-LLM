# =====================================================================
# Product Search Amazon — Utils: DataFrame Validation
# =====================================================================

from typing import Dict, List, Any, Optional
from pyspark.sql import DataFrame
from pyspark.sql import functions as F


def validate_dataframe(
    df: DataFrame,
    required_columns: List[str] = None,
    min_rows: int = 0
) -> Dict[str, Any]:
    """
    Validates a DataFrame has required columns and minimum row count.
    
    Returns:
        Dict with valid (bool), missing_columns (list), row_count (int), errors (list)
    """
    errors = []
    required_columns = required_columns or []
    
    # Check required columns
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        errors.append(f"Missing required columns: {missing}")
    
    # Check row count
    row_count = df.count()
    if row_count < min_rows:
        errors.append(f"Row count {row_count} is below minimum {min_rows}")
    
    return {
        "valid": len(errors) == 0,
        "missing_columns": missing,
        "row_count": row_count,
        "errors": errors,
    }


def check_data_quality(
    df: DataFrame,
    table_name: str,
    pk_column: Optional[str] = None,
    not_null_columns: List[str] = None
) -> Dict[str, Any]:
    """
    Comprehensive data quality check on a DataFrame.
    
    Checks:
    - Non-empty
    - Duplicate primary keys (if pk_column specified)
    - NULL counts for critical columns
    - Column count and schema
    
    Returns:
        Dict with quality metrics
    """
    not_null_columns = not_null_columns or []
    row_count = df.count()
    result = {
        "table_name": table_name,
        "row_count": row_count,
        "column_count": len(df.columns),
        "columns": df.columns,
        "not_null_violations": {},
        "null_counts": {},
        "duplicate_pks": 0,
        "is_empty": row_count == 0,
        "quality_score": 1.0,
    }
    
    # NULL checks
    for col in not_null_columns:
        if col in df.columns:
            null_count = df.filter(F.col(col).isNull()).count()
            result["null_counts"][col] = null_count
            if null_count > 0:
                result["not_null_violations"][col] = null_count
                result["quality_score"] *= 0.9  # Penalize per violation
    
    # Duplicate PK check
    if pk_column and pk_column in df.columns:
        total = df.count()
        distinct = df.select(pk_column).distinct().count()
        result["duplicate_pks"] = total - distinct
        if result["duplicate_pks"] > 0:
            result["quality_score"] *= 0.8
    
    return result