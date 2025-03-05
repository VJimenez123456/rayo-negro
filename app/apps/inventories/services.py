from .models import InventorySchema, InventoryObject
from app.database import get_db_connection
from .helper import (
    select_all_locations,
    select_all_variants,
    select_barcode_variant,
    sql_inventory_update,
    # update_loc_var_in_inventory,
)
from app.apps.system.helper import fetch_shopify_variants_for_items
from app.apps.locations.helper import select_location_id
from typing import Dict, List
from app.apps.inventories.helper import inventory_dict
from app.apps.locations.services import get_all_locations_in_db_dict


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
    variant_id, barcode = None, None
    if result_barcode:
        variant_id = result_barcode["id"]
        barcode = result_barcode["barcode"]

    is_updated = False
    if location_id:
        inventory_obj = (
            variant_id,
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
        inventory_item_id = var_bar["inventory_item_id"]
        if inventory_item_id not in dict_variants:
            dict_variants[inventory_item_id] = 0
        dict_variants[inventory_item_id] = var_bar["barcode"]
    print("dict_variants", len(dict_variants))
    # print("dict_variants", dict_variants)

    update_inventories = []
    for inventory_item_id, locations_stock in inventories.items():
        for location_id, stock in locations_stock.items():
            location_id = f"{location_id}"
            if location_id in dict_locations:
                barcode = dict_variants.get(inventory_item_id, "")
                update_inventories.append((
                    inventory_item_id,
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


async def update_many_inventory_simple_service(
        inventories: List[InventoryObject]):
    update_inventories_list = []
    for inv in inventories:
        update_inventories_list.append((
            inv.variant_id,
            inv.location_id,
            inv.barcode,
            inv.stock
        ))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.executemany(sql_inventory_update, update_inventories_list)
        connection.commit()  # TODO: descomentar
        is_updated = True
    finally:
        cursor.close()
    return is_updated


async def delete_inventories_without_variants(variants: List[int]) -> bool:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        delete_sql = f"""
            DELETE FROM inventory
            WHERE variant_id IN ({', '.join(map(str, variants))});
        """
        cursor.execute(delete_sql)
        connection.commit()
        is_updated = True
    finally:
        cursor.close()
    return is_updated


async def get_variants_with_same_barcode() -> list:
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    data_list = []
    try:
        select_sql = """
            SELECT
                barcode,
                GROUP_CONCAT(DISTINCT variant_id
                ORDER BY variant_id) AS variants
            FROM inventory
            WHERE barcode IS NOT NULL
            GROUP BY barcode HAVING COUNT(DISTINCT variant_id) > 1;
        """
        cursor.execute(select_sql)
        data_list = cursor.fetchall()
    finally:
        cursor.close()
    return data_list


async def update_inventory_for_id_items(var_inv_dict: Dict) -> list:

    inventory_items_id_list = [item for item in var_inv_dict.keys()]
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        inventories = fetch_shopify_variants_for_items(inventory_items_id_list)
        print("Total inventories all locations:", len(inventories))
        all_iventory = inventory_dict(inventories)
        locations_in_db_dict = await get_all_locations_in_db_dict()
        inventories_list = []
        for item_id, level in all_iventory.items():
            inventory_loc_list = []
            for loction_id, stock in level.items():
                _loction_id = locations_in_db_dict.get(f"{loction_id}")
                if _loction_id and stock and item_id in var_inv_dict:
                    inventory_loc_list.append(
                        InventoryObject(**{
                            "variant_id": var_inv_dict[item_id]["id"],
                            "location_id": _loction_id,
                            "barcode": var_inv_dict[item_id]["barcode"],
                            "stock": stock
                        })
                    )
            inventories_list.extend(inventory_loc_list)
        if len(inventories_list) > 0:
            print("Actualizando inventario!!!")
            await update_many_inventory_simple_service(inventories_list)
    finally:
        cursor.close()
    return inventories_list
