# =====================================================================
# Product Search — Shared: Constants
# =====================================================================
# Standard constants for medallion schemas and operational Delta logs.
# =====================================================================

# Medallion Schema Names
BRONZE = "bronze"
SILVER = "silver"
GOLD = "gold"
OPERATIONS = "operations"

# System Log Tables (under OPERATIONS schema)
EXECUTION_LOG = "pipeline_execution_log"
DATA_INGESTION_AUDIT = "data_ingestion_audit"
REJECTED_RECORDS = "rejected_records"
DATA_QUALITY_REPORT = "data_quality_report"

# Vector Search & Embedding Constants
PRODUCT_EMBEDDINGS = "product_embeddings"
VECTOR_SEARCH_ENDPOINT_NAME = "product_search_vs_endpoint"
VECTOR_SEARCH_INDEX_NAME = "product_search_catalog_index"
EMBEDDING_MODEL_ENDPOINT = "databricks-bge-large-en"
LLM_ENDPOINT = "databricks-meta-llama-3-1-70b-instruct"
