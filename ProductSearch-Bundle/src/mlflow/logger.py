# =====================================================================
# Product Search — MLflow: Generic Logging Utilities
# =====================================================================

import mlflow
from src.shared.logger import get_logger

logger = get_logger("mlflow_logger")

def log_parameters(params: dict):
    """
    Logs a dictionary of parameters to the active MLflow run.
    """
    if mlflow.active_run():
        try:
            mlflow.log_params(params)
            logger.info(f"Logged parameters to MLflow: {params}")
        except Exception as e:
            logger.warn(f"Failed to log parameters to MLflow: {str(e)}")

def log_metrics(metrics: dict):
    """
    Logs a dictionary of metrics to the active MLflow run.
    """
    if mlflow.active_run():
        try:
            mlflow.log_metrics(metrics)
            logger.info(f"Logged metrics to MLflow: {metrics}")
        except Exception as e:
            logger.warn(f"Failed to log metrics to MLflow: {str(e)}")

def log_tags(tags: dict):
    """
    Logs a dictionary of tags to the active MLflow run.
    """
    if mlflow.active_run():
        try:
            mlflow.set_tags(tags)
            logger.info(f"Logged tags to MLflow: {tags}")
        except Exception as e:
            logger.warn(f"Failed to log tags to MLflow: {str(e)}")

def log_table_statistics(table_name: str, records_read: int, records_written: int, duplicates: int, quarantined: int):
    """
    Logs conformed table stats (row counts, duplicates, quarantines) as metrics in MLflow.
    """
    if mlflow.active_run():
        metrics = {
            f"{table_name}_records_read": float(records_read),
            f"{table_name}_records_written": float(records_written),
            f"{table_name}_duplicates_removed": float(duplicates),
            f"{table_name}_quarantined_records": float(quarantined)
        }
        log_metrics(metrics)

def log_execution_time(duration_seconds: float, step_name: str = "execution"):
    """
    Logs execution duration metrics.
    """
    if mlflow.active_run():
        metrics = {
            f"duration_{step_name}_seconds": float(duration_seconds)
        }
        log_metrics(metrics)
