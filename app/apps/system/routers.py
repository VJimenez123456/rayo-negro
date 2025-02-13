from fastapi import APIRouter, status
# from starlette.responses import JSONResponse
from .services import (
    # update_inventory_service,
    # update_products_service,
    # update_barcode_in_orders_service,
    # update_locations_in_inventory_service,
    update_barcode_in_inventory_service,
    update_product_for_inventory_service,
    simple_update_barcode_in_inventory_service,
)
from starlette.responses import JSONResponse


router = APIRouter()


# @router.get("/inventory")
# async def update_inventory():
#     is_updated = await update_inventory_service()
#     if not is_updated:
#         JSONResponse(
#             {"message": "Error in update inventory"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully updated inventory",
#     }


@router.get("/simple_inventory_barcode")
async def simple_update_barcode_in_inventory():
    is_updated = await simple_update_barcode_in_inventory_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update barcode-inventory"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully simple updated barcode-inventory",
    }


@router.get("/inventory_barcode")
async def update_inventory_barcode():
    is_updated = await update_barcode_in_inventory_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update barcode-inventory"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated barcode-inventory",
    }


@router.get("/update_product_for_inventory")
async def update_product_for_inventory():
    is_updated = await update_product_for_inventory_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product-inventory"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product-inventory",
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


# @router.get("/update_locations")
# async def update_locations_in_inventory():
#     is_updated = await update_locations_in_inventory_service()
#     if not is_updated:
#         JSONResponse(
#             {"message": "Error in update product"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully updated product",
#     }
