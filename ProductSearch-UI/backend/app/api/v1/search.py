"""
Search API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    SuggestionsResponse,
)
from app.services.search_service import search_service
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_products(request: SearchRequest):
    """
    Perform semantic product search powered by Databricks Vector Search + LLM.

    **Flow:**
    1. LLM query understanding (rewrite + intent extraction via Meta-Llama 3.1 70B)
    2. Vector Search similarity search (BGE-Large-EN embeddings)
    3. SQL Warehouse product detail enrichment (Gold table)
    4. Return ranked, enriched results with full metadata

    **Metadata includes:**
    - `rewritten_query`: LLM-rewritten query for better semantic recall
    - `intent_tokens`: Key concepts extracted by the LLM
    - `model_name`: The embedding model used
    """
    try:
        result = await search_service.search(
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            filters=request.filters,
            use_cache=request.use_cache,
        )
        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Search failed", error=str(e), query=request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search request failed",
        )


@router.get("/", response_model=SearchResponse)
async def search_products_get(
    q: str = Query(..., description="Search query", min_length=1, max_length=200),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=50, description="Results per page"),
    category: Optional[str] = Query(default=None, description="Filter by category"),
    brand: Optional[str] = Query(default=None, description="Filter by brand"),
    min_price: Optional[float] = Query(default=None, description="Minimum price"),
    max_price: Optional[float] = Query(default=None, description="Maximum price"),
    min_rating: Optional[float] = Query(default=None, description="Minimum rating"),
    use_cache: bool = Query(default=True, description="Use cache"),
):
    """
    Perform semantic product search (GET method for browser/URL access).

    **Example:**
    ```
    GET /api/v1/search?q=gaming+laptop&page=1&page_size=20&category=Laptops
    ```
    """
    try:
        filters = {}
        if category:
            filters["category"] = category
        if brand:
            filters["brand"] = brand
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        if min_rating is not None:
            filters["min_rating"] = min_rating

        result = await search_service.search(
            query=q,
            page=page,
            page_size=page_size,
            filters=filters if filters else None,
            use_cache=use_cache,
        )
        return result

    except HTTPException:
        raise

    except Exception as e:
        logger.error("Search failed", error=str(e), query=q)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search request failed",
        )


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_search_suggestions(
    q: str = Query(..., description="Partial search query", min_length=1),
    limit: int = Query(default=5, ge=1, le=10, description="Max suggestions"),
):
    """
    Get LLM-powered search suggestions for autocomplete.

    Uses Databricks Foundation Model API (Meta-Llama 3.1 70B) to generate:
    - **completions**: Auto-completed versions of the partial query
    - **categories**: Relevant product categories
    - **related_suggestions**: Semantically related search queries

    **Example:**
    ```
    GET /api/v1/search/suggestions?q=wireless+headphones&limit=5
    ```
    """
    try:
        result = await search_service.get_suggestions(q, limit)
        return {
            "partial_query": q,
            "completions": result.get("completions", []),
            "categories": result.get("categories", []),
            "related_suggestions": result.get("related_suggestions", []),
        }

    except Exception as e:
        logger.error("Suggestions failed", error=str(e), query=q)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions",
        )
