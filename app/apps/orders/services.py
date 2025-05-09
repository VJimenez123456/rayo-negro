from .models import OrderSchema
from app.database import get_db_connection
from .helper import (
    get_barcodes,
    parser_order,
    parser_items,
    sql_items_update,
    sql_order_update,
)
from typing import List
from mysql.connector import Error


# async def create_order_service(order: OrderSchema):
#     order_obj = tuple(parser_order(order))
#     print("order_obj-c", order_obj)
#     connection = get_db_connection()
#     cursor = connection.cursor(dictionary=True)
#     is_created = False
#     try:
#         # cursor.execute(sql_order_create, order_obj)
#         # connection.commit()
#         is_created = True
#     finally:
#         cursor.close()
#     return is_created


async def update_order_service(order: OrderSchema):
    order_obj = parser_order(order)
    barcodes_dict = get_barcodes(order.line_items)
    order_items = parser_items(order.id, order.line_items, barcodes_dict)
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_updated = False
    try:
        cursor.execute(sql_order_update, order_obj)
        cursor.executemany(sql_items_update, order_items)
        connection.commit()
        is_updated = True
    finally:
        cursor.close()
    return is_updated


async def update_or_create_many_orders_service(
        orders: List[OrderSchema]):
    total_order_obj = []
    total_order_items = []
    for order in orders:
        order_obj = parser_order(order)
        barcodes_dict = get_barcodes(order.line_items)
        order_items = parser_items(order.id, order.line_items, barcodes_dict)
        total_order_obj.append(order_obj)
        total_order_items.extend(order_items)

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    is_created = False
    try:
        # for order_obj
        print("======================order_objs=======================")
        BATCH_SIZE = 500  # noqa
        for i in range(0, len(total_order_obj), BATCH_SIZE):
            batch1 = total_order_obj[i:i+BATCH_SIZE]
            # cursor.executemany(sql_order_update, batch1)
            print(f"Batch {i//BATCH_SIZE + 1} updated successfully.")
        print("======================order_items======================")
        # for order_items
        for i in range(0, len(total_order_items), BATCH_SIZE):
            batch2 = total_order_items[i:i+BATCH_SIZE]
            # cursor.executemany(sql_items_update, batch2)
            print(f"Batch {i//BATCH_SIZE + 1} updated successfully.")
        connection.commit()
        is_created = True
        print("==========================end=========================")
    except Error as e:
        print(f"Error en la inserción: {e}")
        connection.rollback()
    finally:
        cursor.close()
    return is_created
