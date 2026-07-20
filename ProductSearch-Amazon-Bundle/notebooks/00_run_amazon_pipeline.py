# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 Master Amazon Pipeline Orchestrator
# MAGIC **Purpose**: Run the complete Amazon Product Search end-to-end pipeline interactively in Databricks Workspace UI.

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 0: Validate Environment
# COMMAND ----------
# MAGIC %run ./00_validate_environment

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 1: Setup Unity Catalog Platform & Schemas
# COMMAND ----------
# MAGIC %run ./01_setup_platform

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 2: Ingest Raw Amazon CSV (Bronze)
# COMMAND ----------
# MAGIC %run ./02_ingest_amazon_csv

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 3: Bronze to Silver Medallion Transformation
# COMMAND ----------
# MAGIC %run ./03_bronze_to_silver

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 4: Gold Feature Engineering (Catalog & Search Document)
# COMMAND ----------
# MAGIC %run ./04_feature_engineering

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 5: Verify Embeddings Document Readiness
# COMMAND ----------
# MAGIC %run ./05_generate_embeddings

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 6: Create & Sync Delta Vector Search Index
# COMMAND ----------
# MAGIC %run ./06_vector_search_index

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 7: Query Understanding & Term Expansion
# COMMAND ----------
# MAGIC %run ./07_query_understanding

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 8: Execute Hybrid & Semantic Search Pipeline
# COMMAND ----------
# MAGIC %run ./08_semantic_search_pipeline

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 9: Search Relevance Evaluation & MLflow Logging
# COMMAND ----------
# MAGIC %run ./09_search_evaluation

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 10: System Observability & Health Check
# COMMAND ----------
# MAGIC %run ./10_monitoring_healthcheck

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 11: Governance & Security Validation
# COMMAND ----------
# MAGIC %run ./11_governance_validation

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 12: End-to-End Search Integration Test
# COMMAND ----------
# MAGIC %run ./12_test_amazon_search
