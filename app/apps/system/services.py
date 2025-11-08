
import time
from datetime import datetime
from app.apps.inventories.helper import sql_inventory_update
from .helper import (
    delete_inventory,
    # fetch_all_inventory_levels,
    fetch_inventory_levels,
    # fetch_locations,
    fetch_shopify_one_product,
    # fetch_shopify_products,
    fetch_shopify_variants,
    fetch_shopify_variants_for_location,
    # get_location_ids,
    select_all_locations,
    select_inventory,
    select_loc_var_in_inventory,
    update_location_in_inventory,
    fetch_shopify_variant,
    get_all_orders_shopify,
    fetch_shopify_variants_bulk,
    # fetch_shopify_variants_for_items,
    fetch_all_inventory_levels_for_items,
    find_stock_differences_return_shopify,
)
from app.database import get_db_connection
from mysql.connector import Error
from app.apps.products.services import (
    create_variant_service,
    create_many_variant_service,
    delete_many_products_service,
    update_or_create_many_products_service,
    update_product_service,
    delete_product_service,
    get_all_products_in_db,
    get_variants_in_db,
    get_variants_in_with_inventory_items,
    # create_variant,
    delete_many_variants_for_id,
    # delete_variant,
    get_variants_with_ids,
    get_one_product_for_id,
    delete_many_products_service,   
)
from app.apps.inventories.services import (
    # update_many_inventory_service,
    update_many_inventory_simple_service,
    delete_inventories_without_variants,
    get_variants_with_same_barcode,
)
from app.apps.locations.services import (
    get_all_locations_in_db,
    get_one_location_in_db
)
from app.apps.orders.services import (
    update_or_create_many_orders_service
)
from app.apps.products.models import (
    DeleteProductSchema, ProductSchema, Variant
)
from app.apps.orders.models import (
    OrderSchema
)
from app.apps.products.helper import (
    get_products_in_shopify,
    get_variants_in_shopify,
    get_variant_in_shopify,
)
from app.apps.inventories.helper import (
    inventory_dict,
    inventory_level_one_location
)
from app.apps.inventories.models import InventoryObject


async def update_products_service() -> bool:
    print("Init update update_products")
    init_time = time.time()
    is_updated = False
    # connection
    print("Obteniendo detalles de productos de base de datos...")
    products_in_bd = await get_all_products_in_db()
    dict_products_in_db = {}
    for prod in products_in_bd:
        dict_products_in_db[prod["product_id"]] = prod
    print(f"Amount of product in database: {len(products_in_bd)}")

    # Get productos
    print("Obteniendo detalles de productos de Shopify...")
    products_shopify = get_products_in_shopify()
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

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update update_products")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_variants_for_locations_service() -> bool:
    print("Init delete_products_not_exists_service")
    init_time = time.time()
    is_updated = False

    # get locations
    locations_in_db = await get_all_locations_in_db()
    locations_ids = [loc["location_shopify"] for loc in locations_in_db]
    # inventory in shopify
    inventories = []
    for location in locations_ids:
        inventories.extend(fetch_shopify_variants_for_location(location))
        time.sleep(3)
    print("Total inventories all locations:", len(inventories))
    all_iventory = inventory_dict(inventories)
    inventory_ids_in_shopify = [inv_id for inv_id in all_iventory.keys()]
    print("Total variants in shopify", len(inventory_ids_in_shopify))

    # inventory in db
    variants_db = await get_variants_in_db()
    variants_db_dict = {}
    variants_ids_in_db = []
    for var in variants_db:
        inventory_item_id = var["inventory_item_id"]
        if inventory_item_id not in variants_db_dict:
            variants_db_dict[inventory_item_id] = {}
        variants_db_dict[inventory_item_id] = {
            "id": var["id"], "barcode": var["barcode"]
        }
        variants_ids_in_db.append(inventory_item_id)
    print("Total variants in db:", len(variants_ids_in_db))

    # create, update or delete
    set_shopy = set(inventory_ids_in_shopify)
    # print("len_set_shopy", len(set_shopy))
    set_db = set(variants_ids_in_db)
    # print("len_set_db", len(set_db))

    # for delete variants
    delete = list(set_db - set_shopy)
    print("delete", len(delete))
    # for inventory_item_id in delete:
    #     await delete_variant(inventory_item_id)
    #     print("delete", variants_db_dict[inventory_item_id])

    # # for create variants
    # create = list(set_shopy - set_db)
    # print("create", create[:3])
    # print("create", len(create))
    # create new variants:::
    # for inventory_item_id in create:
    #     # print("create", all_iventory[inventory_item_id])
    #     await create_variant(inventory_item_id)

    locations_in_db = await get_all_locations_in_db()
    locations_in_db_dict = {
        loc["location_shopify"]: loc["SucursalID"] for loc in locations_in_db
    }

    inventories_list = []
    list_set_shopy = list(set_shopy)
    for item in list_set_shopy:
        inventory_loc = all_iventory[item]
        inventory_loc_list = []
        for loction_id, stock in inventory_loc.items():
            _loction_id = locations_in_db_dict.get(f"{loction_id}")
            if _loction_id and stock and item in variants_db_dict:
                inventory_loc_list.append(
                    InventoryObject(**{
                        "variant_id": variants_db_dict[item]["id"],
                        "location_id": _loction_id,
                        "barcode": variants_db_dict[item]["barcode"],
                        "stock": stock
                    })
                )
        inventories_list.extend(inventory_loc_list)
    print("inventories_list", inventories_list[:3])
    print("inventories_list", len(inventories_list))
    if len(inventories_list):
        await update_many_inventory_simple_service(inventories_list)

    # end
    end_time = time.time()
    duration = end_time - init_time
    print("Finish delete_products_not_exists_service")
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
            time.sleep(0.1)

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
        print("Obteniendo detalles de pedidos de base de datos...")
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
        inventory_levels_shopify = fetch_inventory_levels()
        print("len", len(inventory_levels_shopify))

        # # Get inventory levels
        # inventory_levels = fetch_inventory_levels(
        #     inventory_item_ids=inventory_item_ids,
        #     location_ids=location_ids
        # )
        # print("inventory_levels", len(inventory_levels))
        # is_updated = await update_many_inventory_service(
        #     inventory_levels)

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
            # print("item", item)
            variant_in_shopy_list.append(item["id"])
            variant_in_shopy_dict[item["id"]] = item["product_id"]

        new_variants_in_shopify = (
                list(set(variants_in_db_list) - set(variant_in_shopy_list))
            )
        print("variant_in_shopy_list:", len(variant_in_shopy_list))
        print("new_variants_in_shopify-len:", len(new_variants_in_shopify))
        print("variant_in_shopy_dict", variant_in_shopy_dict)
        for var in new_variants_in_shopify:
            if var in variant_in_shopy_dict:
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


async def get_products_in_shopify_service() -> bool:
    print("Init update get_products")
    init_time = time.time()
    is_updated = False
    product_shopify = get_products_in_shopify()
    # print("product_shopify", product_shopify)
    print("product_shopify", len(product_shopify))
    end_time = time.time()
    duration = end_time - init_time
    print("Finish update get_products")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_only_variants_service() -> bool:
    print("Init update only_variants")
    init_time = time.time()
    is_updated = False
    variants_shopify = get_variants_in_shopify()
    variants_shopify_objs = [
        Variant(**variant)
        for variant in variants_shopify
    ]
    await create_many_variant_service(variants_shopify_objs)
    print("variants_shopify_objs", len(variants_shopify_objs))
    end_time = time.time()
    duration = end_time - init_time
    print("Finish update only_variants")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def delete_duplicate_variants_service() -> bool:
    print("Init update only_variants")
    init_time = time.time()
    is_deleted = False
    variants_shopify = get_variants_in_shopify()
    variants_shopify_list = [item["id"] for item in variants_shopify]
    variants_db = await get_variants_in_db()
    variants_db_list = [item["id"] for item in variants_db]

    variants_shopify_set = set(variants_shopify_list)
    variants_db_set = set(variants_db_list)

    delete_variants = list(variants_db_set - variants_shopify_set)
    print("delete_variants 1:", len(delete_variants))

    if len(delete_variants):
        delete_var = await delete_many_variants_for_id(delete_variants)
        delete_inv = await delete_inventories_without_variants(delete_variants)
        is_deleted = True if delete_var and delete_inv else False
        print("Verify with shopify variants. is_deleted?:", is_deleted)

    # variants not exist in product variants
    var_inventory = await get_variants_with_same_barcode()
    variants_inventory_list = []
    for item in var_inventory:
        variants_inventory_list.extend(item["variants"].split(","))
    variants_ids_in_db = await get_variants_with_ids(variants_inventory_list)
    var_ids_in_db = [str(item["id"]) for item in variants_ids_in_db]
    var_ids_in_db_set = set(var_ids_in_db)
    variants_inventory_set = set(variants_inventory_list)
    delete_duplicate_var = list(variants_inventory_set - var_ids_in_db_set)

    print("delete_variants 2:", len(delete_duplicate_var))
    if len(delete_duplicate_var) > 0:
        delete_inv = await delete_inventories_without_variants(
            delete_duplicate_var)
        is_deleted = is_deleted and delete_inv
        print("Verify exists variants. is_deleted?:", is_deleted)

    # see variants for delete
    see_variants = list(variants_inventory_set - set(delete_duplicate_var))
    delete_variant_verify = []
    for elem in see_variants:
        time.sleep(1)
        var = get_variant_in_shopify(elem)
        if not var:
            delete_variant_verify.append(elem)

    print("delete_variants 3:", len(delete_variant_verify))
    if len(delete_variant_verify) > 0:
        delete_inv_veri = await delete_inventories_without_variants(
            delete_variant_verify)
        is_deleted = is_deleted and delete_inv_veri
        print("Verify duplicates in inventory. is_deleted?:", is_deleted)

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update only_variants")
    print(f"Execution time: {duration:.4f} seconds")
    return is_deleted


async def update_barcode_inventory() -> bool:
    print("Init update barcode_inventory")
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
            AND variant_id is not null
            ORDER BY id ASC;
        """
        cursor.execute(select_all_inventories)
        inventories_in_bd = cursor.fetchall()
        if len(inventories_in_bd) > 0:
            print("Inventories in bd:", len(inventories_in_bd))
            variants_ids_list = [item["variant_id"] for item in inventories_in_bd] # noqa

            select_variant = f"""
                SELECT variant_id as id, barcode
                FROM product_variant
                WHERE variant_id
                IN ({', '.join(map(str, variants_ids_list))});
            """
            print("select_variant", select_variant)
            cursor.execute(select_variant)
            variants_in_db = cursor.fetchall()
            variants_ids_in_db_dict = {
                item["id"]: item["barcode"] for item in variants_in_db
            }
            _update_barcode_inventory = []
            for item in inventories_in_bd:
                if item["variant_id"] in variants_ids_in_db_dict:
                    _update_barcode_inventory.append(
                        (variants_ids_in_db_dict[item["variant_id"]], item["id"]) # noqa
                    )
            update_orders_sql = "UPDATE inventory SET barcode = %s WHERE id = %s"  # noqa
            cursor.executemany(update_orders_sql, _update_barcode_inventory)
            connection.commit()

        is_updated = True

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update barcode_inventory")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_barcode_order_item() -> bool:
    print("Init update order_items")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        select_all_order_items = """
            SELECT id, barcode, variant_id
            FROM order_item
            WHERE barcode = 'Unknown' OR barcode = ''
            AND variant_id is not null
            ORDER BY id ASC;
        """
        cursor.execute(select_all_order_items)
        order_items_in_bd = cursor.fetchall()
        print("Order items in bd:", len(order_items_in_bd))
        if len(order_items_in_bd) > 0:
            variants_ids_list = [item["variant_id"] for item in order_items_in_bd]  # noqa

            select_variant = f"""
                SELECT variant_id as id, barcode
                FROM product_variant
                WHERE variant_id
                IN ({', '.join(map(str, variants_ids_list))});
            """
            cursor.execute(select_variant)
            variants_in_db = cursor.fetchall()
            variants_ids_in_db_dict = {
                item["id"]: item["barcode"] for item in variants_in_db
            }
            _update_barcode_inventory = []
            for item in order_items_in_bd:
                if item["variant_id"] in variants_ids_in_db_dict:
                    _update_barcode_inventory.append(
                        (variants_ids_in_db_dict[item["variant_id"]], item["id"])  # noqa
                    )
            update_order_item = "UPDATE order_item SET barcode = %s WHERE id = %s"  # noqa
            cursor.executemany(update_order_item, _update_barcode_inventory)
            connection.commit()

        is_updated = True

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


async def update_elements_in_inventory_with_barcodes_service() -> bool:
    print("Init update update_elements_in_inventory_with")
    init_time = time.time()
    is_updated = False
    # connection
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        select_all_inventories = """
            SELECT id, barcode, variant_id
            FROM inventory
            WHERE variant_id is not null
            ORDER BY id ASC;
        """
        cursor.execute(select_all_inventories)
        inventories_in_db = cursor.fetchall()
        dict_variants_inventory = {}
        list_variants_inventory = []
        for item in inventories_in_db:
            variant_id = item["variant_id"]
            if variant_id not in dict_variants_inventory:
                dict_variants_inventory[variant_id] = 0
            dict_variants_inventory[variant_id] = item["id"]
            if variant_id not in list_variants_inventory:
                list_variants_inventory.append(variant_id)

        select_variant_in_db = f"""
            SELECT variant_id as id
            FROM product_variant
            WHERE variant_id
            IN ({', '.join(map(str, list_variants_inventory))});
        """
        cursor.execute(select_variant_in_db)
        variant_in_db = cursor.fetchall()
        variant_in_db_list = [var["id"] for var in variant_in_db]

        delete_inventory = list(
            set(list_variants_inventory) - set(variant_in_db_list)
        )

        ids_inventories_delete = []
        for variant_id in delete_inventory:
            if variant_id in dict_variants_inventory:
                ids_inventories_delete.append(
                    dict_variants_inventory[variant_id])

        print("delete_inventory_ids:::", len(ids_inventories_delete))

        if len(ids_inventories_delete) > 0:
            delete_inventory_in_db = f"""
                DELETE FROM inventory
                WHERE id IN ({', '.join(map(str, ids_inventories_delete))});
            """
            cursor.execute(delete_inventory_in_db)
            connection.commit()

        is_updated = True

    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()

    end_time = time.time()
    duration = end_time - init_time
    print("Finish update update_elements_in_inventory_with")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_product_and_inventory(product_id: int) -> bool:
    try:
        product = await get_one_product_for_id(product_id)
        print("product------>>>>>>>>>>><", product)
    except Exception as e:
        print(f"Error: {e}")


async def update_variants_for_location_id_service(location_id: int) -> bool:
    print("Init delete_products_not_exists_service")
    init_time = time.time()
    is_updated = False

    # get location
    location_in_db = await get_one_location_in_db(location_id)
    # inventory in shopify
    inventor_levels = fetch_shopify_variants_for_location(location_in_db)
    print("Total inventories all locations:", len(inventor_levels))
    inventor_levels_list = inventory_level_one_location(inventor_levels)
    inventory_item_list = [
        inv_id["inventory_item_id"] for inv_id in inventor_levels_list]

    # inventory in db
    variants_db = await get_variants_in_with_inventory_items(
        inventory_item_list)
    variants_db_dict = {}
    for var in variants_db:
        inventory_item_id = var["inventory_item_id"]
        if inventory_item_id not in variants_db_dict:
            variants_db_dict[inventory_item_id] = {}
        variants_db_dict[inventory_item_id] = {
            "id": var["id"], "barcode": var["barcode"]
        }
    print("Total variants in db:", len(variants_db_dict))

    inventories_list = []
    for item in inventor_levels_list:
        inventory_item_id = item["inventory_item_id"]
        if inventory_item_id in variants_db_dict:
            inventory_dict = {
                "variant_id": variants_db_dict[inventory_item_id]["id"],
                "location_id": item["location_id"],
                "barcode": variants_db_dict[inventory_item_id]["barcode"],
                "stock": item["stock"]
            }
            inventories_list.append(InventoryObject(**inventory_dict))
    print("inventories_list", inventories_list[:3])
    print("inventories_list", len(inventories_list))
    if len(inventories_list):
        await update_many_inventory_simple_service(inventories_list)

    # end
    end_time = time.time()
    duration = end_time - init_time
    print("Finish delete_products_not_exists_service")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_barcode_and_sku_variants_service() -> bool:
    print("Init update_barcode_and_sku_variants")
    init_time = time.time()
    is_updated = False

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        select_all_variants = """
            SELECT variant_id, barcode, sku
            FROM product_variant
            WHERE sku = 'Unknown' OR barcode = 'Unknown';
        """
        cursor.execute(select_all_variants)
        variants_in_bd = cursor.fetchall()
        cursor.close()

        if not variants_in_bd:
            print("No inventories with Unknown sku or barcode.")
            return True

        print(f"Found {len(variants_in_bd)} variants to update.")

        update_product_variants = []
        update_inventory_list = []
        for item in variants_in_bd:
            variant_id = item["variant_id"]
            try:
                variant = fetch_shopify_variant(variant_id)
                update_product_variants.append((
                    variant.get("barcode", "Unknown") or "Unknown",
                    variant.get("sku", "Unknown") or "Unknown",
                    variant.get("id")
                ))
                update_inventory_list.append((
                    variant.get("barcode", "Unknown") or "Unknown",
                    variant.get("id")
                ))
            except Exception as e:
                print(f"Error fetching variant {variant_id}: {e}")

        cursor = connection.cursor()

        BATCH_SIZE = 300  # noqa
        # for products variants
        update_product_variant_query = """
            UPDATE product_variant
            SET barcode = %s, sku = %s
            WHERE variant_id = %s;
        """
        for i in range(0, len(update_product_variants), BATCH_SIZE):
            batch = update_product_variants[i:i+BATCH_SIZE]
            try:
                cursor.executemany(update_product_variant_query, batch)
                connection.commit()
                print(f"Batch var {i//BATCH_SIZE + 1} updated successfully.")
            except Error as e:
                print(f"Error in batch {i//BATCH_SIZE + 1}: {e}")
                connection.rollback()
        # for inventory
        update_inventory_query = """
            UPDATE inventory
            SET barcode = %s
            WHERE variant_id = %s;
        """
        for i in range(0, len(update_inventory_list), BATCH_SIZE):
            batch = update_inventory_list[i:i+BATCH_SIZE]
            try:
                cursor.executemany(update_inventory_query, batch)
                connection.commit()
                print(f"Batch inv {i//BATCH_SIZE + 1} updated successfully.")
            except Error as e:
                print(f"Error in batch {i//BATCH_SIZE + 1}: {e}")
                connection.rollback()

        is_updated = True

    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        connection.close()

    end_time = time.time()
    print("Finish update_barcode_and_sku_variants")
    print(f"Execution time: {end_time - init_time:.4f} seconds")
    return is_updated


async def update_or_create_products_and_variants_service():
    print("Init update_or_create_products_and_variants")
    init_time = time.time()
    is_updated = False

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        productos = get_all_products()
        products_schemas = []
        for producto in productos:
            products_schemas.append(ProductSchema(**producto))
        # print("products_schemas0", products_schemas)
        # products_schemas = products_schemas[1: 10]
        # print("products_schemas1", products_schemas)
        BATCH_SIZE = 500  # noqa
        for i in range(0, len(products_schemas), BATCH_SIZE):
            batch = products_schemas[i:i+BATCH_SIZE]
            await update_or_create_many_products_service(batch)
            print(f"Batch {i//BATCH_SIZE + 1} updated successfully.")
            time.sleep(1)

    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        connection.close()

    end_time = time.time()
    print("Finish update_or_create_products_and_variants")
    print(f"Execution time: {end_time - init_time:.4f} seconds")
    return is_updated


async def delete_duplicate_inventory_and_variants_service():
    print("Init update_or_create_products_and_variants")
    init_time = time.time()
    is_updated = False

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    sql_duplicates = """
        SELECT i.* FROM inventory i
        JOIN (
            SELECT barcode, location_id
            FROM inventory GROUP BY barcode, location_id
            HAVING COUNT(*) > 1) dup ON i.barcode = dup.barcode
            AND i.location_id = dup.location_id;
    """

    try:
        cursor.execute(sql_duplicates)
        inventory_duplicates = cursor.fetchall()
        inventory_duplicates_unique_set = set()
        for inventory in inventory_duplicates:
            inventory_duplicates_unique_set.add(inventory["variant_id"])
        inventory_duplicates_unique_list = list(
            inventory_duplicates_unique_set)
        inventory_delete_list = []
        for variant_id in inventory_duplicates_unique_list:
            variant = fetch_shopify_variant(variant_id)
            if not variant.get('id'):
                inventory_delete_list.append(variant_id)

        if len(inventory_delete_list) > 0:
            sql_delete_inventory = f"""
                DELETE FROM inventory
                WHERE variant_id
                IN ({', '.join(map(str, inventory_delete_list))});
            """
            sql_delete_variants = f"""
                DELETE FROM product_variant
                WHERE variant_id
                IN ({', '.join(map(str, inventory_delete_list))});
            """
            cursor.execute(sql_delete_inventory)
            cursor.execute(sql_delete_variants)
        print("inventory_delete_len:", len(inventory_delete_list))

    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        connection.close()

    end_time = time.time()
    print("Finish update_or_create_products_and_variants")
    print(f"Execution time: {end_time - init_time:.4f} seconds")
    return is_updated


async def update_orders_service():
    print("Init update update_orders")
    init_time = time.time()
    is_updated = False

    # Get orders
    print("Obteniendo detalles de pedidos de Shopify...")
    orders_shopify = get_all_orders_shopify()
    print(f"Amount of orders in shofify: {len(orders_shopify)}")

    update_or_create_orders_schema = [
        OrderSchema(**order) for order in orders_shopify
    ]
    await update_or_create_many_orders_service(
        update_or_create_orders_schema)
    print(
        "update_or_create_orders_schema",
        len(update_or_create_orders_schema)
    )
    end_time = time.time()
    duration = end_time - init_time
    print("Finish update update_orders")
    print(f"Execution time: {duration:.4f} seconds")
    return is_updated


async def update_or_create_products_and_variants_shopify_service():
    BATCH_SIZE = 500
    print("Init update_or_create_products_and_variants_shopify_service")
    init_time = time.time()
    is_updated = False

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        productos_shopify = get_products_in_shopify()
        # print("productos_shopify:::--->>>:len", len(productos_shopify))
        # print("productos_shopify:::--->>>", productos_shopify[:1])
        productos_shopify_index = {int(p["id"]): p for p in productos_shopify if "id" in p}
        # print("productos_shopify_index::::::::::::::::::", productos_shopify_index)
        # products_shopify_format = []
        # for producto_shop in productos_shopify:
        #     products_shopify_format.append(ProductSchema(**producto_shop))
        # print("products_shopify_format[:1]", products_shopify_format[:1])
        productos_in_db = await get_all_products_in_db()
        productos_in_db_index = {int(p["product_id"]): p for p in productos_in_db if "product_id" in p}
        # print("productos_in_db_index::::::::::::::::::", productos_in_db_index)
        # print("productos_in_db:::--->>>:len", len(productos_in_db))
        # print("productos_in_db:::--->>>", productos_in_db[:1])

        shop_pids = set(productos_shopify_index.keys())
        db_pids = set(productos_in_db_index.keys())
        
        # # delete product and variants
        eliminar_de_db = list(db_pids - shop_pids)
        # delete_many_products_service(eliminar_de_db)

        # 
        crear_en_db = list(shop_pids - db_pids)
        # if len(crear_en_db):
        #     for i in range(0, len(products_schemas), BATCH_SIZE):
        #         batch = products_schemas[i:i+BATCH_SIZE]
        #         await update_or_create_many_products_service(batch)
        #         print(f"Batch {i//BATCH_SIZE + 1} updated successfully.")
        #         time.sleep(1)

        
        en_ambos = shop_pids & db_pids

        print("crear_en_db", len(crear_en_db))
        print("eliminar_de_db", len(eliminar_de_db))
        print("en_ambos", len(en_ambos))

    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        connection.close()

    end_time = time.time()
    print("Finish update_or_create_products_and_variants_shopify_service")
    print(f"Execution time: {end_time - init_time:.4f} seconds")
    return is_updated


async def synchronize_inventory_service():
    print("Init synchronize_inventory_service")
    init_time = time.time()
    is_updated = False

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    sql_inventory = """
    SELECT i.*, pv.inventory_item_id, l.location_shopify
    FROM inventory AS i
    LEFT JOIN (
        SELECT variant_id, MAX(inventory_item_id) AS inventory_item_id
        FROM product_variant
        GROUP BY variant_id
    ) AS pv
    ON pv.variant_id = i.variant_id
    LEFT JOIN locations AS l
    ON l.SucursalID = i.location_id;
    """

    try:
        cursor.execute(sql_inventory)
        inventory = cursor.fetchall()
        print("inventory", len(inventory))
        inventory_item_id_varant_index = {}
        location_shopify_location_index = {}
        inventory_item_ids = []
        for inv in inventory:
            if "inventory_item_id" in inv and inv["inventory_item_id"] is not None:
                inventory_item_id_varant_index.update({int(inv["inventory_item_id"]): {
                    "variant": inv["variant_id"],
                    "barcode": inv["barcode"],
                }})
                inventory_item_ids.append(inv["inventory_item_id"])
            if "location_shopify" in inv and inv["location_shopify"] != "None":
                location_shopify_location_index.update({int(inv["location_shopify"]): inv["location_id"]})

        unique_inventory_item_ids = list(set(inventory_item_ids))
        inventory_shopify = fetch_all_inventory_levels_for_items(unique_inventory_item_ids)
        print("inventory_shopify", len(inventory_shopify))
        inventory_shopify_with_format = []
        for inv_shop in inventory_shopify:
            if location_shopify_location_index.get(inv_shop["location_id"]):
                inventory_shopify_with_format.append({
                    "variant_id": inventory_item_id_varant_index[inv_shop["inventory_item_id"]]["variant"],
                    "location_id": location_shopify_location_index[inv_shop["location_id"]],
                    "barcode": inventory_item_id_varant_index[inv_shop["inventory_item_id"]]["barcode"],
                    "stock": inv_shop["available"],
                })
        data_for_update = find_stock_differences_return_shopify(
            db_inventory=inventory, shopify_levels=inventory_shopify_with_format)
        print("data_for_update", len(data_for_update))
        # print("data_for_update", data_for_update[:10])
        update_inventories = []
        for elem in data_for_update:
            update_inventories.append((
                elem["variant_id"],
                elem["location_id"],
                elem["barcode"],
                elem["stock"]
            ))
        print("update_inventories", len(update_inventories), update_inventories[:10])
        batch_size = 500
        len_update = len(update_inventories)
        for i in range(0, len_update, batch_size):
            lote = update_inventories[i:i+batch_size]
            cursor.executemany(sql_inventory_update, lote)
            connection.commit()
            print(f"Inserted {i + len(lote)} of {len_update}...")
        is_updated = True

    except Error as e:
        print(f"Database error: {e}")
    finally:
        cursor.close()
        connection.close()

    end_time = time.time()
    print("Finish synchronize_inventory_service")
    print(f"Execution time: {end_time - init_time:.4f} seconds")
    return is_updated

