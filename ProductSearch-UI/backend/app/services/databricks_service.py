"""
Databricks integration service for Vector Search and SQL queries
"""
import time
from typing import List, Dict, Any, Optional
from databricks.sdk import WorkspaceClient
from databricks.vector_search.client import VectorSearchClient
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


class DatabricksService:
    """Service for interacting with Databricks platform"""
    
    def __init__(self):
        """Initialize Databricks clients"""
        self.workspace_client = WorkspaceClient(
            host=settings.databricks_url,
            token=settings.databricks_token
        )
        
        self.vector_search_client = VectorSearchClient(
            workspace_url=settings.databricks_url,
            personal_access_token=settings.databricks_token,
            disable_notice=True
        )
        
        logger.info(
            "Databricks service initialized",
            host=settings.databricks_host,
            endpoint=settings.vector_search_endpoint
        )
    
    async def vector_search(
        self,
        query: str,
        top_k: int = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search using Databricks Vector Search
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filters: Optional metadata filters
            
        Returns:
            Dictionary with search results and metadata
        """
        start_time = time.time()
        
        if top_k is None:
            top_k = settings.vector_search_top_k
        
        try:
            # Get the vector search index
            index = self.vector_search_client.get_index(
                endpoint_name=settings.vector_search_endpoint,
                index_name=f"{settings.full_schema_name}.product_embeddings_index"
            )
            
            # Perform similarity search
            results = index.similarity_search(
                query_text=query,
                columns=["product_id", "product_name", "description", "category", "brand"],
                num_results=top_k,
                filters=filters
            )
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "Vector search completed",
                query=query,
                results_count=len(results.get("result", {}).get("data_array", [])),
                elapsed_ms=elapsed_ms
            )
            
            # Transform results
            data_array = results.get("result", {}).get("data_array", [])
            
            search_results = []
            for row in data_array:
                search_results.append({
                    "product_id": row[0],
                    "product_name": row[1],
                    "description": row[2],
                    "category": row[3],
                    "brand": row[4],
                    "similarity_score": row[-1] if len(row) > 5 else None
                })
            
            return {
                "results": search_results,
                "total_count": len(search_results),
                "elapsed_ms": elapsed_ms
            }
        
        except Exception as e:
            logger.error("Vector search failed", error=str(e), query=query)
            raise
    
    async def get_product_details(
        self,
        product_ids: List[str]
    ) -> Dict[str, Dict[str, Any]]:
        """
        Fetch detailed product information from Unity Catalog
        
        Args:
            product_ids: List of product IDs to fetch
            
        Returns:
            Dictionary mapping product_id to product details
        """
        start_time = time.time()
        
        if not product_ids:
            return {}
        
        try:
            # Build SQL query
            ids_list = ", ".join([f"'{pid}'" for pid in product_ids])
            
            query = f"""
            SELECT 
                p.product_id,
                p.product_name,
                p.description,
                p.brand,
                p.category,
                pr.price,
                pr.currency,
                pa.attributes,
                rs.avg_rating,
                rs.review_count
            FROM {settings.full_schema_name}.product_master p
            LEFT JOIN {settings.full_schema_name}.product_pricing pr 
                ON p.product_id = pr.product_id
            LEFT JOIN {settings.full_schema_name}.product_attributes pa 
                ON p.product_id = pa.product_id
            LEFT JOIN {settings.full_schema_name}.product_review_summary rs 
                ON p.product_id = rs.product_id
            WHERE p.product_id IN ({ids_list})
            """
            
            # Execute query using SQL Warehouse
            with self.workspace_client.sql.statement_execution(
                warehouse_id=settings.sql_warehouse_id,
                statement=query,
                timeout=f"{settings.databricks_read_timeout}s"
            ) as cursor:
                result = cursor.fetchall()
            
            elapsed_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                "Product details fetched",
                product_count=len(result),
                elapsed_ms=elapsed_ms
            )
            
            # Transform results to dictionary
            products = {}
            for row in result:
                product_id = row[0]
                products[product_id] = {
                    "product_id": row[0],
                    "product_name": row[1],
                    "description": row[2],
                    "brand": row[3],
                    "category": row[4],
                    "price": float(row[5]) if row[5] else None,
                    "currency": row[6],
                    "attributes": row[7],
                    "avg_rating": float(row[8]) if row[8] else None,
                    "review_count": int(row[9]) if row[9] else 0
                }
            
            return products
        
        except Exception as e:
            logger.error("Failed to fetch product details", error=str(e))
            raise
    
    async def get_search_analytics(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get search analytics from query logs
        
        Args:
            limit: Number of top queries to return
            
        Returns:
            Dictionary with analytics data
        """
        try:
            query = f"""
            SELECT 
                query_text,
                COUNT(*) as search_count,
                AVG(result_count) as avg_results,
                AVG(search_time_ms) as avg_latency_ms
            FROM {settings.full_schema_name}.search_query_log
            WHERE query_date >= CURRENT_DATE() - INTERVAL 7 DAYS
            GROUP BY query_text
            ORDER BY search_count DESC
            LIMIT {limit}
            """
            
            with self.workspace_client.sql.statement_execution(
                warehouse_id=settings.sql_warehouse_id,
                statement=query
            ) as cursor:
                result = cursor.fetchall()
            
            top_queries = [
                {
                    "query": row[0],
                    "count": row[1],
                    "avg_results": row[2],
                    "avg_latency_ms": row[3]
                }
                for row in result
            ]
            
            return {
                "top_queries": top_queries,
                "period": "last_7_days"
            }
        
        except Exception as e:
            logger.error("Failed to fetch analytics", error=str(e))
            return {"top_queries": [], "period": "last_7_days"}
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of Databricks services
        
        Returns:
            Health status dictionary
        """
        health = {
            "vector_search": "unknown",
            "sql_warehouse": "unknown",
            "unity_catalog": "unknown"
        }
        
        # Check Vector Search endpoint
        try:
            endpoints = self.vector_search_client.list_endpoints()
            endpoint_names = [ep.get("name") for ep in endpoints.get("endpoints", [])]
            
            if settings.vector_search_endpoint in endpoint_names:
                health["vector_search"] = "healthy"
            else:
                health["vector_search"] = "endpoint_not_found"
        
        except Exception as e:
            logger.error("Vector Search health check failed", error=str(e))
            health["vector_search"] = "unhealthy"
        
        # Check SQL Warehouse
        try:
            warehouse = self.workspace_client.warehouses.get(settings.sql_warehouse_id)
            if warehouse.state.value == "RUNNING":
                health["sql_warehouse"] = "healthy"
            else:
                health["sql_warehouse"] = warehouse.state.value
        
        except Exception as e:
            logger.error("SQL Warehouse health check failed", error=str(e))
            health["sql_warehouse"] = "unhealthy"
        
        # Check Unity Catalog
        try:
            query = f"SELECT COUNT(*) FROM {settings.full_schema_name}.product_master LIMIT 1"
            with self.workspace_client.sql.statement_execution(
                warehouse_id=settings.sql_warehouse_id,
                statement=query,
                timeout="10s"
            ) as cursor:
                cursor.fetchone()
            
            health["unity_catalog"] = "healthy"
        
        except Exception as e:
            logger.error("Unity Catalog health check failed", error=str(e))
            health["unity_catalog"] = "unhealthy"
        
        return health


# Global service instance
databricks_service = DatabricksService()
