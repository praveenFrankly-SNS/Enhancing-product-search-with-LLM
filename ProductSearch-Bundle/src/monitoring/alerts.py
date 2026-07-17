# =====================================================================
# Product Search — Monitoring: Alert Ingest & Evaluation
# =====================================================================

from datetime import datetime, timezone
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from src.shared.constants import OPERATIONS, ALERT_LOG

ALERT_SCHEMA = StructType([
    StructField("severity",   StringType(),    False),
    StructField("component",  StringType(),    False),
    StructField("alert_type", StringType(),    False),
    StructField("message",    StringType(),    True),
    StructField("timestamp",  TimestampType(), False),
    StructField("resolved",   StringType(),    True),
])

def check_and_log_alert(
    spark: SparkSession,
    catalog: str,
    severity: str,
    component: str,
    alert_type: str,
    message: str
):
    """
    Appends an alert event log into the operations.alert_log table.
    """
    now = datetime.now(timezone.utc)
    row = [(severity, component, alert_type, message, now, "NO")]
    
    df = spark.createDataFrame(row, ALERT_SCHEMA)
    target_table = f"{catalog}.{OPERATIONS}.{ALERT_LOG}"
    
    try:
        df.write.format("delta").mode("append").saveAsTable(target_table)
        print(f"[{severity.upper()} Alert Logged] Component: {component} | Type: {alert_type} | Message: {message}")
    except Exception as e:
        print(f"[Warning] Failed to write alert to '{target_table}'. Error: {str(e)}")
        print(f"[Alert Fallback] {now} | {severity} | {component} | {alert_type} | {message}")

def evaluate_metric_thresholds(
    spark: SparkSession,
    catalog: str,
    monitoring_config: dict,
    metric_name: str,
    metric_value: float,
    component: str
):
    """
    Evaluates a metric against thresholds configured in pipeline.yml and logs alerts when breached.
    """
    if not monitoring_config or not monitoring_config.get("enabled", True):
        return
        
    thresholds = monitoring_config.get("alert_thresholds", {}).get(metric_name, {})
    if not thresholds:
        return
        
    warning_val = thresholds.get("warning")
    critical_val = thresholds.get("critical")
    
    if critical_val is not None and metric_value >= float(critical_val):
        msg = f"Metric '{metric_name}' value {metric_value} breached CRITICAL threshold ({critical_val})"
        check_and_log_alert(spark, catalog, "CRITICAL", component, f"threshold_breach_{metric_name}", msg)
    elif warning_val is not None and metric_value >= float(warning_val):
        msg = f"Metric '{metric_name}' value {metric_value} breached WARNING threshold ({warning_val})"
        check_and_log_alert(spark, catalog, "WARNING", component, f"threshold_breach_{metric_name}", msg)
