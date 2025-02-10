
import logging
from datetime import datetime
from app.common.utils import (
    fetch_locations,
    get_location_ids,
    fetch_shopify_products,
    fetch_inventory_levels,
)
from app.database import get_db_connection
from mysql.connector import Error
from app.apps.products.services import (
    delete_many_products_service,
    update_or_create_many_products_service
)
from app.apps.products.models import DeleteProductSchema, ProductSchema


#  Logging settings
logging.basicConfig(
    filename='inventario_sync.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def update_products() -> bool:
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        logging.info("Obteniendo detalles de productos de base de datos...")
        select_all_prod = "SELECT * FROM product;"
        cursor.execute(select_all_prod)
        products_in_bd = cursor.fetchall()
        dict_products_in_db = {}
        for prod in products_in_bd:
            dict_products_in_db[prod["product_id"]] = prod
        print(f"Amount of product in database: {len(products_in_bd)}")

        # Get productos
        logging.info("Obteniendo detalles de productos de Shopify...")
        products_shopify = fetch_shopify_products()
        print(f"Amount of product in shofify: {len(products_shopify)}")
        dict_products_in_shopify = {}
        for prod_shopi in products_shopify:
            dict_products_in_shopify[prod_shopi["id"]] = prod_shopi
        delete_products = []
        for key, value in dict_products_in_db.items():
            if key not in dict_products_in_shopify:
                delete_products.append(value)
        print(f"Total products for delete {len(delete_products)}")

        # delete products
        delete_products_schema = [
            DeleteProductSchema(id=prod_del["product_id"])
            for prod_del in delete_products
        ]
        await delete_many_products_service(delete_products_schema)

        # update or create productos
        print("products_shopify", products_shopify[0])
        update_or_create_products_schema = [
            ProductSchema(**prod) for prod in products_shopify
        ]
        await update_or_create_many_products_service(
            update_or_create_products_schema)

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    return is_updated


async def update_barcode_in_orders():
    print("here")
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        logging.info("Obteniendo detalles de pedidos de base de datos...")
        select_all_orders = """
                SELECT *
                FROM order_item
                WHERE barcode is null
                AND variant_id is not null;
            """
        cursor.execute(select_all_orders)
        orders_in_bd = cursor.fetchall()
        print("orders_in_bd", orders_in_bd)
        for order_item in orders_in_bd:
            get_variant = f"""
                SELECT *
                FROM product_variant
                WHERE variant_id = {order_item['variant_id']};
            """
            print("get_variant", get_variant)
            cursor.execute(get_variant)
            get_variant = cursor.fetchone()
            if get_variant:
                update_order_item = f"""
                    UPDATE order_item
                    SET barcode = {get_variant["barcode"]}
                    WHERE id = {order_item['id']};
                """
                print("update_order_item", update_order_item)
                cursor.execute(update_order_item)
                connection.commit()

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    return is_updated


async def update_inventory():
    mensaje = f"->Tarea ejecutada a las {datetime.now()}"
    logging.info(mensaje)
    print(mensaje)
    # code
    try:
        # connection
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        select_all_prod = "SELECT * FROM product;"
        cursor.execute(select_all_prod)
        result = cursor.fetchall()
        print(f"Cantidad {len(result)}")
        # Get all locations
        locations = fetch_locations()
        print("locations---->", locations)
        location_ids = get_location_ids(locations)
        print("location_ids---->", location_ids)

        # Obtener productos activos
        logging.info("Obteniendo detalles de productos de Shopify...")
        products = fetch_shopify_products()
        print("products---->", len(products))
        print("products---->", products[:3])

        if products and len(products) > 0:
            # Obtener los inventory_item_ids para los niveles de inventario
            inventory_item_ids = [
                variant.get('inventory_item_id')
                for product in products
                for variant in product.get('variants', [])
                if variant.get('inventory_item_id')
            ]
            # Delete duplicate
            inventory_item_ids = list(set(inventory_item_ids))
            print("inventory_item_ids", len(inventory_item_ids))
            print("inventory_item_ids", inventory_item_ids[:3])

            # Get inventory levels
            inventory_levels = fetch_inventory_levels(
                inventory_item_ids=inventory_item_ids,
                location_ids=location_ids
            )
            i = 0
            for key, value in inventory_levels.items():
                if i > 3:
                    break
                else:
                    i += 1
                    print("key", key, "value", value)
            print("inventory_levels", len(inventory_levels))

    #         # Insertar o actualizar productos, variantes e inventarios
    #         insert_or_update_products_variants_and_inventory(products, conn, locations, inventory_levels)

    #         # Eliminar productos archivados o borradores si aplica
    #         delete_archived_or_draft_products(products, conn, api_version='2023-07')

    #         logging.info(f"Total de productos procesados: {len(products)}")
    #     else:
    #         logging.info("No se obtuvieron productos de Shopify.")

    #     conn.close()
    except Exception as e:
        logging.exception(f"Se produjo un error inesperado: {e}")

    # logging.info("Esperando 10 minutos para la siguiente sincronización.")
        # time.sleep(600)
    
    finally:
        cursor.close()
