# flake8: noqa
from .models import OrderSchema, LineItem
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Dict, List
import base64
import requests
from app.core.config import settings
from app.database import get_db_connection


sql_order_update = """
    INSERT INTO `order` (
        id, Customer_name, total_price, created_at, order_status, fulfillment_status,
        order_number, return_status, note, location_name, StatusShopify, tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE Customer_name=VALUES(Customer_name),
        total_price=VALUES(total_price), created_at=VALUES(created_at),
        order_status=VALUES(order_status), fulfillment_status=VALUES(fulfillment_status),
        order_number=VALUES(order_number), return_status=VALUES(return_status),
        note=VALUES(note), location_name=VALUES(location_name),
        StatusShopify=VALUES(StatusShopify), tags=VALUES(tags)
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


def parser_order(order: OrderSchema) -> tuple:
    order_id = order.id
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
        translate_status("financial_status", order.financial_status)
        if order.financial_status else "Unknown"
    )
    fulfillment_status = (
        translate_status("fulfillment_status", order.fulfillment_status)
        if order.fulfillment_status else "No completado"
    )
    return_status = translate_status("return_status", fetch_return_status(order_id))

    status_shopify = determine_order_status(order)

    order_obj = (
        order_id,
        customer_name,
        order.total_price or '0.00',
        created_at,
        order_status,
        fulfillment_status,
        order.order_number,
        return_status,
        order.note or '',
        "Unknown",  # location_name
        status_shopify,
        order.tags or ""
    )
    return order_obj


def parser_items(
        order_id: int, items: List[LineItem], barcodes_dict: dict
    ) -> List[tuple]:
    items_objs = []
    for item in items:
        variant_id = item.variant_id
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
            barcodes_dict.get(item.variant_id, "Unknown"),
            validacion_sku,
            image_url,

        ))
    return items_objs


translation_dict = {
    'financial_status': {
        'pending': 'Pendiente',
        'authorized': 'Autorizado',
        'partially_paid': 'Parcialmente pagado',
        'paid': 'Pagado',
        'partially_refunded': 'Parcialmente reembolsado',
        'refunded': 'Reembolsado',
        'voided': 'Anulado'
    },
    'fulfillment_status': {
        'fulfilled': 'Preparado',
        'partial': 'Parcial',
        'restocked': 'Reabastecido',
        'unfulfilled': 'No preparado',
        None: 'No preparado'
    },
    'return_status': {
        'open': 'Abierto',
        'closed': 'Cerrado',
        'none': 'Sin devoluciones'
    }
}


def translate_status(status_type, status_value):
    return translation_dict.get(status_type, {}).get(status_value, status_value)


def fetch_return_status(order_id):
    api_key = settings.SHOPIFY_API_KEY
    api_password = settings.SHOPIFY_API_PASSWORD
    store_url = settings.SHOPIFY_STORE_URL
    base_url = f"https://{store_url}/admin/api/2023-07/orders/{order_id}/refunds.json"
    credentials = f"{api_key}:{api_password}"
    encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Basic {encoded_credentials}'
    }

    response = requests.get(base_url, headers=headers)
    if response.status_code == 200:
        refunds = response.json().get('refunds', [])
        if refunds:
            return 'open' if any('status' in refund and refund['status'] == 'open' for refund in refunds) else 'closed'
        else:
            return 'none'
    return 'none'


def get_barcodes(items: List[LineItem]) -> Dict:
    variants_id = [item.variant_id for item in items]
    get_variants = f"""
        SELECT variant_id, barcode
        FROM product_variant
        WHERE variant_id IN ({', '.join(['%s'] * len(variants_id))})
        """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    try:
        variants_dict = {}
        cursor.execute(get_variants, variants_id)
        variants_objs = cursor.fetchall()
        for var in variants_objs:
            if var["variant_id"] not in variants_dict:
                variants_dict[var["variant_id"]] = var["barcode"]
        # connection.commit()
    finally:
        cursor.close()
    return variants_dict
