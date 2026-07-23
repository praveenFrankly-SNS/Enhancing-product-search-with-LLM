import json
import logging
import os
from typing import Any

import requests
from fastapi import APIRouter, Header, HTTPException, Query
from app.services.session_store import get_session_store
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


def _resolve_session(x_session_id: str | None) -> str:
    sid = x_session_id
    if not sid:
        import uuid
        sid = str(uuid.uuid4())
    return sid


def _call_databricks_serving(
    customer_id: str,
    surface: str,
    current_product_id: str | None,
    session_context: dict,
) -> dict | None:
    endpoint = os.environ.get("RECOMMENDATION_SERVING_ENDPOINT", "")
    host = settings.databricks_host
    token = settings.databricks_token

    if not endpoint or not host or not token:
        logger.info("Recommendation serving endpoint not configured — skipping.")
        return None

    clean_host = host.strip().rstrip("/")
    if not clean_host.startswith("http"):
        clean_host = f"https://{clean_host}"

    url = f"{clean_host}/api/2.0/serving-endpoints/{endpoint}/invocations"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "dataframe_records": [{
            "customer_id": customer_id,
            "surface": surface,
            "current_product_id": current_product_id,
            "limit": 8,
            "session_context": session_context,
        }]
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
        predictions = result.get("predictions", [])
        if predictions:
            return predictions[0] if isinstance(predictions, list) else predictions
        return result
    except Exception as e:
        logger.warning(f"Recommendation serving call failed: {e}")
        return None


@router.get("/")
async def get_recommendations(
    surface: str = Query("HOME", description="HOME | PRODUCT_PAGE | CART"),
    current_product_id: str | None = Query(None, description="Current PDP product ID"),
    x_session_id: str | None = Header(None),
):
    session_id = _resolve_session(x_session_id)
    store = get_session_store()
    ctx = store.get_context(session_id)

    session_context = {
        "recent_searches": ctx.get("recent_searches", []),
        "recent_views": ctx.get("recent_views", []),
        "cart_product_ids": ctx.get("cart_product_ids", []),
    }

    customer_id = ctx.get("customer_id", "CUST-FRANK-001")

    result = _call_databricks_serving(
        customer_id=customer_id,
        surface=surface,
        current_product_id=current_product_id,
        session_context=session_context,
    )

    if result is None:
        return {
            "session_id": session_id,
            "customer_id": customer_id,
            "surface": surface,
            "session_context": session_context,
            "recommendations": [],
            "message": "Recommendation serving endpoint not configured. Set RECOMMENDATION_SERVING_ENDPOINT env var.",
        }

    return {
        "session_id": session_id,
        "customer_id": customer_id,
        "surface": surface,
        "session_context": session_context,
        "recommendations": result.get("recommendations", result),
    }
