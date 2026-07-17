# Databricks notebook source
# MAGIC %md
# MAGIC # Semantic Search Pipeline (Online — Pipeline 2)
# MAGIC **Responsibility**: Runs the full end-to-end online search pipeline for a customer query.
# MAGIC
# MAGIC ## Pipeline Flow
# MAGIC
# MAGIC ```
# MAGIC Customer Query
# MAGIC       ↓
# MAGIC Query Understanding   — LLM intent extraction (rewrite, category, brand, price, filters)
# MAGIC       ↓
# MAGIC Query Embedding       — single BGE embedding via Foundation Model API
# MAGIC       ↓
# MAGIC Hybrid Vector Search  — dense + BM25 against Delta Sync index (top-K candidates)
# MAGIC       ↓
# MAGIC Metadata Filtering    — category, brand, price ceiling, attribute filters
# MAGIC       ↓
# MAGIC Reranking             — optional cross-encoder rescoring (enable via widget)
# MAGIC       ↓
# MAGIC LLM Response          — optional conversational summary (enable via widget)
# MAGIC       ↓
# MAGIC Final Product Results
# MAGIC ```
# MAGIC
# MAGIC Each stage's intermediate output is displayed for inspection.
# MAGIC
# MAGIC %pip install databricks-vectorsearch pyyaml
# COMMAND ----------
import sys
import json
import time
from pathlib import Path
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

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
    GOLD, VECTOR_SEARCH_ENDPOINT_NAME, VECTOR_SEARCH_INDEX_NAME,
    EMBEDDING_MODEL_ENDPOINT, LLM_ENDPOINT,
)
from src.shared.logger import get_logger
from src.search.query_understanding import understand_query
from src.search.search_pipeline import (
    embed_query, hybrid_search, apply_metadata_filters,
    rerank_results, generate_search_response,
)
# COMMAND ----------
spark = SparkSession.builder.getOrCreate()
logger = get_logger("semantic_search_pipeline")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",             "product_search_dev",                    "Catalog Name")
dbutils.widgets.text("environment",         "dev",                                   "Environment")
dbutils.widgets.text("raw_query",           "comfortable ergonomic chair under $400", "Search Query")
dbutils.widgets.text("top_k",              "20",                                     "Hybrid Search top-K candidates")
dbutils.widgets.text("top_n",              "10",                                     "Final results to return")
dbutils.widgets.text("enable_reranking",    "false",                                 "Enable Reranking (true/false)")
dbutils.widgets.text("enable_llm_response", "false",                                 "Enable LLM Response (true/false)")
dbutils.widgets.text("vs_endpoint",         VECTOR_SEARCH_ENDPOINT_NAME,             "VS Endpoint Name")
dbutils.widgets.text("embedding_endpoint",  EMBEDDING_MODEL_ENDPOINT,                "Embedding Endpoint")
dbutils.widgets.text("llm_endpoint",        LLM_ENDPOINT,                            "LLM Endpoint")

config             = get_config(dbutils)
catalog            = config.catalog
raw_query          = dbutils.widgets.get("raw_query").strip()
top_k              = int(dbutils.widgets.get("top_k").strip())
top_n              = int(dbutils.widgets.get("top_n").strip())
enable_reranking   = dbutils.widgets.get("enable_reranking").strip().lower() == "true"
enable_llm_resp    = dbutils.widgets.get("enable_llm_response").strip().lower() == "true"
vs_endpoint        = dbutils.widgets.get("vs_endpoint").strip()
embedding_endpoint = dbutils.widgets.get("embedding_endpoint").strip()
llm_endpoint       = dbutils.widgets.get("llm_endpoint").strip()

index_name = f"{catalog}.{GOLD}.{VECTOR_SEARCH_INDEX_NAME}"

# Resolve workspace URL and token
workspace_url = spark.conf.get("spark.databricks.workspaceUrl", "")
if not workspace_url.startswith("http"):
    workspace_url = f"https://{workspace_url}"
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

logger.info(
    f"Search pipeline starting for query: '{raw_query}'\n"
    f"  Index:      {index_name}\n"
    f"  Top-K:      {top_k} | Top-N: {top_n}\n"
    f"  Reranking:  {enable_reranking} | LLM Response: {enable_llm_resp}"
)
# COMMAND ----------
# MAGIC %md
# MAGIC ### Stage 1 — Query Understanding
# MAGIC Extract structured intent from the raw query using the LLM.
# COMMAND ----------
t0 = time.time()

intent = understand_query(
    raw_query=raw_query,
    workspace_url=workspace_url,
    token=token,
    llm_endpoint=llm_endpoint,
)

t_understand = time.time() - t0
logger.info(f"Query understanding completed in {t_understand:.2f}s")

print(f"\n{'─'*55}")
print(f"  Stage 1 — Query Understanding  ({t_understand:.2f}s)")
print(f"{'─'*55}")
print(f"  Original:  {intent.original_query}")
print(f"  Rewritten: {intent.rewritten_query}")
print(f"  Category:  {intent.category or '(not detected)'}")
print(f"  Brand:     {intent.brand    or '(not detected)'}")
print(f"  Price Max: {intent.price_max or '(not detected)'}")
print(f"  Filters:   {json.dumps(intent.filters)}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Stage 2 — Query Embedding
# MAGIC Generate a single embedding vector for the rewritten query using the BGE model.
# COMMAND ----------
t1 = time.time()

query_vector = embed_query(
    query_text=intent.rewritten_query,
    workspace_url=workspace_url,
    token=token,
    embedding_endpoint=embedding_endpoint,
)

t_embed = time.time() - t1
print(f"\n{'─'*55}")
print(f"  Stage 2 — Query Embedding  ({t_embed:.2f}s)")
print(f"{'─'*55}")
print(f"  Embedding dimensions: {len(query_vector)}")
print(f"  First 5 values: {[round(v, 4) for v in query_vector[:5]]}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Stage 3 — Hybrid Vector Search (Dense + BM25)
# MAGIC Query the Delta Sync index with the embedding vector and rewritten query text.
# COMMAND ----------
t2 = time.time()

vsc      = VectorSearchClient()
vs_index = vsc.get_index(endpoint_name=vs_endpoint, index_name=index_name)

return_columns = [
    "product_id", "product_name", "category_path", "brand_name",
    "selling_price", "average_rating", "review_count", "attribute_summary",
]

raw_results = hybrid_search(
    vs_index=vs_index,
    query_text=intent.rewritten_query,
    query_vector=query_vector,
    columns=return_columns,
    top_k=top_k,
)

t_search = time.time() - t2
print(f"\n{'─'*55}")
print(f"  Stage 3 — Hybrid Search  ({t_search:.2f}s)")
print(f"{'─'*55}")
print(f"  Retrieved {len(raw_results)} candidates (top-{top_k})")

if raw_results:
    # Preview raw results
    raw_df = spark.createDataFrame([
        {
            "product_id":   str(r.get("product_id", "")),
            "product_name": str(r.get("product_name", "")),
            "category":     str(r.get("category_path", "")),
            "price":        str(r.get("selling_price", "")),
            "rating":       str(r.get("average_rating", "")),
        }
        for r in raw_results
    ])
    display(raw_df.limit(10))
# COMMAND ----------
# MAGIC %md
# MAGIC ### Stage 4 — Metadata Filtering
# MAGIC Apply structured filters from query intent to the retrieved candidates.
# COMMAND ----------
t3 = time.time()

filtered_results = apply_metadata_filters(raw_results, intent)

t_filter = time.time() - t3
print(f"\n{'─'*55}")
print(f"  Stage 4 — Metadata Filtering  ({t_filter:.2f}s)")
print(f"{'─'*55}")
print(f"  {len(raw_results)} candidates → {len(filtered_results)} after filtering")
if intent.has_metadata_filters():
    print(f"  Filters applied: category={intent.category}, brand={intent.brand}, "
          f"price_max={intent.price_max}, attribute_filters={intent.filters}")
else:
    print(f"  No metadata filters were extracted from the query.")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Stage 5 — Reranking (Optional)
# MAGIC Second-stage cross-encoder rescoring. Enable via the `enable_reranking` widget.
# COMMAND ----------
t4 = time.time()

if enable_reranking and filtered_results:
    print(f"\n{'─'*55}")
    print(f"  Stage 5 — Reranking (ENABLED)")
    print(f"{'─'*55}")
    final_results = rerank_results(
        results=filtered_results,
        query_text=intent.rewritten_query,
        workspace_url=workspace_url,
        token=token,
        reranker_endpoint=llm_endpoint,
        top_n=top_n,
    )
    t_rerank = time.time() - t4
    print(f"  Reranking completed in {t_rerank:.2f}s. Top-{top_n} results returned.")
else:
    final_results = filtered_results[:top_n]
    print(f"\n  Stage 5 — Reranking SKIPPED (set enable_reranking=true to enable).")
    print(f"  Returning top-{top_n} of {len(filtered_results)} filtered results.")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Stage 6 — LLM Response Generation (Optional)
# MAGIC Conversational summary of the top results. Enable via the `enable_llm_response` widget.
# COMMAND ----------
t5 = time.time()

if enable_llm_resp and final_results:
    print(f"\n{'─'*55}")
    print(f"  Stage 6 — LLM Response Generation (ENABLED)")
    print(f"{'─'*55}")
    llm_response = generate_search_response(
        results=final_results,
        query_text=raw_query,
        workspace_url=workspace_url,
        token=token,
        llm_endpoint=llm_endpoint,
    )
    t_llm = time.time() - t5
    print(f"\n  Response ({t_llm:.2f}s):\n  \"{llm_response}\"")
else:
    print(f"\n  Stage 6 — LLM Response SKIPPED (set enable_llm_response=true to enable).")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Final Results
# COMMAND ----------
total_duration = time.time() - t0
print(f"\n{'='*55}")
print(f"  SEARCH RESULTS for: \"{raw_query}\"")
print(f"  Total pipeline time: {total_duration:.2f}s")
print(f"{'='*55}\n")

if final_results:
    final_df = spark.createDataFrame([
        {
            "rank":         str(i + 1),
            "product_id":   str(r.get("product_id", "")),
            "product_name": str(r.get("product_name", "")),
            "category":     str(r.get("category_path", "")),
            "brand":        str(r.get("brand_name", "")),
            "price":        str(r.get("selling_price", "")),
            "rating":       str(r.get("average_rating", "")),
        }
        for i, r in enumerate(final_results)
    ])
    display(final_df)
else:
    print("  No results found. Try broader search terms or disable filters.")

logger.success(
    f"Search pipeline completed for '{raw_query}' in {total_duration:.2f}s. "
    f"Returned {len(final_results)} results."
)
