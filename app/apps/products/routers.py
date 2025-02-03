from fastapi import APIRouter, status
from starlette.responses import JSONResponse
from .models import DeleteProductSchema, ProductSchema
from .services import (
    create_product_service,
    delete_product_service,
    update_product_service,
)

router = APIRouter()


@router.post("/create")
async def create_product(product: ProductSchema):
    """Create a new  product"""
    is_created = await create_product_service(product)
    if not is_created:
        JSONResponse(
            {"message": "Error in create product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully created product",
    }


@router.post("/update")
async def update_product(product: ProductSchema):
    is_updated = await update_product_service(product)
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }


@router.post("/delete")
async def delete_product(product: DeleteProductSchema):
    is_deleted = await delete_product_service(product)
    if not is_deleted:
        JSONResponse(
            {"message": "Error in delete product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully deleted product",
    }
