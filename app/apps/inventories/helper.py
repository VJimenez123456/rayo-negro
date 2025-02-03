# flake8: noqa
sql_inventory_update = """
    INSERT INTO inventory (variant_id, location_id, barcode, stock)
    VALUES (%s, %s, %s, %s)
"""
