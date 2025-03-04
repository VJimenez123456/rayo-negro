# flake8: noqa
sql_inventory_update = """
    INSERT INTO inventory (variant_id, location_id, barcode, stock)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE barcode=VALUES(barcode), stock=VALUES(stock)
"""

select_barcode_variant = """
    SELECT variant_id AS id, barcode FROM product_variant WHERE inventory_item_id = %s
"""

select_all_locations = """
        SELECT SucursalID as location_id, location_shopify
        FROM locations WHERE location_shopify is not null
    """

select_all_variants = """
    SELECT variant_id as id, barcode, inventory_item_id
    FROM product_variant
    WHERE barcode <> '' OR barcode is not null OR barcode = 'Unknown';
"""

update_loc_var_in_inventory = """
    UPDATE inventory SET stock = %s WHERE location_id = %s AND variant_id = %s;
"""


def inventory_dict(inventories):
    print("inventories-0", inventories)
    print("inventories-0", len(inventories))
    all_iventory = {}
    for level in inventories:
        inventory_item_id = level['inventory_item_id']
        location_id = level['location_id']
        available = level.get('available', 0)
        if inventory_item_id not in all_iventory:
            all_iventory[inventory_item_id] = {}
        all_iventory[inventory_item_id][location_id] = available
    print("all_iventory-1", all_iventory)
    print("all_iventory-1", len(all_iventory))
    return all_iventory

