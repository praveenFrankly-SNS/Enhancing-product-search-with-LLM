# Databricks notebook source
# MAGIC %md
# MAGIC # 07. Query Understanding & Expansion
# MAGIC Demonstrates query preprocessing, intent classification, and LLM term expansion for search.

# COMMAND ----------
import sys
import os

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

from src.search.query_understanding import parse_search_query

sample_queries = [
    "usb c cable fast charge under 500",
    "noise cancelling bluetooth headphones",
    "ergonomic laptop stand for desk"
]

print("🔎 TESTING LLM QUERY UNDERSTANDING & TERM EXPANSION:")
print("=" * 60)
for q in sample_queries:
    res = parse_search_query(q, dbutils)
    print(f"Original Query  : '{res['original_query']}'")
    print(f"Cleaned Query   : '{res['cleaned_query']}'")
    print(f"Category        : {res['category']}")
    print(f"Expanded Terms  : {res['expanded_terms']}")
    print(f"Price Sensitivity: {res['price_sensitivity']}")
    print("-" * 60)
