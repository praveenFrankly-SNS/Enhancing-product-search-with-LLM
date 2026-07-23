# =====================================================================
# Product Search Amazon — Unit Tests: Evaluation Metrics
# =====================================================================

import pytest


def test_precision_at_k():
    """Test precision@k calculation."""
    try:
        from src.evaluation.metrics import precision_at_k
        actual = ["a", "b", "c"]
        predicted = ["a", "d", "e", "f", "g"]
        p = precision_at_k(actual, predicted, k=5)
        assert p == pytest.approx(0.2)  # 1 hit out of 5
    except ImportError:
        pytest.skip("evaluation.metrics not importable outside Databricks")


def test_recall_at_k():
    """Test recall@k calculation."""
    try:
        from src.evaluation.metrics import recall_at_k
        actual = ["a", "b", "c"]
        predicted = ["a", "d", "e", "f", "g"]
        r = recall_at_k(actual, predicted, k=5)
        assert r == pytest.approx(1.0 / 3.0)  # 1 out of 3 relevant found
    except ImportError:
        pytest.skip("evaluation.metrics not importable outside Databricks")


def test_ndcg_at_k():
    """Test NDCG@k calculation."""
    try:
        from src.evaluation.metrics import ndcg_at_k
        actual_rel = [1.0, 1.0, 1.0]
        pred_rel = [1.0, 0.0, 1.0, 0.0]
        ndcg = ndcg_at_k(actual_rel, pred_rel, k=4)
        assert 0 <= ndcg <= 1.0
    except ImportError:
        pytest.skip("evaluation.metrics not importable outside Databricks")


def test_benchmark_queries():
    """Test benchmark query list."""
    try:
        from src.evaluation.benchmark import STANDARD_BENCHMARK_QUERIES
        assert len(STANDARD_BENCHMARK_QUERIES) >= 5
        for q in STANDARD_BENCHMARK_QUERIES:
            assert "query" in q
            assert "keywords" in q
            assert len(q["keywords"]) > 0
    except ImportError:
        pytest.skip("evaluation.benchmark not importable outside Databricks")