# =====================================================================
# Product Search — Secret Scope Governance checks
# =====================================================================

def verify_secrets_prerequisites(dbutils, scope: str, required_keys: list) -> dict:
    """
    Verifies that the configured Secret Scope exists and contains all required
    secret keys. Bypasses actual secret retrieval to protect credentials.
    Returns a dictionary of status results.
    """
    results = {
        "scope_exists": False,
        "available_keys": [],
        "missing_keys": [],
        "errors": []
    }
    
    if not scope:
        results["errors"].append("Secret scope name is empty or not configured in pipeline.yml.")
        return results
        
    try:
        # List all metadata inside the secret scope (raises exception if scope is missing)
        secrets_list = dbutils.secrets.list(scope)
        results["scope_exists"] = True
        
        # Collect existing keys
        existing_keys = [s.key for s in secrets_list]
        results["available_keys"] = existing_keys
        
        # Verify required keys
        for req_key in required_keys:
            # Support pipe-separated alternative keys (e.g. "host|db-host")
            alternatives = [k.strip() for k in req_key.split("|")]
            found = False
            for alt in alternatives:
                if alt in existing_keys:
                    found = True
                    break
            if not found:
                results["missing_keys"].append(req_key)
                results["errors"].append(f"Required secret key '{req_key}' is missing in scope '{scope}'.")
                
    except Exception as e:
        results["errors"].append(f"Secret scope '{scope}' is missing or inaccessible. Detail: {str(e)}")
        
    return results

