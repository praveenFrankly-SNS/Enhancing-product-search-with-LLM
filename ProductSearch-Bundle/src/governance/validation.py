# =====================================================================
# Product Search — Search Input & Config validations
# =====================================================================

import re

def validate_query(query: str, max_length: int = 512, allow_empty: bool = False) -> dict:
    """
    Applies Search Input Validation rules to queries to prevent downstream failures.
    Returns validation status results.
    """
    results = {
        "valid": True,
        "reason": None
    }
    
    if not query or not query.strip():
        if not allow_empty:
            results["valid"] = False
            results["reason"] = "Empty search query is rejected."
        return results
        
    if len(query) > max_length:
        results["valid"] = False
        results["reason"] = f"Query length ({len(query)}) exceeds maximum allowed limit ({max_length} characters)."
        return results
        
    # Check for invalid control characters or malicious structures
    # (Allow normal alphanumeric, spaces, and standard punctuation)
    sanitized_pattern = r"[^\w\s\-\.\,\?\!\'\"]"
    if re.search(sanitized_pattern, query):
        # We flag queries containing anomalous control structures or special script tags
        results["valid"] = False
        results["reason"] = "Query contains unsupported or anomalous characters."
        
    return results

def validate_pipeline_config(config: dict) -> dict:
    """
    Validates that the required pipeline configurations are present and conformed.
    """
    results = {"valid": True, "errors": []}
    
    pipeline_cfg = config.get("pipeline", {})
    if not pipeline_cfg.get("catalog"):
        results["valid"] = False
        results["errors"].append("Missing required parameter: pipeline.catalog")
        
    if not pipeline_cfg.get("secret_scope"):
        results["valid"] = False
        results["errors"].append("Missing required parameter: pipeline.secret_scope")
        
    # Verify governance config block
    gov_cfg = config.get("governance", {})
    if gov_cfg.get("enabled", True):
        secrets_cfg = gov_cfg.get("secrets", {})
        if not secrets_cfg.get("scope"):
            results["valid"] = False
            results["errors"].append("Missing required parameter: governance.secrets.scope")
        if not secrets_cfg.get("required"):
            results["valid"] = False
            results["errors"].append("Missing required parameter: governance.secrets.required")
            
    return results

def validate_environment(spark) -> dict:
    """
    Validates the workspace environment runtime config parameters.
    """
    results = {"valid": True, "errors": []}
    
    # Verify if spark context is running under standard Databricks environment
    try:
        spark_version = spark.conf.get("spark.databricks.clusterUsageTags.sparkVersion", None)
        if not spark_version:
            # Under serverless / Spark Connect, some usage tags are missing, check spark.version
            spark_version = spark.version
        results["spark_version"] = spark_version
    except Exception as e:
        results["valid"] = False
        results["errors"].append(f"Failed to resolve Spark runtime version. Detail: {str(e)}")
        
    return results
