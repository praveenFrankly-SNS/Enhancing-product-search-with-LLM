# =====================================================================
# Product Search Amazon — MLflow: Metric Collector
# =====================================================================

from typing import Dict, Any


def format_search_eval_metrics(mean_p: float, mean_r: float, mean_ndcg: float) -> Dict[str, float]:
    return {
        "eval_mean_precision_at_k": float(mean_p),
        "eval_mean_recall_at_k": float(mean_r),
        "eval_mean_ndcg_at_k": float(mean_ndcg)
    }
