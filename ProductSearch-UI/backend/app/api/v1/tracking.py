import logging
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from app.services.session_store import get_session_store

logger = logging.getLogger("TrackingAPI")
router = APIRouter(tags=["Tracking"])


def _resolve_session(x_session_id: str | None = Header(None)) -> str:
    sid = x_session_id
    if not sid:
        import uuid
        sid = str(uuid.uuid4())
    return sid


class TrackSearchRequest(BaseModel):
    query: str


class TrackViewRequest(BaseModel):
    product_id: str


class TrackCartRequest(BaseModel):
    product_id: str
    action: str = "add"


class TrackResponse(BaseModel):
    status: str = "ok"
    session_id: str


@router.post("/track/search", response_model=TrackResponse)
async def track_search(body: TrackSearchRequest, x_session_id: str | None = Header(None)):
    session_id = _resolve_session(x_session_id)
    store = get_session_store()
    store.track_search(session_id, body.query)
    return TrackResponse(session_id=session_id)


@router.post("/track/view", response_model=TrackResponse)
async def track_view(body: TrackViewRequest, x_session_id: str | None = Header(None)):
    session_id = _resolve_session(x_session_id)
    store = get_session_store()
    store.track_view(session_id, body.product_id)
    return TrackResponse(session_id=session_id)


@router.post("/track/cart", response_model=TrackResponse)
async def track_cart(body: TrackCartRequest, x_session_id: str | None = Header(None)):
    session_id = _resolve_session(x_session_id)
    store = get_session_store()
    if body.action == "add":
        store.add_to_cart(session_id, body.product_id)
    elif body.action == "remove":
        store.remove_from_cart(session_id, body.product_id)
    else:
        raise HTTPException(status_code=400, detail=f"Invalid action: {body.action}")
    return TrackResponse(session_id=session_id)


class ContextResponse(BaseModel):
    session_id: str
    customer_id: str
    recent_searches: list[str]
    recent_views: list[str]
    cart_product_ids: list[str]
    cart_count: int
    search_count: int
    view_count: int


@router.get("/context", response_model=ContextResponse)
async def get_context(x_session_id: str | None = Header(None)):
    session_id = _resolve_session(x_session_id)
    store = get_session_store()
    return store.get_context(session_id)  # type: ignore
