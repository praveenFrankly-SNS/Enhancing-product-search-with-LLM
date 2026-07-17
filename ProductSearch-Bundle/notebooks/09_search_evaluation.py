# Databricks notebook source
# MAGIC %md
# MAGIC # Search Evaluation Pipeline (WANDS Benchmark)
# MAGIC **Responsibility**: Runs benchmark search queries against the live Databricks Vector Search index, calculates Information Retrieval (IR) metrics using relevance ground truth labels, and uploads CSV/JSON reports to MLflow.
# MAGIC 
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import uuid
import time
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from pyspark.sql import SparkSession

# Add project root to sys.path for package imports
try:
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    project_root = "/Workspace" + notebook_path.split("/notebooks/")[0]
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    except NameError:
        pass

from src.shared.config import get_config
from src.shared.constants import GOLD, OPERATIONS
from src.shared.logger import get_logger

# Import Evaluation modules
from src.evaluation.evaluator import run_search_evaluation
from src.evaluation.metrics import aggregate_metrics
from src.evaluation.report import generate_evaluation_reports

# Import MLflow tracking helpers
from src.mlflow.experiment import start_mlflow_run, end_mlflow_run
from src.mlflow.logger import log_parameters, log_metrics, log_execution_time
from src.mlflow.artifacts import log_file_artifact

# Import monitoring telemetry
from src.monitoring.telemetry import record_metric

# Import governance package utilities
from src.governance import (
    validate_pipeline_config,
    verify_secrets_prerequisites,
    verify_catalog_prerequisites,
    record_pipeline_audit
)

# COMMAND ----------
spark = SparkSession.builder.getOrCreate()
logger = get_logger("search_evaluation")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",       "product_search_dev", "Catalog Name")
dbutils.widgets.text("environment",   "dev",                "Environment (dev/staging/prod)")
dbutils.widgets.text("endpoint_name", "product_search_ep",  "Vector Search Endpoint")
dbutils.widgets.text("index_name",    "product_search_dev.gold.product_search_catalog_index", "Vector Search Index")
dbutils.widgets.text("top_k",         "10",                 "Top K Results to Evaluate")

config = get_config(dbutils)
catalog = config.catalog
environment = config.environment

endpoint_name = dbutils.widgets.get("endpoint_name")
index_name = dbutils.widgets.get("index_name")
top_k = int(dbutils.widgets.get("top_k"))
run_id = str(uuid.uuid4())

# ── Enterprise Governance pre-execution validation checks ──────────────
# 1. Run config validation
config_check = validate_pipeline_config(config.yaml_config)
if not config_check["valid"]:
    raise RuntimeError(f"Governance Configuration check failed: {'; '.join(config_check['errors'])}")

# 2. Run secrets validation (this stage does not require database connection secrets)
governance_cfg = config.yaml_config.get("governance", {})
secrets_cfg = governance_cfg.get("secrets", {})
secret_scope = secrets_cfg.get("scope", config.yaml_config.get("pipeline", {}).get("secret_scope", ""))
required_secrets = []
secrets_check = verify_secrets_prerequisites(dbutils, secret_scope, required_secrets)
if not secrets_check["scope_exists"] or secrets_check["missing_keys"]:
    raise RuntimeError(f"Governance Secrets check failed in scope '{secret_scope}': {'; '.join(secrets_check['errors'])}")


# 3. Run catalog validation
catalog_check = verify_catalog_prerequisites(spark, catalog)
if not catalog_check["catalog_exists"] or catalog_check["errors"]:
    raise RuntimeError(f"Governance Catalog check failed on '{catalog}': {'; '.join(catalog_check['errors'])}")

# 4. Log successful validation
record_pipeline_audit(spark, catalog, run_id, "Evaluation", "pre_execution_governance_validation", "SUCCESS", "All governance prerequisites verified successfully.")

start_time = time.time()


logger.info(f"Starting WANDS Search Evaluation (Run ID: {run_id}) against index: {index_name}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Start MLflow Run & Log Parameters
# COMMAND ----------
# Start MLflow run context
start_mlflow_run(config.yaml_config, run_name="Search Evaluation", stage="Evaluation")

# Log execution parameters for reproducibility
log_parameters({
    "catalog": catalog,
    "environment": environment,
    "run_id": run_id,
    "evaluation_top_k": top_k,
    "vector_search_endpoint": endpoint_name,
    "vector_search_index": index_name,
    "embedding_model": "databricks-bge-large-en"
})
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Run Benchmark similarity searches and calculate IR metrics
# COMMAND ----------
# Execute similarity searches across all benchmark queries (fails fast if index is unreachable)
per_query_results = run_search_evaluation(
    spark=spark,
    catalog=catalog,
    gold_schema=GOLD,
    endpoint_name=endpoint_name,
    index_name=index_name,
    top_k=top_k
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Calculate Aggregate Metrics
# COMMAND ----------
# Compute average IR scores across all queries
agg_metrics = aggregate_metrics(per_query_results)

# Display metrics summary
print("=" * 60)
print("             WANDS BENCHMARK EVALUATION SUMMARY")
print("=" * 60)
for metric_name, score in agg_metrics.items():
    print(f"{metric_name:<25}: {score:.4f}")
print("=" * 60)

# Log aggregate scores to MLflow
log_metrics(agg_metrics)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 4. Export Reports & Upload MLflow Artifacts
# COMMAND ----------
# Write files to a temporary directory in workspace and upload to MLflow
with tempfile.TemporaryDirectory() as temp_dir:
    json_path, summary_csv, per_query_csv = generate_evaluation_reports(
        per_query_results=per_query_results,
        aggregate_metrics=agg_metrics,
        output_dir=temp_dir
    )
    
    # Upload generated reports as active run artifacts
    log_file_artifact(json_path, "evaluation_reports")
    log_file_artifact(summary_csv, "evaluation_reports")
    log_file_artifact(per_query_csv, "evaluation_reports")

# Log execution time
duration = time.time() - start_time
log_execution_time(duration, "search_evaluation")

# Log telemetry operational metrics
record_metric(spark, catalog, "Evaluation", "search_evaluation_duration", duration, "seconds", "SUCCESS")
record_metric(spark, catalog, "Evaluation", "average_ndcg_at_k", agg_metrics["ndcg_at_k"], "ndcg", "SUCCESS")
record_metric(spark, catalog, "Evaluation", "benchmark_queries_evaluated", len(per_query_results), "queries", "SUCCESS")

# End MLflow run context
end_mlflow_run()
# COMMAND ----------
# Record audit log
record_pipeline_audit(spark, catalog, run_id, "Evaluation", "search_evaluation_pipeline", "SUCCESS", f"Search evaluation completed. NDCG@10: {agg_metrics['ndcg_at_k']:.4f}.")
logger.success(f"Search evaluation completed successfully! NDCG@{top_k} = {agg_metrics['ndcg_at_k']:.4f}")

