"""
Search API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.models.schemas import (
    SearchRequest,
    SearchResponse,
    SuggestionsResponse
)
from app.services.search_service import search_service
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def search_products(request: SearchRequest):
    """
    Perform semantic product search
    
    **Flow:**
    1. Validate and normalize query
    2. Check cache for results
    3. If cache miss, query Databricks Vector Search
    4. Fetch detailed product information
    5. Return enriched results with metadata
    
    **Performance:**
    - Target latency: < 2-3 seconds
    - Cache hit latency: < 100ms
    - Supports pagination for large result sets
    """
    try:
        result = await search_service.search(
            query=request.query,
            page=request.page,
            page_size=request.page_size,
            filters=request.filters,
            use_cache=request.use_cache
        )
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error("Search failed", error=str(e), query=request.query)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search request failed"
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
    use_cache: bool = Query(default=True, description="Use cache")
):
    """
    Perform semantic product search (GET method for easy browser/URL access)
    
    **Example:**
    ```
    GET /api/v1/search?q=gaming laptop&page=1&page_size=20&category=Electronics
    ```
    """
    try:
        # Build filters dictionary
        filters = {}
        if category:
            filters["category"] = category
        if brand:
            filters["brand"] = brand
        if min_price is not None:
            filters["min_price"] = min_price
        if max_price is not None:
            filters["max_price"] = max_price
        
        result = await search_service.search(
            query=q,
            page=page,
            page_size=page_size,
            filters=filters if filters else None,
            use_cache=use_cache
        )
        
        return result
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error("Search failed", error=str(e), query=q)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search request failed"
        )


@router.get("/suggestions", response_model=SuggestionsResponse)
async def get_search_suggestions(
    q: str = Query(..., description="Partial search query", min_length=1),
    limit: int = Query(default=5, ge=1, le=10, description="Max suggestions")
):
    """
    Get search query suggestions for autocomplete
    
    **Example:**
    ```
    GET /api/v1/search/suggestions?q=lapt&limit=5
    ```
    
    **Response:**
    ```json
    {
      "partial_query": "lapt",
      "suggestions": [
        "laptop gaming",
        "laptop office",
        "laptop stand"
      ]
    }
    ```
    """
    try:
        suggestions = await search_service.get_suggestions(q, limit)
        
        return {
            "partial_query": q,
            "suggestions": suggestions
        }
    
    except Exception as e:
        logger.error("Suggestions failed", error=str(e), query=q)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get suggestions"
        )
