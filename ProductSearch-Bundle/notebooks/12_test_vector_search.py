# Databricks notebook source
# MAGIC %md
# MAGIC # 🔍 Vector Search Index Playground & Query Testing Notebook
# MAGIC **Purpose**: Interactive tool to query and test the live Databricks Vector Search index (`product_search_catalog_index` on `product_search_vs_endpoint`).
# MAGIC 
# MAGIC ### Highlights
# MAGIC - **Single Query Test**: Run any search string (e.g., `coffee machine`, `Door Mat`, `Ergonomic office chair`) and view returned items, raw scores, and calibrated match percentages.
# MAGIC - **Relevance Thresholding**: Test the `0.58` similarity threshold filter to verify how non-catalog queries (e.g., `Smart watch`) are handled.
# MAGIC - **Batch Benchmark Suite**: Run a full suite of common search queries to evaluate catalog search performance.

# COMMAND ----------
# MAGIC %pip install databricks-vectorsearch pyyaml pandas
# COMMAND ----------
import sys
import json
import re
import time
from pathlib import Path
import pandas as pd
from pyspark.sql import SparkSession

spark = SparkSession.builder.getOrCreate()

# COMMAND ----------
# MAGIC %md
# MAGIC ### Configuration Widgets
# COMMAND ----------
# Optional: Override query directly in Python code (leave non-empty to override UI widget)
custom_query_override = "" 

dbutils.widgets.removeAll()
dbutils.widgets.text("catalog",              "product_search_dev", "Catalog Name")
dbutils.widgets.text("endpoint_name",        "product_search_vs_endpoint", "Vector Search Endpoint")
dbutils.widgets.text("index_name",           "product_search_dev.gold.product_search_catalog_index", "Vector Search Index")
dbutils.widgets.text("query",                custom_query_override or "Ergonomic office chair", "Test Search Query")
dbutils.widgets.text("top_k",                "10", "Top K Results")
dbutils.widgets.text("similarity_threshold", "0.58", "Similarity Threshold")
dbutils.widgets.dropdown("run_batch_suite",  "false", ["false", "true"], "Run Full Batch Benchmark Suite?")

catalog = dbutils.widgets.get("catalog")
endpoint_name = dbutils.widgets.get("endpoint_name")
index_name = dbutils.widgets.get("index_name")
user_query = (custom_query_override or dbutils.widgets.get("query")).strip()
top_k = int(dbutils.widgets.get("top_k"))
threshold = float(dbutils.widgets.get("similarity_threshold"))
run_batch = dbutils.widgets.get("run_batch_suite").lower() == "true"

print(f"📌 Target Endpoint:  {endpoint_name}")
print(f"📌 Target Index:     {index_name}")
print(f"📌 Test Query:       '{user_query}'")
print(f"📌 Top K:            {top_k}")
print(f"📌 Threshold:        {threshold}")

# COMMAND ----------
# MAGIC %md
# MAGIC ### Helper Functions for Score Calibration & Vector Search
# COMMAND ----------
from databricks.vector_search.client import VectorSearchClient

def get_vector_search_index(endpoint: str, idx_name: str):
    """Initialize Databricks Vector Search client and retrieve target index."""
    try:
        vs_client = VectorSearchClient(disable_notice=True)
        index = vs_client.get_index(endpoint_name=endpoint, index_name=idx_name)
        print(f"✅ Successfully connected to Vector Search Index: {idx_name}")
        return index
    except Exception as e:
        print(f"❌ Error connecting to Vector Search index: {e}")
        raise e

def execute_search(index, query_text: str, k: int = 10):
    """Execute similarity search against Databricks Vector Search index."""
    columns_to_fetch = [
        "product_id",
        "product_name",
        "category_path",
        "brand_name",
        "selling_price",
        "average_rating",
        "review_count",
        "attribute_summary",
    ]
    
    start_time = time.time()
    response = index.similarity_search(
        query_text=query_text,
        columns=columns_to_fetch,
        num_results=k
    )
    elapsed_ms = int((time.time() - start_time) * 1000)
    
    # Parse results
    manifest = response.get("manifest") or {}
    schema = manifest.get("schema") or {}
    cols_manifest = schema.get("columns") or manifest.get("columns") or response.get("columns") or []
    
    cols = []
    for c in cols_manifest:
        if isinstance(c, dict):
            cols.append(c.get("name"))
        elif isinstance(c, str):
            cols.append(c)
            
    raw_rows = response.get("result", {}).get("data_array") or response.get("data_array") or []
    
    parsed_results = []
    for row in raw_rows:
        if cols and len(row) >= len(cols):
            rdict = dict(zip(cols, row[:len(cols)]))
        else:
            rdict = {}
        score = rdict.pop("score", None) or rdict.pop("__score", None) or 0.6
        rdict["raw_score"] = float(score)
        parsed_results.append(rdict)
        
    return parsed_results, elapsed_ms

def calibrate_and_format(results, query_text: str, min_thresh: float = 0.58):
    """Calibrate similarity scores and label relevance status."""
    if not results:
        return []
    
    query_tokens = [
        t for t in re.findall(r'\w+', query_text.lower())
        if t not in {"with", "for", "the", "and", "under", "in", "of", "to", "a", "an"} and len(t) > 1
    ]
    
    total = len(results)
    raw_scores = [r.get("raw_score", 0.6) for r in results]
    max_raw = max(raw_scores) if raw_scores else 0.7
    min_raw = min(raw_scores) if raw_scores else 0.5

    formatted = []
    for idx, r in enumerate(results):
        raw = r.get("raw_score", 0.6)
        title_lower = str(r.get("product_name", "")).lower()
        cat_lower = str(r.get("category_path", "")).lower()

        title_matches = sum(1 for t in query_tokens if t in title_lower)
        cat_matches = sum(1 for t in query_tokens if t in cat_lower)
        kw_ratio = (title_matches * 1.5 + cat_matches) / max(len(query_tokens), 1) if query_tokens else 0.0

        rank_ratio = idx / max(total - 1, 1)
        top_base = min(0.88 + (0.08 * kw_ratio), 0.97)
        bottom_base = 0.62

        if max_raw > min_raw:
            raw_rel = (raw - min_raw) / (max_raw - min_raw)
        else:
            raw_rel = 1.0 - (rank_ratio * 0.3)

        score_val = bottom_base + (raw_rel * 0.4 + (1 - rank_ratio) * 0.6) * (top_base - bottom_base)
        score_val += (0.03 * kw_ratio)
        final_score = round(min(max(score_val, 0.60), 0.98), 3)

        # Status check
        is_relevant = raw >= min_thresh
        status_label = "✅ Relevant Match" if is_relevant else "⚠️ Low Match (Filtered)"

        formatted.append({
            "Rank": idx + 1,
            "Product ID": r.get("product_id"),
            "Product Name": r.get("product_name"),
            "Category Leaf": str(r.get("category_path", "")).split(">")[-1].strip(),
            "Price (₹)": f"₹{float(r.get('selling_price') or 0):,.2f}",
            "Raw Score": round(raw, 4),
            "Calibrated Score": f"{round(final_score * 100)}%",
            "Relevance Status": status_label,
            "Raw Data": r
        })
    return formatted

# COMMAND ----------
# MAGIC %md
# MAGIC ### 🧪 Single Query Interactive Test
# COMMAND ----------
index = get_vector_search_index(endpoint_name, index_name)

raw_results, elapsed_ms = execute_search(index, user_query, top_k)
formatted_results = calibrate_and_format(raw_results, user_query, threshold)

# Filter relevant items above threshold
relevant_items = [item for item in formatted_results if item["Relevance Status"].startswith("✅")]

print(f"\n📊 Search Results for: '{user_query}'")
print(f"⏱️ Vector Search Latency: {elapsed_ms} ms")
print(f"📦 Total Returned by Vector Search: {len(raw_results)}")
print(f"✨ Relevant Products After Threshold ({threshold}): {len(relevant_items)}\n")

if relevant_items:
    df_display = pd.DataFrame(relevant_items)[["Rank", "Product ID", "Product Name", "Category Leaf", "Price (₹)", "Raw Score", "Calibrated Score", "Relevance Status"]]
    display(df_display)
else:
    print(f"🚫 No products met the relevance threshold ({threshold}) for query '{user_query}'.")
    print("💡 User UI will display the 'No matching products found' screen with catalog category chips.")
    if formatted_results:
        print("\n[Inspecting raw sub-threshold results]:")
        df_sub = pd.DataFrame(formatted_results)[["Rank", "Product ID", "Product Name", "Category Leaf", "Raw Score", "Relevance Status"]]
        display(df_sub)

# COMMAND ----------
# MAGIC %md
# MAGIC ### 🚀 Batch Benchmark Test Suite
# MAGIC Run queries across different product types (`coffee machine`, `Door Mat`, `Smart watch`, `Ergonomic office chair`, `Gaming laptop`, etc.)
# COMMAND ----------
BENCHMARK_QUERIES = [
    "coffee machine",
    "Door Mat",
    "barista comfort anti-fatigue mat",
    "Ergonomic office chair",
    "Smart watch with health tracking",
    "Gaming laptop under $1500",
    "Red flower pot",
    "Sobro smart end table",
    "Outdoor Thermometers",
]

if run_batch or True: # Always ready for execution
    print("=" * 80)
    print("🚀 RUNNING VECTOR SEARCH BENCHMARK TEST SUITE")
    print("=" * 80)
    
    summary_rows = []
    
    for q in BENCHMARK_QUERIES:
        raw_res, ms = execute_search(index, q, k=5)
        formatted_res = calibrate_and_format(raw_res, q, threshold)
        rel_res = [r for r in formatted_res if r["Relevance Status"].startswith("✅")]
        
        top_product = rel_res[0]["Product Name"] if rel_res else "None (Filtered Out)"
        top_raw = rel_res[0]["Raw Score"] if rel_res else (raw_res[0]["raw_score"] if raw_res else 0)
        top_cal = rel_res[0]["Calibrated Score"] if rel_res else "N/A"
        status = f"✅ Passed ({len(rel_res)} items)" if rel_res else "🚫 No Match (Threshold Filtered)"
        
        summary_rows.append({
            "Query": q,
            "Latency (ms)": ms,
            "Status": status,
            "Top Match Product": top_product,
            "Top Raw Score": top_raw,
            "Top Calibrated Match": top_cal
        })
        
    df_summary = pd.DataFrame(summary_rows)
    display(df_summary)
