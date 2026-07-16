# Databricks notebook source
# MAGIC %md
# MAGIC # Vector Search — Endpoint & Delta Sync Index Setup
# MAGIC **Responsibility**: Creates the Databricks Vector Search endpoint and the
# MAGIC Delta Sync index on `gold.product_search_catalog`, completing Pipeline 1
# MAGIC (Product Indexing Pipeline).
# MAGIC
# MAGIC ## Architecture — Option A (Databricks-Managed Embeddings)
# MAGIC
# MAGIC ```text
# MAGIC Gold Product Catalog  (searchable_text column)
# MAGIC           ↓
# MAGIC  Vector Search Delta Sync Index
# MAGIC           ↓
# MAGIC  Automatic Embedding Generation
# MAGIC  (BGE endpoint, managed by Databricks)
# MAGIC ```
# MAGIC
# MAGIC The index reads `searchable_text` from the Gold table, calls the BGE embedding
# MAGIC endpoint automatically, stores the vectors, and stays in sync via Change Data Feed.
# MAGIC No separate embedding generation step is needed.
# MAGIC
# MAGIC **Pipeline position (Offline — Product Indexing Pipeline — final step):**
# MAGIC ```
# MAGIC PostgreSQL → Bronze → Silver → Gold → CDF Prep → [THIS NOTEBOOK]
# MAGIC ```
# MAGIC
# MAGIC %pip install databricks-vectorsearch pyyaml
# COMMAND ----------
import sys
import time
import uuid
from pathlib import Path
from pyspark.sql import SparkSession

# Add project root to sys.path
try:
    notebook_path = dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get()
    project_root = "/Workspace" + notebook_path.split("/notebooks/")[0]
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    except NameError:
        pass

from databricks.vector_search.client import VectorSearchClient

from src.shared.config import get_config
from src.shared.constants import (
    GOLD, OPERATIONS,
    VECTOR_SEARCH_ENDPOINT_NAME,
    VECTOR_SEARCH_INDEX_NAME,
    EMBEDDING_MODEL_ENDPOINT,
)
from src.shared.logger import get_logger
from src.search.vector_index import (
    get_or_create_vs_endpoint,
    get_or_create_delta_sync_index,
    wait_for_index_online,
)
# COMMAND ----------
spark = SparkSession.builder.getOrCreate()
logger = get_logger("vector_search_index")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",          "product_search_dev",          "Catalog Name")
dbutils.widgets.text("environment",      "dev",                         "Environment (dev/staging/prod)")
dbutils.widgets.text("vs_endpoint",      VECTOR_SEARCH_ENDPOINT_NAME,   "Vector Search Endpoint Name")
dbutils.widgets.text("pipeline_type",    "TRIGGERED",                   "Pipeline Type (TRIGGERED / CONTINUOUS)")
dbutils.widgets.text("wait_for_online",  "true",                        "Wait for Index Online? (true/false)")

config          = get_config(dbutils)
catalog         = config.catalog
vs_endpoint     = dbutils.widgets.get("vs_endpoint").strip()
pipeline_type   = dbutils.widgets.get("pipeline_type").strip().upper()
wait_for_online = dbutils.widgets.get("wait_for_online").strip().lower() == "true"
run_id          = str(uuid.uuid4())

# Fully qualified names
source_table = f"{catalog}.{GOLD}.product_search_catalog"
index_name   = f"{catalog}.{GOLD}.{VECTOR_SEARCH_INDEX_NAME}"

logger.info(
    f"Vector Search setup starting (Run ID: {run_id})\n"
    f"  Endpoint:     {vs_endpoint}\n"
    f"  Source table: {source_table}\n"
    f"  Index name:   {index_name}\n"
    f"  Pipeline:     {pipeline_type}\n"
    f"  Embedding:    {EMBEDDING_MODEL_ENDPOINT}"
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Create / Verify Vector Search Endpoint
# MAGIC
# MAGIC An endpoint must exist before creating an index. If it already exists, this step is a no-op.
# COMMAND ----------
t_start = time.time()

workspace_url = spark.conf.get("spark.databricks.workspaceUrl", "")
if not workspace_url.startswith("http"):
    workspace_url = f"https://{workspace_url}"

logger.info(f"Connecting to Vector Search at workspace: {workspace_url}")

# The VectorSearchClient picks up workspace URL and token automatically
# from the Databricks notebook environment
vsc = VectorSearchClient()

endpoint = get_or_create_vs_endpoint(vsc, vs_endpoint)
logger.info(f"Vector Search endpoint '{vs_endpoint}' is ready.")
print(f"✓ Endpoint '{vs_endpoint}' state: {endpoint.get('endpoint_status', {}).get('state', 'UNKNOWN')}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Create Delta Sync Index
# MAGIC
# MAGIC The Delta Sync index watches `gold.product_search_catalog.searchable_text`,
# MAGIC automatically generates BGE embeddings for every row, and keeps vectors
# MAGIC in sync as products are added or updated (via CDF).
# MAGIC
# MAGIC **No separate embedding generation notebook is needed.**
# COMMAND ----------
logger.info(f"Creating Delta Sync index '{index_name}' on source table '{source_table}'...")

index = get_or_create_delta_sync_index(
    client=vsc,
    endpoint_name=vs_endpoint,
    index_name=index_name,
    source_table_name=source_table,
    pipeline_type=pipeline_type,
    primary_key="product_id",
    embedding_source_column="searchable_text",
    embedding_model_endpoint_name=EMBEDDING_MODEL_ENDPOINT,
)

logger.info(f"Delta Sync index creation initiated for '{index_name}'.")
print(f"✓ Index '{index_name}' created/verified.")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Wait for Index to Come Online
# MAGIC
# MAGIC On initial creation, the index must process all 42,994 products and generate
# MAGIC embeddings before it is ready for queries. This typically takes 5–15 minutes.
# MAGIC
# MAGIC For subsequent syncs after catalog refreshes, only changed rows are re-processed.
# COMMAND ----------
if wait_for_online:
    logger.info("Waiting for index to reach ONLINE state (this may take 10–20 minutes on first run)...")
    index = wait_for_index_online(
        client=vsc,
        endpoint_name=vs_endpoint,
        index_name=index_name,
        timeout_minutes=30,
        poll_interval_seconds=30,
    )
    print(f"✓ Index '{index_name}' is ONLINE and ready for queries.")
else:
    print(
        f"ℹ Index '{index_name}' creation triggered. Set wait_for_online=true to poll for completion."
    )
# COMMAND ----------
# MAGIC %md
# MAGIC ### 4. Verify Index — Run a Quick Test Query
# COMMAND ----------
if wait_for_online:
    logger.info("Running verification query against the new index...")
    test_query = "comfortable ergonomic office chair"

    vs_index = vsc.get_index(endpoint_name=vs_endpoint, index_name=index_name)
    test_results = vs_index.similarity_search(
        query_text=test_query,
        query_type="HYBRID",
        columns=["product_id", "product_name", "category_path", "brand_name"],
        num_results=5,
    )

    result_rows = test_results.get("result", {}).get("data_array", [])
    col_names   = [c["name"] for c in test_results.get("result", {}).get("manifest", {}).get("columns", [])]

    print(f"\nTest query: '{test_query}'")
    print(f"Results returned: {len(result_rows)}")
    for row in result_rows:
        row_dict = dict(zip(col_names, row))
        print(f"  - [{row_dict.get('product_id')}] {row_dict.get('product_name')} | {row_dict.get('category_path')}")
# COMMAND ----------
duration = time.time() - t_start

logger.log_execution(
    spark=spark,
    catalog=catalog,
    task_name="vector_search_index",
    table_name=index_name,
    status="SUCCESS",
    rows_processed=0,
    duration_seconds=duration,
    message=f"Delta Sync index '{index_name}' on endpoint '{vs_endpoint}' created successfully.",
)

logger.success(
    f"Vector Search setup complete. Index '{index_name}' is ready for hybrid semantic search."
)
