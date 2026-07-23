# =====================================================================
# Product Search Amazon — Unit Tests: Ingestion
# =====================================================================

import pytest


def test_csv_path_resolution():
    """Test CSV path resolution logic."""
    try:
        from src.ingestion.csv_reader import resolve_amazon_csv_path
        path = resolve_amazon_csv_path(custom_csv_path="/Workspace/dataset/V2/Amazon.csv")
        assert path == "/Workspace/dataset/V2/Amazon.csv"
    except ImportError:
        pytest.skip("ingestion.csv_reader not importable outside Databricks")


def test_csv_path_fallback():
    """Test CSV path falls back to default."""
    try:
        from src.ingestion.csv_reader import resolve_amazon_csv_path
        path = resolve_amazon_csv_path(custom_csv_path=None)
        assert path is not None
        assert isinstance(path, str)
    except ImportError:
        pytest.skip("ingestion.csv_reader not importable outside Databricks")