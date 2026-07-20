# =====================================================================
# Product Search Amazon — Governance: Query Validation
# =====================================================================

def validate_search_query_policy(query: str, max_length: int = 512) -> bool:
    if not query or not query.strip():
        return False
    if len(query) > max_length:
        return False
    return True
