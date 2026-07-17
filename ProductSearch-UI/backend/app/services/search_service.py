"""
Search service orchestrating query processing, caching, and result retrieval
"""
import time
import asyncio
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
        """Initialize search service"""
        self.databricks = databricks_service
        self.cache = cache_service
        logger.info("Search service initialized")
    
    def normalize_query(self, query: str) -> str:
        """
        Normalize search query for consistent caching and processing
        
        Args:
            query: Raw search query
            
        Returns:
            Normalized query string
        """
        # Sanitize first
        query = sanitize_query(query)
        
        # Convert to lowercase
        query = query.lower()
        
        # Remove extra whitespace
        query = ' '.join(query.split())
        
        # Remove common punctuation that doesn't affect meaning
        punctuation_to_remove = "!?."
        for char in punctuation_to_remove:
            query = query.replace(char, "")
        
        return query
    
    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        use_cache: bool = True
    ) -> Dict[str, Any]:
        """
        Perform semantic product search
        
        Args:
            query: Search query text
            page: Page number (1-indexed)
            page_size: Results per page
            filters: Optional filters (category, brand, price range, etc.)
            use_cache: Whether to use cache
            
        Returns:
            Search results with metadata
        """
        start_time = time.time()
        
        # Validate query
        validate_query(query)
        
        # Normalize query
        normalized_query = self.normalize_query(query)
        
        # Set default page size
        if page_size is None:
            page_size = settings.default_page_size
        
        # Validate pagination
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
            filters=filters
        )
        
        # Check cache first
        cached_result = None
        if use_cache:
            cached_result = await self.cache.get_search_results(
                normalized_query,
                page,
                page_size,
                filters
            )
        
        if cached_result:
            # Add timing info
            cached_result["metadata"]["processing_time_ms"] = int((time.time() - start_time) * 1000)
            cached_result["metadata"]["cached"] = True
            
            logger.info(
                "Returning cached search results",
                query=normalized_query,
                results_count=len(cached_result["results"])
            )
            
            return cached_result
        
        # Execute search
        search_result = await self._execute_search(
            normalized_query,
            page,
            page_size,
            filters
        )
        
        # Add timing
        total_time_ms = int((time.time() - start_time) * 1000)
        search_result["metadata"]["processing_time_ms"] = total_time_ms
        search_result["metadata"]["cached"] = False
        
        # Cache results
        if use_cache:
            await self.cache.set_search_results(
                normalized_query,
                search_result,
                page,
                page_size,
                filters
            )
        
        # Log slow queries
        if total_time_ms > settings.slow_query_threshold_ms:
            logger.warning(
                "Slow query detected",
                query=normalized_query,
                processing_time_ms=total_time_ms,
                threshold_ms=settings.slow_query_threshold_ms
            )
        
        logger.info(
            "Search completed",
            query=normalized_query,
            results_count=len(search_result["results"]),
            processing_time_ms=total_time_ms
        )
        
        return search_result
    
    async def _execute_search(
        self,
        query: str,
        page: int,
        page_size: int,
        filters: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute search against Databricks Vector Search
        
        Args:
            query: Normalized search query
            page: Page number
            page_size: Results per page
            filters: Optional filters
            
        Returns:
            Search results dictionary
        """
        # Calculate how many results to fetch from vector search
        # Fetch more than needed to account for filtering
        vector_search_k = page * page_size + 50
        
        # Perform vector search
        vector_start = time.time()
        vector_result = await self.databricks.vector_search(
            query=query,
            top_k=vector_search_k,
            filters=filters
        )
        vector_time_ms = int((time.time() - vector_start) * 1000)
        
        # Get search results
        search_results = vector_result["results"]
        
        # Filter by similarity threshold
        search_results = [
            r for r in search_results
            if r.get("similarity_score", 0) >= settings.similarity_threshold
        ]
        
        # Pagination
        total_results = len(search_results)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_results = search_results[start_idx:end_idx]
        
        # Extract product IDs
        product_ids = [r["product_id"] for r in page_results]
        
        # Fetch detailed product information in parallel
        products_start = time.time()
        
        # Run product details fetch and cache operations concurrently
        product_details_task = self.databricks.get_product_details(product_ids)
        
        # Execute parallel operations
        product_details = await product_details_task
        
        products_time_ms = int((time.time() - products_start) * 1000)
        
        # Merge vector search results with product details
        enriched_results = []
        for result in page_results:
            product_id = result["product_id"]
            details = product_details.get(product_id, {})
            
            enriched_results.append({
                "product_id": product_id,
                "product_name": details.get("product_name", result.get("product_name")),
                "description": details.get("description", result.get("description")),
                "brand": details.get("brand", result.get("brand")),
                "category": details.get("category", result.get("category")),
                "price": details.get("price"),
                "currency": details.get("currency", "INR"),
                "attributes": details.get("attributes", {}),
                "avg_rating": details.get("avg_rating"),
                "review_count": details.get("review_count", 0),
                "similarity_score": result.get("similarity_score"),
                "image_url": self._generate_image_url(product_id)
            })
        
        return {
            "query": query,
            "total_results": total_results,
            "page": page,
            "page_size": page_size,
            "total_pages": (total_results + page_size - 1) // page_size,
            "results": enriched_results,
            "metadata": {
                "vector_search_time_ms": vector_time_ms,
                "product_fetch_time_ms": products_time_ms,
                "filters_applied": filters or {}
            }
        }
    
    async def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed product information by ID
        
        Args:
            product_id: Product identifier
            
        Returns:
            Product details or None if not found
        """
        # Check cache first
        cached_product = await self.cache.get_product(product_id)
        if cached_product:
            logger.info("Returning cached product", product_id=product_id)
            return cached_product
        
        # Fetch from Databricks
        products = await self.databricks.get_product_details([product_id])
        product = products.get(product_id)
        
        if product:
            # Add image URL
            product["image_url"] = self._generate_image_url(product_id)
            
            # Cache the product
            await self.cache.set_product(product_id, product)
            
            logger.info("Product fetched and cached", product_id=product_id)
        
        return product
    
    async def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """
        Get search suggestions based on partial query
        
        Args:
            partial_query: Partial search query
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested queries
        """
        # This is a simplified implementation
        # In production, you might use a dedicated suggestion service
        # or analyze historical queries
        
        normalized = self.normalize_query(partial_query)
        
        if len(normalized) < 2:
            return []
        
        # For demo purposes, return some common suggestions
        # In production, query the search_query_log table
        suggestions = [
            f"{normalized} {suffix}"
            for suffix in ["laptop", "chair", "desk", "phone", "headphones"]
            if suffix.startswith(normalized) or normalized in suffix
        ]
        
        return suggestions[:limit]
    
    @staticmethod
    def _generate_image_url(product_id: str) -> str:
        """
        Generate product image URL
        
        Args:
            product_id: Product ID
            
        Returns:
            Image URL (placeholder for now)
        """
        # In production, this would point to actual product images
        # stored in cloud storage (S3, Azure Blob, etc.)
        return f"/api/v1/products/{product_id}/image"
    
    async def get_search_stats(self) -> Dict[str, Any]:
        """
        Get search statistics
        
        Returns:
            Dictionary with search statistics
        """
        cache_stats = await self.cache.get_stats()
        analytics = await self.databricks.get_search_analytics(limit=10)
        
        return {
            "cache": cache_stats,
            "top_queries": analytics.get("top_queries", []),
            "analytics_period": analytics.get("period", "unknown")
        }


# Global service instance
search_service = SearchService()
