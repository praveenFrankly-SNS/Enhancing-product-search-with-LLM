# =====================================================================
# Product Search Amazon — MLflow: Artifact Logger
# =====================================================================

import os
import json
import mlflow


def log_json_artifact(data: dict, artifact_name: str):
    try:
        temp_path = f"/tmp/{artifact_name}"
        with open(temp_path, "w") as f:
            json.dump(data, f, indent=2)
        mlflow.log_artifact(temp_path)
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception as e:
        print(f"Notice logging JSON artifact to MLflow: {e}")
