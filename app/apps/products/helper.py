# flake8: noqa
from .models import ProductSchema  #, Variant
# from typing import List
from app.common.utils import (
    MIN_INTERVAL,
    backoff_from_bucket,
    get_credentials_shopify,
    get_link_next,
    get_retry_after,
    log_api_call,
    make_session,
    RateLimiter,
)
import requests
import random, time


sql_product_create = """
    INSERT INTO product (product_id, title, vendor, price, sku, image_url)
    VALUES (%s, %s, %s, %s, %s, %s)
"""

sql_variant_create = """
    INSERT INTO product_variant (variant_id, product_id, title, sku, price, stock, barcode, inventory_item_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
"""
sql_product_update = """
    INSERT INTO product (product_id, title, vendor, price, sku, image_url)
    VALUES (%s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE title=VALUES(title), vendor=VALUES(vendor), price=VALUES(price), sku=VALUES(sku), image_url=VALUES(image_url)
"""
sql_variant_update = """
    INSERT INTO product_variant (variant_id, product_id, title, sku, price, stock, barcode, inventory_item_id)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ON DUPLICATE KEY UPDATE title=VALUES(title), sku=VALUES(sku), price=VALUES(price), stock=VALUES(stock), barcode=VALUES(barcode), inventory_item_id=VALUES(inventory_item_id)
"""
select_product = "SELECT * FROM product WHERE product_id = %s"

delete_product = "DELETE FROM product WHERE product_id = %s"

delete_product_variants = "DELETE FROM product_variant WHERE product_id = %s"

select_variant = "SELECT stock FROM product_variant WHERE variant_id = %s"


def clean_string(value):
    if value is None:
        return 'Unknown'
    return value.encode('ascii', 'ignore').decode('ascii')


def get_product_and_variants(product: ProductSchema) -> tuple:
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
            clean_string(variant.barcode),
            variant.inventory_item_id
        ))
    return new_product, variant_values


def get_products_in_shopify() -> list:
    products = []
    base_url, headers = get_credentials_shopify()
    url = f"{base_url}/products.json?limit=250"

    rate_limiter = RateLimiter(max_calls=4, period=1.0, min_interval=MIN_INTERVAL)
    session = make_session()

    while url:
        try:
            rate_limiter.wait()
            response = session.get(url, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                fetched_products = data.get('products', [])
                products.extend(fetched_products)

                # autorregulación según uso del bucket
                backoff_from_bucket(response.headers)

                # paginación por Link
                link_header = response.headers.get('Link')
                if link_header:
                    next_url = get_link_next(link_header)
                    url = next_url
                else:
                    url = None

            elif response.status_code == 429:
                # Respetar Retry-After
                wait_s = get_retry_after(response.headers, default_seconds=1.0)
                print(f"429 recibido. Esperando {wait_s:.2f}s según Retry-After…")
                time.sleep(wait_s)
                # No avances de página ni rompas; reintenta misma URL
                continue

            else:
                # 5xx se reintentan via Retry del session; aquí solo log
                print(f"Error inesperado al obtener productos: {response.status_code} {response.text}.")
                if 500 <= response.status_code < 600:
                    # Pequeño backoff manual adicional
                    time.sleep(0.5 + random.random() * 0.5)
                    continue
                # Para 4xx (excepto 429), salimos para no ciclar
                break

        except requests.RequestException:
            print("Error en la solicitud HTTP para productos.")
            # backoff leve antes de reintentar el bucle
            time.sleep(0.7 + random.random() * 0.5)
            continue

    session.close()
    return products


def get_variants_in_shopify() -> list:
    variants = []
    base_url, headers = get_credentials_shopify()
    url = f"{base_url}/variants.json?limit=250"
    rate_limiter = RateLimiter(max_calls=4, period=2)
    session = requests.Session()
    variants = []

    while url:
        try:
            rate_limiter.wait()
            response = session.get(url, headers=headers)
            # log_api_call(response)
            if response.status_code == 200:
                data = response.json()
                fetched_variants = data.get('variants', [])
                variants.extend(fetched_variants)
                # pagination manager
                link_header = response.headers.get('Link')
                if link_header:
                    url = get_link_next(link_header)
                else:
                    url = None
            else:
                print(f"Error inesperado al obtener productos: {response.status_code} {response.text}.")
        except requests.RequestException as e:
            print(f"Error en la solicitud HTTP para productos.")
            break
    session.close()
    return variants


def get_variant_in_shopify(variant_id: int):
    base_url, headers = get_credentials_shopify()
    url = f"{base_url}/variants/{variant_id}.json"
    rate_limiter = RateLimiter(max_calls=4, period=1)
    session = requests.Session()
    variant = None
    try:
        rate_limiter.wait()
        response = session.get(url, headers=headers)
        # log_api_call(response)
        if response.status_code == 200:
            data = response.json()
            variant = data.get('variant', {})
        else:
            print(f"Error inesperado al obtener variants: {response.status_code} {response.text}.")
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP para variants.")
    session.close()
    return variant
