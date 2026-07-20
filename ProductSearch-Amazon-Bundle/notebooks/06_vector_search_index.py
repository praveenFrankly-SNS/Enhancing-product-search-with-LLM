# Databricks notebook source
# MAGIC %md
# MAGIC # 06. Vector Search Index Setup & Sync
# MAGIC Provisions Vector Search Endpoint (`product_search_endpoint`) and Syncs `amazon_product_vs_index`.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
catalog = dbutils.widgets.get("catalog").strip()

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

from src.search.vector_index import create_or_sync_amazon_vector_index

print(f"🚀 Provisioning / Syncing Vector Search Index for catalog '{catalog}'...")
result = create_or_sync_amazon_vector_index(
    catalog=catalog,
    gold_schema="gold",
    table_name="amazon_product_catalog",
    index_name="amazon_product_vs_index",
    endpoint_name="product_search_endpoint"
)

print(f"✅ Vector Search Index operation result: {result}")
