# =====================================================================
# Product Search — Shared: Configuration Helper
# =====================================================================
# Merges YAML configurations, environment overrides, and active
# Databricks UI widget inputs into a single unified config object.
# =====================================================================

import os
from src.shared.utils.config_loader import load_config

class PipelineConfig:
    def __init__(self, dbutils=None):
        # 1. Resolve Environment Target
        self.environment = "dev"
        if dbutils:
            try:
                self.environment = dbutils.widgets.get("environment").strip()
            except Exception:
                pass
        if not self.environment:
            self.environment = os.getenv("PIPELINE_ENV", "dev")

        # 2. Load configurations from YAML config files (base + overrides)
        self.yaml_config = load_config(self.environment)
        
        # 3. Resolve target catalog (widget values override YAML)
        self.catalog = self.yaml_config.get("pipeline", {}).get("catalog", "product_search_dev")
        if dbutils:
            try:
                self.catalog = dbutils.widgets.get("catalog").strip()
            except Exception:
                pass

        # 4. Resolve Bronze schema
        self.bronze_schema = self.yaml_config.get("pipeline", {}).get("bronze_schema", "bronze")
        if dbutils:
            try:
                self.bronze_schema = dbutils.widgets.get("schema").strip()
            except Exception:
                pass

        # 5. Resolve Operations schema
        self.ops_schema = self.yaml_config.get("pipeline", {}).get("operations_schema", "operations")
        
        # 6. Resolve Secret Scope
        self.secret_scope = self.yaml_config.get("pipeline", {}).get("secret_scope", "supabase-creds")
        if dbutils:
            try:
                self.secret_scope = dbutils.widgets.get("secret_scope").strip()
            except Exception:
                pass

        # 7. Resolve partition counts for parallel JDBC reads
        self.num_partitions = int(self.yaml_config.get("ingestion", {}).get("num_partitions", 4))
        if dbutils:
            try:
                self.num_partitions = int(dbutils.widgets.get("num_partitions").strip())
            except Exception:
                pass

        # 8. Resolve full_refresh mode (widget value overrides default)
        self.full_refresh = True
        if dbutils:
            try:
                val = dbutils.widgets.get("full_refresh").strip().lower()
                self.full_refresh = val in ["true", "yes", "1"]
            except Exception:
                pass

        # 9. Get raw source-to-target ingestion table configurations
        self.tables = self.yaml_config.get("ingestion", {}).get("tables", [])


def get_config(dbutils=None) -> PipelineConfig:
    """Instantiates and returns the unified configuration helper."""
    return PipelineConfig(dbutils)
