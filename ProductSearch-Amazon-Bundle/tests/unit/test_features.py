# =====================================================================
# Product Search Amazon — Unit Tests: Feature Engineering
# =====================================================================

import pytest


def test_gold_catalog_import():
    """Test gold catalog builder imports."""
    try:
        from src.feature_engineering.amazon_features import build_amazon_gold_catalog
        assert callable(build_amazon_gold_catalog)
    except ImportError:
        pytest.skip("feature_engineering.amazon_features not importable outside Databricks")


def test_prepare_embedding_docs_import():
    """Test embedding document preparation imports."""
    try:
        from src.embeddings.preparation import prepare_embedding_documents
        assert callable(prepare_embedding_documents)
    except ImportError:
        pytest.skip("embeddings.preparation not importable outside Databricks")


def test_validate_embedding_readiness_import():
    """Test embedding readiness validation imports."""
    try:
        from src.embeddings.preparation import validate_embedding_readiness
        assert callable(validate_embedding_readiness)
    except ImportError:
        pytest.skip("embeddings.preparation not importable outside Databricks")