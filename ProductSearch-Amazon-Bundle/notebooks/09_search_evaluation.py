# Databricks notebook source
# MAGIC %md
# MAGIC # 09. Search Relevance Evaluation
# MAGIC Runs benchmark evaluation suite with realistic search queries and logs
# MAGIC NDCG, Precision@k, Recall@k metrics to MLflow. Supports both vector search
# MAGIC and SQL fallback for comprehensive evaluation.

# COMMAND ----------
import sys
import os
import time
import json

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("num_results", "10", "Number of results per query")
catalog = dbutils.widgets.get("catalog").strip()
num_results = int(dbutils.widgets.get("num_results").strip())

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

from pyspark.sql import SparkSession
from src.evaluation.benchmark import STANDARD_BENCHMARK_QUERIES
from src.evaluation.report import generate_evaluation_report
from src.evaluation.evaluator import SearchEvaluator
from src.search.evaluation import evaluate_retrieval_relevance
from src.search.search_pipeline import execute_amazon_product_search
from src.mlflow.logger import log_mlflow_run_metrics
from src.shared.logger import PipelineLogger

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

print(f"📊 Running Search Relevance Evaluation Suite on Amazon Catalog (top-{num_results})")
print("=" * 60)

evaluator = SearchEvaluator(top_k=num_results)
eval_results = []
query_times = []

for idx, test_case in enumerate(STANDARD_BENCHMARK_QUERIES):
    q = test_case["query"]
    kws = test_case["keywords"]
    
    print(f"\n[{idx+1}/{len(STANDARD_BENCHMARK_QUERIES)}] Query: '{q}' (keywords: {kws})")
    
    try:
        q_start = time.time()
        results = execute_amazon_product_search(
            query_text=q,
            catalog=catalog,
            num_results=num_results
        )
        q_duration = time.time() - q_start
        query_times.append(q_duration)
        
        retrieved_ids = [r.get("product_id", "") for r in results]
        
        # Evaluate relevance
        rel_score = evaluate_retrieval_relevance(results, kws)
        
        ground_truth = kws  # Use keywords as approximate ground truth
        metrics = evaluator.evaluate_query(ground_truth, retrieved_ids)
        
        eval_results.append({
            "query": q,
            "results_count": len(results),
            "duration_ms": round(q_duration * 1000, 1),
            **metrics
        })
        
        print(f"  • Results: {len(results)} products found")
        print(f"  • Precision@{num_results}: {metrics['precision_at_k']:.4f}")
        print(f"  • Recall@{num_results}: {metrics['recall_at_k']:.4f}")
        print(f"  • NDCG@{num_results}: {metrics['ndcg_at_k']:.4f}")
        print(f"  • Keyword relevance: {rel_score:.4f}")
        print(f"  • Latency: {q_duration*1000:.0f}ms")
        
    except Exception as e:
        print(f"⚠️  Error evaluating query '{q}': {str(e)[:100]}")
        eval_results.append({
            "query": q,
            "results_count": 0,
            "duration_ms": 0,
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "ndcg_at_k": 0.0,
        })

# ── Generate summary report ──
summary = generate_evaluation_report(eval_results)
summary["total_queries"] = len(STANDARD_BENCHMARK_QUERIES)
summary["successful_queries"] = sum(1 for r in eval_results if r["results_count"] > 0)
summary["avg_latency_ms"] = round(sum(r["duration_ms"] for r in eval_results) / max(len(eval_results), 1), 1)

print("\n" + "=" * 60)
print("📈 EVALUATION REPORT")
print("=" * 60)
for k, v in summary.items():
    print(f"  • {k}: {v}")

# ── Log to MLflow ──
print("\n📝 Logging evaluation results to MLflow...")
log_mlflow_run_metrics(
    params={
        "catalog": catalog,
        "eval_suite": "standard_benchmark",
        "top_k": num_results,
        "num_queries": len(STANDARD_BENCHMARK_QUERIES),
    },
    metrics={
        "mean_precision_at_k": summary.get("mean_precision_at_k", 0.0),
        "mean_recall_at_k": summary.get("mean_recall_at_k", 0.0),
        "mean_ndcg_at_k": summary.get("mean_ndcg_at_k", 0.0),
        "avg_latency_ms": summary.get("avg_latency_ms", 0.0),
        "success_rate": round(summary["successful_queries"] / max(summary["total_queries"], 1), 4),
    },
    run_name="Amazon_Search_Evaluation"
)

duration = time.time() - start_time
logger.log_execution("Evaluation", "search_evaluation", "SUCCESS", 0, summary["total_queries"], duration)
print(f"\n✅ Evaluation complete. Tested {summary['total_queries']} queries in {duration:.2f}s")