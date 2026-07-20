# Databricks notebook source
# MAGIC %md
# MAGIC # 08. Semantic & Hybrid Search Execution
# MAGIC Runs vector similarity search queries against `amazon_product_vs_index`.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("query", "fast charging usb cable", "Search Query")

catalog = dbutils.widgets.get("catalog").strip()
search_query = dbutils.widgets.get("query").strip()

def resolve_and_add_root():
    try:
        ctx = dbutils.notebook.entry_point.getDbutils().notebook().getContext()
        nb_path = ctx.notebookPath().get()
        full_ws_path = nb_path if nb_path.startswith("/Workspace") else f"/Workspace{nb_path}"
        if "/notebooks" in full_ws_path:
            base_dir = full_ws_path.split("/notebooks")[0]
            if base_dir not in sys.path:
                sys.path.insert(0, base_dir)
    except Exception:
        pass

resolve_and_add_root()

from src.search.search_pipeline import execute_amazon_product_search

print(f"🔎 Executing Vector Search for query: '{search_query}' in catalog '{catalog}'...")
results = execute_amazon_product_search(
    query_text=search_query,
    catalog=catalog,
    num_results=5
)

print(f"✅ Found {len(results)} matching products:")
for i, item in enumerate(results, 1):
    print(f"\nResult #{i}:")
    print(f"  • Product ID: {item.get('product_id')}")
    print(f"  • Name      : {item.get('product_name')}")
    print(f"  • Category  : {item.get('category')}")
    print(f"  • Price     : {item.get('discounted_price')}")
    print(f"  • Rating    : {item.get('rating')}")
