# flake8: noqa
import requests
from requests import Response
import time
import os
from collections import deque
import certifi
import random
import unicodedata
from app.core.config import settings
from math import ceil
from app.common.utils import (
    get_credentials_shopify,
    get_link_next,
    log_api_call,
    RateLimiter,
    make_session,
    MAX_CALLS_PER_SECOND,
    MIN_INTERVAL,
    get_retry_after,
)
from typing import List, Dict, Any, Iterable, Tuple

DESIRED_LOCATIONS = [
    'CANCÚN',
    'CEDIS',
    'EXPERIENCIA',
    'GUADALAJARA',
    'LIVERPOOL',
    'ONLINE',
    'RAYONETA 1.0',
    'RAYONETA 2.0'
]


select_all_locations = """
    SELECT SucursalID as id, location_shopify
    FROM locations
    ORDER BY id ASC;
"""

select_inventory = """
    SELECT id, location_id, variant_id
    FROM inventory
    WHERE location_id > 13
    ORDER BY id ASC;
"""

select_loc_var_in_inventory = """
    SELECT id FROM inventory WHERE location_id = %s AND variant_id = %s;
"""

update_location_in_inventory = """
    UPDATE inventory SET location_id = %s WHERE id = %s;
"""

delete_inventory = """DELETE FROM inventory WHERE id = %s;"""


def clean_string(s):
    # Función para limpiar strings
    if s:
        return s.strip().replace("'", "''")
    return 'Unknown'


def validate_barcode(barcode):
    # Función para validar barcode (puedes ajustar según tus reglas)
    if barcode and barcode != '':
        return True
    return False


def get_location_ids(locations: dict) -> list:
    # Función para filtrar las ubicaciones deseadas
    new_locations = []
    for loc_id in locations.keys():
        new_locations.append(loc_id)
    return new_locations


def handle_rate_limiting(response: Response, attempt, backoff_factor, max_wait_time):
    # Función para manejar rate limiting
    if response.status_code == 429:
        retry_after = int(float(response.headers.get('Retry-After', 4)))
        wait_time = min(backoff_factor ** attempt * retry_after, max_wait_time)
        # Añadir jitter
        wait_time = wait_time / 2 + random.uniform(0, wait_time / 2)
        print(f"Límite de tasa excedido. Reintentando después de {wait_time:.2f} segundos.")
        time.sleep(wait_time)
        return True
    return False


def normalize_string(s):
    # Función para normalizar strings (eliminar acentos y convertir a mayúsculas)
    if not s:
        return ''
    nfkd_form = unicodedata.normalize('NFKD', s)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return only_ascii.upper()


def fetch_locations():
    # Función para obtener ubicaciones desde Shopify
    base_url, headers = get_credentials_shopify()
    url = f"{base_url}/locations.json"
    session = requests.Session()
    locations = {}
    # Ajustar para 4 llamadas por segundo
    rate_limiter = RateLimiter(max_calls=4, period=1)

    max_retries = 5
    backoff_factor = 2
    max_wait_time = 60

    for attempt in range(max_retries):
        try:
            rate_limiter.wait()
            response = session.get(url, headers=headers)
            log_api_call(response)
            if response.status_code == 200:
                data = response.json()
                for loc in data.get('locations', []):
                    loc_id = loc.get('id')
                    loc_name = loc.get('name')
                    locations[loc_id] = loc_name
                    print(f"Location ID: {loc_id}, Nombre original: {loc_name}")
                print(f"Obtenidas {len(locations)} ubicaciones.")
                return locations
            elif response.status_code == 429:
                print(f"Error al obtener ubicaciones: {response.status_code} {response.text}")
                if handle_rate_limiting(response, attempt, backoff_factor, max_wait_time):
                    continue
            else:
                print(f"Error al obtener ubicaciones: {response.status_code} {response.text}")
                wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                print(f"Esperando {wait_time} segundos antes de reintentar.")
                time.sleep(wait_time)
        except requests.RequestException as e:
            wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
            print(f"Error en la solicitud HTTP para ubicaciones (intento {attempt+1}): {e}. Reintentando después de {wait_time} segundos.")
            time.sleep(wait_time)

    print("Máximo número de intentos alcanzado para obtener ubicaciones. No se obtuvieron ubicaciones.")
    return locations  # Devolverá vacío


def fetch_shopify_variants(variants: list) -> list:
    base_url, headers = get_credentials_shopify()
    session = requests.Session()
    variants_shopify = []
    rate_limiter = RateLimiter(max_calls=4, period=1)
    for variant_id in variants:
        base_url = f"{base_url}/variants/{variant_id}.json"
        try:
            rate_limiter.wait()
            response = session.get(base_url, headers=headers)
            log_api_call(response)
            if response.status_code == 200:
                data = response.json()
                fetched_variants = data.get('variant', {})
                variants_shopify.append(fetched_variants)
            # else:
            #     print(f"Error inesperado al obtener variantes: {response.status_code} {response.text}.")
        except requests.RequestException as e:
            print(f"Error en la solicitud HTTP para productos.")
            time.sleep(3)

    session.close()
    print(f"Total de productos obtenidos: {len(variants)}")
    return variants_shopify


def fetch_shopify_variants_for_location(location_id) -> list:
    base_url, headers = get_credentials_shopify()
    session = requests.Session()
    inventory = []
    rate_limiter = RateLimiter(max_calls=4, period=1)
    base_url = f"{base_url}/inventory_levels.json"
    url = f"{base_url}?limit=250&location_ids={location_id}"
    try:
        while url:
            rate_limiter.wait()
            response = session.get(url, headers=headers)
            # log_api_call(response)
            if response.status_code == 200:
                data = response.json()
                fetched_inventory = data.get('inventory_levels', [])
                inventory.extend(fetched_inventory)
            link_header = response.headers.get('Link')
            if link_header:
                url = get_link_next(link_header)
            else:
                url = None
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP para inventario.")
    print(f"In {location_id} exists {len(inventory)} elements")
    session.close()
    return inventory


def fetch_shopify_one_product(product_id: int) -> dict:
    base_url, headers = get_credentials_shopify()
    session = requests.Session()
    rate_limiter = RateLimiter(max_calls=4, period=1)
    url = f"{base_url}/products/{product_id}.json"

    try:
        rate_limiter.wait()
        response = session.get(url, headers=headers)
        log_api_call(response)
        if response.status_code == 200:
            data = response.json()
            fetched_variants = data.get('product', {})
        else:
            print(f"Error inesperado al obtener variantes: {response.status_code} {response.text}.")
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP para productos.")
        time.sleep(1)

    session.close()
    return fetched_variants


# Función para obtener niveles de inventario desde Shopify
def fetch_inventory_levels(inventory_item_ids, location_ids):
    """
    Obtiene los niveles de inventario para una lista de inventory_item_ids y location_ids,
    retornando un diccionario de {inventory_item_id: {location_id: available, ...}, ...}.
    """
    if not inventory_item_ids:
        print("No hay inventory_item_ids para obtener niveles de inventario.")
        return {}

    base_url, headers = get_credentials_shopify()
    url = f"{base_url}/inventory_levels.json"
    inventory_dict = {}
    batch_size = 25  # Tamaño de lote reducido
    total_batches = ceil(len(inventory_item_ids) / batch_size)
    session = requests.Session()
    rate_limiter = RateLimiter(max_calls=4, period=1)  # Ajustar para 4 llamadas por segundo
    max_retries = 5
    backoff_factor = 2
    max_wait_time = 60

    for i in range(total_batches):
        batch_ids = inventory_item_ids[i * batch_size: (i + 1) * batch_size]
        params = {
            'inventory_item_ids': ','.join(map(str, batch_ids)),
            'location_ids': ','.join(map(str, location_ids))
        }

        for attempt in range(max_retries):
            try:
                rate_limiter.wait()
                response = session.get(url, headers=headers, params=params)
                log_api_call(response)
                if response.status_code == 200:
                    data = response.json()
                    inventory_levels = data.get('inventory_levels', [])
                    if not inventory_levels:
                        print(f"No se encontraron niveles de inventario para el lote {i+1}/{total_batches}.")
                    for level in inventory_levels:
                        inventory_item_id = level['inventory_item_id']
                        location_id = level['location_id']
                        available = level.get('available', 0)
                        if inventory_item_id not in inventory_dict:
                            inventory_dict[inventory_item_id] = {}
                        inventory_dict[inventory_item_id][location_id] = available
                        print(f"Inventory Item ID: {inventory_item_id}, Location ID: {location_id}, Available: {available}")
                    print(f"Niveles de inventario obtenidos para el lote {i+1}/{total_batches}.")
                    break
                elif response.status_code == 429:
                    print(f"Error al obtener niveles de inventario: {response.status_code} {response.text}")
                    if handle_rate_limiting(response, attempt, backoff_factor, max_wait_time):
                        continue
                else:
                    print(f"Error al obtener niveles de inventario (intento {attempt+1}): {response.status_code} {response.text}. Reintentando.")
                    wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                    print(f"Esperando {wait_time} segundos antes de reintentar.")
                    time.sleep(wait_time)
            except requests.RequestException as e:
                wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                print(f"Error en la solicitud HTTP para inventarios (intento {attempt+1}): {e}. Reintentando después de {wait_time} segundos.")
                time.sleep(wait_time)
        else:
            print(f"Máximo número de intentos alcanzado para el lote {i+1}/{total_batches}. Saliendo del fetch de inventarios.")
            continue

        print(f"Procesado lote de inventarios. Total hasta ahora: {len(inventory_dict)}")

    session.close()
    return inventory_dict


# Función para obtener niveles de inventario desde Shopify
def fetch_all_inventory_levels():
    """
    Obtiene los niveles de inventario para una lista de inventory_item_ids y location_ids,
    retornando un diccionario de {inventory_item_id: {location_id: available, ...}, ...}.
    """

    base_url, headers = get_credentials_shopify()
    base_url = f"{base_url}/inventory_levels.json?locationids=66148433965"
    url = f"{base_url}?limit=250"
    inventory_dict = {}
    session = requests.Session()
    rate_limiter = RateLimiter(max_calls=4, period=1)
    max_wait_time = 60
    inventory_levels_list = []
    wait_time = max_wait_time

    # while url:
    #     for attempt in range(max_retries):
    try:
        rate_limiter.wait()
        response = session.get(url, headers=headers)
        # print("response.json()", response.json())
        log_api_call(response)
        if response.status_code == 200:
            data = response.json()
            inventory_levels = data.get('inventory_levels', [])
            inventory_levels_list.extend(inventory_levels)
            for level in inventory_levels:
                inventory_item_id = level['inventory_item_id']
                location_id = level['location_id']
                available = level.get('available', 0)
                if inventory_item_id not in inventory_dict:
                    inventory_dict[inventory_item_id] = {}
                inventory_dict[inventory_item_id][location_id] = available
                print(f"Inventory Item ID: {inventory_item_id}, Location ID: {location_id}, Available: {available}")
            # Manejar paginación
            link_header = response.headers.get('Link')
            print("link_header", link_header)
            # if link_header:
            #     links = link_header.split(',')
            #     url = None
            #     for link in links:
            #         if 'rel="next"' in link:
            #             start = link.find('<') + 1
            #             end = link.find('>')
            #             if start > 0 and end > start:
            #                 url = link[start:end]
            #             break
            # else:
            #     url = None
            # break
        elif response.status_code == 422:
            print(f"422: Error al obtener niveles de inventario: {response.text}")
        elif response.status_code == 429:
            print(f"429: Error al obtener niveles de inventario: {response.text}")
            # if handle_rate_limiting(response, attempt, backoff_factor, max_wait_time):
            #     continue
        else:
            # print(f"Error al obtener niveles de inventario (intento {attempt+1}): {response.status_code} {response.text}. Reintentando.")
            # wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
            print(f"Esperando {wait_time} segundos antes de reintentar.")
            time.sleep(wait_time)
    except requests.RequestException as e:
        # wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
        # print(f"Error en la solicitud HTTP para inventarios (intento {attempt+1}): {e}. Reintentando después de {wait_time} segundos.")
        time.sleep(wait_time)
    print("inventory_levels_list", len(inventory_levels_list))
    print("inventory_levels_list", inventory_levels_list)
    print(f"Procesado lote de inventarios. Total hasta ahora: {len(inventory_dict)}")

    session.close()
    return inventory_dict


def fetch_shopify_variants_for_items(items_id: list) -> list:
    base_url, headers = get_credentials_shopify()
    session = requests.Session()
    rate_limiter = RateLimiter(max_calls=4, period=1)
    url = f"{base_url}/inventory_levels.json"
    params = {
        'inventory_item_ids': ','.join(map(str, items_id)),
        'limit': 250
    }
    inventory = []
    try:
        while url:
            rate_limiter.wait()
            response = session.get(url, headers=headers, params=params)
            log_api_call(response)
            if response.status_code == 200:
                data = response.json()
                fetched_inventory = data.get('inventory_levels', [])
                inventory.extend(fetched_inventory)
            link_header = response.headers.get('Link')
            if link_header:
                url = get_link_next(link_header)
                params = None
            else:
                url = None
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP para inventario.")
    print(f"In items exists {len(inventory)} elements")
    session.close()
    return inventory


def fetch_shopify_variant(variant_id: int) -> dict:
    base_url, headers = get_credentials_shopify()
    session = requests.Session()
    variant = {}
    rate_limiter = RateLimiter(max_calls=4, period=1)
    base_url = f"{base_url}/variants/{variant_id}.json"
    try:
        rate_limiter.wait()
        response = session.get(base_url, headers=headers)
        # log_api_call(response)
        if response.status_code == 200:
            data = response.json()
            variant = data.get('variant', {})
    except requests.RequestException as e:
        print(f"Error en la solicitud HTTP para inventario.")
    session.close()
    return variant

def fetch_shopify_variant_single(
    session: requests.Session,
    base_url: str,
    headers: Dict[str, str],
    variant_id: int,
    rate_limiter: RateLimiter,
    timeout: float = 30.0,
) -> Dict[str, Any]:
    """
    Obtiene una variante individual, respetando rate limit = 4 rps.
    Maneja 429 con Retry-After. Devuelve {} si falla.
    """
    url = f"{base_url}/variants/{int(variant_id)}.json"

    # Cada intento pasa por el limiter
    rate_limiter.wait()
    resp = session.get(url, headers=headers, timeout=timeout)

    if resp.status_code == 200:
        return resp.json().get("variant", {}) or {}

    if resp.status_code == 429:
        # Respeta Retry-After y reintenta una vez manualmente acá
        wait_s = get_retry_after(resp.headers, default_seconds=1.0)
        time.sleep(wait_s)
        rate_limiter.wait()
        resp = session.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return resp.json().get("variant", {}) or {}

    # Para 5xx, los reintentos principales los maneja la Session; si aún así cae aquí:
    if 500 <= resp.status_code < 600:
        time.sleep(0.5 + random.random() * 0.7)
        rate_limiter.wait()
        resp = session.get(url, headers=headers, timeout=timeout)
        if resp.status_code == 200:
            return resp.json().get("variant", {}) or {}

    # Log opcional:
    # print(f"[{variant_id}] Error {resp.status_code}: {resp.text[:200]}")
    return {}

def fetch_shopify_variants_bulk(variant_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Obtiene en bloque todas las variantes pasadas. Garantiza no exceder 4 rps.
    Reutiliza Session y RateLimiter. Devuelve lista con los dicts de 'variant' (o {} en fallos).
    """
    if not variant_ids:
        return []

    base_url, headers = get_credentials_shopify()
    session = make_session()
    limiter = RateLimiter(max_calls=MAX_CALLS_PER_SECOND, period=1.0, min_interval=MIN_INTERVAL)

    results: List[Dict[str, Any]] = []
    try:
        for vid in variant_ids:
            variant = fetch_shopify_variant_single(
                session=session,
                base_url=base_url,
                headers=headers,
                variant_id=vid,
                rate_limiter=limiter,
            )
            results.append(variant)
    finally:
        session.close()

    return results


def get_all_orders_shopify() -> dict:
    base_url, headers = get_credentials_shopify()
    orders = []
    url = f"{base_url}/orders.json?limit=250"
    cert_path = os.environ.get('SSL_CERT_FILE', certifi.where())
    session = requests.Session()
    session.verify = cert_path
    rate_limiter = RateLimiter(max_calls=4, period=1)
    while url:
        try:
            rate_limiter.wait()
            response = session.get(url, headers=headers)
            print("response.status_code", response.status_code)
            if response.status_code == 200:
                data = response.json()
                orders.extend(data.get('orders', []))
            print(f"orders obtenidos hasta ahora: {len(orders)}")

            # Manejar paginación
            link_header = response.headers.get('Link')
            if link_header and 'rel="next"' in link_header:
                next_url = link_header.split(';')[0].strip('<>')
                url = next_url
                # time.sleep(0.1)
            else:
                url = None
        except requests.RequestException as e:
            print(f"Error en la solicitud HTTP para orders. {e}")
            # time.sleep(3)
    session.close()
    return orders


def get_all_products():
    base_url, headers = get_credentials_shopify()
    productos = []
    url = f"{base_url}/products.json?limit=250"
    session = requests.Session()
    rate_limiter = RateLimiter(max_calls=4, period=1)
    while url:
        try:
            rate_limiter.wait()
            response = session.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                productos.extend(data.get('products', []))
            print(f"Productos obtenidos hasta ahora: {len(productos)}")

            # Manejar paginación
            link_header = response.headers.get('Link')
            if link_header and 'rel="next"' in link_header:
                next_url = link_header.split(';')[0].strip('<>')
                url = next_url
                # time.sleep(0.1)
            else:
                url = None
        except requests.RequestException as e:
            print(f"Error en la solicitud HTTP para productos. {e}")
            time.sleep(3)
    session.close()
    return productos


# # Función para insertar o actualizar productos, variantes e inventarios en la base de datos
# def insert_or_update_products_variants_and_inventory(products, conn, locations, inventory_levels):

#     cursor = conn.cursor()
#     product_values = []
#     variant_values = []
#     log_values = []
#     inventory_item_to_variant = {}
#     variant_id_to_barcode = {}
#     barcodes_set = set()
#     duplicate_barcodes = set()

#     # Filtrar ubicaciones deseadas
#     desired_location_ids = [loc_id for loc_id in locations if normalize_string(locations[loc_id]) in [normalize_string(name) for name in DESIRED_LOCATIONS]]

#     if not desired_location_ids:
#         print("No se encontraron las ubicaciones deseadas. Verifica los nombres de las ubicaciones en Shopify.")
#         cursor.close()
#         return

#     # Recolectar inventory_item_ids y verificar unicidad de barcodes
#     for product in products:
#         product_id = product['id']
#         title = clean_string(product.get('title', 'Unknown'))
#         vendor = clean_string(product.get('vendor', 'Unknown'))
#         first_variant = product.get('variants', [])[0] if product.get('variants') else {}
#         price = first_variant.get('price', '0.00')
#         sku = clean_string(first_variant.get('sku', 'Unknown'))
#         image_url = clean_string(product.get('image', {}).get('src', 'Unknown')) if product.get('image') else 'Unknown'

#         product_values.append((product_id, title, vendor, price, sku, image_url))

#         for variant in product.get('variants', []):
#             variant_id = variant.get('id')
#             if not variant_id:
#                 print(f"Variante sin variant_id para el producto {product_id}")
#                 continue
#             variant_title = clean_string(variant.get('title', 'Unknown'))
#             variant_sku = clean_string(variant.get('sku', 'Unknown'))
#             variant_price = variant.get('price', '0.00')
#             variant_barcode_original = variant.get('barcode', 'Unknown')
#             variant_barcode = clean_string(variant_barcode_original)
#             inventory_item_id = variant.get('inventory_item_id')  # No usaremos esta variable para la base de datos

#             # Validar el barcode
#             if not validate_barcode(variant_barcode):
#                 print(f"Barcode inválido para la variante ID {variant_id}: '{variant_barcode}'. Se establecerá como 'Unknown'.")
#                 variant_barcode = 'Unknown'

#             # Comprobar si el barcode está duplicado
#             if variant_barcode in barcodes_set:
#                 duplicate_barcodes.add(variant_barcode)
#                 print(f"Barcode duplicado para la variante ID {variant_id}: '{variant_barcode}'. Se establecerá como 'Unknown'.")
#                 variant_barcode = 'Unknown'
#             elif variant_barcode != 'Unknown':
#                 barcodes_set.add(variant_barcode)

#             # Mapear inventory_item_id a variant_id (para uso interno)
#             if inventory_item_id:
#                 inventory_item_to_variant[inventory_item_id] = variant_id

#             # Guardar el mapeo de variant_id a barcode
#             variant_id_to_barcode[variant_id] = variant_barcode

#             # Agregar variante a la lista para insertar/actualizar
#             variant_values.append((
#                 variant_id,
#                 product_id,
#                 variant_title,
#                 variant_sku,
#                 variant_price,
#                 0,  # Inicializar stock a 0, se actualizará luego
#                 variant_barcode,
#                 None,  # location_id, se actualizará
#                 'Unknown'  # location_name, se actualizará
#             ))


#     # Insertar o actualizar productos
#     sql_product = """
#     INSERT INTO productos (product_id, title, vendor, price, sku, image_url)
#     VALUES (%s, %s, %s, %s, %s, %s)
#     ON DUPLICATE KEY UPDATE title=VALUES(title), vendor=VALUES(vendor), price=VALUES(price), sku=VALUES(sku), image_url=VALUES(image_url)
#     """
#     try:
#         cursor.executemany(sql_product, product_values)
#         print(f"{cursor.rowcount} productos insertados o actualizados.")
#     except mysql.connector.Error as err:
#         print(f"Error al insertar o actualizar productos: {err}")


#     # Insertar o actualizar variantes
#     sql_variant = """
#     INSERT INTO product_variants (
#         variant_id,
#         product_id, 
#         title, 
#         sku, 
#         price, 
#         stock, 
#         barcode, 
#         location_id,
#         location_name
#     )
#     VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#     ON DUPLICATE KEY UPDATE 
#         title=VALUES(title), 
#         sku=VALUES(sku), 
#         price=VALUES(price), 
#         stock=VALUES(stock), 
#         barcode=VALUES(barcode), 
#         location_id=VALUES(location_id),
#         location_name=VALUES(location_name)
#     """
#     print(variant_values[1])
    
#     try:
#         cursor.executemany(sql_variant, variant_values)
#         print(f"{cursor.rowcount} variantes insertadas o actualizadas.")
#     except mysql.connector.Error as err:
#         print(f"Error al insertar o actualizar variantes: {err}")

#     # Obtener los inventory_item_ids para los niveles de inventario
#     inventory_item_ids = list(inventory_item_to_variant.keys())

#     # Obtener los niveles de inventario
#     inventory_levels_fetched = inventory_levels  # Ya se ha obtenido fuera de esta función

#     # Procesar los niveles de inventario
#     for inventory_item_id, loc_dict in inventory_levels_fetched.items():
#         variant_id = inventory_item_to_variant.get(inventory_item_id)
#         if not variant_id:
#             print(f"No se encontró variant_id para inventory_item_id {inventory_item_id}")
#             continue

#         variant_barcode = variant_id_to_barcode.get(variant_id, 'Unknown')

#         for location_id, available in loc_dict.items():
#             # Obtener el nombre de la ubicación
#             location_name = locations.get(location_id, 'Unknown')

#             if location_name == 'Unknown':
#                 print(f"Location ID {location_id} no tiene un nombre asociado. Verifica las ubicaciones obtenidas.")
#             else:
#                 print(f"Location ID {location_id} mapeado a {location_name}")

#             # Obtener el stock anterior para esta variante y ubicación
#             try:
#                 cursor.execute("""
#                     SELECT stock FROM product_variants 
#                     WHERE variant_id = %s AND location_id = %s
#                 """, (variant_id, location_id))
#                 result = cursor.fetchone()
#                 previous_stock = result[0] if result else None
#             except mysql.connector.Error as err:
#                 print(f"Error al obtener el stock anterior para variant_id {variant_id}, location_id {location_id}: {err}")
#                 previous_stock = None

#             if previous_stock is not None and previous_stock != available:
#                 diferencia = available - previous_stock
#                 log_values.append((
#                     inventory_item_id,
#                     location_id,
#                     previous_stock,
#                     available,
#                     diferencia,
#                     variant_barcode,
#                     variant_id,  # producto_id
#                     variant_id,  # variante_id (puedes ajustar si es necesario)
#                     location_name
#                 ))

#             # Actualizar el stock en la base de datos
#             try:
#                 cursor.execute("""
#                     UPDATE product_variants
#                     SET stock = %s
#                     WHERE variant_id = %s AND location_id = %s
#                 """, (available, variant_id, location_id))
#                 print(f"Actualizado stock para variant_id {variant_id}, location_id {location_id} a {available}.")
#             except mysql.connector.Error as err:
#                 print(f"Error al actualizar stock para variant_id {variant_id}, location_id {location_id}: {err}")

#     # Insertar logs de inventario si hay cambios
#     if log_values:
#         sql_log = """
#         INSERT INTO LogsInventario (
#             inventory_item_id, 
#             location_id, 
#             cantidad_anterior, 
#             cantidad_nueva, 
#             diferencia, 
#             barcode, 
#             producto_id, 
#             variante_id, 
#             nombre_ubicacion
#         )
#         VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
#         """
#         try:
#             cursor.executemany(sql_log, log_values)
#             print(f"{cursor.rowcount} registros de logs de inventario insertados.")
#         except mysql.connector.Error as err:
#             print(f"Error al insertar logs de inventario: {err}")

#     try:
#         conn.commit()
#         print("Transacción de base de datos confirmada.")
#     except mysql.connector.Error as err:
#         print(f"Error al confirmar la transacción: {err}")
#         conn.rollback()
#         print("Transacción revertida debido a un error.")

#     cursor.close()

# ----------------- Chunking por URL y por cantidad -----------------
def chunk_ids_by_url_capacity(
    base_url: str,
    ids: List[int],
    max_ids_per_call: int = 50,
    url_max_len: int = 3800,
    limit_param: int = 250,
) -> Iterable[List[int]]:
    """
    Parte la lista de ids en trozos que no excedan:
      - max_ids_per_call (p.ej. 50)
      - url_max_len (p.ej. ~3800 chars)
    Se calcula la URL exacta con requests para asegurar longitud.
    """
    url = f"{base_url}/inventory_levels.json"
    current: List[int] = []
    session = requests.Session()  # sólo para preparar URL
    try:
        for id_ in ids:
            candidate = current + [id_]
            params = {"inventory_item_ids": ",".join(map(str, candidate)), "limit": limit_param}
            prep = requests.Request("GET", url, params=params).prepare()
            url_len = len(prep.url or "")
            if len(candidate) > max_ids_per_call or url_len > url_max_len:
                if not current:
                    # Si un solo id ya excediera (muy improbable), lo mandamos solo
                    yield [id_]
                    current = []
                else:
                    yield current
                    current = [id_]
            else:
                current = candidate
        if current:
            yield current
    finally:
        session.close()

# ----------------- Fetch paginado por lote -----------------
def fetch_inventory_levels_for_chunk(
    session: requests.Session,
    limiter: RateLimiter,
    base_url: str,
    headers: Dict[str, str],
    item_ids_chunk: List[int],
    timeout: float = 30.0,
) -> List[Dict[str, Any]]:
    """
    Hace GET /inventory_levels.json para un chunk de ids y pagina por Link.
    """
    url = f"{base_url}/inventory_levels.json"
    params = {
        "inventory_item_ids": ",".join(map(str, item_ids_chunk)),
        "limit": 250,
    }
    results: List[Dict[str, Any]] = []

    while url:
        limiter.wait()
        resp = session.get(url, headers=headers, params=params, timeout=timeout)

        if resp.status_code == 200:
            data = resp.json() or {}
            results.extend(data.get("inventory_levels", []))
            # Siguiente página (dentro del MISMO chunk)
            link_header = resp.headers.get("Link")
            if link_header:
                url = get_link_next(link_header)
                params = None  # importante: después de la primera, no vuelvas a pasar params
            else:
                url = None
                break

        elif resp.status_code == 429:
            # Respeta Retry-After y reintenta misma URL
            wait_s = get_retry_after(resp.headers, default_seconds=1.0)
            time.sleep(wait_s)
            continue

        elif 500 <= resp.status_code < 600:
            # backoff y reintento manual
            time.sleep(0.6 + random.random() * 0.8)
            continue
        else:
            # 4xx distinto de 429: aborta este chunk
            # print(f"Error {resp.status_code}: {resp.text[:200]}")
            break

    return results

# ----------------- Función principal: 5,919 ids sin pasar de 4 rps -----------------
def fetch_all_inventory_levels_for_items(all_item_ids: List[int]) -> List[Dict[str, Any]]:
    """
    Recorre TODOS los inventory_item_ids en chunks aceptables por Shopify,
    pagina dentro de cada chunk y agrega todo en una sola lista.
    """
    if not all_item_ids:
        return []

    base_url, headers = get_credentials_shopify()
    session = make_session()
    limiter = RateLimiter(max_calls=MAX_CALLS_PER_SECOND, period=1.0, min_interval=MIN_INTERVAL)

    all_results: List[Dict[str, Any]] = []

    try:
        # 1) Partir ids por capacidad de URL / cantidad
        for idx, chunk in enumerate(
            chunk_ids_by_url_capacity(base_url, all_item_ids, max_ids_per_call=50, url_max_len=3800, limit_param=250),
            start=1
        ):
            # 2) Para cada chunk, pagina internamente
            chunk_results = fetch_inventory_levels_for_chunk(
                session=session,
                limiter=limiter,
                base_url=base_url,
                headers=headers,
                item_ids_chunk=chunk,
            )
            all_results.extend(chunk_results)

            # (Opcional) pequeño respiro entre chunks si vas muy justo de límite compartido
            # time.sleep(0.05)

            # print(f"Chunk {idx}: ids={len(chunk)} niveles={len(chunk_results)}")
    finally:
        session.close()

    # (Opcional) deduplicar por inventory_item_id + location_id si hiciera falta
    # seen = set()
    # dedup = []
    # for r in all_results:
    #     key = (r.get("inventory_item_id"), r.get("location_id"))
    #     if key not in seen:
    #         seen.add(key)
    #         dedup.append(r)
    # return dedup

    return all_results

Key = Tuple[int, int, str]

def _key(row: Dict[str, Any]) -> Key:
    return (
        int(row["variant_id"]),
        int(row["location_id"]),
        str(row.get("barcode", "")).strip()
    )

def find_stock_differences_return_shopify(
    db_inventory: List[Dict[str, Any]],         # primera lista (tu DB)
    shopify_levels: List[Dict[str, Any]],       # segunda lista (Shopify)
    db_stock_field: str = "stock",
    shopify_stock_field: str = "stock",
) -> List[Dict[str, Any]]:
    """
    Devuelve objetos de Shopify (variant_id, location_id, barcode, stock)
    SOLO cuando el stock difiere respecto a tu DB.
    """
    # Indexa tu DB por llave compuesta
    db_by_key: Dict[Key, Dict[str, Any]] = {_key(r): r for r in db_inventory}

    diffs: List[Dict[str, Any]] = []

    for s in shopify_levels:
        k = _key(s)
        db_row = db_by_key.get(k)
        if db_row is None:
            # No existe en DB → no comparamos (si quisieras incluirlos como "nuevos", cámbialo)
            continue

        db_stock = int(db_row.get(db_stock_field) or 0)
        shop_stock = int(s.get(shopify_stock_field) or 0)

        if db_stock != shop_stock:
            # responde con el objeto de Shopify
            diffs.append({
                "variant_id": k[0],
                "location_id": k[1],
                "barcode": k[2],
                "stock": shop_stock,
            })

    return diffs
