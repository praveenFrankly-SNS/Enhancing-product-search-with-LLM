# =====================================================================
# Product Search — Governance policies & rules
# =====================================================================

REQUIRED_SCHEMAS = ["bronze", "silver", "gold", "operations"]

# Schemas and tables where read (SELECT) and write (MODIFY) permissions are verified
REQUIRED_TABLES_READ = {
    "bronze": [
        "product", "query", "label", "brand", 
        "category", "product_master", "product_pricing", 
        "product_attributes", "product_review_summary"
    ],
    "silver": ["product", "product_review_summary"],
    "gold": ["product_search_catalog", "query", "label"]
}

REQUIRED_TABLES_WRITE = {
    "silver": ["product", "product_review_summary"],
    "gold": ["product_search_catalog", "query", "label"],
    "operations": [
        "pipeline_execution_log", "data_ingestion_audit", 
        "rejected_records", "data_quality_report", 
        "monitoring_metrics", "health_status", "alert_log",
        "audit_log", "security_validation"
    ]
}
