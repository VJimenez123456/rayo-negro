from .models import OrderSchema
from app.database import get_db_connection
from .helper import (
    get_barcodes,
    parser_order,
    parser_items,
    sql_items_update,
    sql_order_update,
)


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
