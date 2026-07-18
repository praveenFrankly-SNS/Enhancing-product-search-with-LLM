# Databricks notebook source
# MAGIC %md
# MAGIC # 🚀 Master Amazon Pipeline Orchestrator
# MAGIC **Purpose**: Run the complete Amazon Product Search ingestion & vector search indexing pipeline interactively.
# MAGIC 
# MAGIC > **Note**: Use this master notebook directly in Databricks Workspace UI if automated Job runs are restricted on Community / Trial accounts.

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 1: Validate Environment
# COMMAND ----------
# MAGIC %run ./00_validate_environment

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 2: Setup Unity Catalog Delta Table Schema
# COMMAND ----------
# MAGIC %run ./01_setup_platform

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 3: Ingest Amazon CSV & Build Embeddings Document
# COMMAND ----------
# MAGIC %run ./02_ingest_amazon_csv

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 4: Create & Sync Delta Vector Search Index
# COMMAND ----------
# MAGIC %run ./03_vector_search_index

# COMMAND ----------
# MAGIC %md
# MAGIC ### Step 5: Test Vector Search Query
# COMMAND ----------
# MAGIC %run ./04_test_amazon_search
