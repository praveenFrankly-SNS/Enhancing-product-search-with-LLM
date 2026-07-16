# =====================================================================
# Product Search — Shared: Data Quality & Quarantine Manager
# =====================================================================

import uuid
from datetime import datetime, timezone
from typing import Tuple, List, Dict
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, DateType, TimestampType, LongType, DoubleType
)

REJECTION_SCHEMA = StructType([
    StructField("rejection_id",     StringType(), False),
    StructField("run_id",           StringType(), False),
    StructField("run_date",         DateType(),   True),
    StructField("source_table",     StringType(), True),
    StructField("rule_name",        StringType(), True),
    StructField("violation_reason", StringType(), True),
    StructField("record_key",       StringType(), True),
    StructField("created_at",       TimestampType(), True),
])

def log_dq_report(
    spark: SparkSession,
    catalog: str,
    ops_schema: str,
    run_id: str,
    table_name: str,
    stage: str,
    records_read: int,
    records_written: int,
    duplicates: int,
    invalid_records: int,
    status: str = "SUCCESS",
    error_message: str = ""
):
    """
    Logs data quality execution details to operations.data_quality_report.
    """
    quality_score = float(records_written) / float(records_read) if records_read > 0 else 1.0
    
    schema = StructType([
        StructField("report_id",        StringType(),    False),
        StructField("run_id",           StringType(),    False),
        StructField("run_date",         DateType(),      True),
        StructField("table_name",       StringType(),    True),
        StructField("stage",            StringType(),    True),
        StructField("execution_time",   TimestampType(), True),
        StructField("status",           StringType(),    True),
        StructField("records_read",     LongType(),      True),
        StructField("records_written",  LongType(),      True),
        StructField("duplicates",       LongType(),      True),
        StructField("invalid_records",  LongType(),      True),
        StructField("quality_score",    DoubleType(),    True),
        StructField("error_message",    StringType(),    True),
        StructField("created_at",       TimestampType(), True),
    ])
    
    now = datetime.now(timezone.utc)
    row = [{
        "report_id": str(uuid.uuid4()),
        "run_id": run_id,
        "run_date": now.date(),
        "table_name": table_name,
        "stage": stage,
        "execution_time": now,
        "status": status,
        "records_read": int(records_read),
        "records_written": int(records_written),
        "duplicates": int(duplicates),
        "invalid_records": int(invalid_records),
        "quality_score": round(quality_score, 4),
        "error_message": error_message,
        "created_at": now
    }]
    
    spark.createDataFrame(row, schema=schema).write.mode("append").saveAsTable(
        f"{catalog}.{ops_schema}.data_quality_report"
    )

def write_violations_to_quarantine(
    spark: SparkSession,
    violations: List[Dict],
    catalog: str,
    ops_schema: str
):
    """
    Appends list of violation dicts to the quarantine table operations.rejected_records.
    """
    if not violations:
        return
        
    reject_df = spark.createDataFrame(violations, schema=REJECTION_SCHEMA)
    reject_df.write.mode("append").saveAsTable(
        f"{catalog}.{ops_schema}.rejected_records"
    )
