from fastapi import APIRouter, status
# from starlette.responses import JSONResponse
from .services import (
    delete_products_not_exists_service,
    update_inventory_service,
    update_products_service,
    update_barcode_in_orders_service,
    update_locations_in_inventory_service,
    update_barcode_in_inventory_service,
    update_product_for_inventory_service,
    update_variants_for_locations_service,
    update_only_variants_service,
    simple_update_barcode_in_inventory_service,
    get_products_in_shopify_service,
)
from starlette.responses import JSONResponse


router = APIRouter()


# checked
@router.get("/products")
async def update_products():
    is_updated = await update_products_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update products"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated products",
    }


@router.get("/update_only_variants")
async def update_only_variants():
    is_updated = await update_only_variants_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update variants_for_locations"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated variants_for_locations",
    }


@router.get("/update_variants_for_locations")
async def update_variants_for_locations():
    is_updated = await update_variants_for_locations_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update variants_for_locations"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated variants_for_locations",
    }


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


# @router.get("/simple_inventory_barcode")
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


# @router.get("/inventory_barcode")
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


# @router.get("/update_product_for_inventory")
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


# @router.get("/barcode_in_orders")
async def update_barcode_in_orders():
    is_updated = await update_barcode_in_orders_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }


# @router.get("/update_locations")
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


# @router.get("/delete_products_not_exists")
async def delete_products_not_exists():
    is_updated = await delete_products_not_exists_service()
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }
