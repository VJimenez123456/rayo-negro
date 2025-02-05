from .models import InventorySchema
from app.database import get_db_connection
from .helper import sql_inventory_update
from app.apps.locations.helper import select_location_id


async def update_inventory_service(inventory: InventorySchema):
    # TODO: por que la duplicación de variant-location
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(select_location_id, (inventory.location_id,))
    result = cursor.fetchone()
    location_id = result["SucursalID"] if result else None
    print("location_id---->", location_id)
    is_updated = False
    if location_id:
        inventory_obj = (
            inventory.inventory_item_id,
            location_id,
            "barcode",
            inventory.available
        )
        print("inventory_obj", inventory_obj)
        try:
            cursor.execute(sql_inventory_update, inventory_obj)
            connection.commit()
            is_updated = True
        finally:
            cursor.close()
    return is_updated
