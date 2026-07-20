# =====================================================================
# Product Search Amazon — Shared: Pipeline Logger
# =====================================================================

import logging
import time
from datetime import datetime, timezone
from typing import Optional
from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, LongType, TimestampType

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("AmazonProductSearch")

EXEC_LOG_SCHEMA = StructType([
    StructField("run_id", StringType(), False),
    StructField("job_name", StringType(), False),
    StructField("task_name", StringType(), False),
    StructField("status", StringType(), False),
    StructField("records_in", LongType(), True),
    StructField("records_out", LongType(), True),
    StructField("execution_duration_sec", DoubleType(), True),
    StructField("error_message", StringType(), True),
    StructField("logged_at", TimestampType(), False)
])


class PipelineLogger:
    def __init__(self, spark: SparkSession, catalog: str, ops_schema: str = "operations"):
        self.spark = spark
        self.catalog = catalog
        self.ops_schema = ops_schema
        self.log_table = f"`{catalog}`.{ops_schema}.pipeline_execution_log"

    def log_execution(
        self,
        job_name: str,
        task_name: str,
        status: str,
        records_in: int = 0,
        records_out: int = 0,
        duration_sec: float = 0.0,
        error_msg: Optional[str] = None
    ):
        logger.info(f"[{job_name}:{task_name}] Status={status} Duration={duration_sec:.2f}s Records={records_out}")
        
        try:
            log_row = [(
                f"{job_name}_{int(time.time())}",
                job_name,
                task_name,
                status,
                records_in,
                records_out,
                float(duration_sec),
                error_msg or "",
                datetime.now(timezone.utc)
            )]
            df = self.spark.createDataFrame(log_row, schema=EXEC_LOG_SCHEMA)
            df.write.mode("append").format("delta").saveAsTable(self.log_table)
        except Exception as e:
            logger.warning(f"Could not persist log entry to operational log table {self.log_table}: {e}")
