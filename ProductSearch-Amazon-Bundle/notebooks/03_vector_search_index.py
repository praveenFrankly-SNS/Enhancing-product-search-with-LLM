# Databricks notebook source
# MAGIC %md
# MAGIC # 03. Vector Search Index Creation & Delta Sync (Amazon Variant)
# MAGIC Creates and syncs the Delta Sync Vector Search index (`amazon_product_catalog_index`) on `product_search_vs_endpoint`.

# COMMAND ----------
# MAGIC %pip install databricks-vectorsearch
# COMMAND ----------
import time
from pyspark.sql import SparkSession
from databricks.vector_search.client import VectorSearchClient

spark = SparkSession.builder.getOrCreate()

dbutils.widgets.text("catalog",         "product_search_dev",          "Catalog Name")
dbutils.widgets.text("vs_endpoint",      "product_search_vs_endpoint",  "Vector Search Endpoint")
dbutils.widgets.text("embedding_model",  "databricks-bge-large-en",     "Embedding Serving Endpoint")

catalog = dbutils.widgets.get("catalog")
endpoint_name = dbutils.widgets.get("vs_endpoint")
embedding_model = dbutils.widgets.get("embedding_model")

source_table_name = f"{catalog}.gold.amazon_product_catalog"
index_name = f"{catalog}.gold.amazon_product_catalog_index"

print(f"📌 Vector Search Endpoint:  {endpoint_name}")
print(f"📌 Source Delta Table:      {source_table_name}")
print(f"📌 Target Vector Index:     {index_name}")
print(f"📌 Embedding Model:         {embedding_model}")

# COMMAND ----------
client = VectorSearchClient(disable_notice=True)

# 1. Verify Endpoint Status
try:
    ep = client.get_endpoint(endpoint_name)
    print(f"✅ Vector Search Endpoint Status: {ep.get('endpoint_status', {}).get('state')}")
except Exception as e:
    print(f"❌ Endpoint '{endpoint_name}' not reachable: {e}")
    raise e

# COMMAND ----------
# 2. Create or Sync Delta Sync Index
index_exists = False
try:
    index = client.get_index(endpoint_name=endpoint_name, index_name=index_name)
    index_exists = True
    print(f"ℹ️ Vector Search Index '{index_name}' already exists.")
except Exception:
    index_exists = False

if not index_exists:
    print(f"🚀 Creating new Delta Sync Vector Search Index: {index_name}...")
    index = client.create_delta_sync_index(
        endpoint_name=endpoint_name,
        index_name=index_name,
        source_table_name=source_table_name,
        pipeline_type="TRIGGERED",
        primary_key="product_id",
        embedding_source_column="search_document",
        embedding_model_endpoint_name=embedding_model,
    )
    print(f"✅ Vector Search Index creation initiated: {index_name}")
else:
    print(f"🔄 Triggering sync for existing index: {index_name}...")
    try:
        index.sync()
    except Exception as se:
        print(f"Sync trigger notice: {se}")

# COMMAND ----------
# 3. Wait for Index to become ONLINE
print("⏳ Waiting for Index sync to complete and become ONLINE...")
max_wait_seconds = 600
start_time = time.time()

while time.time() - start_time < max_wait_seconds:
    status = client.get_index(endpoint_name=endpoint_name, index_name=index_name).describe()
    state = status.get("status", {}).get("detailed_state", "UNKNOWN")
    print(f"  Current Index State: {state}")
    if "ONLINE" in state.upper():
        print("🎉 Vector Search Index is ONLINE and ready for similarity queries!")
        break
    time.sleep(15)

# COMMAND ----------
display(spark.sql(f"SELECT COUNT(*) as indexed_rows FROM {source_table_name}"))
