# =====================================================================
# Product Search — Monitoring: Telemetry Ingest
# =====================================================================

from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, TimestampType
from src.shared.constants import OPERATIONS, MONITORING_METRICS

# Match the schema defined in setup platform
TELEMETRY_SCHEMA = StructType([
    StructField("timestamp",      TimestampType(), False),
    StructField("pipeline_stage", StringType(),    True),
    StructField("metric_name",    StringType(),    False),
    StructField("metric_value",   DoubleType(),    False),
    StructField("unit",           StringType(),    True),
    StructField("status",         StringType(),    True),
])

def record_metric(
    spark: SparkSession,
    catalog: str,
    pipeline_stage: str,
    metric_name: str,
    metric_value: float,
    unit: str,
    status: str = "SUCCESS"
):
    """
    Appends a single conformed metric row to the operations.monitoring_metrics table.
    """
    now = datetime.now(timezone.utc)
    row = [(now, pipeline_stage, metric_name, float(metric_value), unit, status)]
    
    df = spark.createDataFrame(row, TELEMETRY_SCHEMA)
    target_table = f"{catalog}.{OPERATIONS}.{MONITORING_METRICS}"
    
    try:
        df.write.format("delta").mode("append").saveAsTable(target_table)
    except Exception as e:
        # Fall back to printing to standard out in case of write access error
        print(f"[Warning] Failed to write telemetry to '{target_table}'. Error: {str(e)}")
        print(f"[Telemetry Fallback] {now} | {pipeline_stage} | {metric_name} = {metric_value} {unit} ({status})")
