# flake8: noqa
sql_location_create = """
    INSERT INTO locations (SucursalNombre, location_shopify)
    VALUES (%s, %s, %s)
"""
sql_location_update = """
    INSERT INTO locations (SucursalID, SucursalNombre, location_shopify)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE SucursalNombre=VALUES(SucursalNombre), location_shopify=VALUES(location_shopify)
"""

select_location = "SELECT * FROM locations WHERE location_shopify = %s"

select_location_id = "SELECT SucursalID FROM locations WHERE location_shopify = %s"

delete_location = "DELETE FROM locations WHERE location_shopify = %s"
