# =====================================================================
# Product Search — Evaluation: Information Retrieval (IR) Metrics
# =====================================================================

import math
from typing import List, Set, Dict

def precision_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Computes the fraction of conformed retrieved products that are relevant.
    """
    if not retrieved_ids or not ground_truth_ids or k <= 0:
        return 0.0
        
    top_k_retrieved = retrieved_ids[:k]
    relevant_retrieved = [pid for pid in top_k_retrieved if pid in ground_truth_ids]
    return len(relevant_retrieved) / float(k)

def recall_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Computes the fraction of all conformed relevant products that were retrieved.
    """
    if not ground_truth_ids:
        return 1.0
    if not retrieved_ids or k <= 0:
        return 0.0
        
    top_k_retrieved = retrieved_ids[:k]
    relevant_retrieved = [pid for pid in top_k_retrieved if pid in ground_truth_ids]
    return len(relevant_retrieved) / float(len(ground_truth_ids))

def mean_reciprocal_rank(retrieved_ids: List[str], ground_truth_ids: Set[str]) -> float:
    """
    Computes the reciprocal rank of the first conformed relevant result in the list.
    """
    if not retrieved_ids or not ground_truth_ids:
        return 0.0
        
    for index, pid in enumerate(retrieved_ids):
        if pid in ground_truth_ids:
            return 1.0 / (index + 1)
            
    return 0.0

def ndcg_at_k(retrieved_ids: List[str], ground_truth_relevance_map: Dict[str, float], k: int) -> float:
    """
    Computes the Normalized Discounted Cumulative Gain (NDCG) using graded relevance weights.
    Exact = 1.0, Partial = 0.75, Irrelevant = 0.0.
    """
    if not retrieved_ids or not ground_truth_relevance_map or k <= 0:
        return 0.0
        
    # 1. Compute Discounted Cumulative Gain (DCG@K)
    dcg = 0.0
    top_k_retrieved = retrieved_ids[:k]
    for index, pid in enumerate(top_k_retrieved):
        rel = ground_truth_relevance_map.get(pid, 0.0)
        # Using the standard DCG formulation: rel_i / log2(i + 1) where rank is (index + 1)
        dcg += rel / math.log2(index + 2)
        
    # 2. Compute Ideal Discounted Cumulative Gain (IDCG@K)
    # Sort all available ground truth relevance scores in descending order
    ideal_relevances = sorted(ground_truth_relevance_map.values(), reverse=True)
    idcg = 0.0
    for index, rel in enumerate(ideal_relevances[:k]):
        idcg += rel / math.log2(index + 2)
        
    if idcg == 0.0:
        return 0.0
        
    return dcg / idcg

def hit_rate_at_k(retrieved_ids: List[str], ground_truth_ids: Set[str], k: int) -> float:
    """
    Computes binary indicator if at least one relevant product was retrieved in top-k.
    """
    if not retrieved_ids or not ground_truth_ids or k <= 0:
        return 0.0
        
    top_k_retrieved = retrieved_ids[:k]
    for pid in top_k_retrieved:
        if pid in ground_truth_ids:
            return 1.0
            
    return 0.0

def aggregate_metrics(per_query_metrics: List[Dict[str, float]]) -> Dict[str, float]:
    """
    Averages metrics across all queries.
    """
    if not per_query_metrics:
        return {
            "precision_at_k": 0.0,
            "recall_at_k": 0.0,
            "mrr": 0.0,
            "ndcg_at_k": 0.0,
            "hit_rate_at_k": 0.0
        }
        
    total_queries = len(per_query_metrics)
    sums = {
        "precision_at_k": 0.0,
        "recall_at_k": 0.0,
        "mrr": 0.0,
        "ndcg_at_k": 0.0,
        "hit_rate_at_k": 0.0
    }
    
    for q_metrics in per_query_metrics:
        for k in sums.keys():
            sums[k] += q_metrics.get(k, 0.0)
            
    return {k: round(v / total_queries, 4) for k, v in sums.items()}
