# =====================================================================
# Product Search Amazon — Embeddings: Generator & Endpoint Verification
# =====================================================================

import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    from databricks.sdk import WorkspaceClient
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    logger.warning("databricks.sdk not available, embedding verification will be limited")


def verify_embedding_endpoint(
    endpoint_name: str = "databricks-bge-large-en",
    workspace_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Verifies that the embedding model serving endpoint exists and is responsive.

    Args:
        endpoint_name: Name of the Databricks serving endpoint for embeddings.
        workspace_client: Optional pre-configured WorkspaceClient.

    Returns:
        Dict with status, endpoint_name, and details.
    """
    if not HAS_SDK:
        return {
            "status": "sdk_unavailable",
            "endpoint_name": endpoint_name,
            "message": "databricks.sdk not installed. Verify endpoint manually in Databricks UI.",
        }

    try:
        w = workspace_client or WorkspaceClient()
        endpoint = w.serving_endpoints.get(name=endpoint_name)
        return {
            "status": "available",
            "endpoint_name": endpoint_name,
            "state": endpoint.state.config_update if hasattr(endpoint.state, "config_update") else "unknown",
            "details": str(endpoint),
        }
    except Exception as e:
        logger.warning(f"Embedding endpoint '{endpoint_name}' check failed: {e}")
        return {
            "status": "unavailable",
            "endpoint_name": endpoint_name,
            "error": str(e),
        }


def generate_embeddings(
    texts: list,
    endpoint_name: str = "databricks-bge-large-en",
    workspace_client: Optional[Any] = None
) -> Dict[str, Any]:
    """
    Generates embeddings for a list of text strings using a Databricks
    Foundation Model serving endpoint.

    Args:
        texts: List of text strings to embed.
        endpoint_name: Databricks serving endpoint name.
        workspace_client: Optional pre-configured WorkspaceClient.

    Returns:
        Dict with embeddings (list), dimension, and status.
    """
    if not HAS_SDK:
        return {
            "status": "sdk_unavailable",
            "message": "databricks.sdk not installed. Cannot generate embeddings.",
            "embeddings": [],
            "dimension": 0,
        }

    if not texts:
        return {"status": "empty_input", "embeddings": [], "dimension": 0}

    try:
        w = workspace_client or WorkspaceClient()
        response = w.serving_endpoints.query(
            name=endpoint_name,
            inputs={"input": texts},
        )

        # Parse response - structure depends on model
        if hasattr(response, "data"):
            embeddings = [item["embedding"] for item in response.data]
        elif isinstance(response, dict) and "data" in response:
            embeddings = [item["embedding"] for item in response["data"]]
        else:
            embeddings = []

        dimension = len(embeddings[0]) if embeddings else 0
        return {
            "status": "success",
            "embeddings": embeddings,
            "dimension": dimension,
            "count": len(embeddings),
        }
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return {"status": "error", "error": str(e), "embeddings": [], "dimension": 0}