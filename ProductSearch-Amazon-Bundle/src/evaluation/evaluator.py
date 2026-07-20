# =====================================================================
# Product Search Amazon — Evaluation: Evaluator Engine
# =====================================================================

from typing import Dict, List, Any
from src.evaluation.metrics import precision_at_k, recall_at_k, ndcg_at_k


class SearchEvaluator:
    def __init__(self, top_k: int = 10):
        self.top_k = top_k

    def evaluate_query(self, ground_truth: List[str], retrieved_ids: List[str]) -> Dict[str, float]:
        p_k = precision_at_k(ground_truth, retrieved_ids, self.top_k)
        r_k = recall_at_k(ground_truth, retrieved_ids, self.top_k)
        
        # Binary relevance NDCG approximation
        actual_rel = [1.0] * len(ground_truth)
        pred_rel = [1.0 if pid in ground_truth else 0.0 for pid in retrieved_ids[:self.top_k]]
        ndcg_val = ndcg_at_k(actual_rel, pred_rel, self.top_k)

        return {
            "precision_at_k": p_k,
            "recall_at_k": r_k,
            "ndcg_at_k": ndcg_val
        }
