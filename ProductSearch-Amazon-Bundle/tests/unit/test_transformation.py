# =====================================================================
# Product Search Amazon — Unit Tests: Transformation & Deduplication
# =====================================================================

import pytest


def test_deduplication_import():
    """Test deduplication module imports."""
    try:
        from src.transformation.deduplication import deduplicate_products
        assert callable(deduplicate_products)
    except ImportError:
        pytest.skip("transformation.deduplication not importable outside Databricks")


def test_quality_filter_import():
    """Test quality filter module imports."""
    try:
        from src.transformation.quality import filter_valid_products
        assert callable(filter_valid_products)
    except ImportError:
        pytest.skip("transformation.quality not importable outside Databricks")


def test_amazon_transformer_import():
    """Test amazon transformer module imports."""
    try:
        from src.transformation.amazon_transformer import transform_raw_to_silver
        assert callable(transform_raw_to_silver)
    except ImportError:
        pytest.skip("transformation.amazon_transformer not importable outside Databricks")