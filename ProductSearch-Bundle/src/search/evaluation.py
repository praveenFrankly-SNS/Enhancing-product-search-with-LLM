# =====================================================================
# Product Search — Search: Offline Evaluation
# =====================================================================
# Computes standard IR evaluation metrics against the WANDS gold labels
# (gold.label table). Uses the full offline search pipeline to generate
# predictions, then scores them against human-annotated relevance.
#
# Metrics Computed:
#   - Precision@K   — fraction of retrieved items that are relevant
#   - Recall@K      — fraction of relevant items that were retrieved
#   - MRR           — Mean Reciprocal Rank of the first relevant result
#   - NDCG@K        — Normalized Discounted Cumulative Gain (graded relevance)
#
# Label Score Mapping (from gold.label):
#   Exact      → 1.0
#   Partial    → 0.75
#   Irrelevant → 0.0
#
# NDCG uses the graded label_score values directly (not binary),
# leveraging the full richness of the WANDS annotation scheme.
# =====================================================================

import math
import logging
from typing import List, Dict, Tuple, Optional, Any

logger = logging.getLogger(__name__)

# Minimum label_score to be considered "relevant" for binary metrics
RELEVANCE_THRESHOLD = 0.5  # Exact (1.0) and Partial (0.75) are relevant


# ── Metric Functions ──────────────────────────────────────────────────

def precision_at_k(
    retrieved_ids: List[str],
    relevant_ids: set,
    k: int,
) -> float:
    """
    Precision@K: fraction of the top-K retrieved items that are relevant.
    A product is relevant if its label_score >= RELEVANCE_THRESHOLD (Exact or Partial).

    Args:
        retrieved_ids: Ordered list of retrieved product_ids (rank 1 first)
        relevant_ids: Set of relevant product_ids for this query
        k: Cutoff depth

    Returns:
        Precision@K in [0, 1]
    """
    if not retrieved_ids or k == 0:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for pid in top_k if pid in relevant_ids)
    return hits / k


def recall_at_k(
    retrieved_ids: List[str],
    relevant_ids: set,
    k: int,
) -> float:
    """
    Recall@K: fraction of all relevant items that appear in the top-K results.
    Perfect recall = 1.0 (all relevant items retrieved in top K).

    Args:
        retrieved_ids: Ordered list of retrieved product_ids
        relevant_ids: Set of relevant product_ids for this query
        k: Cutoff depth

    Returns:
        Recall@K in [0, 1]
    """
    if not relevant_ids:
        return 1.0  # Vacuously true — no relevant items to miss
    top_k = set(retrieved_ids[:k])
    hits = len(top_k & relevant_ids)
    return hits / len(relevant_ids)


def reciprocal_rank(
    retrieved_ids: List[str],
    relevant_ids: set,
) -> float:
    """
    Reciprocal Rank for a single query.
    Returns 1/rank of the first relevant item in the ranked list.
    Returns 0.0 if no relevant item is found.

    Args:
        retrieved_ids: Ordered list of retrieved product_ids
        relevant_ids: Set of relevant product_ids for this query

    Returns:
        Reciprocal rank in (0, 1]
    """
    for rank, pid in enumerate(retrieved_ids, start=1):
        if pid in relevant_ids:
            return 1.0 / rank
    return 0.0


def dcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k: int,
) -> float:
    """
    Discounted Cumulative Gain@K using graded relevance scores.
    Uses log base 2 discounting: DCG = sum(rel_i / log2(i+2)) for i in [0, k-1].

    Args:
        retrieved_ids: Ordered list of retrieved product_ids
        relevance_scores: Dict mapping product_id → label_score (0.0, 0.75, 1.0)
        k: Cutoff depth

    Returns:
        DCG@K value
    """
    dcg = 0.0
    for i, pid in enumerate(retrieved_ids[:k]):
        score = relevance_scores.get(pid, 0.0)
        dcg += score / math.log2(i + 2)
    return dcg


def ndcg_at_k(
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k: int,
) -> float:
    """
    Normalized Discounted Cumulative Gain@K.
    Normalizes DCG@K by the ideal DCG (all items perfectly ranked by relevance).

    Args:
        retrieved_ids: Ordered list of retrieved product_ids
        relevance_scores: Dict mapping product_id → label_score
        k: Cutoff depth

    Returns:
        NDCG@K in [0, 1]
    """
    actual_dcg = dcg_at_k(retrieved_ids, relevance_scores, k)

    # Ideal DCG: sort all labeled products by score descending
    ideal_scores = sorted(relevance_scores.values(), reverse=True)
    ideal_dcg = sum(
        score / math.log2(i + 2) for i, score in enumerate(ideal_scores[:k])
    )

    return actual_dcg / ideal_dcg if ideal_dcg > 0 else 0.0


# ── Per-Query Evaluation ──────────────────────────────────────────────

def evaluate_query(
    query_id: str,
    retrieved_ids: List[str],
    relevance_scores: Dict[str, float],
    k_values: List[int] = (5, 10),
) -> Dict[str, Any]:
    """
    Computes all evaluation metrics for a single query.

    Args:
        query_id: Query identifier
        retrieved_ids: Ordered list of retrieved product_ids
        relevance_scores: Dict mapping product_id → label_score (0.0, 0.75, 1.0)
        k_values: List of cutoff depths to evaluate at

    Returns:
        Dict with all metric values for this query
    """
    relevant_ids = {
        pid for pid, score in relevance_scores.items()
        if score >= RELEVANCE_THRESHOLD
    }

    result = {"query_id": query_id}
    for k in k_values:
        result[f"precision@{k}"] = precision_at_k(retrieved_ids, relevant_ids, k)
        result[f"recall@{k}"]    = recall_at_k(retrieved_ids, relevant_ids, k)
        result[f"ndcg@{k}"]      = ndcg_at_k(retrieved_ids, relevance_scores, k)

    result["mrr"] = reciprocal_rank(retrieved_ids, relevant_ids)
    result["num_relevant"] = len(relevant_ids)
    result["num_retrieved"] = len(retrieved_ids)
    return result


# ── Aggregate Evaluation ──────────────────────────────────────────────

def aggregate_metrics(
    per_query_results: List[Dict[str, Any]],
    k_values: List[int] = (5, 10),
) -> Dict[str, float]:
    """
    Aggregates per-query metrics into macro-averaged scores.

    Args:
        per_query_results: List of dicts from evaluate_query()
        k_values: Must match the k_values used in evaluate_query()

    Returns:
        Dict of aggregated metric → mean score across all queries
    """
    if not per_query_results:
        return {}

    n = len(per_query_results)
    aggregated = {}

    for k in k_values:
        aggregated[f"mean_precision@{k}"] = (
            sum(r[f"precision@{k}"] for r in per_query_results) / n
        )
        aggregated[f"mean_recall@{k}"] = (
            sum(r[f"recall@{k}"] for r in per_query_results) / n
        )
        aggregated[f"mean_ndcg@{k}"] = (
            sum(r[f"ndcg@{k}"] for r in per_query_results) / n
        )

    aggregated["mean_mrr"] = sum(r["mrr"] for r in per_query_results) / n
    aggregated["num_queries_evaluated"] = n
    return aggregated


# ── Spark DataFrame Helpers ───────────────────────────────────────────

def build_relevance_map_from_spark(
    labels_df,
    query_id: str,
) -> Dict[str, float]:
    """
    Builds the relevance_scores dict for a single query_id
    from the Spark Gold labels DataFrame.

    Args:
        labels_df: Spark DataFrame for gold.label with columns
                   (query_id, product_id, label_score)
        query_id: The query to build the map for

    Returns:
        Dict mapping product_id → label_score
    """
    from pyspark.sql import functions as F
    rows = (
        labels_df
        .filter(F.col("query_id") == query_id)
        .select("product_id", "label_score")
        .collect()
    )
    return {str(row["product_id"]): float(row["label_score"]) for row in rows}


def print_evaluation_report(
    aggregate: Dict[str, float],
    k_values: List[int] = (5, 10),
    search_strategy: str = "Hybrid Search",
) -> None:
    """
    Prints a formatted evaluation report to stdout.
    """
    print(f"\n{'='*60}")
    print(f"  Evaluation Report — {search_strategy}")
    print(f"  Queries evaluated: {aggregate.get('num_queries_evaluated', 0)}")
    print(f"{'='*60}")
    for k in k_values:
        print(f"  Precision@{k:<3}  {aggregate.get(f'mean_precision@{k}', 0.0):.4f}")
        print(f"  Recall@{k:<5}    {aggregate.get(f'mean_recall@{k}', 0.0):.4f}")
        print(f"  NDCG@{k:<6}     {aggregate.get(f'mean_ndcg@{k}', 0.0):.4f}")
        print()
    print(f"  MRR              {aggregate.get('mean_mrr', 0.0):.4f}")
    print(f"{'='*60}\n")
