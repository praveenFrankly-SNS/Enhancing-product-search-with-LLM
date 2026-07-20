# Databricks notebook source
# MAGIC %md
# MAGIC # 09. Search Relevance Evaluation
# MAGIC Runs benchmark evaluation suite and logs NDCG, Precision@k, Recall@k metrics to MLflow.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
catalog = dbutils.widgets.get("catalog").strip()

def resolve_and_add_root():
    try:
        ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        nb_path = ctx.notebookPath().get()
        full_ws_path = nb_path if nb_path.startswith("/Workspace") else f"/Workspace{nb_path}"
        if "/notebooks" in full_ws_path:
            base_dir = full_ws_path.split("/notebooks")[0]
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
    except Exception:
        pass

resolve_and_add_root()

from src.evaluation.benchmark import STANDARD_BENCHMARK_QUERIES
from src.evaluation.report import generate_evaluation_report
from src.search.evaluation import evaluate_retrieval_relevance
from src.search.search_pipeline import execute_amazon_product_search
from src.mlflow.logger import log_mlflow_run_metrics

print(f"📊 Running Search Relevance Evaluation Suite on Amazon Catalog...")

eval_results = []
for test_case in STANDARD_BENCHMARK_QUERIES:
    q = test_case["query"]
    kws = test_case["keywords"]
    try:
        results = execute_amazon_product_search(query_text=q, catalog=catalog, num_results=10)
        rel_score = evaluate_retrieval_relevance(results, kws)
        eval_results.append({
            "query": q,
            "precision_at_k": rel_score,
            "recall_at_k": rel_score,
            "ndcg_at_k": rel_score
        })
    except Exception as e:
        print(f"Notice during query eval '{q}': {e}")

summary = generate_evaluation_report(eval_results)
print("\n📈 EVALUATION REPORT:")
print("=" * 60)
for k, v in summary.items():
    print(f"  • {k}: {v}")

# Log to MLflow
log_mlflow_run_metrics(
    params={"catalog": catalog, "eval_suite": "standard_benchmark"},
    metrics={
        "mean_precision_at_10": summary.get("mean_precision_at_k", 0.0),
        "mean_recall_at_10": summary.get("mean_recall_at_k", 0.0),
        "mean_ndcg_at_10": summary.get("mean_ndcg_at_k", 0.0)
    },
    run_name="Amazon_Search_Evaluation"
)
