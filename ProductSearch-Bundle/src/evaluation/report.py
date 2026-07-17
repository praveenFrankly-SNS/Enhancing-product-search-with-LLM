# =====================================================================
# Product Search — Evaluation: Report Exporter
# =====================================================================

import os
import json
import csv
from typing import List, Dict, Tuple

def generate_evaluation_reports(
    per_query_results: List[Dict],
    aggregate_metrics: Dict[str, float],
    output_dir: str
) -> Tuple[str, str, str]:
    """
    Saves and exports JSON and CSV metrics reports.
    Returns (report_json_path, summary_csv_path, per_query_csv_path).
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Sort queries by NDCG to identify best/worst queries
    sorted_queries = sorted(per_query_results, key=lambda x: x["ndcg_at_k"], reverse=True)
    best_queries = sorted_queries[:10]
    worst_queries = sorted_queries[-10:]
    
    # Calculate retrieval statistics
    total_retrieval_time = sum(q["retrieval_time_seconds"] for q in per_query_results)
    avg_retrieval_time = total_retrieval_time / len(per_query_results) if per_query_results else 0.0
    
    total_returned = sum(len(q["retrieved_ids"]) for q in per_query_results)
    avg_returned = total_returned / len(per_query_results) if per_query_results else 0.0
    
    # 2. Build evaluation_report.json
    report_json = {
        "aggregate_metrics": aggregate_metrics,
        "statistics": {
            "total_benchmark_queries": len(per_query_results),
            "average_retrieval_time_seconds": round(avg_retrieval_time, 4),
            "average_returned_results": round(avg_returned, 2)
        },
        "worst_performing_queries": [
            {
                "query": q["query"],
                "precision_at_k": q["precision_at_k"],
                "ndcg_at_k": q["ndcg_at_k"],
                "mrr": q["mrr"]
            }
            for q in worst_queries
        ],
        "best_performing_queries": [
            {
                "query": q["query"],
                "precision_at_k": q["precision_at_k"],
                "ndcg_at_k": q["ndcg_at_k"],
                "mrr": q["mrr"]
            }
            for q in best_queries
        ]
    }
    
    json_path = os.path.join(output_dir, "evaluation_report.json")
    with open(json_path, "w") as f:
        json.dump(report_json, f, indent=2)
        
    # 3. Build evaluation_summary.csv
    summary_path = os.path.join(output_dir, "evaluation_summary.csv")
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Metric", "Average Value"])
        for k, v in aggregate_metrics.items():
            writer.writerow([k, v])
            
    # 4. Build per_query_results.csv
    per_query_path = os.path.join(output_dir, "per_query_results.csv")
    with open(per_query_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Query ID", "Query", "Retrieved Products Count", "Relevant Products Count",
            "Precision", "Recall", "MRR", "NDCG", "Hit Rate", "Retrieval Time Seconds"
        ])
        for q in per_query_results:
            writer.writerow([
                q["query_id"],
                q["query"],
                len(q["retrieved_ids"]),
                q["relevant_count"],
                q["precision_at_k"],
                q["recall_at_k"],
                q["mrr"],
                q["ndcg_at_k"],
                q["hit_rate_at_k"],
                round(q["retrieval_time_seconds"], 4)
            ])
            
    return json_path, summary_path, per_query_path
