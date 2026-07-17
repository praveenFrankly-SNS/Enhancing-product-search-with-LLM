"""
Search service orchestrating query processing, caching, and result retrieval.
Delegates to DatabricksService for all AI/ML operations.
"""
import time
from typing import Dict, Any, List, Optional

from app.core.config import settings
from app.core.security import sanitize_query, validate_query
from app.core.logging import get_logger
from app.services.databricks_service import databricks_service
from app.services.cache_service import cache_service

logger = get_logger(__name__)


class SearchService:
    """Enterprise search service with caching and optimization"""

    def __init__(self):
        self.databricks = databricks_service
        self.cache = cache_service
        logger.info("Search service initialized")

    def normalize_query(self, query: str) -> str:
        """Normalize search query for consistent caching and processing."""
        query = sanitize_query(query)
        query = query.lower()
        query = ' '.join(query.split())
        for char in "!?.":
            query = query.replace(char, "")
        return query

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform semantic product search powered by Databricks Vector Search + LLM.

        Flow:
        1. Normalize query
        2. Check in-memory cache
        3. LLM query understanding (rewrite + intent extraction)
        4. Vector Search similarity search
        5. SQL Warehouse product detail enrichment
        6. Return paginated, enriched results with full metadata
        """
        start_time = time.time()

        validate_query(query)
        normalized_query = self.normalize_query(query)

        if page_size is None:
            page_size = settings.default_page_size
        if page < 1:
            page = 1
        if page_size > settings.max_results_per_page:
            page_size = settings.max_results_per_page

        logger.info(
            "Search requested",
            query=query,
            normalized_query=normalized_query,
            page=page,
            page_size=page_size,
            filters=filters,
        )

        # Cache check
        cached_result = None
        if use_cache:
            cached_result = await self.cache.get_search_results(
                normalized_query, page, page_size, filters
            )

        if cached_result:
            cached_result["metadata"]["processing_time_ms"] = int((time.time() - start_time) * 1000)
            cached_result["metadata"]["cached"] = True
            logger.info("Returning cached results", query=normalized_query)
            return cached_result

        # Execute live search
        search_result = await self._execute_search(normalized_query, page, page_size, filters)

        total_time_ms = int((time.time() - start_time) * 1000)
        search_result["metadata"]["processing_time_ms"] = total_time_ms
        search_result["metadata"]["cached"] = False

        if use_cache:
            await self.cache.set_search_results(
                normalized_query, search_result, page, page_size, filters
            )

        if total_time_ms > settings.slow_query_threshold_ms:
            logger.warning(
                "Slow query detected",
                query=normalized_query,
                processing_time_ms=total_time_ms,
            )

        logger.info(
            "Search completed",
            query=normalized_query,
            results_count=len(search_result["results"]),
            processing_time_ms=total_time_ms,
        )

        return search_result

    async def _execute_search(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Execute search against Databricks Vector Search with SQL enrichment."""

        # Fetch enough results to cover pagination + filtering
        vector_search_k = page * page_size + 50

        vector_start = time.time()
        vector_result = await self.databricks.vector_search(
            query=query,
            top_k=vector_search_k,
            filters=filters,
        )
        vector_time_ms = int((time.time() - vector_start) * 1000)

        search_results = vector_result["results"]
        rewritten_query = vector_result.get("rewritten_query", query)
        intent_tokens = vector_result.get("intent_tokens", [])
        model_name = vector_result.get("model_name", settings.embedding_model_endpoint)

        # Similarity threshold filter
        search_results = [
            r for r in search_results
            if r.get("similarity_score", 0) >= settings.similarity_threshold
        ]

        total_results = len(search_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = search_results[start_idx:end_idx]

        # Fetch enriched product details from SQL Warehouse
        product_ids = [r.get("product_id") for r in page_results if r.get("product_id")]

        products_start = time.time()
        product_details = await self.databricks.get_product_details(product_ids)
        products_time_ms = int((time.time() - products_start) * 1000)

        # Merge vector scores with SQL product details
        enriched_results = []
        for result in page_results:
            product_id = result.get("product_id", "")
            details = product_details.get(product_id, {})

            enriched_results.append({
                "product_id": product_id,
                "product_name": details.get("product_name") or result.get("product_name"),
                "description": details.get("description") or result.get("attribute_summary"),
                "brand": details.get("brand") or result.get("brand_name"),
                "category": details.get("category") or result.get("category_path"),
                "price": details.get("price") or _safe_float(result.get("selling_price")),
                "currency": "INR",
                "attributes": {"summary": details.get("attribute_summary") or result.get("attribute_summary")},
                "avg_rating": details.get("avg_rating") or _safe_float(result.get("average_rating")),
                "review_count": details.get("review_count") or int(result.get("review_count") or 0),
                "similarity_score": result.get("similarity_score"),
                "image_url": None,
                "attribute_summary": details.get("attribute_summary") or result.get("attribute_summary"),
                "review_summary": details.get("review_summary") or result.get("review_summary"),
            })

        return {
            "query": query,
            "total_results": total_results,
            "page": page,
            "page_size": page_size,
            "total_pages": max(1, (total_results + page_size - 1) // page_size),
            "results": enriched_results,
            "metadata": {
                "vector_search_time_ms": vector_time_ms,
                "product_fetch_time_ms": products_time_ms,
                "filters_applied": filters or {},
                "rewritten_query": rewritten_query,
                "intent_tokens": intent_tokens,
                "model_name": model_name,
            },
        }

    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed product information by ID."""
        cached_product = await self.cache.get_product(product_id)
        if cached_product:
            return cached_product

        products = await self.databricks.get_product_details([product_id])
        product = products.get(product_id)

        if product:
            product["image_url"] = None
            await self.cache.set_product(product_id, product)

        return product

    async def get_suggestions(self, partial_query: str, limit: int = 5) -> Dict[str, Any]:
        """
        Get LLM-powered search suggestions from Databricks.

        Returns grouped suggestions: completions, categories, related_suggestions.
        """
        if len(partial_query.strip()) < 2:
            return {"completions": [], "categories": [], "related_suggestions": []}

        return await self.databricks.get_suggestions(partial_query, limit)

    async def get_categories(self) -> List[Dict[str, Any]]:
        """Get all product categories with counts."""
        return await self.databricks.get_categories()

    async def get_brands(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get brands, optionally filtered by category."""
        return await self.databricks.get_brands(category)

    async def get_search_stats(self) -> Dict[str, Any]:
        """Get search statistics."""
        cache_stats = await self.cache.get_stats()
        analytics = await self.databricks.get_search_analytics(limit=10)
        return {
            "cache": cache_stats,
            "top_queries": analytics.get("top_queries", []),
            "analytics_period": analytics.get("period", "unknown"),
        }


def _safe_float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (TypeError, ValueError):
        return None


# Global service instance
search_service = SearchService()
