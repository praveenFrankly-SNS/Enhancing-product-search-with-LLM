import logging
import threading
from typing import Any

logger = logging.getLogger("SessionStore")

MAX_SEARCHES_PER_SESSION = 10
MAX_VIEWS_PER_SESSION = 20
MAX_CART_ITEMS_PER_SESSION = 20


class SessionStore:
    def __init__(self):
        self._sessions: dict[str, dict] = {}
        self._lock = threading.Lock()

    def _ensure_session(self, session_id: str) -> dict:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = {
                    "recent_searches": [],
                    "recent_views": [],
                    "cart_product_ids": [],
                    "customer_id": None,
                }
            return self._sessions[session_id]

    def track_search(self, session_id: str, query: str) -> None:
        session = self._ensure_session(session_id)
        with self._lock:
            searches = session["recent_searches"]
            searches.insert(0, query)
            session["recent_searches"] = searches[:MAX_SEARCHES_PER_SESSION]
        logger.info(f"[{session_id}] Tracked search: '{query}'")

    def track_view(self, session_id: str, product_id: str) -> None:
        session = self._ensure_session(session_id)
        with self._lock:
            views = session["recent_views"]
            if product_id in views:
                views.remove(product_id)
            views.insert(0, product_id)
            session["recent_views"] = views[:MAX_VIEWS_PER_SESSION]
        logger.info(f"[{session_id}] Tracked view: {product_id}")

    def add_to_cart(self, session_id: str, product_id: str) -> None:
        session = self._ensure_session(session_id)
        with self._lock:
            cart = session["cart_product_ids"]
            if product_id not in cart:
                cart.append(product_id)
            session["cart_product_ids"] = cart[:MAX_CART_ITEMS_PER_SESSION]
        logger.info(f"[{session_id}] Added to cart: {product_id}")

    def remove_from_cart(self, session_id: str, product_id: str) -> None:
        session = self._ensure_session(session_id)
        with self._lock:
            cart = session["cart_product_ids"]
            if product_id in cart:
                cart.remove(product_id)
        logger.info(f"[{session_id}] Removed from cart: {product_id}")

    def set_customer_id(self, session_id: str, customer_id: str) -> None:
        session = self._ensure_session(session_id)
        with self._lock:
            session["customer_id"] = customer_id
        logger.info(f"[{session_id}] Customer ID set: {customer_id}")

    def get_context(self, session_id: str) -> dict[str, Any]:
        session = self._ensure_session(session_id)
        with self._lock:
            return {
                "session_id": session_id,
                "customer_id": session.get("customer_id", "CUST-FRANK-001"),
                "recent_searches": list(session["recent_searches"]),
                "recent_views": list(session["recent_views"]),
                "cart_product_ids": list(session["cart_product_ids"]),
                "cart_count": len(session["cart_product_ids"]),
                "search_count": len(session["recent_searches"]),
                "view_count": len(session["recent_views"]),
            }


_session_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    global _session_store
    if _session_store is None:
        _session_store = SessionStore()
    return _session_store
