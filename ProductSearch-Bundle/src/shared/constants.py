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
