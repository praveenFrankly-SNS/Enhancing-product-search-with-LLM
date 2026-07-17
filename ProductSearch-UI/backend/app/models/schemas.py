"""
Pydantic models for request/response validation
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator


class SearchRequest(BaseModel):
    """Search request model"""
    query: str = Field(..., description="Search query text", min_length=1, max_length=200)
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=50, description="Results per page")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters")
    use_cache: bool = Field(default=True, description="Whether to use cache")
    
    @validator('query')
    def query_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()


class ProductResult(BaseModel):
    """Product search result model"""
    product_id: str
    product_name: str
    description: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    price: Optional[float]
    currency: str = "INR"
    attributes: Optional[Dict[str, Any]]
    avg_rating: Optional[float]
    review_count: int = 0
    similarity_score: Optional[float]
    image_url: Optional[str]


class SearchMetadata(BaseModel):
    """Search metadata model"""
    vector_search_time_ms: int
    product_fetch_time_ms: int
    processing_time_ms: int
    cached: bool
    filters_applied: Dict[str, Any] = {}


class SearchResponse(BaseModel):
    """Search response model"""
    query: str
    total_results: int
    page: int
    page_size: int
    total_pages: int
    results: List[ProductResult]
    metadata: SearchMetadata


class ProductDetailResponse(BaseModel):
    """Detailed product response model"""
    product_id: str
    product_name: str
    description: Optional[str]
    brand: Optional[str]
    category: Optional[str]
    price: Optional[float]
    currency: str = "INR"
    attributes: Optional[Dict[str, Any]]
    avg_rating: Optional[float]
    review_count: int = 0
    image_url: Optional[str]


class SuggestionsResponse(BaseModel):
    """Search suggestions response"""
    partial_query: str
    suggestions: List[str]


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    version: str
    environment: str
    services: Dict[str, str]


class CacheStats(BaseModel):
    """Cache statistics"""
    enabled: bool
    connected_clients: Optional[int]
    used_memory: Optional[str]
    total_keys: Optional[int]
    hits: Optional[int]
    misses: Optional[int]
    hit_rate: Optional[float]


class TopQuery(BaseModel):
    """Top search query statistics"""
    query: str
    count: int
    avg_results: float
    avg_latency_ms: float


class SearchStats(BaseModel):
    """Search statistics response"""
    cache: CacheStats
    top_queries: List[TopQuery]
    analytics_period: str


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str
    detail: Optional[str]
    timestamp: str
