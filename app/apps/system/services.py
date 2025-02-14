
import logging
import time
from datetime import datetime
from .helper import (
    delete_inventory,
    # fetch_all_inventory_levels,
    fetch_inventory_levels,
    fetch_locations,
    fetch_shopify_one_product,
    fetch_shopify_products,
    fetch_shopify_variants,
    get_location_ids,
    select_all_locations,
    select_inventory,
    select_loc_var_in_inventory,
    update_location_in_inventory,
)
from app.database import get_db_connection
from mysql.connector import Error
from app.apps.products.services import (
    create_variant_service,
    delete_many_products_service,
    update_or_create_many_products_service,
    update_product_service,
    delete_product_service,
)
from app.apps.inventories.services import update_many_inventory_service
from app.apps.products.models import (
    DeleteProductSchema, ProductSchema, Variant
)


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


async def simple_update_barcode_in_inventory_service() -> bool:
    print("Init update order_items")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        select_all_inventories = """
            SELECT id, barcode, variant_id
            FROM inventory
            WHERE barcode = 'Unknown' OR barcode = ''
            ORDER BY id ASC;
        """
        cursor.execute(select_all_inventories)
        inventories_in_bd = cursor.fetchall()
        print("Orders in bd:", len(inventories_in_bd))
        count_update = 0
        for item in inventories_in_bd:
            select_barcode = f"""
                SELECT barcode, variant_id
                FROM product_variant
                WHERE variant_id = {item["variant_id"]}
            """
            cursor.execute(select_barcode)
            variant = cursor.fetchone()
            if variant:
                update_query = """
                    UPDATE inventory SET barcode = %s WHERE id = %s
                """
                cursor.execute(update_query, (variant["barcode"], item["id"]))
                connection.commit()
                count_update += 1
            time.sleep(0.5)

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update order_items")
    print(f"Updated {count_update} elements")
    print(f"Execution simple_update time: {duration:.4f} seconds")
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


async def update_barcode_in_inventory_service() -> bool:
    print("Init update order_items")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        select_all_inventories = """
            SELECT id, barcode, variant_id
            FROM inventory
            WHERE barcode = 'Unknown' OR barcode = ''
            ORDER BY id ASC;
        """
        cursor.execute(select_all_inventories)
        inventories_in_bd = cursor.fetchall()
        print("Inventories in bd:", len(inventories_in_bd))
        select_variant = """
            SELECT variant_id, barcode
            FROM product_variant
            WHERE barcode <> 'Unknown' AND barcode <> '';
        """
        cursor.execute(select_variant)
        variant_in_db = cursor.fetchall()
        variants_dict = {}
        for var in variant_in_db:
            variants_dict[var["variant_id"]] = var["barcode"]
        update_barcode_in_variant = []
        for inventory in inventories_in_bd:
            if inventory["variant_id"] in variants_dict:
                update_barcode_in_variant.append(
                    (variants_dict[inventory["variant_id"]], inventory["id"])
                )
        update_order_item = "UPDATE inventory SET barcode = %s WHERE id = %s"
        len_update = len(update_barcode_in_variant)
        # batch_size = 500
        # for i in range(0, len_update, batch_size):
        #     lote = update_barcode_in_variant[i:i+batch_size]
        #     cursor.executemany(update_order_item, lote)
        #     connection.commit()
        #     print(f"Inserted {i + len(lote)} of {len_update}...")
        cursor.executemany(update_order_item, update_barcode_in_variant)
        connection.commit()
        print(f"Inserted {len_update} in inventory...")

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


async def update_product_for_inventory_service() -> bool:
    print("Init update order_items")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        select_all_inventories = """
            SELECT id, barcode, variant_id
            FROM inventory
            WHERE barcode = 'Unknown' OR barcode = ''
            ORDER BY id ASC;
        """
        cursor.execute(select_all_inventories)
        inventories_in_bd = cursor.fetchall()
        print("Inventories in bd:", len(inventories_in_bd))
        barcode_variants = {}
        all_variant_ids = []
        for inventory in inventories_in_bd:
            all_variant_ids.append(inventory["variant_id"])
            barcode_variants.update({inventory["variant_id"]: ""})
        new_variants_in_shopify = []
        if len(all_variant_ids) > 0:
            get_variants = f"""
                SELECT variant_id as id, barcode
                FROM product_variant
                WHERE variant_id
                IN ({', '.join(map(str, all_variant_ids))})
            """
            cursor.execute(get_variants)
            variants_products_in_db = cursor.fetchall()
            variants_products_list = []
            for variants in variants_products_in_db:
                variants_products_list.append(variants["id"])
                barcode_variants[variants["id"]] = variants["barcode"]

            new_variants_in_shopify = (
                list(set(all_variant_ids) - set(variants_products_list))
            )
            print("new_variants_in_shopify->len", len(new_variants_in_shopify))
            print("new_variants_in_shopify", new_variants_in_shopify[:3])
            variants_shopify = fetch_shopify_variants(new_variants_in_shopify)
            created_number = 0
            updated_number = 0
            print("variants_shopify", variants_shopify[:3])
            for var_shop in variants_shopify:
                product_id = var_shop.get("product_id")
                barcode_variants[var_shop["id"]] = var_shop.get("barcode", "")
                if product_id:
                    query = f"""
                        SELECT product_id FROM product
                        WHERE product_id = {product_id};
                    """
                    cursor.execute(query)
                    products_in_db = cursor.fetchone()
                    if products_in_db:
                        created_number += 1
                        await create_variant_service(Variant(**var_shop))
                    else:
                        updated_number += 1
                        product_shopify = fetch_shopify_one_product(product_id)
                        await update_product_service(product_shopify)
            print("created_number", created_number)
            print("updated_number", updated_number)
        else:
            print("Update 0 variants")

        list_barcode_variant = [
            (barcode, variant_key)
            for variant_key, barcode in barcode_variants.items()
        ]
        print("list_barcode_variant", list_barcode_variant[:3])
        query_update = """
            UPDATE inventory
            SET barcode = %s
            WHERE variant_id = %s;
        """
        cursor.executemany(query_update, list_barcode_variant)
        connection.commit()

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
    print("Init update order_items")
    init_time = time.time()
    print(f"->Tarea ejecutada a las {datetime.now()}")
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
            print("inventory_levels", len(inventory_levels))
            is_updated = await update_many_inventory_service(
                inventory_levels)

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


async def update_locations_in_inventory_service() -> bool:
    print("Init update order_items")
    init_time = time.time()
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    elements_update = 0
    elements_delete = 0
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
        for item in locations_in_inventory:
            location_shopify = f"{item['location_id']}"
            if location_shopify in locations_dict:
                cursor.execute(
                    select_loc_var_in_inventory,
                    (item["location_id"], item["variant_id"])
                )
                result = cursor.fetchone()
                if not result:
                    elements_update += 1
                    # print("UPDATE")
                    cursor.execute(
                        update_location_in_inventory,
                        (locations_dict[location_shopify], item["id"])
                    )
                else:
                    elements_delete += 1
                    # print("DELETE")
                    cursor.execute(delete_inventory, (item["id"],))
                # connection.commit()

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    end_time = time.time()
    duration = end_time - init_time
    print(f"Total items updated: {elements_update}")
    print(f"Total items deleted: {elements_delete}")
    print("Finish update order_items")
    print(f"Execution time: {duration:.4f} seconds")


async def delete_products_not_exists_service() -> bool:
    print("Init delete_products_not_exists_service")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        inventory_db = """
            SELECT id, barcode, variant_id
            FROM inventory
            WHERE barcode = 'Unknown' OR barcode = ''
            ORDER BY id ASC;
        """
        cursor.execute(inventory_db)
        data_inventory_db = cursor.fetchall()
        print("Inventories in bd:", len(data_inventory_db))
        variants_in_db_list = [ele["variant_id"] for ele in data_inventory_db]
        variant_in_shopy = fetch_shopify_variants(variants_in_db_list)
        print("variant_in_shopy", len(variant_in_shopy))
        variant_in_shopy_list = []
        variant_in_shopy_dict = {}
        for item in variant_in_shopy:
            variant_in_shopy_list.append(item["id"])
            variant_in_shopy_dict[item["id"]] = item["product_id"]

        new_variants_in_shopify = (
                list(set(variants_in_db_list) - set(variant_in_shopy_list))
            )
        print("new_variants_in_shopify-len:", len(new_variants_in_shopify))

        for var in new_variants_in_shopify:
            product_id = variant_in_shopy_dict[var]
            select_vars_prod = f"""
                SELECT variant_id
                FROM product_variant
                WHERE product_id = {product_id}
            """
            cursor.execute(select_vars_prod)
            variants_for_product = cursor.fetchall()
            len_variants_for_product = len(variants_for_product)
            if len_variants_for_product > 1:
                delete_sql = f"""
                    DELETE FROM product_variant
                    WHERE variant_id = {var};
                """
                cursor.execute(delete_sql)
                connection.commit()
            elif len_variants_for_product == 1:
                delete_product_service(DeleteProductSchema(id=product_id))
        is_updated = True
    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    end_time = time.time()
    duration = end_time - init_time
    print("Finish delete_products_not_exists_service")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated
