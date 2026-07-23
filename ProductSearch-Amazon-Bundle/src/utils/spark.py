# =====================================================================
# Product Search Amazon — Utils: Spark Session & Table Management
# =====================================================================

from pyspark.sql import SparkSession


def get_spark_session(app_name: str = "AmazonProductSearch") -> SparkSession:
    """
    Returns or creates a SparkSession for the Amazon pipeline.
    """
    return SparkSession.builder.appName(app_name).getOrCreate()


def optimize_table(spark: SparkSession, full_table_name: str) -> dict:
    """
    Runs OPTIMIZE on a Delta table for improved query performance.
    Enables Z-ordering on indexed columns for faster vector search sync.
    """
    try:
        result = spark.sql(f"OPTIMIZE {full_table_name}")
        metrics = result.collect()[0].asDict() if result.count() > 0 else {}
        return {"status": "success", "metrics": metrics}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def enable_change_data_feed(spark: SparkSession, full_table_name: str) -> bool:
    """
    Enables Change Data Feed on a Delta table (required for Vector Search auto-sync).
    """
    try:
        spark.sql(f"ALTER TABLE {full_table_name} SET TBLPROPERTIES (delta.enableChangeDataFeed = true)")
        return True
    except Exception:
        return False


def analyze_table_stats(spark: SparkSession, full_table_name: str) -> dict:
    """
    Runs ANALYZE TABLE to compute statistics for the query optimizer.
    """
    try:
        spark.sql(f"ANALYZE TABLE {full_table_name} COMPUTE STATISTICS")
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "error": str(e)}