# =====================================================================
# Product Search Amazon — MLflow: Param & Metric Logger
# =====================================================================

import mlflow
from typing import Dict, Any


def log_mlflow_run_metrics(params: Dict[str, Any], metrics: Dict[str, float], run_name: str = "search_eval"):
    try:
        with mlflow.start_run(run_name=run_name):
            for k, v in params.items():
                mlflow.log_param(k, v)
            for k, v in metrics.items():
                mlflow.log_metric(k, float(v))
            print(f"✅ MLflow run '{run_name}' logged successfully.")
    except Exception as e:
        print(f"Notice logging MLflow run metrics: {e}")
