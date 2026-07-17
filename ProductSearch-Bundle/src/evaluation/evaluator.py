# =====================================================================
# Product Search — Evaluation: Orchestration Loop
# =====================================================================

import time
from typing import List, Dict, Tuple
from src.evaluation.benchmark import load_benchmark_queries, load_relevance_labels, load_product_names_map
from src.evaluation.metrics import precision_at_k, recall_at_k, mean_reciprocal_rank, ndcg_at_k, hit_rate_at_k

def similarity_search_vector_index(endpoint_name: str, index_name: str, query_text: str, k: int) -> List[str]:
    """
    Queries the live Databricks Vector Search index.
    Fails fast with a clear exception message if Vector Search is unavailable.
    """
    try:
        from databricks.vector_search.client import VectorSearchClient
        client = VectorSearchClient()
        index = client.get_index(endpoint_name=endpoint_name, index_name=index_name)
        response = index.similarity_search(
            query_text=query_text,
            columns=["product_id"],
            num_results=k
        )
        
        data = response.get("result", {}).get("data_array", [])
        return [str(row[0]) for row in data]
    except Exception as e:
        raise RuntimeError(
            f"Vector Search query failed for index '{index_name}' on endpoint '{endpoint_name}'. "
            f"Vector Search endpoint is unavailable. Search evaluation requires a live index. "
            f"Error: {str(e)}"
        )

def run_search_evaluation(
    spark,
    catalog: str,
    gold_schema: str,
    endpoint_name: str,
    index_name: str,
    top_k: int = 10
) -> List[Dict]:
    """
    Executes similarity searches across all benchmark queries,
    calculates metrics per query, and compiles detailed results.
    """
    # 1. Load conformed queries, labels, and product catalog name mapping
    queries = load_benchmark_queries(spark, catalog, gold_schema)
    labels_map = load_relevance_labels(spark, catalog, gold_schema)
    product_names = load_product_names_map(spark, catalog, gold_schema)
    
    per_query_results = []
    
    for q in queries:
        qid = q["query_id"]
        query_text = q["original_query"]
        
        # Get conformed relevant products for this query
        gt_relevances = labels_map.get(qid, {})
        gt_ids = {pid for pid, score in gt_relevances.items() if score > 0.0}
        
        # 2. Retrieve Top-K search results (fails fast if index query fails)
        t_start = time.time()
        retrieved_ids = similarity_search_vector_index(endpoint_name, index_name, query_text, top_k)
        retrieval_time = time.time() - t_start
        
        # Resolve conformed product names for inspections
        retrieved_names = [product_names.get(pid, f"(unknown product: {pid})") for pid in retrieved_ids]
        
        # 3. Compute IR metrics
        p = precision_at_k(retrieved_ids, gt_ids, top_k)
        r = recall_at_k(retrieved_ids, gt_ids, top_k)
        mrr = mean_reciprocal_rank(retrieved_ids, gt_ids)
        ndcg = ndcg_at_k(retrieved_ids, gt_relevances, top_k)
        hit = hit_rate_at_k(retrieved_ids, gt_ids, top_k)
        
        per_query_results.append({
            "query_id": qid,
            "query": query_text,
            "retrieved_ids": retrieved_ids,
            "retrieved_names": retrieved_names,
            "retrieval_time_seconds": retrieval_time,
            "precision_at_k": p,
            "recall_at_k": r,
            "mrr": mrr,
            "ndcg_at_k": ndcg,
            "hit_rate_at_k": hit,
            "relevant_count": len(gt_ids)
        })
        
    return per_query_results
