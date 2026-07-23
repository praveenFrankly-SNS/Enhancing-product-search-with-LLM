# =====================================================================
# Product Search Amazon — Unit Tests: Search Pipeline
# =====================================================================

import pytest


def test_search_pipeline_import():
    """Test search pipeline module imports."""
    try:
        from src.search.search_pipeline import execute_amazon_product_search
        assert callable(execute_amazon_product_search)
    except ImportError:
        pytest.skip("search.search_pipeline not importable outside Databricks")


def test_hybrid_search_import():
    """Test hybrid search module imports."""
    try:
        from src.search.search_pipeline import execute_hybrid_search
        assert callable(execute_hybrid_search)
    except ImportError:
        pytest.skip("search.search_pipeline not importable outside Databricks")


def test_query_understanding_import():
    """Test query understanding module imports."""
    try:
        from src.search.query_understanding import parse_search_query
        result = parse_search_query("laptop", dbutils=None)
        assert "original_query" in result
        assert "cleaned_query" in result
        assert "category" in result
        assert result["original_query"] == "laptop"
    except ImportError:
        pytest.skip("search.query_understanding not importable outside Databricks")


def test_vector_index_import():
    """Test vector index module imports."""
    try:
        from src.search.vector_index import create_or_sync_amazon_vector_index
        assert callable(create_or_sync_amazon_vector_index)
    except ImportError:
        pytest.skip("search.vector_index not importable outside Databricks")


def test_evaluate_retrieval_relevance():
    """Test retrieval relevance scoring."""
    try:
        from src.search.evaluation import evaluate_retrieval_relevance
        results = [
            {"search_document": "USB cable for fast charging"},
            {"search_document": "Bluetooth headphones wireless"},
        ]
        score = evaluate_retrieval_relevance(results, ["cable", "usb"])
        assert score == 0.5  # 1 out of 2 matched
    except ImportError:
        pytest.skip("search.evaluation not importable outside Databricks")