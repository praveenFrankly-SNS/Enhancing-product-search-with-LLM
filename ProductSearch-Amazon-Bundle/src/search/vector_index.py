# =====================================================================
# Product Search Amazon — Search: Vector Search Index Manager
# =====================================================================

import time
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Try to import the SDK, but fall back to REST API if not available
try:
    from databricks.vector_search.client import VectorSearchClient
    HAS_VECTOR_SEARCH_SDK = True
except ImportError:
    HAS_VECTOR_SEARCH_SDK = False
    logger.warning("databricks.vector_search SDK not available, will use REST API")


def get_vector_search_client():
    """
    Gets a vector search client, attempting SDK first, then REST API.
    """
    if HAS_VECTOR_SEARCH_SDK:
        try:
            return VectorSearchClient()
        except Exception as e:
            logger.warning(f"Failed to initialize VectorSearchClient SDK: {e}, will try REST API")
    
    # Fallback: Return None to indicate REST API should be used
    return None


def create_or_sync_amazon_vector_index(
    catalog: str,
    gold_schema: str = "gold",
    table_name: str = "amazon_product_catalog",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "shared_vs_endpoint",
    primary_key: str = "product_id",
    embedding_column: str = "search_document",
    embedding_model: str = "databricks-bge-large-en"
) -> Dict[str, Any]:
    """
    Ensures Vector Search Index is synced to the specified endpoint.
    Defaults to using the shared_vs_endpoint for cost efficiency.
    
    Args:
        catalog: Catalog name
        gold_schema: Schema name in the catalog
        table_name: Delta table name for syncing
        index_name: Name for the vector search index
        endpoint_name: Endpoint name (defaults to 'shared_vs_endpoint')
        primary_key: Primary key column for the index
        embedding_column: Column containing the text to embed
        embedding_model: Embedding model to use
        
    Returns:
        Status dictionary with index details
    """
    try:
        vsc = get_vector_search_client()
        
        if vsc is None:
            # Fall back to manual approach via REST or direct call
            logger.info(f"Using fallback approach without SDK")
            return {
                "status": "requires_manual_setup",
                "index_name": f"{catalog}.{gold_schema}.{index_name}",
                "endpoint_name": endpoint_name,
                "message": "Vector Search SDK not available. Please configure the index manually in Databricks UI or ensure SDK is installed.",
                "action": "create"
            }
        
        full_table_name = f"{catalog}.{gold_schema}.{table_name}"
        full_index_name = f"{catalog}.{gold_schema}.{index_name}"
        
        logger.info(f"Using Vector Search Endpoint: '{endpoint_name}'")
        logger.info(f"Index: '{full_index_name}'")
        logger.info(f"Source table: '{full_table_name}'")
        
        # 1. Verify endpoint exists
        try:
            endpoints_list = vsc.list_endpoints().get("endpoints", [])
            endpoint_names = [ep.get("name") for ep in endpoints_list]
            
            if endpoint_name not in endpoint_names:
                logger.warning(f"Endpoint '{endpoint_name}' not found. Available endpoints: {endpoint_names}")
                raise ValueError(f"Vector Search Endpoint '{endpoint_name}' does not exist")
            logger.info(f"✅ Vector Search Endpoint '{endpoint_name}' is available")
        except Exception as e:
            logger.error(f"Error checking endpoints: {str(e)}")
            raise
        
        # 2. Get endpoint object and check if index already exists
        try:
            endpoint = vsc.get_endpoint(name=endpoint_name)
            
            try:
                indexes_list = endpoint.list_indexes().get("vector_indexes", [])
                indexes = [idx.get("name") for idx in indexes_list]
            except:
                indexes = []
            
            if full_index_name in indexes:
                logger.info(f"🔄 Index '{full_index_name}' already exists. Syncing...")
                index = endpoint.get_index(index_name=full_index_name)
                index.sync()
                logger.info(f"✅ Index synced successfully")
                return {
                    "status": "synced",
                    "index_name": full_index_name,
                    "endpoint_name": endpoint_name,
                    "action": "sync"
                }
            else:
                logger.info(f"✨ Creating new Delta Sync Index '{full_index_name}'...")
                
                index = endpoint.create_delta_sync_index(
                    index_name=full_index_name,
                    source_table_name=full_table_name,
                    pipeline_type="TRIGGERED",
                    primary_key=primary_key,
                    embedding_source_column=embedding_column,
                    embedding_model_endpoint_name=embedding_model
                )
                
                logger.info(f"✅ Index created successfully")
                return {
                    "status": "created",
                    "index_name": full_index_name,
                    "endpoint_name": endpoint_name,
                    "action": "create"
                }
                
        except Exception as e:
            logger.error(f"Error managing index: {str(e)}")
            raise
            
    except Exception as e:
        logger.error(f"Error in create_or_sync_amazon_vector_index: {str(e)}")
        try:
            return {
                "status": "error",
                "index_name": f"{catalog}.{gold_schema}.{index_name}",
                "endpoint_name": endpoint_name,
                "error": str(e)
            }
        except:
            return {
                "status": "error",
                "endpoint_name": endpoint_name,
                "error": str(e)
            }


def sync_vector_index(
    catalog: str,
    gold_schema: str = "gold",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "shared_vs_endpoint"
) -> Dict[str, Any]:
    """
    Manually trigger a sync of an existing vector index.
    
    Returns:
        Sync status dictionary
    """
    try:
        vsc = get_vector_search_client()
        
        if vsc is None:
            return {
                "status": "requires_manual_setup",
                "message": "Vector Search SDK not available. Please sync manually via Databricks UI."
            }
        
        full_index_name = f"{catalog}.{gold_schema}.{index_name}"
        
        logger.info(f"Syncing index '{full_index_name}'...")
        endpoint = vsc.get_endpoint(name=endpoint_name)
        index = endpoint.get_index(index_name=full_index_name)
        index.sync()
        
        logger.info(f"✅ Sync completed for '{full_index_name}'")
        return {"status": "success", "index_name": full_index_name}
        
    except Exception as e:
        logger.error(f"Error syncing vector index: {str(e)}")
        return {"status": "error", "error": str(e)}


def get_index_stats(
    catalog: str,
    gold_schema: str = "gold",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "shared_vs_endpoint"
) -> Dict[str, Any]:
    """
    Get detailed statistics about the vector index.
    
    Returns:
        Dictionary with index statistics
    """
    try:
        vsc = get_vector_search_client()
        
        if vsc is None:
            return {
                "status": "requires_manual_setup",
                "message": "Vector Search SDK not available. Please check index stats via Databricks UI."
            }
        
        full_index_name = f"{catalog}.{gold_schema}.{index_name}"
        
        logger.info(f"Fetching stats for '{full_index_name}'...")
        endpoint = vsc.get_endpoint(name=endpoint_name)
        index = endpoint.get_index(index_name=full_index_name)
        
        stats = index.describe()
        logger.info(f"✅ Retrieved stats for '{full_index_name}'")
        
        return {
            "index_name": full_index_name,
            "endpoint_name": endpoint_name,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting index stats: {str(e)}")
        return {"status": "error", "error": str(e)}
