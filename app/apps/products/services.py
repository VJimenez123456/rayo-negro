from .models import DeleteProductSchema, ProductSchema, Variant
from .helper import get_product_and_variants
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
from typing import List
from mysql.connector import Error

BATCH_SIZE = 500


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


async def update_or_create_many_products_service(
        products: List[ProductSchema]):
    total_products = []
    total_variants = []
    for product in products:
        new_product, new_variants = get_product_and_variants(product)
        total_products.append(new_product)
        total_variants.extend(new_variants)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_created = False
    try:
        print("total_variants", len(total_variants))
        print("total_products", len(total_products))
        cursor.executemany(sql_product_update, total_products)
        cursor.executemany(sql_variant_update, total_variants)
        connection.commit()
        is_created = True
    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    return is_created


async def delete_many_products_service(products: List[DeleteProductSchema]):
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    is_deleted = False
    try:
        products_for_delete = []
        for product in products:
            cursor.execute(select_product, (product.id,))
            result = cursor.fetchone()
            if result:
                products_for_delete.append(product)

        products_for_execute = [(prod.id,) for prod in products_for_delete]
        # Primero eliminar las variantes asociadas al producto
        cursor.executemany(delete_product_variants, products_for_execute)
        # Luego eliminar el producto
        cursor.executemany(delete_product, products_for_execute)
        connection.commit()  # TODO: descomentar
        is_deleted = True
    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    return is_deleted


async def create_variant_service(variant: Variant) -> bool:
    new_variant = (
        variant.id,
        variant.product_id,
        clean_string(variant.title),
        clean_string(variant.sku),
        variant.price or '0.00',
        variant.inventory_quantity or 0,
        clean_string(variant.barcode)
    )
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_created = False
    try:
        cursor.execute(sql_variant_create, new_variant)
        connection.commit()
        is_created = True
    finally:
        cursor.close()
    return is_created


async def get_all_products_in_db() -> list:
    products_in_bd = []
    try:
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        select_all_prod = "SELECT * FROM product;"
        cursor.execute(select_all_prod)
        products_in_bd = cursor.fetchall()
    except Error as e:
        print(f"Error get products {e}")
        connection.rollback()
    finally:
        cursor.close()
    return products_in_bd


async def get_variants_in_db() -> list:
    variants = []
    try:
        # connection
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        get_variants = """
            SELECT variant_id as id, barcode
            FROM product_variant
            ORDER BY variant_id ASC
        """
        cursor.execute(get_variants)
        variants = cursor.fetchall()
    except Error as e:
        print(f"Error get products {e}")
        connection.rollback()
    finally:
        cursor.close()
    return variants
