# flake8: noqa
sql_location_create = """
    INSERT INTO location (id, Location_name, created_at)
    VALUES (%s, %s, %s)
"""
sql_location_update = """
    INSERT INTO location (id, Location_name, created_at)
    VALUES (%s, %s, %s)
    ON DUPLICATE KEY UPDATE Location_name=VALUES(Location_name), created_at=VALUES(created_at)
"""

select_location = "SELECT * FROM locations WHERE id = %s"

delete_location = "DELETE FROM locations WHERE id = %s"
