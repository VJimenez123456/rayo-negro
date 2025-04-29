from fastapi import APIRouter, status
# from starlette.responses import JSONResponse
from .models import InventorySchema
from .services import (
    update_inventory_service,
    update_inventory_for_transfers_service,
)
from starlette.responses import JSONResponse


router = APIRouter()


@router.post("/update")
async def update_inventory(inventory: InventorySchema):
    is_updated = await update_inventory_service(inventory)
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }


# @router.post("/update")
# async def update_inventory_for_transfers(inventory: InventorySchema):
#     is_updated = await update_inventory_for_transfers_service(inventory)
#     if not is_updated:
#         JSONResponse(
#             {"message": "Error in update product"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully updated product",
#     }
