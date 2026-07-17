# =====================================================================
# Product Search — MLflow: Experiment & Run Context Manager
# =====================================================================

import mlflow
from src.shared.logger import get_logger

logger = get_logger("mlflow_experiment")

def setup_mlflow_experiment(config: dict) -> str:
    """
    Sets the active MLflow experiment path based on configurations.
    Returns the resolved path.
    """
    mlflow_cfg = config.get("mlflow", {})
    if not mlflow_cfg.get("enabled", True):
        logger.info("MLflow logging is disabled in configuration.")
        return "disabled"
        
    experiment_path = mlflow_cfg.get("experiment_path", "/Shared/Product_Search_ML")
    
    try:
        # Explicitly set URIs to avoid CONFIG_NOT_AVAILABLE errors on serverless compute
        mlflow.set_tracking_uri("databricks")
        mlflow.set_registry_uri("databricks-uc")
        
        mlflow.set_experiment(experiment_path)
        logger.info(f"MLflow active experiment set to: {experiment_path}")
    except Exception as e:
        logger.warn(f"Failed to set MLflow experiment to {experiment_path}. Error: {str(e)}")
        active_exp = mlflow.get_experiment_by_name(experiment_path)
        if active_exp:
            experiment_path = active_exp.name
        else:
            experiment_path = "default"
            
    return experiment_path

def start_mlflow_run(config: dict, run_name: str, stage: str):
    """
    Starts an MLflow run under the configured experiment.
    Sets standard tags automatically.
    Returns the active run object.
    """
    mlflow_cfg = config.get("mlflow", {})
    if not mlflow_cfg.get("enabled", True):
        return None
        
    setup_mlflow_experiment(config)
    
    run = mlflow.start_run(run_name=run_name)
    
    # Log common tags
    common_tags = {
        "project": mlflow_cfg.get("tags", {}).get("project", "Product Search"),
        "stage": stage,
        "pipeline": "Offline",
        "environment": config.get("pipeline", {}).get("catalog", "product_search_dev").split("_")[-1]
    }
    mlflow.set_tags(common_tags)
    
    logger.info(f"Successfully started MLflow run '{run_name}' with tags: {common_tags}")
    return run

def end_mlflow_run():
    """
    Ends the currently active MLflow run.
    """
    try:
        mlflow.end_run()
        logger.info("Ended active MLflow run.")
    except Exception as e:
        logger.warn(f"Error ending MLflow run: {str(e)}")
