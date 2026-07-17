# =====================================================================
# Product Search — Search: Unified Online Search Pipeline
# =====================================================================
# Orchestrates the complete Pipeline 2 (Online Semantic Search) flow:
#
#   Customer Query
#         ↓
#   Query Understanding  (LLM intent extraction)
#         ↓
#   Query Embedding      (single embedding via Foundation Model API)
#         ↓
#   Hybrid Vector Search (dense + BM25 against Delta Sync index)
#         ↓
#   Metadata Filtering   (category, brand, price, attribute filters)
#         ↓
#   Reranking            (optional cross-encoder / VS Reranker)
#         ↓
#   LLM Response         (optional conversational summary)
#         ↓
#   Final Results
#
# Each stage is independently callable for testing and inspection.
# =====================================================================

import json
import logging
import requests
from typing import Optional, List, Dict, Any

from src.search.query_understanding import QueryIntent

logger = logging.getLogger(__name__)


# ── Stage 1: Query Embedding ──────────────────────────────────────────

def embed_query(
    query_text: str,
    workspace_url: str,
    token: str,
    embedding_endpoint: str = "databricks-bge-large-en",
) -> List[float]:
    """
    Generates a single embedding vector for the search query using the
    Databricks Foundation Model API. The same model that the Vector Search
    Delta Sync Index uses, ensuring embedding space alignment.

    Args:
        query_text: The (optionally rewritten) customer query string
        workspace_url: Databricks workspace base URL
        token: Databricks access token
        embedding_endpoint: Foundation Model API endpoint for embedding

    Returns:
        List of floats representing the query embedding vector
    """
    endpoint_url = (
        f"{workspace_url.rstrip('/')}/serving-endpoints/{embedding_endpoint}/invocations"
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {"input": [query_text]}

    response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data["data"][0]["embedding"]


# ── Stage 2: Hybrid Vector Search ────────────────────────────────────

def hybrid_search(
    vs_index,
    query_text: str,
    query_vector: List[float],
    columns: List[str],
    top_k: int = 20,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Executes a hybrid (dense + BM25) search against the Vector Search index.
    Returns the raw top-K candidate results.

    Args:
        vs_index: VectorSearchIndex object from the Databricks SDK
        query_text: The query string (used for BM25 component)
        query_vector: The dense query embedding vector
        columns: Columns to return from the index
        top_k: Number of candidates to retrieve
        filters: Optional dict of metadata filters for index pushdown

    Returns:
        List of result dicts with the requested columns + similarity score
    """
    search_kwargs = dict(
        query_vector=query_vector,
        query_text=query_text,
        query_type="HYBRID",
        columns=columns,
        num_results=top_k,
    )
    if filters:
        search_kwargs["filters_json"] = json.dumps(filters)

    response = vs_index.similarity_search(**search_kwargs)
    results = response.get("result", {}).get("data_array", [])
    col_names = [c["name"] for c in response.get("result", {}).get("manifest", {}).get("columns", [])]
    return [dict(zip(col_names, row)) for row in results]


# ── Stage 3: Metadata Filtering ───────────────────────────────────────

def apply_metadata_filters(
    results: List[Dict[str, Any]],
    intent: QueryIntent,
) -> List[Dict[str, Any]]:
    """
    Post-retrieval metadata filter applied to the top-K candidates.
    Handles filters that weren't pushed into the VS index query.

    Filters applied (when present in intent):
      - category: case-insensitive substring match on category_path
      - brand: case-insensitive exact match on brand_name
      - price_max: upper bound on selling_price
      - intent.filters: key-value attribute matching (best effort)

    Args:
        results: Raw search results from hybrid_search()
        intent: Extracted QueryIntent with filter fields

    Returns:
        Filtered list of results
    """
    filtered = results

    if intent.category:
        cat = intent.category.lower()
        filtered = [
            r for r in filtered
            if cat in (r.get("category_path") or "").lower()
        ]

    if intent.brand:
        brand = intent.brand.lower()
        filtered = [
            r for r in filtered
            if brand == (r.get("brand_name") or "").lower()
        ]

    if intent.price_max is not None:
        filtered = [
            r for r in filtered
            if r.get("selling_price") is None
            or r.get("selling_price") <= intent.price_max
        ]

    # Apply extensible attribute filters from the filters dict
    for attr_key, attr_value in (intent.filters or {}).items():
        attr_value_lower = str(attr_value).lower()
        filtered = [
            r for r in filtered
            if attr_value_lower in (r.get("attribute_summary") or "").lower()
        ]

    logger.info(
        f"Metadata filtering: {len(results)} candidates → {len(filtered)} after filter."
    )
    return filtered


# ── Stage 4: Reranking (Optional) ────────────────────────────────────

def rerank_results(
    results: List[Dict[str, Any]],
    query_text: str,
    workspace_url: str,
    token: str,
    reranker_endpoint: str = "databricks-meta-llama-3-1-70b-instruct",
    top_n: int = 10,
) -> List[Dict[str, Any]]:
    """
    Optional second-stage reranking using an LLM-based cross-encoder.
    Re-scores candidate results based on query-product relevance.

    When the Databricks Vector Search Reranker is available in your
    workspace, prefer using it directly via the VS SDK's rerank() method.
    This function provides an LLM-based fallback reranker.

    Args:
        results: Filtered candidate products from apply_metadata_filters()
        query_text: The (optionally rewritten) customer query
        workspace_url: Databricks workspace base URL
        token: Databricks access token
        reranker_endpoint: LLM endpoint to use for scoring
        top_n: Number of results to return after reranking

    Returns:
        Reranked and truncated list of top results
    """
    if not results:
        return results

    # Build a simple scoring prompt for each candidate
    system_prompt = (
        "You are a product search relevance scorer. "
        "Given a query and a product description, score the product's relevance "
        "on a scale of 0.0 (completely irrelevant) to 1.0 (perfectly relevant). "
        "Respond ONLY with a single float number. No explanation."
    )

    endpoint_url = (
        f"{workspace_url.rstrip('/')}/serving-endpoints/{reranker_endpoint}/invocations"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    scored_results = []
    for result in results:
        product_text = (
            f"Name: {result.get('product_name', '')}\n"
            f"Category: {result.get('category_path', '')}\n"
            f"Attributes: {result.get('attribute_summary', '')}"
        )
        user_message = f"Query: {query_text}\n\nProduct:\n{product_text}"

        try:
            response = requests.post(
                endpoint_url,
                headers=headers,
                json={
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "max_tokens": 8,
                    "temperature": 0.0,
                },
                timeout=15,
            )
            response.raise_for_status()
            score_str = response.json()["choices"][0]["message"]["content"].strip()
            score = float(score_str)
        except Exception as e:
            logger.warning(f"Reranker failed for product '{result.get('product_id')}': {e}")
            score = result.get("score", 0.0) or 0.0

        scored_results.append({**result, "rerank_score": score})

    scored_results.sort(key=lambda x: x.get("rerank_score", 0.0), reverse=True)
    logger.info(f"Reranking complete: returning top {top_n} of {len(scored_results)} candidates.")
    return scored_results[:top_n]


# ── Stage 5: LLM Response Generation (Optional) ──────────────────────

def generate_search_response(
    results: List[Dict[str, Any]],
    query_text: str,
    workspace_url: str,
    token: str,
    llm_endpoint: str = "databricks-meta-llama-3-1-70b-instruct",
    top_n: int = 5,
) -> str:
    """
    Optional conversational LLM response summarizing the top search results
    in natural language. Useful for chat-style interfaces.

    When the user simply wants a ranked list of products, skip this stage
    and present the results table directly.

    Args:
        results: Final ranked search results
        query_text: Original customer query
        workspace_url: Databricks workspace base URL
        token: Databricks access token
        llm_endpoint: Foundation Model API endpoint for response generation
        top_n: Number of top products to summarize

    Returns:
        Natural language response string
    """
    if not results:
        return "I couldn't find any products matching your search. Try different search terms."

    top_products = results[:top_n]
    products_text = "\n".join([
        f"- {r.get('product_name', 'Unknown')} | "
        f"Category: {r.get('category_path', 'N/A')} | "
        f"Price: ${r.get('selling_price', 'N/A')} | "
        f"Rating: {r.get('average_rating', 'N/A')}"
        for r in top_products
    ])

    system_prompt = (
        "You are a helpful retail shopping assistant. "
        "Given a customer's search query and a list of matching products, "
        "write a friendly 2-3 sentence summary highlighting the best options "
        "and key features relevant to the customer's needs. "
        "Be concise and helpful."
    )
    user_message = (
        f"Customer searched for: \"{query_text}\"\n\n"
        f"Top matching products:\n{products_text}"
    )

    endpoint_url = (
        f"{workspace_url.rstrip('/')}/serving-endpoints/{llm_endpoint}/invocations"
    )
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    try:
        response = requests.post(
            endpoint_url,
            headers=headers,
            json={
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 256,
                "temperature": 0.3,
            },
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f"LLM response generation failed: {e}")
        return f"Found {len(results)} products matching '{query_text}'."


# ── Unified Pipeline Entry Point ──────────────────────────────────────

def run_search_pipeline(
    raw_query: str,
    vs_index,
    workspace_url: str,
    token: str,
    embedding_endpoint: str = "databricks-bge-large-en",
    llm_endpoint: str = "databricks-meta-llama-3-1-70b-instruct",
    intent: Optional[QueryIntent] = None,
    columns: Optional[List[str]] = None,
    top_k: int = 20,
    top_n: int = 10,
    enable_reranking: bool = False,
    enable_llm_response: bool = False,
) -> Dict[str, Any]:
    """
    Runs the complete Online Semantic Search Pipeline (Pipeline 2) for a query.

    Flow:
      raw_query → [Query Understanding] → QueryIntent
               → [Query Embedding]      → vector
               → [Hybrid Search]        → top-K candidates
               → [Metadata Filtering]   → filtered candidates
               → [Reranking]            → top-N (optional)
               → [LLM Response]         → summary string (optional)

    Args:
        raw_query: Customer's raw search query string
        vs_index: Databricks VectorSearchIndex object
        workspace_url: Databricks workspace URL
        token: Databricks PAT or service principal token
        embedding_endpoint: Endpoint name for embedding generation
        llm_endpoint: Endpoint name for query understanding + LLM response
        intent: Pre-computed QueryIntent (skip LLM call if already available)
        columns: Columns to return from the index (defaults to standard set)
        top_k: Number of raw hybrid search candidates
        top_n: Final number of results to return
        enable_reranking: Whether to run the optional reranking stage
        enable_llm_response: Whether to generate an LLM conversational response

    Returns:
        dict with keys:
            - intent (QueryIntent): Extracted query intent
            - results (list): Ranked product results
            - llm_response (str|None): Conversational response if enabled
            - pipeline_stages (dict): Per-stage candidate counts for debugging
    """
    default_columns = [
        "product_id", "product_name", "category_path", "brand_name",
        "selling_price", "average_rating", "review_count",
        "attribute_summary", "searchable_text",
    ]
    if columns is None:
        columns = default_columns

    pipeline_stages = {}

    # Stage 1 — Query Understanding (skip if intent already supplied)
    if intent is None:
        from src.search.query_understanding import understand_query
        intent = understand_query(raw_query, workspace_url, token, llm_endpoint)

    query_for_search = intent.rewritten_query or raw_query
    logger.info(f"Query: '{raw_query}' → Rewritten: '{query_for_search}'")

    # Stage 2 — Query Embedding
    query_vector = embed_query(query_for_search, workspace_url, token, embedding_endpoint)

    # Stage 3 — Hybrid Vector Search
    raw_results = hybrid_search(
        vs_index=vs_index,
        query_text=query_for_search,
        query_vector=query_vector,
        columns=columns,
        top_k=top_k,
    )
    pipeline_stages["after_hybrid_search"] = len(raw_results)

    # Stage 4 — Metadata Filtering
    filtered_results = apply_metadata_filters(raw_results, intent)
    pipeline_stages["after_metadata_filter"] = len(filtered_results)

    # Stage 5 — Reranking (optional)
    final_results = filtered_results
    if enable_reranking and final_results:
        final_results = rerank_results(
            results=final_results,
            query_text=query_for_search,
            workspace_url=workspace_url,
            token=token,
            reranker_endpoint=llm_endpoint,
            top_n=top_n,
        )
    else:
        final_results = final_results[:top_n]
    pipeline_stages["after_reranking"] = len(final_results)

    # Stage 6 — LLM Response (optional)
    llm_response = None
    if enable_llm_response and final_results:
        llm_response = generate_search_response(
            results=final_results,
            query_text=raw_query,
            workspace_url=workspace_url,
            token=token,
            llm_endpoint=llm_endpoint,
        )

    return {
        "intent": intent,
        "results": final_results,
        "llm_response": llm_response,
        "pipeline_stages": pipeline_stages,
    }
