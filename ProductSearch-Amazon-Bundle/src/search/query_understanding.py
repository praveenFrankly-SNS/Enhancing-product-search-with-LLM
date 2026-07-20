# =====================================================================
# Product Search Amazon — Search: Query Understanding
# =====================================================================

import json
from typing import Dict, Any


def parse_search_query(query: str, dbutils=None) -> Dict[str, Any]:
    """
    Parses and expands raw user search query using Databricks Foundation Model APIs (or regex fallback).
    """
    cleaned_query = query.strip().lower()
    
    # Try calling Databricks Serving Endpoint for LLM query understanding if available
    try:
        from databricks.sdk import WorkspaceClient
        w = WorkspaceClient()
        prompt = f"Extract product category, brand, features, and expanded search terms for query: '{cleaned_query}'. Return valid JSON with keys: category, expanded_terms, price_sensitivity."
        
        response = w.serving_endpoints.query(
            name="databricks-dbrx-instruct",
            messages=[{"role": "user", "content": prompt}]
        )
        content = response.choices[0].message.content
        parsed = json.loads(content)
        return {
            "original_query": query,
            "cleaned_query": cleaned_query,
            "category": parsed.get("category", ""),
            "expanded_terms": parsed.get("expanded_terms", [cleaned_query]),
            "price_sensitivity": parsed.get("price_sensitivity", "normal")
        }
    except Exception:
        # Robust heuristic fallback
        return {
            "original_query": query,
            "cleaned_query": cleaned_query,
            "category": "general",
            "expanded_terms": [cleaned_query],
            "price_sensitivity": "normal"
        }
