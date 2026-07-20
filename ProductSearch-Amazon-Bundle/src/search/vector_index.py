# =====================================================================
# Product Search Amazon — Search: Vector Search Index Manager
# =====================================================================

import time
from typing import Dict, Any
from databricks.vector_search.client import VectorSearchClient


def create_or_sync_amazon_vector_index(
    catalog: str,
    gold_schema: str = "gold",
    table_name: str = "amazon_product_catalog",
    index_name: str = "amazon_product_vs_index",
    endpoint_name: str = "product_search_endpoint",
    primary_key: str = "product_id",
    embedding_column: str = "search_document"
) -> Dict[str, Any]:
    """
    Ensures Vector Search Endpoint exists and syncs Delta Sync Index for Amazon Catalog.
    """
    vsc = VectorSearchClient()

    # 1. Ensure Endpoint Exists
    endpoints = [ep["name"] for ep in vsc.list_endpoints().get("endpoints", [])]
    if endpoint_name not in endpoints:
        print(f"🚀 Creating Vector Search Endpoint: '{endpoint_name}'...")
        vsc.create_endpoint(name=endpoint_name, endpoint_type="STANDARD")
        
        # Wait for endpoint creation
        for _ in range(30):
            ep_status = vsc.get_endpoint(name=endpoint_name)
            if ep_status.get("endpoint_status", {}).get("state") == "ONLINE":
                print(f"✅ Vector Search Endpoint '{endpoint_name}' is ONLINE.")
                break
            time.sleep(10)

    full_table_name = f"{catalog}.{gold_schema}.{table_name}"
    full_index_name = f"{catalog}.{gold_schema}.{index_name}"

    # 2. Check existing index
    indexes = [idx.get("name") for idx in vsc.list_indexes(endpoint_name=endpoint_name).get("vector_indexes", [])]

    if full_index_name in indexes:
        print(f"🔄 Syncing existing Vector Search Index '{full_index_name}'...")
        index = vsc.get_index(endpoint_name=endpoint_name, index_name=full_index_name)
        index.sync()
        return {"status": "synced", "index_name": full_index_name}
    else:
        print(f"✨ Creating Delta Sync Index '{full_index_name}' on table '{full_table_name}'...")
        index = vsc.create_delta_sync_index(
            endpoint_name=endpoint_name,
            index_name=full_index_name,
            source_table_name=full_table_name,
            pipeline_type="TRIGGERED",
            primary_key=primary_key,
            embedding_source_column=embedding_column,
            embedding_model_endpoint_name="databricks-bge-large-en"
        )
        return {"status": "created", "index_name": full_index_name}
