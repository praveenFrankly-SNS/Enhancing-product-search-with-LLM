# =====================================================================
# Product Search Amazon — Search: Hybrid & Vector Search Execution
# =====================================================================

from typing import List, Dict, Any, Optional
from databricks.vector_search.client import VectorSearchClient
from pyspark.sql import SparkSession
import logging


logger = logging.getLogger(__name__)


def execute_amazon_product_search(
    query_text: str,
    catalog: str,
    gold_schema: str = "gold",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "shared_vs_endpoint",
    num_results: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    min_score: float = 0.0
) -> List[Dict[str, Any]]:
    """
    Executes similarity search against Amazon Product Vector Index.
    
    Args:
        query_text: The search query string
        catalog: Catalog name (e.g., 'product_search_dev')
        gold_schema: Schema name containing the index
        index_name: Name of the vector search index
        endpoint_name: Name of the vector search endpoint (defaults to 'shared_vs_endpoint')
        num_results: Number of results to return
        filters: Optional filters to apply (e.g., price range, category)
        min_score: Minimum relevance score (0.0 to 1.0)
        
    Returns:
        List of matching products with metadata
    """
    try:
        vsc = VectorSearchClient()
        full_index_name = f"{catalog}.{gold_schema}.{index_name}"
        
        logger.info(f"Searching index '{full_index_name}' on endpoint '{endpoint_name}' with query: '{query_text}'")
        
        # Get endpoint and index
        endpoint = vsc.get_endpoint(name=endpoint_name)
        index = endpoint.get_index(index_name=full_index_name)
        
        results = index.similarity_search(
            query_text=query_text,
            columns=[
                "product_id", 
                "product_name", 
                "category", 
                "discounted_price", 
                "actual_price",
                "discount_percentage",
                "rating", 
                "rating_count",
                "img_link", 
                "product_link",
                "search_document"
            ],
            num_results=num_results,
            filters=filters
        )
        
        output = []
        columns = [col["name"] for col in results.get("manifest", {}).get("columns", [])]
        
        for row in results.get("result", {}).get("data_array", []):
            row_dict = dict(zip(columns, row))
            
            # Add score if available in results
            if "score" in row_dict:
                score = float(row_dict.get("score", 0))
                if score >= min_score:
                    output.append(row_dict)
            else:
                output.append(row_dict)
        
        logger.info(f"Found {len(output)} matching products")
        return output
        
    except Exception as e:
        logger.error(f"Error executing vector search: {str(e)}")
        raise


def execute_hybrid_search(
    query_text: str,
    catalog: str,
    gold_schema: str = "gold",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "shared_vs_endpoint",
    num_results: int = 10,
    keyword_weight: float = 0.3,
    semantic_weight: float = 0.7,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Executes hybrid search combining keyword and semantic (vector) search.
    
    Args:
        query_text: The search query
        catalog: Catalog name
        gold_schema: Schema name
        index_name: Vector index name
        endpoint_name: Vector search endpoint (defaults to 'shared_vs_endpoint')
        num_results: Number of results to return
        keyword_weight: Weight for keyword matching (0.0-1.0)
        semantic_weight: Weight for semantic similarity (0.0-1.0)
        filters: Optional filters to apply
        
    Returns:
        Ranked list of matching products
    """
    try:
        spark = SparkSession.builder.getOrCreate()
        full_table = f"`{catalog}`.{gold_schema}.amazon_product_catalog"
        
        # 1. Get semantic results from vector search
        semantic_results = execute_amazon_product_search(
            query_text=query_text,
            catalog=catalog,
            gold_schema=gold_schema,
            index_name=index_name,
            endpoint_name=endpoint_name,
            num_results=num_results * 2,  # Get more results for scoring
            filters=filters
        )
        
        # 2. Get keyword results from SQL
        keyword_query = f"""
        SELECT 
            product_id,
            product_name,
            category,
            discounted_price,
            actual_price,
            discount_percentage,
            rating,
            rating_count,
            img_link,
            product_link,
            search_document
        FROM {full_table}
        WHERE search_document LIKE '%{query_text}%'
        LIMIT {num_results * 2}
        """
        
        keyword_results = spark.sql(keyword_query).collect()
        
        # 3. Combine and rank results
        combined = {}
        
        # Add semantic results with semantic weight
        for i, result in enumerate(semantic_results):
            pid = result.get("product_id")
            if pid:
                score = (1.0 - (i / max(1, len(semantic_results)))) * semantic_weight
                combined[pid] = {**result, "score": score}
        
        # Add/merge keyword results with keyword weight
        for i, result in enumerate(keyword_results):
            pid = result.product_id
            if pid:
                keyword_score = (1.0 - (i / max(1, len(keyword_results)))) * keyword_weight
                if pid in combined:
                    combined[pid]["score"] += keyword_score
                else:
                    combined[pid] = {
                        "product_id": result.product_id,
                        "product_name": result.product_name,
                        "category": result.category,
                        "discounted_price": result.discounted_price,
                        "actual_price": result.actual_price,
                        "discount_percentage": result.discount_percentage,
                        "rating": result.rating,
                        "rating_count": result.rating_count,
                        "img_link": result.img_link,
                        "product_link": result.product_link,
                        "search_document": result.search_document,
                        "score": keyword_score
                    }
        
        # Sort by combined score
        ranked_results = sorted(
            combined.values(),
            key=lambda x: x.get("score", 0),
            reverse=True
        )[:num_results]
        
        logger.info(f"Hybrid search found {len(ranked_results)} results")
        return ranked_results
        
    except Exception as e:
        logger.error(f"Error executing hybrid search: {str(e)}")
        # Fallback to semantic search only
        return execute_amazon_product_search(
            query_text=query_text,
            catalog=catalog,
            gold_schema=gold_schema,
            index_name=index_name,
            endpoint_name=endpoint_name,
            num_results=num_results,
            filters=filters
        )


def get_vector_index_status(
    catalog: str,
    gold_schema: str = "gold",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "shared_vs_endpoint"
) -> Dict[str, Any]:
    """
    Gets detailed status of the vector search index.
    
    Returns:
        Dictionary with index status, size, sync status, etc.
    """
    try:
        vsc = VectorSearchClient()
        full_index_name = f"{catalog}.{gold_schema}.{index_name}"
        
        # Get endpoint and index
        endpoint = vsc.get_endpoint(name=endpoint_name)
        index = endpoint.get_index(index_name=full_index_name)
        
        return {
            "index_name": full_index_name,
            "endpoint_name": endpoint_name,
            "status": "active",
            "index_details": index.describe()
        }
    except Exception as e:
        logger.error(f"Error getting vector index status: {str(e)}")
        return {"status": "error", "message": str(e)}
