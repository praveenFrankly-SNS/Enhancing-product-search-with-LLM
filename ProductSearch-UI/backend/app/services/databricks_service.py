"""
Databricks integration service for semantic product search.

Connects to:
- Databricks Vector Search (embedding-based similarity search)
- Databricks SQL Warehouse (Gold table product details + analytics)
- Databricks Foundation Model APIs (LLM query understanding + suggestions)

Falls back gracefully if credentials are not configured.
"""
import json
import re
import time
import asyncio
import logging
from typing import List, Dict, Any, Optional

import requests

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── LLM System Prompts ────────────────────────────────────────────────────────

_SUGGESTIONS_SYSTEM_PROMPT = """You are a retail product search assistant.

Given a partial search query typed by a user, generate intelligent autocomplete suggestions.

Return ONLY a valid JSON object with these fields:
- "completions": list of 5 complete query strings that naturally complete the user's input (ordered by relevance)
- "categories": list of up to 3 relevant product categories (e.g. "Laptops", "Office Chairs", "Smart Watches")
- "related_suggestions": list of up to 5 semantically related but distinct search queries a user might also want

Focus on products from these categories: Laptops, Audio, Smart Watches, Home & Kitchen, Office Furniture, Monitors.

Respond ONLY with the JSON object. No explanation, no markdown, no code fences.

Example:
Input: "wireless noise cancellation headphones"
Output: {
  "completions": [
    "wireless noise cancellation headphones",
    "wireless noise cancellation headphones for travel",
    "wireless noise cancellation headphones for gaming",
    "wireless noise cancellation headphones under 100",
    "wireless noise cancellation headphones with long battery life"
  ],
  "categories": ["Audio", "Headphones"],
  "related_suggestions": [
    "Best headphones for work from home",
    "Bluetooth headphones with mic",
    "Over ear noise cancelling headphones",
    "Premium wireless headphones",
    "Headphones for online meetings"
  ]
}"""

_QUERY_UNDERSTANDING_SYSTEM_PROMPT = """You are a retail product search query analyzer.

Given a customer search query, extract structured search intent and return ONLY valid JSON.

Your response must be a single JSON object with these fields:
- "rewritten_query" (string): A clean, specific version of the query optimized for semantic search.
- "category" (string or null): The product category if detectable. null if unclear.
- "brand" (string or null): The brand name if mentioned. null if not mentioned.
- "price_max" (number or null): The maximum price if mentioned (numeric only). null if not mentioned.
- "intent_tokens" (list of strings): Key concepts from the query (3-6 words/phrases) that describe what the user wants.
- "filters" (object): Additional attribute filters inferred. {} if none.

Respond ONLY with the JSON object. No explanation, no markdown, no code fences."""


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


def _standardize_product_dict(row_dict: dict) -> dict:
    """Extract product attributes with multi-alias fallbacks for maximum resilience."""
    def get_any(keys: list, default=None):
        for k in keys:
            if k in row_dict and row_dict[k] is not None:
                s_val = str(row_dict[k]).strip()
                if s_val != "" and s_val.lower() != "null" and s_val.lower() != "none":
                    return row_dict[k]
        return default

    pid = str(get_any(["product_id", "id", "sku"], "unknown"))
    name = get_any(["product_name", "product_title", "title", "name", "normalized_name"])
    if not name:
        name = f"Product {pid}" if pid != "unknown" else "Unnamed Product"

    cat = get_any(["category_path", "category_hierarchy", "category", "category_name"], "General")
    brand = get_any(["brand_name", "brand", "manufacturer"], "")
    price = _safe_float(get_any(["selling_price", "price", "list_price", "unit_price"]))
    rating = _safe_float(get_any(["average_rating", "avg_rating", "reviews_average_rating", "rating"]))
    reviews = int(get_any(["review_count", "reviews_rating_count", "rating_count", "num_reviews"]) or 0)
    attr_summary = get_any(["attribute_summary", "normalized_description", "product_features"], "")
    rev_summary = get_any(["review_summary"], "")
    desc = get_any(["searchable_text", "description", "attribute_summary"], attr_summary)

    return {
        "product_id": pid,
        "product_name": name,
        "category_path": cat,
        "brand_name": brand,
        "selling_price": price,
        "average_rating": rating,
        "review_count": reviews,
        "attribute_summary": attr_summary,
        "review_summary": rev_summary,
        "searchable_text": desc,
    }


# ── SQL execution helper ──────────────────────────────────────────────────────

def _run_sql(statement: str) -> List[Dict[str, Any]]:
    """
    Execute a SQL statement on the configured Databricks SQL Warehouse
    using the Statements API (no heavy SDK dependency at import time).
    Returns list of row dicts.
    """
    if not settings.is_databricks_configured or not settings.sql_warehouse_id:
        logger.warning("SQL Warehouse not configured — skipping SQL query")
        return []

    url = f"{settings.databricks_url}/api/2.0/sql/statements"
    headers = {
        "Authorization": f"Bearer {settings.databricks_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "warehouse_id": settings.sql_warehouse_id,
        "statement": statement,
        "wait_timeout": "30s",
        "on_wait_timeout": "CANCEL",
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=35)
        resp.raise_for_status()
        data = resp.json()

        status = data.get("status", {}).get("state", "UNKNOWN")
        if status not in ("SUCCEEDED",):
            logger.error("SQL statement failed", state=status, statement=statement[:100])
            return []

        result = data.get("result", {})
        schema = data.get("manifest", {}).get("schema", {}).get("columns", [])
        col_names = [c["name"] for c in schema]
        rows = result.get("data_array", [])

        return [dict(zip(col_names, row)) for row in rows]

    except requests.exceptions.RequestException as e:
        logger.error("SQL Warehouse request failed", error=str(e))
        return []


_LLM_DISABLED = False


def _call_llm(system_prompt: str, user_content: str) -> Optional[str]:
    """Call Databricks Foundation Model API (chat completions)."""
    global _LLM_DISABLED
    if not settings.is_databricks_configured or _LLM_DISABLED:
        return None

    endpoint_url = (
        f"{settings.databricks_url}/serving-endpoints/"
        f"{settings.llm_endpoint}/invocations"
    )
    headers = {
        "Authorization": f"Bearer {settings.databricks_token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "max_tokens": 512,
        "temperature": 0.0,
    }

    try:
        resp = requests.post(endpoint_url, headers=headers, json=payload, timeout=3.0)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as e:
        if e.response is not None and e.response.status_code == 404:
            logger.warning(
                "LLM serving endpoint not found (404) — disabling LLM query rewriting to maintain fast search latency",
                endpoint=settings.llm_endpoint,
            )
            _LLM_DISABLED = True
        return None
    except Exception as e:
        logger.debug("LLM API call skipped", error=str(e))
        return None


def _parse_json_response(raw: Optional[str]) -> Optional[Dict]:
    """Strip markdown fences and parse JSON from LLM response."""
    if not raw:
        return None
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning("Failed to parse LLM JSON response", raw=raw[:200])
        return None


# ── Main Service ──────────────────────────────────────────────────────────────

class DatabricksService:
    """Service for interacting with Databricks platform (Vector Search + SQL + LLM)."""

    def __init__(self):
        """Initialize Databricks clients."""
        self._vs_client = None
        self._vs_index = None

        if settings.is_databricks_configured:
            try:
                from databricks.vector_search.client import VectorSearchClient
                self._vs_client = VectorSearchClient(
                    workspace_url=settings.databricks_url,
                    personal_access_token=settings.databricks_token,
                    disable_notice=True,
                )
                self._vs_index = self._vs_client.get_index(
                    endpoint_name=settings.vector_search_endpoint,
                    index_name=settings.vector_search_index_name,
                )
                logger.info(
                    "Databricks service initialized (live mode)",
                    endpoint=settings.vector_search_endpoint,
                    index=settings.vector_search_index_name,
                )
            except Exception as e:
                logger.error("Failed to initialize Vector Search client", error=str(e))
                self._vs_client = None
                self._vs_index = None
        else:
            logger.warning(
                "Databricks credentials not configured — service running in degraded mode. "
                "Set DATABRICKS_HOST, DATABRICKS_TOKEN, VECTOR_SEARCH_ENDPOINT, "
                "and SQL_WAREHOUSE_ID in your .env file."
            )

    # ── Vector Search ─────────────────────────────────────────────────────────

    async def vector_search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None,
        dataset: str = "wands",
    ) -> Dict[str, Any]:
        """
        Perform semantic similarity search using Databricks Vector Search.
        Supports dataset routing: 'wands' (30k) or 'amazon' (1.5k rich e-commerce).
        """
        start_time = time.time()

        if top_k is None:
            top_k = settings.vector_search_top_k

        # ── Step 1: LLM Query Understanding ───────────────────────────────────
        intent = await asyncio.get_event_loop().run_in_executor(
            None, self._understand_query, query
        )
        rewritten_query = intent.get("rewritten_query", query)
        intent_tokens = intent.get("intent_tokens", [])
        llm_category = intent.get("category")
        llm_brand = intent.get("brand")
        llm_price_max = intent.get("price_max")

        # ── Step 2: Build metadata filters ────────────────────────────────────
        vs_filters = {}
        active_filters = filters or {}

        if active_filters.get("category") or llm_category:
            cat_col = "category" if dataset == "amazon" else "category_path"
            vs_filters[cat_col] = active_filters.get("category") or llm_category
        if (active_filters.get("brand") or llm_brand) and dataset != "amazon":
            vs_filters["brand_name"] = active_filters.get("brand") or llm_brand

        # ── Step 3: Vector Search ─────────────────────────────────────────────
        results = await asyncio.get_event_loop().run_in_executor(
            None,
            self._execute_vector_search,
            rewritten_query,
            top_k,
            vs_filters if vs_filters else None,
            dataset,
        )

        # ── Step 4: Apply price filtering (post-search) ────────────────────────
        price_max = active_filters.get("max_price") or llm_price_max
        price_min = active_filters.get("min_price")
        min_rating = active_filters.get("min_rating")

        if price_max or price_min or min_rating:
            filtered = []
            for r in results:
                price = r.get("selling_price") or r.get("price") or 0
                rating = r.get("average_rating") or r.get("avg_rating") or 0
                if price_max and price > price_max:
                    continue
                if price_min and price < price_min:
                    continue
                if min_rating and rating < min_rating:
                    continue
                filtered.append(r)
            results = filtered

        elapsed_ms = int((time.time() - start_time) * 1000)
        logger.info(
            "Vector search completed",
            query=query,
            rewritten_query=rewritten_query,
            dataset=dataset,
            results_count=len(results),
            elapsed_ms=elapsed_ms,
        )

        return {
            "results": results,
            "total_count": len(results),
            "elapsed_ms": elapsed_ms,
            "rewritten_query": rewritten_query,
            "intent_tokens": intent_tokens,
            "model_name": settings.embedding_model_endpoint,
        }

    def _understand_query(self, query: str) -> Dict[str, Any]:
        """Call LLM to understand and rewrite the query. Returns intent dict."""
        raw = _call_llm(_QUERY_UNDERSTANDING_SYSTEM_PROMPT, query)
        parsed = _parse_json_response(raw)
        if parsed:
            return parsed
        # Fallback: pass-through with basic token extraction
        tokens = [t for t in query.lower().split() if len(t) > 3 and t not in {"with", "for", "the", "and", "under"}]
        return {
            "rewritten_query": query,
            "category": None,
            "brand": None,
            "price_max": None,
            "intent_tokens": tokens[:6],
            "filters": {},
        }

    def _execute_vector_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict] = None,
        dataset: str = "wands",
    ) -> List[Dict[str, Any]]:
        """Execute vector search against the specified dataset index."""
        if self._vs_client is None:
            logger.warning("Vector Search client not available — returning empty results")
            return []

        target_index_name = (
            settings.amazon_index_name if dataset == "amazon" else settings.wands_index_name
        )

        try:
            target_index = self._vs_client.get_index(
                endpoint_name=settings.vector_search_endpoint,
                index_name=target_index_name,
            )
        except Exception as ie:
            logger.warning(
                "Target index not found or offline, falling back to default index",
                target_index=target_index_name,
                error=str(ie),
            )
            target_index = self._vs_index

        if target_index is None:
            return []

        if dataset == "amazon":
            columns = [
                "product_id",
                "product_name",
                "category",
                "discounted_price",
                "actual_price",
                "discount_percentage",
                "rating",
                "rating_count",
                "about_product",
                "review_title",
                "review_content",
                "img_link",
                "product_link",
            ]
        else:
            columns = [
                "product_id",
                "product_name",
                "category_path",
                "brand_name",
                "selling_price",
                "average_rating",
                "review_count",
                "attribute_summary",
                "review_summary",
            ]

        try:
            kwargs = {
                "query_text": query,
                "columns": columns,
                "num_results": top_k,
            }
            if filters:
                clean_filters = {k: v for k, v in filters.items() if v}
                if clean_filters:
                    kwargs["filters"] = clean_filters

            try:
                response = target_index.similarity_search(**kwargs)
            except Exception as fe:
                if filters and "filters" in kwargs:
                    logger.warning("Vector search filter parameter failed, retrying without filter", error=str(fe))
                    kwargs.pop("filters", None)
                    response = target_index.similarity_search(**kwargs)
                else:
                    raise fe

            manifest = response.get("manifest") or {}
            schema = manifest.get("schema") or {}
            cols_manifest = schema.get("columns") or manifest.get("columns") or response.get("columns") or []

            ret_cols = []
            for c in cols_manifest:
                if isinstance(c, dict):
                    ret_cols.append(c.get("name"))
                elif isinstance(c, str):
                    ret_cols.append(c)

            res_obj = response.get("result")
            if isinstance(res_obj, dict):
                raw_results = res_obj.get("data_array") or []
            else:
                raw_results = response.get("data_array") or []

            results = []
            for row in raw_results:
                if len(ret_cols) > 0 and len(row) >= len(ret_cols):
                    row_dict = dict(zip(ret_cols, row[:len(ret_cols)]))
                else:
                    row_dict = {}

                score = row_dict.pop("score", None) or row_dict.pop("__score", None) or 0.8
                row_dict["similarity_score"] = float(score)

                mapped = _standardize_product_dict(row_dict)
                mapped["similarity_score"] = float(score)
                results.append(mapped)

            return results

        except Exception as e:
            logger.error("Vector search execution failed", error=str(e))
            return []

    async def get_product_details(
        self, product_ids: List[str], dataset: str = "wands"
    ) -> Dict[str, Dict[str, Any]]:
        """Fetch full product details from the Gold table via SQL Warehouse."""
        if not product_ids:
            return {}

        clean_ids = [f"'{pid}'" for pid in product_ids if pid]
        if not clean_ids:
            return {}

        target_table = settings.amazon_table_name if dataset == "amazon" else settings.wands_table_name
        ids_str = ", ".join(clean_ids)
        sql = f"""
            SELECT *
            FROM {target_table}
            WHERE product_id IN ({ids_str})
        """

        rows = await asyncio.get_event_loop().run_in_executor(None, _run_sql, sql)

        products = {}
        for row in rows:
            mapped = _standardize_product_dict(row)
            pid = mapped["product_id"]
            products[pid] = mapped

        return products

    async def get_product_by_id(self, product_id: str, dataset: str = "wands") -> Optional[Dict[str, Any]]:
        """Fetch single product by ID."""
        products = await self.get_product_details([product_id], dataset=dataset)
        return products.get(product_id)

    async def get_related_products(
        self,
        product_id: str,
        query_text: str,
        limit: int = 4,
        dataset: str = "wands",
    ) -> List[Dict[str, Any]]:
        """Get related products using Vector Search similarity."""
        res = await self.vector_search(query=query_text, top_k=limit + 5, dataset=dataset)
        related = [
            r for r in res["results"]
            if r.get("product_id") != product_id
        ]
        return related[:limit]

    # ── Categories & Brands (SQL Warehouse) ──────────────────────────────────

    async def get_categories(self, dataset: str = "wands") -> List[Dict[str, Any]]:
        """Get distinct categories with product counts from Gold table."""
        target_table = settings.amazon_table_name if dataset == "amazon" else settings.wands_table_name
        cat_col = "category" if dataset == "amazon" else "category_path"
        sql = f"""
            SELECT {cat_col} as category_path, COUNT(*) as product_count
            FROM {target_table}
            WHERE {cat_col} IS NOT NULL AND {cat_col} != ''
            GROUP BY {cat_col}
            ORDER BY product_count DESC
            LIMIT 30
        """
        rows = await asyncio.get_event_loop().run_in_executor(None, _run_sql, sql)
        return [
            {"name": r["category_path"], "count": int(r.get("product_count") or 0)}
            for r in rows
        ]

    async def get_brands(self, category: Optional[str] = None, dataset: str = "wands") -> List[Dict[str, Any]]:
        """Get distinct brands with product counts from Gold table."""
        if dataset == "amazon":
            return []
        target_table = settings.wands_table_name
        where_clause = "WHERE brand_name IS NOT NULL AND brand_name != ''"
        if category:
            where_clause += f" AND category_path = '{category}'"

        sql = f"""
            SELECT brand_name, COUNT(*) as product_count
            FROM {target_table}
            {where_clause}
            GROUP BY brand_name
            ORDER BY product_count DESC
            LIMIT 50
        """
        rows = await asyncio.get_event_loop().run_in_executor(None, _run_sql, sql)
        return [
            {"name": r["brand_name"], "count": int(r.get("product_count") or 0)}
            for r in rows
        ]

    # ── LLM-Powered Suggestions ───────────────────────────────────────────────

    async def get_suggestions(self, partial_query: str, limit: int = 5) -> Dict[str, Any]:
        """Generate intelligent autocomplete suggestions using Databricks LLM."""
        return {"completions": [], "categories": [], "related_suggestions": []}

    # ── Analytics ─────────────────────────────────────────────────────────────

    async def get_search_analytics(self, limit: int = 10) -> Dict[str, Any]:
        """Get top popular search queries from the search_query_log table."""
        return {"top_queries": [], "period": "last_7_days"}

    # ── Health Check ──────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Check connectivity to Databricks services."""
        if not settings.is_databricks_configured:
            return {
                "vector_search": "not_configured",
                "sql_warehouse": "not_configured",
                "unity_catalog": "not_configured",
                "llm": "not_configured",
            }

        vs_status = "healthy" if self._vs_client is not None else "unavailable"
        try:
            rows = await asyncio.get_event_loop().run_in_executor(
                None, _run_sql, "SELECT 1 as ping"
            )
            sql_status = "healthy" if rows else "unavailable"
        except Exception:
            sql_status = "error"

        # Check LLM endpoint
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                _call_llm,
                "Say 'ok' and nothing else.",
                "ping",
            )
            llm_status = "healthy" if result else "unavailable"
        except Exception:
            llm_status = "error"

        return {
            "vector_search": vs_status,
            "sql_warehouse": sql_status,
            "unity_catalog": f"{sql_status} ({settings.gold_table})",
            "llm": llm_status,
        }


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# Global service instance
databricks_service = DatabricksService()
