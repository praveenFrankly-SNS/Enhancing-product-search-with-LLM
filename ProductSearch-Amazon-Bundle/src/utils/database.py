# =====================================================================
# Product Search Amazon — Utils: Database Connection Helpers
# =====================================================================

from typing import Optional
from pyspark.sql import SparkSession


def get_database_connection(spark: SparkSession, catalog: str, schema: str) -> str:
    """
    Returns the fully qualified table prefix for a given catalog and schema.
    """
    return f"`{catalog}`.{schema}"


def check_table_exists(spark: SparkSession, full_table_name: str) -> bool:
    """
    Checks if a Delta table exists in Unity Catalog.
    """
    try:
        spark.sql(f"DESCRIBE TABLE EXTENDED {full_table_name}")
        return True
    except Exception:
        return False


def get_table_row_count(spark: SparkSession, full_table_name: str) -> int:
    """
    Returns the approximate row count for a Delta table.
    """
    try:
        return spark.table(full_table_name).count()
    except Exception:
        return 0


def optimize_delta_table(spark: SparkSession, full_table_name: str) -> dict:
    """
    Runs OPTIMIZE on a Delta table for performance.
    Returns dict with metrics.
    """
    try:
        result = spark.sql(f"OPTIMIZE {full_table_name}")
        metrics = result.collect()[0].asDict() if result.count() > 0 else {}
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def vacuum_delta_table(spark: SparkSession, full_table_name: str, retention_hours: int = 168) -> dict:
    """
    Runs VACUUM on a Delta table to clean up old files.
    Default retention is 7 days (168 hours).
    """
    try:
        spark.sql(f"VACUUM {full_table_name} RETAIN {retention_hours} HOURS")
        return {"status": "success", "retention_hours": retention_hours}
    except Exception as e:
        return {"status": "error", "error": str(e)}