# =====================================================================
# Product Search — Search: Vector Search Index Helpers
# =====================================================================
# Manages the Databricks Vector Search endpoint lifecycle and the
# Delta-Sync index creation on gold.product_search_catalog.
#
# Architecture (Option A — Databricks-Managed Embeddings):
#   Gold Product Catalog (searchable_text)
#         ↓
#   Vector Search Delta Sync Index
#         ↓
#   Automatic Embedding Generation (BGE endpoint, managed by Databricks)
#
# The index stays in sync with the Gold table automatically via CDC.
# =====================================================================

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Endpoint Management ───────────────────────────────────────────────

def get_or_create_vs_endpoint(client, endpoint_name: str) -> dict:
    """
    Idempotently creates a Vector Search endpoint.
    Returns the endpoint status dict once the endpoint is ONLINE.

    Args:
        client: VectorSearchClient instance
        endpoint_name: Name of the endpoint to create or fetch

    Returns:
        Endpoint status dictionary
    """
    try:
        endpoint = client.get_endpoint(endpoint_name)
        logger.info(f"Vector Search endpoint '{endpoint_name}' already exists.")
        return endpoint
    except Exception:
        logger.info(f"Creating Vector Search endpoint '{endpoint_name}'...")
        client.create_endpoint(name=endpoint_name, endpoint_type="STANDARD")

    return _wait_for_endpoint_online(client, endpoint_name)


def _wait_for_endpoint_online(client, endpoint_name: str,
                               timeout_minutes: int = 20) -> dict:
    """
    Polls every 30 seconds until the endpoint reaches ONLINE state.
    Raises TimeoutError if the endpoint does not become online within the timeout.
    """
    deadline = time.time() + timeout_minutes * 60
    while time.time() < deadline:
        endpoint = client.get_endpoint(endpoint_name)
        state = endpoint.get("endpoint_status", {}).get("state", "UNKNOWN")
        logger.info(f"Endpoint '{endpoint_name}' state: {state}")
        if state == "ONLINE":
            return endpoint
        if state in ("OFFLINE", "FAILED"):
            raise RuntimeError(
                f"Vector Search endpoint '{endpoint_name}' entered state '{state}'."
            )
        time.sleep(30)
    raise TimeoutError(
        f"Vector Search endpoint '{endpoint_name}' did not become ONLINE "
        f"within {timeout_minutes} minutes."
    )


# ── Index Management ──────────────────────────────────────────────────

def get_or_create_delta_sync_index(
    client,
    endpoint_name: str,
    index_name: str,
    source_table_name: str,
    primary_key: str,
    embedding_source_column: str,
    embedding_model_endpoint_name: str,
    pipeline_type: str = "TRIGGERED",
) -> dict:
    """
    Idempotently creates a Delta Sync Vector Search index with
    Databricks-managed embeddings (Option A architecture).

    The embedding model endpoint generates and maintains embeddings
    automatically from `embedding_source_column` whenever the source
    Delta table changes — no separate embedding generation step needed.

    Args:
        client: VectorSearchClient instance
        endpoint_name: Name of the hosting VS endpoint
        index_name: Fully-qualified index name (catalog.schema.index_name)
        source_table_name: Fully-qualified Gold Delta table (catalog.schema.table)
        primary_key: Primary key column of the source table
        embedding_source_column: Column whose text will be embedded (searchable_text)
        embedding_model_endpoint_name: Databricks embedding endpoint (BGE / other)
        pipeline_type: "TRIGGERED" (manual sync) or "CONTINUOUS" (auto CDC sync)

    Returns:
        Index status dictionary
    """
    try:
        index = client.get_index(endpoint_name=endpoint_name, index_name=index_name)
        logger.info(
            f"Vector Search index '{index_name}' already exists on "
            f"endpoint '{endpoint_name}'. Skipping creation."
        )
        return index
    except Exception:
        logger.info(
            f"Creating Delta Sync index '{index_name}' on endpoint '{endpoint_name}'..."
        )

    index = client.create_delta_sync_index(
        endpoint_name=endpoint_name,
        index_name=index_name,
        source_table_name=source_table_name,
        pipeline_type=pipeline_type,
        primary_key=primary_key,
        embedding_source_column=embedding_source_column,
        embedding_model_endpoint_name=embedding_model_endpoint_name,
    )
    logger.info(f"Delta Sync index '{index_name}' creation initiated.")
    return index


def wait_for_index_online(
    client,
    endpoint_name: str,
    index_name: str,
    timeout_minutes: int = 30,
    poll_interval_seconds: int = 30,
) -> dict:
    """
    Polls until the Vector Search index reaches ONLINE (READY) state.
    Returns the final index status dict.

    Raises TimeoutError if the index does not become online in time.
    Raises RuntimeError if the index enters a terminal failure state.
    """
    deadline = time.time() + timeout_minutes * 60
    while time.time() < deadline:
        index = client.get_index(endpoint_name=endpoint_name, index_name=index_name)
        status = index.describe().get("status", {})
        detailed_state = status.get("detailed_state", "UNKNOWN")
        ready = status.get("ready", False)

        logger.info(
            f"Index '{index_name}' status: {detailed_state} | ready: {ready}"
        )

        if ready or detailed_state in ("ONLINE", "ONLINE_NO_PENDING_UPDATE"):
            logger.info(f"Index '{index_name}' is ONLINE and ready for queries.")
            return index

        if detailed_state in ("FAILED", "OFFLINE"):
            message = status.get("message", "No message provided.")
            raise RuntimeError(
                f"Vector Search index '{index_name}' entered state "
                f"'{detailed_state}': {message}"
            )

        time.sleep(poll_interval_seconds)

    raise TimeoutError(
        f"Vector Search index '{index_name}' did not become ONLINE "
        f"within {timeout_minutes} minutes."
    )


def sync_index(client, endpoint_name: str, index_name: str) -> None:
    """
    Triggers a manual sync of a TRIGGERED pipeline Delta Sync index.
    Use this after the Gold table has been refreshed to pull in new products.
    """
    logger.info(f"Triggering manual sync for index '{index_name}'...")
    index = client.get_index(endpoint_name=endpoint_name, index_name=index_name)
    index.sync()
    logger.info(f"Sync triggered for index '{index_name}'.")
