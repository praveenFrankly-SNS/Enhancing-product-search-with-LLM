# =====================================================================
# Product Search Amazon — MLflow: Experiment Tracking Setup
# =====================================================================

import mlflow


def setup_mlflow_experiment(experiment_path: str = "/Shared/Amazon_Product_Search_ML"):
    try:
        mlflow.set_experiment(experiment_path)
        print(f"🧪 MLflow experiment set to: '{experiment_path}'")
    except Exception as e:
        print(f"Notice setting MLflow experiment: {e}")
