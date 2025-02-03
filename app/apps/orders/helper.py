# flake8: noqa
from .models import OrderSchema, LineItem
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List

sql_order_update = """
    INSERT INTO order (id, Customer_name, total_price, created_at, order_status, fulfillment_status, order_number, return_status, note, location_name, StatusShopify, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE Customer_name=VALUES(Customer_name), total_price=VALUES(total_price), created_at=VALUES(created_at), order_status=VALUES(order_status), fulfillment_status=VALUES(fulfillment_status), order_number=VALUES(order_number), return_status=VALUES(return_status), note=VALUES(note), location_name=VALUES(location_name), StatusShopify=VALUES(StatusShopify), tags=VALUES(tags)
"""

sql_items_update = """
    INSERT INTO order_item (id, order_id, product_id, variant_id, title, quantity, price, sku, barcode, ValidacionSku, image_url)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE product_id=VALUES(product_id), variant_id=VALUES(variant_id), title=VALUES(title), quantity=VALUES(quantity), price=VALUES(price), sku=VALUES(sku), barcode=VALUES(barcode), ValidacionSku=VALUES(ValidacionSku), image_url=VALUES(image_url)
"""


def determine_order_status(order: OrderSchema):
    if order.cancelled_at:
        return 'Canceled'
    elif order.closed_at:
        return 'Archived'
    else:
        return 'Open'


def translate(key):
    return key


def parser_order(order: OrderSchema) -> tuple:
    customer_name = 'Unknown'
    if order.shipping_address:
        customer_name = order.shipping_address.name
    elif order.customer:
        customer_name = order.customer.default_address.name

    mexico_tz = ZoneInfo("America/Mexico_City")
    created_at = datetime.strptime(
        order.created_at, '%Y-%m-%dT%H:%M:%S%z').astimezone(
            mexico_tz).replace(tzinfo=None) if order.created_at else None

    # traducir
    order_status = (
        translate(order.financial_status)
        if order.financial_status else "Unknown"
    )
    fulfillment_status = (
        translate(order.fulfillment_status)
        if order.fulfillment_status else "No completado"
    )
    return_status = translate("return_status")

    status_shopify = determine_order_status(order)

    order_obj = (
        order.id,
        customer_name,
        order.total_price or '0.00',
        created_at,
        order_status,
        fulfillment_status,
        order.order_number,
        return_status,  # preguntar
        order.note or '',
        "Unknown",  # location_name: preguntar por esto
        status_shopify,  # StatusShopify
        order.tags or ""
    )
    return order_obj


def parser_items(order_id: int, items: List[LineItem]) -> List[tuple]:
    items_objs = []
    for item in items:
        variant_id = item.variant_id
        barcode = ''  # preguntar
        validacion_sku = ''
        image_url = ''
        items_objs.append((
            item.id,
            order_id,
            item.product_id,
            variant_id,
            item.title,
            item.quantity,
            item.price,
            item.sku,
            barcode,
            validacion_sku,
            image_url,

        ))
    return items_objs
