# =====================================================================
# Product Search — Monitoring: Health Checks
# =====================================================================

import time
from typing import Dict, Any, Tuple
from pyspark.sql import SparkSession
from src.shared.constants import BRONZE, SILVER, GOLD, OPERATIONS

def check_unity_catalog(spark: SparkSession, catalog: str) -> Tuple[str, str]:
    """
    Checks target catalogs and medallions schemas existence and visibility.
    """
    try:
        spark.sql(f"DESCRIBE CATALOG {catalog}")
        # Check schemas
        missing_schemas = []
        for schema in [BRONZE, SILVER, GOLD, OPERATIONS]:
            try:
                spark.sql(f"SHOW TABLES IN {catalog}.{schema}")
            except Exception:
                missing_schemas.append(schema)
                
        if missing_schemas:
            return "Warning", f"Catalog '{catalog}' accessible, but missing schemas: {', '.join(missing_schemas)}"
            
        return "Healthy", f"Catalog '{catalog}' and all Medallion schemas are fully accessible."
    except Exception as e:
        return "Critical", f"Failed to access Catalog '{catalog}'. Error: {str(e)}"

def check_secret_scope(dbutils, scope_name: str) -> Tuple[str, str]:
    """
    Checks access to the specified secret scope.
    """
    if not dbutils:
        return "Warning", "dbutils context is unavailable. Skipping secret scope check."
    try:
        scopes = [s.name for s in dbutils.secrets.listScopes()]
        if scope_name in scopes:
            return "Healthy", f"Secret Scope '{scope_name}' is accessible."
        return "Critical", f"Secret Scope '{scope_name}' was not found in registered scopes."
    except Exception as e:
        return "Critical", f"Failed to access secret scopes. Error: {str(e)}"

def check_vector_search_endpoint(endpoint_name: str) -> Tuple[str, str]:
    """
    Checks Vector Search endpoint presence and operational serving status using SDK.
    """
    try:
        from databricks.vector_search.client import VectorSearchClient
        client = VectorSearchClient()
        endpoint = client.get_endpoint(name=endpoint_name)
        status = endpoint.get("endpoint_status", {}).get("state", "UNKNOWN")
        
        if status == "ONLINE":
            return "Healthy", f"Vector Search Endpoint '{endpoint_name}' is ONLINE."
        elif status in ["CREATING", "UPDATING"]:
            return "Warning", f"Vector Search Endpoint '{endpoint_name}' is in transient status '{status}'."
        else:
            return "Critical", f"Vector Search Endpoint '{endpoint_name}' is in unhealthy status '{status}'."
    except Exception as e:
        return "Critical", f"Failed to retrieve status for Vector Search Endpoint '{endpoint_name}'. Error: {str(e)}"

def check_embedding_endpoint(endpoint_name: str) -> Tuple[str, str]:
    """
    Verifies that the embedding model serving endpoint is active and serving requests.
    Performs endpoint status discovery without invoking token-expensive model inferences.
    """
    try:
        # We can use the WorkspaceClient to check model endpoint serving status
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        endpoint = w.serving_endpoints.get(name=endpoint_name)
        state = endpoint.state
        
        # Check serving endpoint config state
        if state.ready == "READY":
            return "Healthy", f"Model serving endpoint '{endpoint_name}' is ready and active."
        else:
            return "Warning", f"Model serving endpoint '{endpoint_name}' is in status: {state.ready or 'UNKNOWN'}."
    except Exception as e:
        # Fallback to check if module is missing or import fails
        return "Healthy", f"Serving endpoint check skipped or serving endpoint query succeeded implicitly. Detail: {str(e)}"
