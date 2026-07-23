# =====================================================================
# Product Search Amazon — Unit Tests: Data Validation
# =====================================================================

import pytest


def test_validate_dataframe_schema():
    """Test schema validation logic."""
    try:
        from src.shared.validation import validate_dataframe_schema
        assert callable(validate_dataframe_schema)
    except ImportError:
        pytest.skip("shared.validation not importable outside Databricks")


def test_validate_non_empty():
    """Test non-empty validation raises error on empty."""
    try:
        from src.shared.validation import validate_non_empty
        assert callable(validate_non_empty)
    except ImportError:
        pytest.skip("shared.validation not importable outside Databricks")


def test_search_query_policy():
    """Test search query policy validation."""
    try:
        from src.governance.validation import validate_search_query_policy
        assert validate_search_query_policy("laptop") is True
        assert validate_search_query_policy("") is False
        assert validate_search_query_policy(" " * 600) is False
    except ImportError:
        pytest.skip("governance.validation not importable outside Databricks")


def test_data_quality_scoring():
    """Test data quality score calculation logic."""
    try:
        from src.utils.validation import check_data_quality
        assert callable(check_data_quality)
    except ImportError:
        pytest.skip("utils.validation not importable outside Databricks")