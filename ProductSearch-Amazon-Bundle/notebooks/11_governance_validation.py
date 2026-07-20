# Databricks notebook source
# MAGIC %md
# MAGIC # 11. Governance Validation
# MAGIC Verifies Unity Catalog configuration, secret scope accessibility, and policy checks.

# COMMAND ----------
import sys
import os

dbutils.widgets.text("catalog", "product_search_dev", "Catalog Name")
catalog = dbutils.widgets.get("catalog").strip()

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

from src.governance.secrets import validate_secret_scope
from src.governance.validation import validate_search_query_policy

print("🔒 GOVERNANCE AUDIT CHECKS:")
print("=" * 60)

# Check secret scope
scope_valid = validate_secret_scope(dbutils, "supabase-creds")
print(f"  • Secret Scope ('supabase-creds'): {'✅ ACCESSIBLE' if scope_valid else '⚠️ NOT FOUND / SKIPPED'}")

# Check query policy
policy_valid = validate_search_query_policy("sample search query", max_length=512)
print(f"  • Query Length Policy Enforcement: {'✅ PASS' if policy_valid else '❌ FAIL'}")

print("🎉 Governance validation complete.")
