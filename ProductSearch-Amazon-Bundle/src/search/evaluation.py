# =====================================================================
# Product Search Amazon — Search: Evaluation Helper
# =====================================================================

from typing import List, Dict, Any


def evaluate_retrieval_relevance(results: List[Dict[str, Any]], target_keywords: List[str]) -> float:
    """
    Computes keyword matching relevance score across top retrieved results.
    """
    if not results:
        return 0.0

    matched = 0
    for item in results:
        doc_text = str(item.get("search_document", "")).lower()
        if any(kw.lower() in doc_text for kw in target_keywords):
            matched += 1

    return float(matched) / len(results)
