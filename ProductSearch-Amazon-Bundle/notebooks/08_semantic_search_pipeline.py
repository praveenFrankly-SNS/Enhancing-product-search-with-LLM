# Databricks notebook source
# MAGIC %md
# MAGIC # 08. Semantic & Hybrid Search Execution
# MAGIC Demonstrates vector similarity search and hybrid (semantic + keyword) search against `amazon_product_vs_index`.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("query", "fast charging usb cable", "Search Query")
dbutils.widgets.dropdown("search_type", "semantic", ["semantic", "hybrid"])
dbutils.widgets.text("num_results", "5", "Number of Results")

catalog = dbutils.widgets.get("catalog").strip()
search_query = dbutils.widgets.get("query").strip()
search_type = dbutils.widgets.get("search_type").strip()
num_results = int(dbutils.widgets.get("num_results").strip())

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

from src.search.search_pipeline import (
    execute_amazon_product_search,
    execute_hybrid_search,
    get_vector_index_status
)
import pandas as pd

print(f"🔎 Product Search Execution")
print(f"📦 Catalog: {catalog}")
print(f"🔍 Query: '{search_query}'")
print(f"📊 Search Type: {search_type.upper()}")
print(f"📈 Results: {num_results}")
print("=" * 80)

try:
    # Get index status first
    print("\n📌 Vector Search Index Status:")
    status = get_vector_index_status(
        catalog=catalog,
        gold_schema="gold",
        index_name="amazon_product_vs_index",
        endpoint_name="shared_vs_endpoint"
    )
    if status.get("status") == "active":
        print(f"  ✅ Index is active and ready")
    else:
        print(f"  ⚠️  {status}")
    
    # Execute search
    if search_type == "semantic":
        print(f"\n🔎 Executing SEMANTIC search...")
        results = execute_amazon_product_search(
            query_text=search_query,
            catalog=catalog,
            gold_schema="gold",
            index_name="amazon_product_vs_index",
            endpoint_name="shared_vs_endpoint",
            num_results=num_results
        )
    else:  # hybrid
        print(f"\n🔎 Executing HYBRID search (semantic + keyword)...")
        results = execute_hybrid_search(
            query_text=search_query,
            catalog=catalog,
            gold_schema="gold",
            index_name="amazon_product_vs_index",
            endpoint_name="shared_vs_endpoint",
            num_results=num_results,
            keyword_weight=0.3,
            semantic_weight=0.7
        )
    
    # Display results
    print(f"\n{'='*80}")
    print(f"✅ Found {len(results)} matching products:")
    print(f"{'='*80}\n")
    
    for i, item in enumerate(results, 1):
        print(f"{'─'*80}")
        print(f"Result #{i}:")
        print(f"  🆔 Product ID      : {item.get('product_id')}")
        print(f"  📦 Name            : {item.get('product_name')}")
        print(f"  🏷️  Category        : {item.get('category')}")
        print(f"  💰 Discounted Price: ₹{item.get('discounted_price', 'N/A')}")
        print(f"  💵 Actual Price    : ₹{item.get('actual_price', 'N/A')}")
        print(f"  🏷️  Discount        : {item.get('discount_percentage', 'N/A')}%")
        print(f"  ⭐ Rating          : {item.get('rating', 'N/A')}/5.0 ({item.get('rating_count', 0)} reviews)")
        if search_type == "hybrid" and "score" in item:
            print(f"  📊 Relevance Score : {item.get('score', 0):.4f}")
        print(f"  🔗 Link            : {item.get('product_link', 'N/A')}")
    
    print(f"\n{'='*80}")
    print(f"✅ Search completed successfully")
    
except Exception as e:
    print(f"\n❌ Error during search execution:")
    print(f"  {str(e)}")
    import traceback
    traceback.print_exc()
