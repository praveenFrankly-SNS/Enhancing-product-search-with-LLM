# Databricks notebook source
# MAGIC %md
# MAGIC # Query Understanding — LLM Intent Extraction
# MAGIC **Responsibility**: Demonstrates the Query Understanding stage of Pipeline 2.
# MAGIC
# MAGIC Uses Databricks Foundation Model APIs (LLM) to extract structured intent
# MAGIC from a raw customer query before it enters the search pipeline.
# MAGIC
# MAGIC ## What This Stage Produces
# MAGIC
# MAGIC ```json
# MAGIC {
# MAGIC   "rewritten_query": "ergonomic office chair with lumbar support",
# MAGIC   "category": "Office Chairs",
# MAGIC   "brand": null,
# MAGIC   "price_max": 400.0,
# MAGIC   "filters": {
# MAGIC     "color": "black",
# MAGIC     "material": "leather"
# MAGIC   }
# MAGIC }
# MAGIC ```
# MAGIC
# MAGIC The `filters` dict is open-ended: any attribute extracted by the LLM
# MAGIC (color, material, size, style, etc.) flows through to metadata filtering
# MAGIC without requiring schema changes.
# MAGIC
# MAGIC **Pipeline position (Online — Semantic Search Pipeline):**
# MAGIC ```
# MAGIC Customer Query → [THIS STAGE] → Query Embedding → Hybrid Search → ...
# MAGIC ```
# MAGIC
# MAGIC %pip install pyyaml
# COMMAND ----------
import sys
import json
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

from src.shared.config import get_config
from src.shared.constants import LLM_ENDPOINT
from src.shared.logger import get_logger
from src.search.query_understanding import understand_query, QueryIntent
# COMMAND ----------
spark = SparkSession.builder.getOrCreate()
logger = get_logger("query_understanding")
# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
dbutils.widgets.text("catalog",      "product_search_dev",          "Catalog Name")
dbutils.widgets.text("environment",  "dev",                         "Environment")
dbutils.widgets.text("raw_query",    "comfortable black office chair under $400", "Search Query")
dbutils.widgets.text("llm_endpoint", LLM_ENDPOINT,                  "LLM Endpoint Name")

config       = get_config(dbutils)
raw_query    = dbutils.widgets.get("raw_query").strip()
llm_endpoint = dbutils.widgets.get("llm_endpoint").strip()

# Resolve workspace URL and token from Databricks context
workspace_url = spark.conf.get("spark.databricks.workspaceUrl", "")
if not workspace_url.startswith("http"):
    workspace_url = f"https://{workspace_url}"
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

logger.info(f"Running query understanding for: '{raw_query}' using endpoint: {llm_endpoint}")
# COMMAND ----------
# MAGIC %md
# MAGIC ### 1. Extract Query Intent
# MAGIC
# MAGIC The LLM receives the raw query and returns structured JSON.
# MAGIC The system prompt instructs the model to:
# MAGIC - Rewrite the query for better semantic recall
# MAGIC - Extract category, brand, price ceiling
# MAGIC - Capture any product attribute filters (color, material, etc.) in the `filters` dict
# COMMAND ----------
intent = understand_query(
    raw_query=raw_query,
    workspace_url=workspace_url,
    token=token,
    llm_endpoint=llm_endpoint,
)

print(f"\nInput Query:  '{intent.original_query}'")
print(f"\nExtracted Intent:")
print(json.dumps(intent.to_dict(), indent=2))
# COMMAND ----------
# MAGIC %md
# MAGIC ### 2. Visualize Intent as a Table
# COMMAND ----------
from pyspark.sql.types import StructType, StructField, StringType, FloatType

intent_rows = [{
    "original_query":  intent.original_query,
    "rewritten_query": intent.rewritten_query,
    "category":        intent.category or "(not detected)",
    "brand":           intent.brand    or "(not detected)",
    "price_max":       str(intent.price_max) if intent.price_max else "(not detected)",
    "filters":         json.dumps(intent.filters) if intent.filters else "{}",
}]

intent_df = spark.createDataFrame(intent_rows)
display(intent_df)
# COMMAND ----------
# MAGIC %md
# MAGIC ### 3. Test a Range of WANDS-Style Queries
# MAGIC
# MAGIC Run query understanding across representative query types to demonstrate
# MAGIC how the LLM handles vocabulary mismatches, natural language, and attribute extraction.
# COMMAND ----------
test_queries = [
    "cozy reading chair",
    "something for a small apartment balcony",
    "ashley mid century modern sofa in grey",
    "kids wooden bunk bed under $500",
    "dark wood office desk with storage drawers",
    "outdoor patio set for 6 people waterproof",
]

logger.info(f"Running intent extraction on {len(test_queries)} test queries...")

results = []
for q in test_queries:
    intent_i = understand_query(q, workspace_url, token, llm_endpoint)
    results.append({
        "original_query":  intent_i.original_query,
        "rewritten_query": intent_i.rewritten_query,
        "category":        intent_i.category or "",
        "brand":           intent_i.brand    or "",
        "price_max":       str(intent_i.price_max) if intent_i.price_max else "",
        "filters":         json.dumps(intent_i.filters),
    })

results_df = spark.createDataFrame(results)
display(results_df)
# COMMAND ----------
logger.success("Query understanding demo completed successfully.")
