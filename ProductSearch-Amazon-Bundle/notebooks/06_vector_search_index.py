# Databricks notebook source
# MAGIC %md
# MAGIC # 06. Vector Search Index Setup & Sync
# MAGIC Provisions/Syncs `amazon_product_vs_index` on the shared Vector Search Endpoint (`shared_vs_endpoint`).
# MAGIC This uses a shared endpoint for cost efficiency while maintaining isolation through namespaced index names.

# COMMAND ----------
import sys
import os

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
print("=" * 60)

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

print("\n" + "=" * 60)
print(f"Result:")
for key, value in result.items():
    if key != "stats":
        print(f"  • {key}: {value}")
    else:
        print(f"  • {key}:")
        for k, v in value.items():
            print(f"      - {k}: {v}")

print("\n✅ Operation completed successfully")
