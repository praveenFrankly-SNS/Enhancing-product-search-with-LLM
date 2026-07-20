# =====================================================================
# Product Search Amazon — Monitoring: System Health Inspector
# =====================================================================

from typing import Dict, Any
from pyspark.sql import SparkSession


def check_table_health(spark: SparkSession, catalog: str, schema: str, table_name: str) -> Dict[str, Any]:
    full_table = f"`{catalog}`.{schema}.{table_name}"
    try:
        df = spark.table(full_table)
        cnt = df.count()
        num_cols = len(df.columns)
        return {
            "table_name": full_table,
            "status": "HEALTHY",
            "record_count": cnt,
            "column_count": num_cols,
            "error": None
        }
    except Exception as e:
        return {
            "table_name": full_table,
            "status": "UNHEALTHY",
            "record_count": 0,
            "column_count": 0,
            "error": str(e)
        }
