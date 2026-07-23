# =====================================================================
# Product Search Amazon — Unit Tests: Configuration Loading
# =====================================================================

import os
import sys
import tempfile
import yaml
import pytest


@pytest.fixture
def sample_pipeline_config():
    """Creates a sample pipeline YAML config for testing."""
    return {
        "pipeline": {
            "write_mode": "overwrite",
            "catalog": "product_search_dev",
            "bronze_schema": "bronze",
            "silver_schema": "silver",
            "gold_schema": "gold",
            "operations_schema": "operations",
            "secret_scope": "supabase-creds",
        },
        "ingestion": {
            "source_type": "csv",
            "default_csv_path": "/Workspace/dataset/V2/Amazon.csv",
        },
        "mlflow": {
            "enabled": True,
            "experiment_path": "/Shared/Amazon_Product_Search_ML",
        },
    }


def test_config_loader_import():
    """Test that config_loader module can be imported."""
    try:
        from src.shared.utils.config_loader import load_config, get_project_root
        assert callable(load_config)
        assert callable(get_project_root)
    except ImportError:
        pytest.skip("config_loader not importable outside Databricks")


def test_yaml_parse(sample_pipeline_config):
    """Test that YAML config can be parsed correctly."""
    yaml_str = yaml.dump(sample_pipeline_config)
    parsed = yaml.safe_load(yaml_str)
    assert parsed["pipeline"]["catalog"] == "product_search_dev"
    assert parsed["pipeline"]["bronze_schema"] == "bronze"
    assert parsed["ingestion"]["default_csv_path"] == "/Workspace/dataset/V2/Amazon.csv"


def test_config_env_overrides():
    """Test environment variable overrides."""
    os.environ["AMAZON_CATALOG"] = "test_catalog"
    try:
        from src.utils.config import get_amazon_config
        catalog = get_amazon_config("CATALOG", "default_catalog")
        assert catalog == "test_catalog"
    except ImportError:
        pytest.skip("utils.config not importable outside Databricks")
    finally:
        del os.environ["AMAZON_CATALOG"]