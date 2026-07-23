# Databricks notebook source
# MAGIC %md
# MAGIC # 08. Semantic & Hybrid Search Execution
# MAGIC Demonstrates vector similarity search and hybrid (semantic + keyword) search against `amazon_product_vs_index`.
# MAGIC Includes explicit error checking and result validation.

# COMMAND ----------
import sys
import os
import traceback

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
    get_vector_index_status,
    execute_sql_keyword_search
)
import pandas as pd

print(f"🔎 Product Search Execution")
print(f"📦 Catalog: {catalog}")
print(f"🔍 Query: '{search_query}'")
print(f"📊 Search Type: {search_type.upper()}")
print(f"📈 Results: {num_results}")
print("=" * 80)

try:
    # ===== DATA VALIDATION =====
    print("\n1️⃣  Data Validation:")
    print("-" * 80)
    
    # Check if gold table exists and has data
    gold_table = f"`{catalog}`.gold.amazon_product_catalog"
    try:
        product_count = spark.sql(f"SELECT COUNT(*) as cnt FROM {gold_table}").collect()[0]['cnt']
        print(f"✅ Products in catalog: {product_count}")
        
        if product_count == 0:
            raise ValueError(f"❌ No products found in {gold_table}")
        
        # Sample data check
        sample = spark.sql(f"SELECT product_id, product_name FROM {gold_table} LIMIT 1").collect()
        if sample:
            print(f"✅ Sample product: {sample[0]['product_name']}")
    
    except Exception as e:
        print(f"❌ Data validation failed: {str(e)}")
        raise RuntimeError(f"Cannot access product data: {str(e)}")
    
    # ===== INDEX STATUS CHECK =====
    print("\n2️⃣  Vector Search Index Status:")
    print("-" * 80)
    
    status = get_vector_index_status(
        catalog=catalog,
        gold_schema="gold",
        index_name="amazon_product_vs_index",
        endpoint_name="shared_vs_endpoint"
    )
    
    if status.get("status") == "active":
        print(f"✅ Index is active and ready")
    elif status.get("status") == "sdk_unavailable":
        print(f"⚠️  Vector Search SDK unavailable")
        print(f"   Fallback: Using SQL keyword search")
    else:
        print(f"⚠️  Index status: {status.get('status')}")
    
    # ===== EXECUTE SEARCH =====
    print("\n3️⃣  Executing Search:")
    print("-" * 80)
    
    try:
        if search_type == "semantic":
            print(f"🔎 Executing SEMANTIC search...")
            results = execute_amazon_product_search(
                query_text=search_query,
                catalog=catalog,
                gold_schema="gold",
                index_name="amazon_product_vs_index",
                endpoint_name="shared_vs_endpoint",
                num_results=num_results
            )
        else:  # hybrid
            print(f"🔎 Executing HYBRID search (semantic + keyword)...")
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
    
    except Exception as e:
        print(f"❌ Search execution failed: {str(e)}")
        print(f"   Falling back to SQL keyword search...")
        results = execute_sql_keyword_search(search_query, catalog, num_results=num_results)
    
    # ===== RESULT VALIDATION =====
    print("\n4️⃣  Result Validation:")
    print("-" * 80)
    
    if len(results) == 0:
        print(f"⚠️  WARNING: Search returned NO results")
        print(f"   Query: '{search_query}'")
        print(f"   Search type: {search_type}")
        print(f"   This could mean:")
        print(f"   - No products match the query")
        print(f"   - Vector index not synchronized")
        print(f"   - Search function failed silently")
    else:
        print(f"✅ Found {len(results)} matching products")
        
        # Validate result structure
        required_fields = ["product_id", "product_name"]
        for i, result in enumerate(results):
            for field in required_fields:
                if field not in result:
                    raise ValueError(f"Result {i} missing field: {field}")
        print(f"✅ All results have required fields")
    
    # ===== DISPLAY RESULTS =====
    print("\n5️⃣  Search Results:")
    print("=" * 80)
    
    if len(results) == 0:
        print("No results found.")
    else:
        for i, item in enumerate(results, 1):
            print(f"\n{'─'*80}")
            print(f"Result #{i}:")
            print(f"  🆔 Product ID      : {item.get('product_id', 'N/A')}")
            print(f"  📦 Name            : {item.get('product_name', 'N/A')}")
            print(f"  🏷️  Category        : {item.get('category', 'N/A')}")
            print(f"  💰 Discounted Price: ₹{item.get('discounted_price', 'N/A')}")
            print(f"  💵 Actual Price    : ₹{item.get('actual_price', 'N/A')}")
            print(f"  🏷️  Discount        : {item.get('discount_percentage', 'N/A')}%")
            print(f"  ⭐ Rating          : {item.get('rating', 'N/A')}/5.0 ({item.get('rating_count', 0)} reviews)")
            if search_type == "hybrid" and "score" in item:
                print(f"  📊 Relevance Score : {item.get('score', 0):.4f}")
            print(f"  🔗 Link            : {item.get('product_link', 'N/A')}")
    
    print(f"\n{'='*80}")
    print(f"✅ Search completed successfully")
    
    # ===== SUMMARY STATISTICS =====
    print(f"\n📊 Summary:")
    print(f"  - Query: '{search_query}'")
    print(f"  - Results found: {len(results)}")
    print(f"  - Search type: {search_type}")
    
    if len(results) > 0:
        avg_rating = sum(float(r.get('rating') or 0) for r in results) / len(results)
        print(f"  - Average rating: {avg_rating:.2f}/5.0")

except RuntimeError as e:
    print(f"\n❌ CRITICAL ERROR: {str(e)}")
    print("\nTroubleshooting:")
    print("1. Ensure gold table has data: spark.sql('SELECT COUNT(*) FROM ...")
    print("2. Check Vector Search endpoint availability")
    print("3. Verify embeddings have been generated")
    traceback.print_exc()
    raise

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    raise
