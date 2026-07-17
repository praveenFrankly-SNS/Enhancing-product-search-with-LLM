# =====================================================================
# Product Search — MLflow: Artifact Upload Utilities
# =====================================================================

import mlflow
import os
from src.shared.logger import get_logger

logger = get_logger("mlflow_artifacts")

def log_file_artifact(local_path: str, artifact_path: str = None):
    """
    Logs a local file as an MLflow run artifact.
    """
    if mlflow.active_run():
        if os.path.exists(local_path):
            try:
                mlflow.log_artifact(local_path, artifact_path=artifact_path)
                logger.info(f"Successfully uploaded artifact '{local_path}' to MLflow path '{artifact_path}'.")
            except Exception as e:
                logger.warn(f"Failed to upload artifact to MLflow: {str(e)}")
        else:
            logger.warn(f"Artifact local path does not exist: {local_path}")

def log_dict_artifact(data: dict, file_name: str, artifact_path: str = None):
    """
    Saves a dictionary as a JSON file and logs it as an MLflow run artifact.
    """
    if mlflow.active_run():
        try:
            mlflow.log_dict(data, f"{artifact_path}/{file_name}" if artifact_path else file_name)
            logger.info(f"Successfully logged JSON dict '{file_name}' to MLflow.")
        except Exception as e:
            logger.warn(f"Failed to log JSON dict to MLflow: {str(e)}")
