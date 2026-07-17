# =====================================================================
# Product Search — Search: Query Understanding
# =====================================================================
# LLM-based query understanding layer using Databricks Foundation
# Model APIs. Extracts structured search intent from a raw customer
# query, enabling downstream metadata filtering and query rewriting.
#
# Output Structure:
#   {
#     "rewritten_query": "ergonomic office chair with lumbar support",
#     "category": "Office Furniture",
#     "brand": null,
#     "price_max": 500.0,
#     "filters": {
#       "color": "Black",
#       "material": "Mesh"
#     }
#   }
#
# The `filters` dict is intentionally open-ended so attribute-level
# filters (color, material, size, etc.) can be pushed down to the
# Vector Search metadata filter without changing the interface.
# =====================================================================

import json
import logging
import re
import requests
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# ── System prompt for structured JSON intent extraction ───────────────
_QUERY_UNDERSTANDING_SYSTEM_PROMPT = """You are a retail product search query analyzer.

Given a customer search query, extract structured search intent and return ONLY valid JSON.

Your response must be a single JSON object with these fields:
- "rewritten_query" (string): A clean, specific version of the query optimized for semantic search. Expand abbreviations, fix spelling, add context where appropriate.
- "category" (string or null): The product category if detectable (e.g. "Office Chairs", "Sofas", "Outdoor Furniture"). null if unclear.
- "brand" (string or null): The brand name if mentioned. null if not mentioned.
- "price_max" (number or null): The maximum price if mentioned (numeric only, no currency symbols). null if not mentioned.
- "filters" (object): An object of additional product attribute filters inferred from the query. Examples: {"color": "black", "material": "leather", "size": "queen"}. Use an empty object {} if no attributes are detectable.

Respond ONLY with the JSON object. No explanation, no markdown, no code fences.

Examples:

Input: "comfortable black leather office chair under $400"
Output: {"rewritten_query": "comfortable leather office chair with ergonomic support", "category": "Office Chairs", "brand": null, "price_max": 400.0, "filters": {"color": "black", "material": "leather"}}

Input: "ashley mid century sofa"
Output: {"rewritten_query": "mid century modern sofa", "category": "Sofas", "brand": "Ashley", "price_max": null, "filters": {"style": "mid century modern"}}

Input: "cozy reading chair"
Output: {"rewritten_query": "comfortable accent armchair for reading", "category": "Accent Chairs", "brand": null, "price_max": null, "filters": {}}
"""


# ── Data Model ────────────────────────────────────────────────────────

@dataclass
class QueryIntent:
    """
    Structured representation of a customer search query's intent,
    as extracted by the LLM query understanding layer.
    """
    original_query: str
    rewritten_query: str
    category: Optional[str] = None
    brand: Optional[str] = None
    price_max: Optional[float] = None
    filters: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "original_query": self.original_query,
            "rewritten_query": self.rewritten_query,
            "category": self.category,
            "brand": self.brand,
            "price_max": self.price_max,
            "filters": self.filters,
        }

    def has_metadata_filters(self) -> bool:
        """Returns True if any structured filters are available for pushdown."""
        return bool(self.category or self.brand or self.price_max or self.filters)


# ── Core Understanding Function ───────────────────────────────────────

def understand_query(
    raw_query: str,
    workspace_url: str,
    token: str,
    llm_endpoint: str = "databricks-meta-llama-3-1-70b-instruct",
    max_tokens: int = 512,
    temperature: float = 0.0,
) -> QueryIntent:
    """
    Calls the Databricks Foundation Model API (chat completions) to
    extract structured intent from a raw customer query.

    Args:
        raw_query: The original, unprocessed customer query string
        workspace_url: Databricks workspace URL (e.g. https://adb-xxx.azuredatabricks.net)
        token: Databricks personal access token or service principal token
        llm_endpoint: Foundation Model API endpoint name for the LLM
        max_tokens: Maximum tokens in the LLM response
        temperature: LLM temperature (0.0 = deterministic, recommended for structured output)

    Returns:
        QueryIntent dataclass with all extracted fields
    """
    endpoint_url = f"{workspace_url.rstrip('/')}/serving-endpoints/{llm_endpoint}/invocations"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messages": [
            {"role": "system", "content": _QUERY_UNDERSTANDING_SYSTEM_PROMPT},
            {"role": "user", "content": raw_query},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    try:
        response = requests.post(endpoint_url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        raw_content = response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        logger.error(f"LLM API call failed for query '{raw_query}': {e}")
        return _fallback_intent(raw_query)
    except (KeyError, IndexError) as e:
        logger.error(f"Unexpected LLM response format: {e}")
        return _fallback_intent(raw_query)

    return _parse_intent(raw_query, raw_content)


def _parse_intent(original_query: str, llm_response: str) -> QueryIntent:
    """
    Parses the LLM JSON response into a QueryIntent object.
    Falls back to a safe default if parsing fails.
    """
    # Strip any accidental markdown code fences
    cleaned = re.sub(r"```(?:json)?", "", llm_response).strip().rstrip("`").strip()

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(
            f"Failed to parse LLM response as JSON for query '{original_query}'. "
            f"Raw response: {llm_response[:300]}"
        )
        return _fallback_intent(original_query)

    return QueryIntent(
        original_query=original_query,
        rewritten_query=data.get("rewritten_query") or original_query,
        category=data.get("category"),
        brand=data.get("brand"),
        price_max=_safe_float(data.get("price_max")),
        filters=data.get("filters") or {},
    )


def _fallback_intent(raw_query: str) -> QueryIntent:
    """
    Returns a safe fallback QueryIntent when the LLM call fails.
    The pipeline continues with the original query and no filters applied.
    """
    logger.warning(
        f"Using fallback intent (pass-through) for query: '{raw_query}'"
    )
    return QueryIntent(
        original_query=raw_query,
        rewritten_query=raw_query,
        category=None,
        brand=None,
        price_max=None,
        filters={},
    )


def _safe_float(value) -> Optional[float]:
    """Safely converts a value to float, returning None on failure."""
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


# ── Batch Understanding ───────────────────────────────────────────────

def understand_queries_batch(
    queries: list,
    workspace_url: str,
    token: str,
    llm_endpoint: str = "databricks-meta-llama-3-1-70b-instruct",
) -> list:
    """
    Runs query understanding for a list of raw query strings.
    Returns a list of QueryIntent objects in the same order.

    Used primarily by the evaluation pipeline to process WANDS queries.
    """
    return [
        understand_query(q, workspace_url, token, llm_endpoint)
        for q in queries
    ]
