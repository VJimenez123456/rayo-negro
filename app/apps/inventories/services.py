from .models import InventorySchema
from app.database import get_db_connection
from .helper import (
    select_all_locations,
    select_all_variants,
    select_barcode_variant,
    sql_inventory_update,
)
from app.apps.locations.helper import select_location_id
from typing import List


async def update_inventory_service(inventory: InventorySchema):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # for location
    cursor.execute(select_location_id, (inventory.location_id,))
    result = cursor.fetchone()
    location_id = result["SucursalID"] if result else None
    # for barcode
    cursor.execute(select_barcode_variant, (inventory.inventory_item_id,))
    result_barcode = cursor.fetchone()
    barcode = result_barcode["barcode"] if result_barcode else 'Unknown'

    is_updated = False
    if location_id:
        inventory_obj = (
            inventory.inventory_item_id,
            location_id,
            barcode,
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


async def update_many_inventory_service(inventories: List[InventorySchema]):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # for location
    cursor.execute(select_all_locations)
    locations = cursor.fetchall()
    print("locations", locations)
    dict_locations = {}
    for location in locations:
        dict_locations[location["location_id"]] = location["location_shopify"]
    # for variants
    cursor.execute(select_all_variants)
    variants = cursor.fetchall()
    print("variants", variants)
    dict_variants = {}
    for variant in variants:
        dict_variants[variant["variant_id"]] = variant["barcode"]
    update_inventories = []
    for inventory in inventories:
        update_inventories.append((
            inventory.inventory_item_id,
            dict_locations[inventory.location_id],
            dict_variants[inventory.inventory_item_id],
            inventory.available
        ))
    is_updated = False
    try:
        cursor.executemany(sql_inventory_update, update_inventories)
        # connection.commit()  # TODO: descomentar
        is_updated = True
    finally:
        cursor.close()
    return is_updated
