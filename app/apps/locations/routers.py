from fastapi import APIRouter, status
from starlette.responses import JSONResponse
from .models import LocationSchema  # , DeleteLocationSchema
from .services import (
    create_location_service,
    # delete_location_service,
    update_location_service
)

router = APIRouter()


# @router.post("/create")
# async def create_location(location: LocationSchema):
#     is_created = await create_location_service(location)
#     if not is_created:
#         JSONResponse(
#             {"message": "Error in create product"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully created product",
#     }


@router.post("/update")
async def update_location(location: LocationSchema):
    is_updated = await update_location_service(location)
    if not is_updated:
        JSONResponse(
            {"message": "Error in update product"},
            status_code=status.HTTP_400_BAD_REQUEST
        )
    return {
        "message": "Successfully updated product",
    }


# @router.post("/delete")
# async def delete_location(location: DeleteLocationSchema):
#     is_deleted = await delete_location_service(location)
#     if not is_deleted:
#         JSONResponse(
#             {"message": "Error in delete product"},
#             status_code=status.HTTP_400_BAD_REQUEST
#         )
#     return {
#         "message": "Successfully deleted product",
#     }
