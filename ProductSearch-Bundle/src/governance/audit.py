# =====================================================================
# Product Search — Governance Auditing & Logging
# =====================================================================

import sys
import time
from datetime import datetime, timezone
from pyspark.sql.types import StructType, StructField, StringType, TimestampType
from src.shared.constants import OPERATIONS, AUDIT_LOG, SECURITY_VALIDATION
from src.shared.logger import get_logger

logger = get_logger("governance_audit")

def record_pipeline_audit(spark, catalog: str, run_id: str, pipeline_stage: str, action: str, status: str, message: str):
    """
    Records an auditable record of pipeline step executions inside the
    operations.audit_log table.
    """
    now = datetime.now(timezone.utc)
    AUDIT_SCHEMA = StructType([
        StructField("timestamp",      TimestampType(), False),
        StructField("run_id",         StringType(),    False),
        StructField("pipeline_stage", StringType(),    True),
        StructField("action",         StringType(),    False),
        StructField("status",         StringType(),    False),
        StructField("message",        StringType(),    True),
    ])
    
    row = [(now, run_id, pipeline_stage, action, status, message)]
    df = spark.createDataFrame(row, AUDIT_SCHEMA)
    
    target_table = f"{catalog}.{OPERATIONS}.{AUDIT_LOG}"
    try:
        df.write.format("delta").mode("append").saveAsTable(target_table)
        logger.info(f"Audited action '{action}' on stage '{pipeline_stage}' (Status: {status})")
    except Exception as e:
        logger.warn(f"Failed to write to audit log table {target_table}. Error: {str(e)}")

def record_security_validation(spark, catalog: str, validation_type: str, component: str, result: str, details: str):
    """
    Records security validation checks results into the
    operations.security_validation table.
    """
    now = datetime.now(timezone.utc)
    SEC_SCHEMA = StructType([
        StructField("validation_type", StringType(),    False),
        StructField("component",       StringType(),    False),
        StructField("result",          StringType(),    False),
        StructField("details",         StringType(),    True),
        StructField("checked_at",      TimestampType(), False),
    ])
    
    row = [(validation_type, component, result, details, now)]
    df = spark.createDataFrame(row, SEC_SCHEMA)
    
    target_table = f"{catalog}.{OPERATIONS}.{SECURITY_VALIDATION}"
    try:
        df.write.format("delta").mode("append").saveAsTable(target_table)
        logger.info(f"Recorded security validation check: type={validation_type}, comp={component}, res={result}")
    except Exception as e:
        logger.warn(f"Failed to write to security validation table {target_table}. Error: {str(e)}")
