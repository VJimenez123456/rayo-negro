# flake8: noqa
sql_product_create = """
    INSERT INTO product (product_id, title, vendor, price, sku, image_url)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

sql_variant_create = """
    INSERT INTO product_variant (variant_id, product_id, title, sku, price, stock, barcode)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
sql_product_update = """
    INSERT INTO product (product_id, title, vendor, price, sku, image_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE title=VALUES(title), vendor=VALUES(vendor), price=VALUES(price), sku=VALUES(sku), image_url=VALUES(image_url)
"""
sql_variant_update = """
    INSERT INTO product_variant (variant_id, product_id, title, sku, price, stock, barcode)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE title=VALUES(title), sku=VALUES(sku), price=VALUES(price), stock=VALUES(stock), barcode=VALUES(barcode)
"""
select_product = "SELECT * FROM product WHERE product_id = %s"

delete_product = "DELETE FROM product WHERE product_id = %s"

delete_product_variants = "DELETE FROM product_variant WHERE product_id = %s"

select_variant = "SELECT stock FROM product_variant WHERE variant_id = %s"


def clean_string(value):
    if value is None:
        return 'Unknown'
    return value.encode('ascii', 'ignore').decode('ascii')
