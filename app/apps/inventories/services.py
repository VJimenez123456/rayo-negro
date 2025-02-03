from .models import InventorySchema
from app.database import get_db_connection
from .helper import sql_inventory_update


async def update_inventory_service(inventory: InventorySchema):
    # TODO: por que la duplicación de variant-location
    inventory_obj = (
        inventory.inventory_item_id,
        inventory.location_id,
        "barcode",
        inventory.available
    )
    print("inventory_obj", inventory_obj)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_updated = False
    try:
        cursor.execute(sql_inventory_update, inventory_obj)
        connection.commit()
        is_updated = True
    finally:
        cursor.close()
    return is_updated
