# flake8: noqa
sql_location_create = """
    INSERT INTO location (Locatiosn_name, created_at, location_shopify)
    VALUES (%s, %s, %s)
"""
sql_location_update = """
    INSERT INTO location (id, Location_name, created_at, location_shopify)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE Location_name=VALUES(Location_name), created_at=VALUES(created_at), location_shopify=VALUES(location_shopify)
"""

select_location = "SELECT * FROM location WHERE location_shopify = %s"

select_location_id = "SELECT id FROM location WHERE location_shopify = %s"

delete_location = "DELETE FROM location WHERE location_shopify = %s"
