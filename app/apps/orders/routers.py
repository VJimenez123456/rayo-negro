from fastapi import APIRouter, status
from starlette.responses import JSONResponse
from .models import OrderSchema
from .services import update_order_service

router = APIRouter()


# @router.post("/create")
# async def create_order(order: OrderSchema):
#     """Create a new order"""
#     is_created = await create_order_service(order)
#     if not is_created:
#         JSONResponse(
#             {"message": "Error in create product"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully created product",
#     }


@router.post("/update")
async def update_order(order: OrderSchema):
    is_updated = await update_order_service(order)
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }


# @router.post("/delete")
# async def delete_order(order: dict):
#     print("order:", order)
#     return {"message": "ordero creado", "order": order}
