from .models import LocationSchema  # , DeleteLocationSchema
from app.database import get_db_connection
from .helper import (
    # delete_location,
    select_location_id,
    sql_location_create,
    sql_location_update
)


async def create_location_service(location: LocationSchema):
    location_obj = (location.name, location.created_at, location.id)
    print("location_obj-c", location_obj)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_created = False
    try:
        cursor.execute(sql_location_create, location_obj)
        connection.commit()
        is_created = True
    finally:
        cursor.close()
    return is_created


async def update_location_service(location: LocationSchema):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    print("loc-shopify", location.id)
    cursor.execute(select_location_id, (location.id,))
    result = cursor.fetchone()
    print("result", result)
    location_id = result["SucursalID"] if result else None
    print("location_id", location_id)
    is_updated = False
    if location_id:
        location_obj = (location_id, location.name, location.updated_at, location.id)
        print("location_obj-u", location_obj)
        try:
            cursor.execute(sql_location_update, location_obj)
            connection.commit()
            is_updated = True
        finally:
            cursor.close()
    return is_updated


# async def delete_location_service(location: DeleteLocationSchema):
#     location_id = location.id
#     print("location_obj-u", location_id)
#     connection = get_db_connection()
#     cursor = connection.cursor(dictionary=True)
#     cursor.execute(select_location, (location_id,))
#     result = cursor.fetchone()
#     is_deleted = False
#     if result:
#         try:
#             cursor.execute(delete_location, (location_id,))
#             connection.commit()
#             is_deleted = True
#         finally:
#             cursor.close()
#     return is_deleted
