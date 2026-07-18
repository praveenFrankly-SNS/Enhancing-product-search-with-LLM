"""
Products API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, status
from typing import Optional
from app.services.search_service import search_service
from app.services.databricks_service import databricks_service
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/categories")
async def get_categories(
    dataset: str = Query(default="wands", description="Dataset variant: 'wands' or 'amazon'")
):
    """
    Get all product categories with counts from the Gold table.
    """
    try:
        categories = await databricks_service.get_categories(dataset=dataset)
        return {"categories": categories}
    except Exception as e:
        logger.error("Failed to fetch categories", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch categories",
        )


@router.get("/brands")
async def get_brands(
    category: Optional[str] = Query(default=None, description="Filter brands by category"),
    dataset: str = Query(default="wands", description="Dataset variant: 'wands' or 'amazon'"),
):
    """
    Get distinct brands with product counts, optionally filtered by category.
    """
    try:
        brands = await databricks_service.get_brands(category=category, dataset=dataset)
        return {"brands": brands}
    except Exception as e:
        logger.error("Failed to fetch brands", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch brands",
        )


@router.get("/{product_id}")
async def get_product(
    product_id: str,
    dataset: str = Query(default="wands", description="Dataset variant: 'wands' or 'amazon'"),
):
    """
    Get full product details by ID from the specified dataset Gold table.
    """
    try:
        product = await databricks_service.get_product_by_id(product_id, dataset=dataset)

        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product '{product_id}' not found",
            )

        query_text = product.get("description") or product.get("attribute_summary") or product.get("product_name") or ""
        related = await databricks_service.get_related_products(
            product_id=product_id,
            query_text=query_text,
            limit=4,
            dataset=dataset,
        )

        return {
            **product,
            "related_products": related,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to fetch product", product_id=product_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product details",
        )


@router.get("/{product_id}/image")
async def get_product_image(product_id: str):
    """
    Product image placeholder — redirects to picsum seeded by product_id hash.
    Replace with actual image storage (S3, Azure Blob, DBFS) in production.
    """
    from fastapi.responses import RedirectResponse
    seed = abs(hash(product_id)) % 1000
    return RedirectResponse(
        url=f"https://picsum.photos/seed/{seed}/400/400",
        status_code=302,
    )
