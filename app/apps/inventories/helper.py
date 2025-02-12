# flake8: noqa
sql_inventory_update = """
    INSERT INTO inventory (variant_id, location_id, barcode, stock)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE barcode=VALUES(barcode), stock=VALUES(stock)
"""

select_barcode_variant = """
    SELECT barcode FROM product_variant WHERE variant_id = %s
"""

select_all_locations = """
        SELECT SucursalID as location_id, location_shopify
        FROM locations WHERE location_shopify is not null
    """

select_all_variants = "SELECT variant_id, barcode FROM product_variant"

update_loc_var_in_inventory = """
    UPDATE inventory SET stock = %s WHERE location_id = %s AND variant_id = %s;
"""
