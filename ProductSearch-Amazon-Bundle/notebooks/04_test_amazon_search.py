# Databricks notebook source
# MAGIC %md
# MAGIC # 04. Test Amazon Vector Search Index
# MAGIC Interactive notebook for testing similarity search queries against `product_search_dev.gold.amazon_product_catalog_index`.

# COMMAND ----------
# MAGIC %pip install databricks-vectorsearch pandas
# COMMAND ----------
import time
import pandas as pd
from pyspark.sql import SparkSession
from databricks.vector_search.client import VectorSearchClient

spark = SparkSession.builder.getOrCreate()

dbutils.widgets.text("catalog",        "product_search_dev", "Catalog Name")
dbutils.widgets.text("vs_endpoint",    "product_search_vs_endpoint", "Vector Search Endpoint")
dbutils.widgets.text("query",          "Fast Charging Cable", "Search Query")
dbutils.widgets.text("top_k",          "10", "Top K Results")

catalog = dbutils.widgets.get("catalog")
endpoint_name = dbutils.widgets.get("vs_endpoint")
user_query = dbutils.widgets.get("query").strip()
top_k = int(dbutils.widgets.get("top_k"))

index_name = f"{catalog}.gold.amazon_product_catalog_index"

print(f"🔍 Searching Amazon Index: {index_name}")
print(f"🔎 Query: '{user_query}'")

# COMMAND ----------
client = VectorSearchClient(disable_notice=True)
index = client.get_index(endpoint_name=endpoint_name, index_name=index_name)

response = index.similarity_search(
    query_text=user_query,
    columns=[
        "product_id",
        "product_name",
        "category",
        "discounted_price",
        "actual_price",
        "rating",
        "rating_count",
        "img_link"
    ],
    num_results=top_k
)

manifest = response.get("manifest") or {}
cols_manifest = manifest.get("schema", {}).get("columns") or response.get("columns") or []
cols = [c.get("name") if isinstance(c, dict) else c for c in cols_manifest]
data_rows = response.get("result", {}).get("data_array") or response.get("data_array") or []

results = []
for idx, r in enumerate(data_rows):
    rdict = dict(zip(cols, r[:len(cols)])) if cols else {}
    score = rdict.pop("score", None) or rdict.pop("__score", None) or 0.7
    results.append({
        "Rank": idx + 1,
        "Product ID": rdict.get("product_id"),
        "Product Name": rdict.get("product_name"),
        "Category": rdict.get("category"),
        "Price (₹)": f"₹{rdict.get('discounted_price')}",
        "Rating": f"⭐ {rdict.get('rating')} ({rdict.get('rating_count')} reviews)",
        "Raw Score": round(float(score), 4),
        "Image Link": rdict.get("img_link")
    })

df = pd.DataFrame(results)
display(df)
