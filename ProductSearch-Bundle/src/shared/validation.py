# =====================================================================
# Product Search — Shared: Data Validation Helpers
# =====================================================================
# General-purpose database validation checks for validating target Delta tables.
# =====================================================================

from pyspark.sql import DataFrame
from pyspark.sql.functions import col


def validate_dataframe_not_empty(df: DataFrame, table_name: str) -> int:
    """Verifies that the DataFrame has rows. Returns row count if valid."""
    row_count = df.count()
    if row_count == 0:
        raise ValueError(f"Validation failed: Table '{table_name}' is empty.")
    return row_count


def validate_required_columns(df: DataFrame, required_cols: list, table_name: str):
    """Verifies that all required columns are present in the DataFrame schema."""
    df_cols = df.columns
    missing_cols = [c for c in required_cols if c not in df_cols]
    if missing_cols:
        raise ValueError(
            f"Validation failed: Table '{table_name}' is missing required columns: {missing_cols}"
        )


def check_null_keys(df: DataFrame, primary_key: str, table_name: str) -> int:
    """Checks for null values in the primary key column. Returns count of null records."""
    null_count = df.filter(col(primary_key).isNull()).count()
    if null_count > 0:
        raise ValueError(
            f"Validation failed: Table '{table_name}' contains {null_count} null keys in column '{primary_key}'"
        )
    return null_count


def check_duplicate_keys(df: DataFrame, primary_key: str, table_name: str) -> int:
    """Checks for duplicate values in the primary key column."""
    total_count = df.count()
    distinct_count = df.select(primary_key).distinct().count()
    duplicates = total_count - distinct_count
    if duplicates > 0:
        raise ValueError(
            f"Validation failed: Table '{table_name}' contains {duplicates} duplicate keys in column '{primary_key}'"
        )
    return duplicates


def check_null_mandatory_fields(df: DataFrame, mandatory_fields: list, table_name: str):
    """Checks for null values in mandatory fields that should never be null."""
    for field in mandatory_fields:
        if field in df.columns:
            null_count = df.filter(col(field).isNull()).count()
            if null_count > 0:
                raise ValueError(
                    f"Validation failed: Table '{table_name}' contains {null_count} nulls in mandatory field '{field}'"
                )


def check_fk_integrity(df: DataFrame, fk_col: str, parent_df: DataFrame, parent_pk: str, table_name: str):
    """Verifies that all non-null foreign keys refer to existing primary keys in parent dataframe."""
    if fk_col in df.columns and parent_pk in parent_df.columns:
        # Get count of rows where foreign key is set but does not exist in parent primary keys
        parent_keys = parent_df.select(parent_pk).distinct()
        orphans = df.filter(col(fk_col).isNotNull()).join(
            parent_keys,
            df[fk_col] == parent_keys[parent_pk],
            "left_anti"
        ).count()
        
        if orphans > 0:
            raise ValueError(
                f"Validation failed: Referential integrity check on Table '{table_name}' failed. "
                f"Column '{fk_col}' has {orphans} orphaned references not found in parent table column '{parent_pk}'."
            )


def validate_data_types(df: DataFrame, expected_types: dict, table_name: str):
    """Checks that columns match expected Spark types (e.g. 'string', 'double', 'integer')."""
    for col_name, expected_type in expected_types.items():
        if col_name in df.columns:
            actual_type = [f.dataType.simpleString() for f in df.schema.fields if f.name == col_name][0]
            # Match variations like 'double' vs 'decimal(12,2)'
            if expected_type == "double" and "decimal" in actual_type:
                continue
            if expected_type == "string" and "varchar" in actual_type:
                continue
            if actual_type != expected_type:
                raise TypeError(
                    f"Validation failed: Table '{table_name}' field '{col_name}' type is '{actual_type}' "
                    f"but expected type is '{expected_type}'"
                )
