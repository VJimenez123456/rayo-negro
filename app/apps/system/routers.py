from fastapi import APIRouter, status
# from starlette.responses import JSONResponse
from .services import (
    update_inventory_service,
    # update_products_service,
    # update_barcode_in_orders_service,
    update_locations_in_inventory_service,
)
from starlette.responses import JSONResponse


router = APIRouter()


@router.get("/inventory")
async def update_inventory():
    is_updated = await update_inventory_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update inventory"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated inventory",
    }


# @router.get("/products")
# async def update_products():
#     is_updated = await update_products_service()
#     if not is_updated:
#         JSONResponse(
#             {"message": "Error in update products"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully updated products",
#     }


# @router.get("/barcode_in_orders")
# async def update_barcode_in_orders():
#     is_updated = await update_barcode_in_orders_service()
#     if not is_updated:
#         JSONResponse(
#             {"message": "Error in update product"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully updated product",
#     }


@router.get("/update_locations")
async def update_locations_in_inventory():
    is_updated = await update_locations_in_inventory_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }
