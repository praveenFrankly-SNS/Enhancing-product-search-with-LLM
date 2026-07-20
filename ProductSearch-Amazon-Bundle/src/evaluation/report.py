# =====================================================================
# Product Search Amazon — Evaluation: Report Generator
# =====================================================================

from typing import Dict, List, Any


def generate_evaluation_report(eval_results: List[Dict[str, Any]]) -> Dict[str, float]:
    """Computes mean metrics across evaluation test suite."""
    if not eval_results:
        return {"mean_precision": 0.0, "mean_recall": 0.0, "mean_ndcg": 0.0}

    mean_p = sum(r.get("precision_at_k", 0.0) for r in eval_results) / len(eval_results)
    mean_r = sum(r.get("recall_at_k", 0.0) for r in eval_results) / len(eval_results)
    mean_ndcg = sum(r.get("ndcg_at_k", 0.0) for r in eval_results) / len(eval_results)

    return {
        "mean_precision_at_k": round(mean_p, 4),
        "mean_recall_at_k": round(mean_r, 4),
        "mean_ndcg_at_k": round(mean_ndcg, 4),
        "total_queries_evaluated": len(eval_results)
    }
