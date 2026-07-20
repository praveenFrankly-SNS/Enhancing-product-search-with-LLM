# =====================================================================
# Product Search Amazon — Governance: Secret Scope Validator
# =====================================================================

def validate_secret_scope(dbutils=None, scope_name: str = "supabase-creds") -> bool:
    if not dbutils:
        return True
    try:
        dbutils.secrets.list(scope_name)
        return True
    except Exception as e:
        print(f"⚠️ Secret scope '{scope_name}' check note: {e}")
        return False
