# flake8: noqa
sql_inventory_update = """
    INSERT INTO inventory (variant_id, location_id, barcode, stock)
    VALUES (%s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE barcode=VALUES(barcode), stock=VALUES(stock)
"""
