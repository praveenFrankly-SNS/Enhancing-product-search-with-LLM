# =====================================================================
# Product Search Amazon — Monitoring: Structured Event Logger
# =====================================================================

import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, TimestampType


EVENT_LOG_SCHEMA = StructType([
    StructField("event_id", StringType(), False),
    StructField("event_type", StringType(), False),
    StructField("pipeline_stage", StringType(), False),
    StructField("status", StringType(), False),
    StructField("records_processed", LongType(), True),
    StructField("duration_seconds", DoubleType(), True),
    StructField("error_message", StringType(), True),
    StructField("metadata", StringType(), True),
    StructField("logged_at", TimestampType(), False),
])


class EventLogger:
    """
    Structured event logger for pipeline observability.
    Logs events to both console and a Delta table for downstream monitoring.
    """

    def __init__(self, spark: SparkSession, catalog: str, ops_schema: str = "operations"):
        self.spark = spark
        self.catalog = catalog
        self.ops_schema = ops_schema
        self.log_table = f"`{catalog}`.{ops_schema}.pipeline_events"

    def log_event(
        self,
        event_type: str,
        pipeline_stage: str,
        status: str,
        records_processed: int = 0,
        duration_seconds: float = 0.0,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Logs a structured pipeline event.

        Args:
            event_type: Type of event (e.g., 'ingestion', 'transformation', 'search')
            pipeline_stage: Pipeline stage name (e.g., 'bronze_ingestion', 'silver_transform')
            status: 'SUCCESS', 'FAILED', 'WARNING', 'SKIPPED'
            records_processed: Number of records processed
            duration_seconds: Execution duration
            error_message: Error details if failed
            metadata: Additional structured metadata as dict
        """
        event_id = f"{pipeline_stage}_{int(time.time())}"
        metadata_json = json.dumps(metadata) if metadata else "{}"

        # Console log
        print(f"[EVENT] {event_id} | {event_type}:{pipeline_stage} | Status={status} | "
              f"Records={records_processed} | Duration={duration_seconds:.2f}s")

        # Persist to Delta table
        try:
            row = [(
                event_id,
                event_type,
                pipeline_stage,
                status,
                records_processed,
                float(duration_seconds),
                error_message or "",
                metadata_json,
                datetime.now(timezone.utc),
            )]
            df = self.spark.createDataFrame(row, schema=EVENT_LOG_SCHEMA)
            df.write.mode("append").format("delta").saveAsTable(self.log_table)
        except Exception as e:
            print(f"Warning: Could not persist event to {self.log_table}: {e}")

    def log_search_event(
        self,
        query: str,
        num_results: int,
        latency_ms: float,
        status: str = "SUCCESS",
        error_message: Optional[str] = None,
    ):
        """
        Logs a search query event specifically for monitoring search performance.
        """
        self.log_event(
            event_type="search_query",
            pipeline_stage="semantic_search",
            status=status,
            records_processed=num_results,
            duration_seconds=latency_ms / 1000.0,
            error_message=error_message,
            metadata={
                "query": query[:200],
                "query_length": len(query),
                "latency_ms": latency_ms,
            },
        )