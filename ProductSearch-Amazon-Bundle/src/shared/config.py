# =====================================================================
# Product Search Amazon — Shared: Configuration Helper
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

        # 4. Resolve Bronze & Silver Schemas
        self.bronze_schema = self.yaml_config.get("pipeline", {}).get("bronze_schema", "bronze")
        self.silver_schema = self.yaml_config.get("pipeline", {}).get("silver_schema", "silver")
        self.gold_schema = self.yaml_config.get("pipeline", {}).get("gold_schema", "gold")
        self.ops_schema = self.yaml_config.get("pipeline", {}).get("operations_schema", "operations")
        
        # 5. Resolve Secret Scope
        self.secret_scope = self.yaml_config.get("pipeline", {}).get("secret_scope", "supabase-creds")
        if dbutils:
            try:
                self.secret_scope = dbutils.widgets.get("secret_scope").strip()
            except Exception:
                pass

        # 6. Resolve CSV path
        self.default_csv_path = self.yaml_config.get("ingestion", {}).get("default_csv_path", "/Workspace/dataset/V2/Amazon.csv")
        if dbutils:
            try:
                custom_csv = dbutils.widgets.get("csv_path").strip()
                if custom_csv:
                    self.default_csv_path = custom_csv
            except Exception:
                pass

        # 7. Resolve full_refresh mode
        self.full_refresh = True
        if dbutils:
            try:
                val = dbutils.widgets.get("full_refresh").strip().lower()
                self.full_refresh = val in ["true", "yes", "1"]
            except Exception:
                pass


def get_config(dbutils=None) -> PipelineConfig:
    """Instantiates and returns the unified configuration helper."""
    return PipelineConfig(dbutils)
