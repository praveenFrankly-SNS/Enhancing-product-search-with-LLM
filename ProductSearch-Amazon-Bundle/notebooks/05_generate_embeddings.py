# Databricks notebook source
# MAGIC %md
# MAGIC # 05. Generate & Verify Embeddings
# MAGIC Validates `search_document` text readiness, prepares embedding documents,
# MAGIC verifies embedding model endpoint connectivity, and generates sample embeddings
# MAGIC to validate the pipeline before vector index creation.

# COMMAND ----------
import sys
import os
import time

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
dbutils.widgets.text("embedding_endpoint", "databricks-bge-large-en", "Embedding Model Endpoint")
catalog = dbutils.widgets.get("catalog").strip()
embedding_endpoint = dbutils.widgets.get("embedding_endpoint").strip()

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

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from src.embeddings.preparation import prepare_embedding_documents, validate_embedding_readiness
from src.embeddings.generator import verify_embedding_endpoint, generate_embeddings
from src.shared.logger import PipelineLogger

spark = SparkSession.builder.getOrCreate()
logger = PipelineLogger(spark, catalog)
start_time = time.time()

gold_table = f"`{catalog}`.gold.amazon_product_catalog"

# ── Stage 1: Read Gold Catalog ──
print(f"� Reading Gold Catalog table: {gold_table}")
df = spark.table(gold_table)
total_docs = df.count()
print(f"📊 Total documents: {total_docs}")

# ── Stage 2: Prepare embedding documents ──
print("\n🔧 Preparing embedding documents...")
docs_df = prepare_embedding_documents(
    df=df,
    text_columns=["product_name", "category", "about_product", "review_title", "review_content"],
    max_length=8192
)

# ── Stage 3: Validate embedding readiness ──
print("\n🔍 Validating embedding readiness...")
readiness = validate_embedding_readiness(docs_df, doc_column="embedding_document")
print(f"  • Total documents: {readiness['total_documents']}")
print(f"  • Empty documents: {readiness['empty_documents']}")
print(f"  • Ready for embedding: {readiness['ready']}")

if readiness["empty_documents"] > 0:
    print(f"⚠️  Sample empty records: {readiness['sample_empty_records']}")

if not readiness["ready"]:
    print("❌ Embedding readiness check failed - all documents must have content")
    logger.log_execution("Embeddings", "validate_readiness", "FAILED", total_docs, 0, time.time() - start_time, "Empty documents found")
    raise ValueError("Embedding readiness check failed")

# ── Stage 4: Verify embedding endpoint ──
print(f"\n🔌 Verifying embedding endpoint '{embedding_endpoint}'...")
endpoint_status = verify_embedding_endpoint(endpoint_name=embedding_endpoint)
print(f"  • Status: {endpoint_status['status']}")
if endpoint_status["status"] == "unavailable":
    print(f"⚠️  Embedding endpoint not available. Will use auto-embedding via Vector Search index sync.")
    print(f"    Error: {endpoint_status.get('error', 'unknown')}")
elif endpoint_status["status"] == "sdk_unavailable":
    print(f"⚠️  SDK not available. Vector Search index will handle embeddings automatically.")

# ── Stage 5: Generate sample embeddings for validation ──
if endpoint_status["status"] == "available":
    print("\n🧪 Generating sample embeddings for validation...")
    sample_docs = docs_df.select("embedding_document").limit(5).collect()
    sample_texts = [row["embedding_document"] for row in sample_docs]
    
    embedding_result = generate_embeddings(
        texts=sample_texts,
        endpoint_name=embedding_endpoint
    )
    
    if embedding_result["status"] == "success":
        print(f"✅ Generated {embedding_result['count']} embeddings")
        print(f"📐 Embedding dimension: {embedding_result['dimension']}")
    else:
        print(f"⚠️  Sample embedding generation: {embedding_result.get('status', 'error')}")
else:
    print("\nℹ️  Skipping sample embedding generation (endpoint unavailable)")
    print("   Vector Search Delta Sync Index will generate embeddings automatically")

# ── Stage 6: Document length statistics ──
doc_lengths = docs_df.withColumn("doc_length", F.length(F.col("embedding_document")))
length_stats = doc_lengths.agg(
    F.avg("doc_length").alias("avg_length"),
    F.min("doc_length").alias("min_length"),
    F.max("doc_length").alias("max_length"),
    F.stddev("doc_length").alias("std_length")
).collect()[0]
print(f"\n📝 Document length statistics:")
print(f"  • Avg: {round(length_stats['avg_length'] or 0, 0)} chars")
print(f"  • Min: {length_stats['min_length'] or 0} chars")
print(f"  • Max: {length_stats['max_length'] or 0} chars")

# Show sample embedding documents
print("\n📄 Sample embedding documents:")
display(docs_df.select("product_id", "product_name", "embedding_document").limit(3))

duration = time.time() - start_time
logger.log_execution("Embeddings", "validate_and_prepare", "SUCCESS", total_docs, total_docs, duration)
print(f"\n✅ Embedding preparation complete. Ready for Vector Search index creation.")
print(f"⏱️  Duration: {duration:.2f}s")