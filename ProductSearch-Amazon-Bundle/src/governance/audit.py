# =====================================================================
# Product Search Amazon — Governance: Audit Logger
# =====================================================================

from datetime import datetime, timezone
from pyspark.sql import SparkSession


def log_governance_audit_event(spark: SparkSession, catalog: str, action: str, details: str):
    audit_table = f"`{catalog}`.operations.audit_log"
    try:
        data = [(action, details, datetime.now(timezone.utc))]
        df = spark.createDataFrame(data, ["action", "details", "timestamp"])
        df.write.mode("append").format("delta").saveAsTable(audit_table)
    except Exception as e:
        print(f"Notice: Governance audit log persistence: {e}")
