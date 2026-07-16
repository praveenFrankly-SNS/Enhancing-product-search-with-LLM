# =====================================================================
# Product Search — Shared: Unified Logger
# =====================================================================
# Provides JSON-formatted stdout logging and standardized execution logging 
# to the operations Delta metadata tables.
# =====================================================================

import logging
import json
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional
from pyspark.sql import SparkSession
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    DoubleType, DateType, TimestampType
)
from src.shared.constants import OPERATIONS, EXECUTION_LOG, DATA_INGESTION_AUDIT


class PipelineLogger:
    """
    Structured logger that emits JSON-formatted log lines to stdout.
    Each line includes: timestamp, level, module, run_id, and message.
    """
    def __init__(self, module: str, run_id: str = "unknown"):
        self.module = module
        self.run_id = run_id
        self._logger = logging.getLogger(module)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
        self._logger.setLevel(logging.DEBUG)

    def _format(self, level: str, message: str, **kwargs) -> str:
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "module": self.module,
            "run_id": self.run_id,
            "message": message,
        }
        payload.update(kwargs)
        return json.dumps(payload)

    def info(self, message: str, **kwargs):
        self._logger.info(self._format("INFO", message, **kwargs))

    def warn(self, message: str, **kwargs):
        self._logger.warning(self._format("WARN", message, **kwargs))

    def error(self, message: str, **kwargs):
        self._logger.error(self._format("ERROR", message, **kwargs))

    def debug(self, message: str, **kwargs):
        self._logger.debug(self._format("DEBUG", message, **kwargs))

    def success(self, message: str, **kwargs):
        self._logger.info(self._format("SUCCESS", message, **kwargs))


class AcceleratorLogger:
    """
    Unified logger class wrapping structural JSON stdout log prints and
    database execution log table insertions.
    """
    def __init__(self, module_name: str, run_id: Optional[str] = None):
        self.run_id = run_id or str(uuid.uuid4())
        self.stdout_logger = PipelineLogger(module=module_name, run_id=self.run_id)

    def info(self, msg: str, **kwargs):
        self.stdout_logger.info(msg, **kwargs)

    def warn(self, msg: str, **kwargs):
        self.stdout_logger.warn(msg, **kwargs)

    def error(self, msg: str, **kwargs):
        self.stdout_logger.error(msg, **kwargs)

    def success(self, msg: str, **kwargs):
        self.stdout_logger.success(msg, **kwargs)

    def log_execution(self, spark: SparkSession, catalog: str, task_name: str, 
                      table_name: str, status: str, rows_processed: int, 
                      duration_seconds: float, message: str = ""):
        """
        Appends a standardized performance auditing record directly to the 
        delta log table operations.pipeline_execution_log.
        """
        log_record = [{
            "log_id":           str(uuid.uuid4()),
            "run_id":           self.run_id,
            "run_date":         datetime.now(timezone.utc).date(),
            "task_name":        task_name,
            "table_name":       table_name,
            "status":           status,
            "rows_processed":   int(rows_processed),
            "duration_seconds": round(duration_seconds, 2),
            "message":          message,
            "created_at":       datetime.now(timezone.utc),
        }]
        
        schema = StructType([
            StructField("log_id",           StringType(),    False),
            StructField("run_id",           StringType(),    False),
            StructField("run_date",         DateType(),      True),
            StructField("task_name",        StringType(),    True),
            StructField("table_name",       StringType(),    True),
            StructField("status",           StringType(),    True),
            StructField("rows_processed",   LongType(),      True),
            StructField("duration_seconds", DoubleType(),    True),
            StructField("message",          StringType(),    True),
            StructField("created_at",       TimestampType(), True),
        ])
        
        log_table = f"{catalog}.{OPERATIONS}.{EXECUTION_LOG}"
        try:
            df = spark.createDataFrame(log_record, schema=schema)
            df.write.mode("append").saveAsTable(log_table)
            self.info("Delta execution log appended successfully", log_table=log_table, status=status, table=table_name)
        except Exception as err:
            self.warn(
                f"Could not insert execution log to Delta table: {err}. Logging metadata via stdout instead.",
                status=status,
                table=table_name,
                rows_processed=rows_processed,
                duration_s=round(duration_seconds, 2),
                execution_message=message
            )

    def log_ingestion_audit(self, spark: SparkSession, catalog: str, 
                            source_table: str, target_table: str, status: str, 
                            rows_read: int, rows_written: int, 
                            duration_seconds: float, message: str = ""):
        """
        Logs detailed statistics about raw JDBC ingestion to operations.data_ingestion_audit.
        """
        audit_record = [{
            "audit_id":         str(uuid.uuid4()),
            "run_id":           self.run_id,
            "table_name":       target_table,
            "source_table":     source_table,
            "status":           status,
            "rows_read":        int(rows_read),
            "rows_written":     int(rows_written),
            "duration_seconds": round(duration_seconds, 2),
            "message":          message,
            "created_at":       datetime.now(timezone.utc),
        }]
        
        schema = StructType([
            StructField("audit_id",         StringType(),    False),
            StructField("run_id",           StringType(),    False),
            StructField("table_name",       StringType(),    True),
            StructField("source_table",     StringType(),    True),
            StructField("status",           StringType(),    True),
            StructField("rows_read",        LongType(),      True),
            StructField("rows_written",     LongType(),      True),
            StructField("duration_seconds", DoubleType(),    True),
            StructField("message",          StringType(),    True),
            StructField("created_at",       TimestampType(), True),
        ])
        
        audit_table = f"{catalog}.{OPERATIONS}.{DATA_INGESTION_AUDIT}"
        try:
            df = spark.createDataFrame(audit_record, schema=schema)
            df.write.mode("append").saveAsTable(audit_table)
            self.info("Ingestion audit log appended successfully", table=target_table, status=status)
        except Exception as err:
            self.warn(
                f"Could not append to ingestion audit Delta log: {err}. Logging metadata via stdout instead.",
                status=status,
                table=target_table,
                rows_read=rows_read,
                rows_written=rows_written,
                duration_s=round(duration_seconds, 2),
                execution_message=message
            )


def get_logger(module_name: str, run_id: Optional[str] = None) -> AcceleratorLogger:
    """Helper method to instantiate unified logger."""
    return AcceleratorLogger(module_name, run_id)
