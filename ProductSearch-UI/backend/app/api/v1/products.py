"""
Product API endpoints
"""
from fastapi import APIRouter, HTTPException, Path, status
from app.models.schemas import ProductDetailResponse
from app.services.search_service import search_service
from app.core.logging import get_logger


logger = get_logger(__name__)
router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=ProductDetailResponse)
async def get_product_details(
    product_id: str = Path(..., description="Product ID")
):
    """
    Get detailed information for a specific product
    
    **Example:**
    ```
    GET /api/v1/products/PROD_12345
    ```
    
    **Response includes:**
    - Complete product information
    - Pricing details
    - Product attributes
    - Review statistics
    - Product images
    """
    try:
        product = await search_service.get_product_by_id(product_id)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product {product_id} not found"
            )
        
        return product
    
    except HTTPException:
        raise
    
    except Exception as e:
        logger.error("Failed to fetch product", product_id=product_id, error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch product details"
        )
