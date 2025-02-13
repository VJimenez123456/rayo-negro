from .models import InventorySchema
from app.database import get_db_connection
from .helper import (
    select_all_locations,
    select_all_variants,
    select_barcode_variant,
    sql_inventory_update,
    # update_loc_var_in_inventory,
)
from app.apps.locations.helper import select_location_id
from typing import Dict


async def update_inventory_service(inventory: InventorySchema):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # for location
    cursor.execute(select_location_id, (inventory.location_id,))
    result = cursor.fetchone()
    location_id = result["SucursalID"] if result else None
    # for barcode
    print("inventory.inventory_item_id", inventory.inventory_item_id)
    cursor.execute(select_barcode_variant, (inventory.inventory_item_id,))
    result_barcode = cursor.fetchone()
    print("result_barcode", result_barcode)
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


async def update_many_inventory_service(inventories: Dict):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    # for location
    cursor.execute(select_all_locations)
    locations = cursor.fetchall()
    # print("locations", locations)
    dict_locations = {}
    for location in locations:
        dict_locations[location["location_shopify"]] = location["location_id"]
    # for barcodes
    cursor.execute(select_all_variants)
    variants_barcode = cursor.fetchall()
    print("variants_barcode", variants_barcode)
    dict_variants = {}
    for var_bar in variants_barcode:
        if var_bar["id"] not in dict_variants:
            dict_variants[var_bar["id"]] = var_bar["barcode"]
    print("dict_variants", len(dict_variants))
    # print("dict_variants", dict_variants)

    update_inventories = []
    for variant_id, locations_stock in inventories.items():
        for location_id, stock in locations_stock.items():
            location_id = f"{location_id}"
            if location_id in dict_locations:
                barcode = dict_variants.get(f"{variant_id}", "")
                print("barcode", barcode)
                update_inventories.append((
                    variant_id,
                    location_id,
                    barcode,
                    stock
                ))
    is_updated = False
    try:
        print("update_inventories", len(update_inventories))
        print("update_inventories", update_inventories[:10])
        # cursor.executemany(sql_inventory_update, update_inventories)
        # connection.commit()  # TODO: descomentar
        is_updated = True
    finally:
        cursor.close()
    return is_updated
