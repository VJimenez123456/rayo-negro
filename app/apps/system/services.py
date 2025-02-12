
import logging
import time
from datetime import datetime
from .helper import (
    fetch_locations,
    get_location_ids,
    fetch_shopify_products,
    fetch_inventory_levels,
    select_all_locations,
    select_inventory,
    update_location_in_inventory,
)
from app.database import get_db_connection
from mysql.connector import Error
from app.apps.products.services import (
    delete_many_products_service,
    update_or_create_many_products_service
)
from app.apps.inventories.services import update_many_inventory_service
from app.apps.products.models import DeleteProductSchema, ProductSchema
from app.apps.inventories.models import InventorySchema


#  Logging settings
logging.basicConfig(
    filename='inventario_sync.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


async def update_products_service() -> bool:
    print("Init update update_products")
    init_time = time.time()
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
        # print("products_shopify", products_shopify[0])
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

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update update_products")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_barcode_in_orders_service() -> bool:
    print("Init update order_items")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        logging.info("Obteniendo detalles de pedidos de base de datos...")
        select_all_orders = """
            SELECT id, barcode, variant_id
            FROM order_item
            WHERE variant_id is not null
            AND barcode = ''
            ORDER BY variant_id ASC;
        """
        cursor.execute(select_all_orders)
        orders_in_bd = cursor.fetchall()
        print("Orders in bd:", len(orders_in_bd))
        select_variant = """
            SELECT variant_id, barcode FROM product_variant;
        """
        cursor.execute(select_variant)
        variant_in_db = cursor.fetchall()
        variants_dict = {}
        for var in variant_in_db:
            variants_dict[var["variant_id"]] = var["barcode"]
        update_barcode_in_variant = []
        for order_item in orders_in_bd:
            if order_item["variant_id"] in variants_dict:
                update_barcode_in_variant.append(
                    (variants_dict[order_item["variant_id"]], order_item["id"])
                )
        len_update = len(update_barcode_in_variant)
        print("update_barcode_in_variant len:", len_update)
        update_order_item = """
            UPDATE order_item
            SET barcode = %s
            WHERE id = %s
        """
        batch_size = 500
        for i in range(0, len_update, batch_size):
            lote = update_barcode_in_variant[i:i+batch_size]
            cursor.executemany(update_order_item, lote)
            connection.commit()
            print(f"Inserted {i + len(lote)} of {len_update}...")
        # cursor.executemany(update_order_item, update_barcode_in_variant)
        # connection.commit()

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update order_items")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_inventory_service() -> bool:
    mensaje = f"->Tarea ejecutada a las {datetime.now()}"
    logging.info(mensaje)
    print(mensaje)
    is_updated = False
    # code
    try:
        # connection
        connection = get_db_connection()
        cursor = connection.cursor(dictionary=True)
        select_all_prod = "SELECT * FROM product;"
        cursor.execute(select_all_prod)
        result = cursor.fetchall()
        print(f"Total elements in db {len(result)}")
        # Get all locations
        locations = fetch_locations()
        location_ids = get_location_ids(locations)

        # Obtener productos activos
        logging.info("Obteniendo detalles de productos de Shopify...")
        products = fetch_shopify_products()
        print("Products in shopify:::", len(products))

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

            # Get inventory levels
            inventory_levels = fetch_inventory_levels(
                inventory_item_ids=inventory_item_ids,
                location_ids=location_ids
            )
            # print("inventory_levels-obj", inventory_levels[0])
            print("inventory_levels", len(inventory_levels))
            inventories_schemas = [
                InventorySchema(**item) for item in inventory_levels
            ]
            is_updated = await update_many_inventory_service(
                inventories_schemas)

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()

    finally:
        cursor.close()

    return is_updated


async def update_locations_in_inventory_service() -> bool:
    print("Init update order_items")
    init_time = time.time()
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(select_all_locations)
        locations = cursor.fetchall()
        locations_dict = {
            location["location_shopify"]: location["id"]
            for location in locations
            if location["location_shopify"]
        }
        print("locations_dict", locations_dict)
        cursor.execute(select_inventory)
        locations_in_inventory = cursor.fetchall()
        print("locations_in_inventory", len(locations_in_inventory))
        update_list = []
        for item in locations_in_inventory:
            if item["location_id"] in locations_dict:
                update_list.append(
                    (locations_dict[item["location_id"]], item["id"])
                )
        print("update_list", update_list)
        # cursor.executemany(update_location_in_inventory, )
        # connection.commit()
    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    end_time = time.time()
    duration = end_time - init_time
    print("Finish update order_items")
    print(f"Execution time: {duration:.4f} seconds")
