"""
Health check and monitoring endpoints
"""
from fastapi import APIRouter
from datetime import datetime
from app.models.schemas import HealthResponse, SearchStats
from app.services.databricks_service import databricks_service
from app.services.search_service import search_service
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/health", tags=["health"])


@router.get("/", response_model=HealthResponse)
async def health_check():
    """
    Basic health check endpoint
    
    **Returns:**
    - Application status
    - Version information
    - Environment
    """
    return {
        "status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {
            "api": "healthy"
        }
    }


@router.get("/detailed", response_model=HealthResponse)
async def detailed_health_check():
    """
    Detailed health check including all backend services
    
    **Checks:**
    - Databricks Vector Search
    - SQL Warehouse
    - Unity Catalog
    - Cache service
    
    **Returns:**
    - Overall system health
    - Individual service status
    """
    try:
        # Check Databricks services
        databricks_health = await databricks_service.health_check()
        
        # Check cache
        cache_stats = await search_service.cache.get_stats()
        cache_status = "healthy" if cache_stats.get("enabled") else "disabled"
        
        # Determine overall status
        all_healthy = all(
            status == "healthy"
            for status in databricks_health.values()
        )
        
        overall_status = "healthy" if all_healthy else "degraded"
        
        return {
            "status": overall_status,
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {
                "api": "healthy",
                "vector_search": databricks_health.get("vector_search", "unknown"),
                "sql_warehouse": databricks_health.get("sql_warehouse", "unknown"),
                "unity_catalog": databricks_health.get("unity_catalog", "unknown"),
                "cache": cache_status
            }
        }
    
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "services": {
                "api": "unhealthy"
            }
        }


@router.get("/stats", response_model=SearchStats)
async def get_statistics():
    """
    Get search and system statistics
    
    **Returns:**
    - Cache statistics (hit rate, memory usage)
    - Top search queries
    - Average search latency
    - Analytics period
    """
    try:
        stats = await search_service.get_search_stats()
        return stats
    
    except Exception as e:
        logger.error("Failed to fetch stats", error=str(e))
        # Return minimal stats on error
        return {
            "cache": {"enabled": False},
            "top_queries": [],
            "analytics_period": "unknown"
        }


@router.get("/ping")
async def ping():
    """
    Simple ping endpoint for load balancer health checks
    
    **Returns:**
    ```json
    {
      "status": "ok",
      "timestamp": "2024-01-15T10:30:00Z"
    }
    ```
    """
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat()
    }
