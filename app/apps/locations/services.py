from .models import LocationSchema, DeleteLocationSchema
from app.database import get_db_connection
from .helper import (
    delete_location,
    select_location,
    # select_location_id,
    sql_location_create,
    sql_location_update
)
from mysql.connector import Error


async def create_location_service(location: LocationSchema):
    location_obj = (location.name, location.id)
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
    is_updated = False
    location_obj = (location.id, location.name, location.id)
    try:
        cursor.execute(sql_location_update, location_obj)
        connection.commit()
        is_updated = True
    finally:
        cursor.close()
    return is_updated


async def delete_location_service(location: DeleteLocationSchema):
    location_id = location.id
    print("location_obj-u", location_id)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(select_location, (location_id,))
    result = cursor.fetchone()
    is_deleted = False
    if result:
        try:
            cursor.execute(delete_location, (location_id,))
            connection.commit()
            is_deleted = True
        finally:
            cursor.close()
    return is_deleted


async def get_all_locations_in_db() -> list:
    locations_in_db = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        locations_sql = """
            SELECT SucursalID, location_shopify
            FROM locations
            WHERE location_shopify is not null
            ORDER BY SucursalID ASC;
        """
        cursor.execute(locations_sql)
        locations_in_db = cursor.fetchall()
    except Error as e:
        print(f"Error get products {e}")
        connection.rollback()
    finally:
        cursor.close()
    return locations_in_db


async def get_all_locations_in_db_dict() -> dict:
    locations = await get_all_locations_in_db()
    return {loc["location_shopify"]: loc["SucursalID"] for loc in locations}
