# =====================================================================
# Product Search Amazon — Search: Hybrid & Vector Search Execution
# =====================================================================

from typing import List, Dict, Any
from databricks.vector_search.client import VectorSearchClient
from pyspark.sql import SparkSession


def execute_amazon_product_search(
    query_text: str,
    catalog: str,
    gold_schema: str = "gold",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "product_search_endpoint",
    num_results: int = 10,
    filters: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    """
    Executes similarity search against Amazon Product Vector Index.
    """
    vsc = VectorSearchClient()
    full_index_name = f"{catalog}.{gold_schema}.{index_name}"
    
    index = vsc.get_index(endpoint_name=endpoint_name, index_name=full_index_name)
    
    results = index.similarity_search(
        query_text=query_text,
        columns=["product_id", "product_name", "category", "discounted_price", "rating", "img_link", "search_document"],
        num_results=num_results,
        filters=filters
    )
    
    output = []
    columns = [col["name"] for col in results.get("manifest", {}).get("columns", [])]
    for row in results.get("result", {}).get("data_array", []):
        row_dict = dict(zip(columns, row))
        output.append(row_dict)
        
    return output
