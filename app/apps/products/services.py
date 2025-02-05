from .models import DeleteProductSchema, ProductSchema
from app.database import get_db_connection
from .helper import (
    clean_string,
    delete_product,
    select_product,
    delete_product_variants,
    # select_variant,
    sql_product_create,
    sql_product_update,
    sql_variant_create,
    sql_variant_update,
)


async def create_product_service(product: ProductSchema):
    print("product_id:", product.id)
    variants = product.variants
    new_product = (
        product.id,
        product.title,
        product.vendor,
        variants[0].price,
        variants[0].sku or "Unknown",
        product.image.src if product.image else "Unknown"
    )
    variant_values = []
    for variant in variants:
        variant_values.append((
            variant.id,
            product.id,
            clean_string(variant.title),
            clean_string(variant.sku),
            variant.price or '0.00',
            variant.inventory_quantity or 0,
            clean_string(variant.barcode)
        ))
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_created = False
    try:
        cursor.execute(sql_product_create, new_product)
        cursor.executemany(sql_variant_create, variant_values)
        connection.commit()
        is_created = True
    finally:
        cursor.close()
    return is_created


async def update_product_service(product: ProductSchema):
    print("product_id:", product.id)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    variants = product.variants
    product_id = product.id
    new_product = (
        product_id,
        product.title,
        product.vendor,
        variants[0].price,
        variants[0].sku or "Unknown",
        product.image.src if product.image else "Unknown"
    )
    variant_values = []
    for variant in variants:
        variant_id = variant.id
        variant_stock = variant.inventory_quantity or 0
        variant_barcode = clean_string(variant.barcode)
        variant_values.append((
            variant_id,
            product_id,
            clean_string(variant.title),
            clean_string(variant.sku),
            variant.price or '0.00',
            variant_stock,
            variant_barcode
        ))
        # cursor.execute(select_variant, (variant_id,))

    is_updated = False
    try:
        cursor.execute(sql_product_update, new_product)
        cursor.executemany(sql_variant_update, variant_values)
        connection.commit()
        is_updated = True
    finally:
        cursor.close()
    return is_updated


async def delete_product_service(product: DeleteProductSchema):
    product_id = product.id
    print("product_id:", product_id)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(select_product, (product_id,))
    result = cursor.fetchone()
    is_deleted = False
    if result:
        try:
            # Primero eliminar las variantes asociadas al producto
            cursor.execute(delete_product_variants, (product_id,))
            # Luego eliminar el producto
            cursor.execute(delete_product, (product_id,))
            connection.commit()
            is_deleted = True
        finally:
            cursor.close()
    return is_deleted
