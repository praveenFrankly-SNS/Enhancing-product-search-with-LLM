# Databricks notebook source
# MAGIC %md
# MAGIC # 06. Vector Search Index Setup & Sync
# MAGIC Provisions/Syncs `amazon_product_vs_index` on the shared Vector Search Endpoint (`shared_vs_endpoint`).
# MAGIC This uses a shared endpoint for cost efficiency while maintaining isolation through namespaced index names.

# COMMAND ----------
import sys
import os
import traceback

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("endpoint_name", "shared_vs_endpoint", "Vector Search Endpoint Name")
dbutils.widgets.dropdown("action", "sync_or_create", ["sync_or_create", "sync_only", "status"])

catalog = dbutils.widgets.get("catalog").strip()
endpoint_name = dbutils.widgets.get("endpoint_name").strip()
action = dbutils.widgets.get("action").strip()

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

from src.search.vector_index import create_or_sync_amazon_vector_index, sync_vector_index, get_index_stats

print(f"🚀 Vector Search Index Manager")
print(f"📦 Catalog: {catalog}")
print(f"🔗 Endpoint: {endpoint_name}")
print(f"⚙️  Action: {action}")
print("=" * 70)

try:
    if action == "sync_or_create":
        print("\n✨ Creating or syncing Vector Search Index...")
        result = create_or_sync_amazon_vector_index(
            catalog=catalog,
            gold_schema="gold",
            table_name="amazon_product_catalog",
            index_name="amazon_product_vs_index",
            endpoint_name=endpoint_name,
            primary_key="product_id",
            embedding_column="search_document",
            embedding_model="databricks-bge-large-en"
        )
        
    elif action == "sync_only":
        print("\n🔄 Syncing existing Vector Search Index...")
        result = sync_vector_index(
            catalog=catalog,
            gold_schema="gold",
            index_name="amazon_product_vs_index",
            endpoint_name=endpoint_name
        )
        
    elif action == "status":
        print("\n📊 Fetching Vector Search Index Status...")
        result = get_index_stats(
            catalog=catalog,
            gold_schema="gold",
            index_name="amazon_product_vs_index",
            endpoint_name=endpoint_name
        )
    
    # ===== EXPLICIT ERROR CHECKING =====
    print("\n" + "=" * 70)
    
    # Check if result is error
    if isinstance(result, dict):
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error")
            print(f"❌ OPERATION FAILED: {error_msg}")
            raise RuntimeError(f"Vector index operation failed: {error_msg}")
        
        elif result.get("status") == "requires_manual_setup":
            print(f"⚠️  MANUAL SETUP REQUIRED")
            print(f"   Message: {result.get('message')}")
            print(f"   Recommendation: {result.get('message')}")
        
        else:
            # Success case - print details
            print(f"✅ OPERATION SUCCESSFUL")
            print(f"   Status: {result.get('status').upper()}")
            print(f"   Action: {result.get('action', 'unknown').upper()}")
            print(f"   Index: {result.get('index_name')}")
            print(f"   Endpoint: {result.get('endpoint_name')}")
            
            # Print additional details
            if "stats" in result:
                print(f"\n   📊 Index Statistics:")
                for key, value in result.get("stats", {}).items():
                    print(f"      - {key}: {value}")
    else:
        raise ValueError(f"Unexpected result type: {type(result)}")
    
    print("\n" + "=" * 70)
    print("✅ Vector Search Index operation completed successfully!")

except RuntimeError as e:
    print(f"\n❌ CRITICAL ERROR: {str(e)}")
    print("\nTroubleshooting steps:")
    print("1. Verify Vector Search SDK is installed:")
    print("   %pip install databricks-vector-search")
    print("   dbutils.library.restartPython()")
    print("2. Check if 'shared_vs_endpoint' exists in Databricks Vector Search")
    print("3. Verify catalog and gold table exist:")
    print(f"   spark.sql('SELECT COUNT(*) FROM `{catalog}`.gold.amazon_product_catalog').show()")
    traceback.print_exc()
    raise

except Exception as e:
    print(f"\n❌ ERROR: {str(e)}")
    print("\nFull traceback:")
    traceback.print_exc()
    raise
