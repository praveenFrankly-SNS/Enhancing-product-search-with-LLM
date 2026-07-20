# =====================================================================
# Product Search Amazon — Evaluation: Metrics (NDCG, Precision@k, Recall@k)
# =====================================================================

import math
from typing import List


def precision_at_k(actual: List[str], predicted: List[str], k: int = 10) -> float:
    if not predicted or k <= 0:
        return 0.0
    pred_k = predicted[:k]
    relevant = set(actual)
    hits = sum(1 for p in pred_k if p in relevant)
    return hits / float(k)


def recall_at_k(actual: List[str], predicted: List[str], k: int = 10) -> float:
    if not actual or k <= 0:
        return 0.0
    pred_k = predicted[:k]
    relevant = set(actual)
    hits = sum(1 for p in pred_k if p in relevant)
    return hits / float(len(actual))


def ndcg_at_k(actual_relevance: List[float], predicted_relevance: List[float], k: int = 10) -> float:
    def dcg(relevances):
        return sum((2**r - 1) / math.log2(i + 2) for i, r in enumerate(relevances[:k]))

    dcg_val = dcg(predicted_relevance)
    idcg_val = dcg(sorted(actual_relevance, reverse=True))
    if idcg_val == 0:
        return 0.0
    return dcg_val / idcg_val
