# flake8: noqa
import requests
from requests import Response
import time
import logging
from collections import deque
import random
import unicodedata
from app.core.config import settings
from math import ceil


#  Logging settings
logging.basicConfig(
    filename='inventario_sync.log',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

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


def get_auth_headers(api_key: str, password: str):
    return {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': password
    }


def get_credentials() -> dict:
    api_version = '2023-07'
    api_key = settings.SHOPIFY_API_KEY,
    password = settings.SHOPIFY_API_PASSWORD
    store_name = get_store_name(settings.SHOPIFY_STORE_URL)
    credentials = {
        "base_url": f"https://{store_name}/admin/api/{api_version}",
        "headers": get_auth_headers(api_key, password)
    }
    return credentials


def get_store_name(store_url):
    return store_url


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


class RateLimiter:
    # The `RateLimiter` class in Python is designed to handle
    # rate limiting for Shopify API requests by managing the number
    # of calls made within a specified period.
    def __init__(self, max_calls, period):
        self.calls = deque()
        self.max_calls = max_calls
        self.period = period  # en segundos

    def wait(self):
        current = time.time()
        while self.calls and self.calls[0] <= current - self.period:
            self.calls.popleft()
        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (current - self.calls[0])
            # Añadir jitter
            wait_time = wait_time / 2 + random.uniform(0, wait_time / 2)
            logging.info(f"Rate limit alcanzado. Esperando {wait_time:.2f} segundos.")
            time.sleep(wait_time)
        self.calls.append(time.time())


def handle_rate_limiting(response: Response, attempt, backoff_factor, max_wait_time):
    # Función para manejar rate limiting
    if response.status_code == 429:
        retry_after = int(float(response.headers.get('Retry-After', 4)))
        wait_time = min(backoff_factor ** attempt * retry_after, max_wait_time)
        # Añadir jitter
        wait_time = wait_time / 2 + random.uniform(0, wait_time / 2)
        logging.warning(f"Límite de tasa excedido. Reintentando después de {wait_time:.2f} segundos.")
        time.sleep(wait_time)
        return True
    return False


def log_api_call(response: Response):
    # Función para registrar el límite de llamadas a la API
    call_limit = response.headers.get('X-Shopify-Shop-Api-Call-Limit')
    if call_limit:
        used, total = map(int, call_limit.split('/'))
        logging.debug(f"API Call Limit: {used}/{total}")


def normalize_string(s):
    # Función para normalizar strings (eliminar acentos y convertir a mayúsculas)
    if not s:
        return ''
    nfkd_form = unicodedata.normalize('NFKD', s)
    only_ascii = nfkd_form.encode('ASCII', 'ignore').decode('utf-8')
    return only_ascii.upper()


def fetch_locations():
    # Función para obtener ubicaciones desde Shopify
    credentials = get_credentials()
    base_url = f"{credentials['base_url']}/locations.json"
    headers = credentials["headers"]
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
            response = session.get(base_url, headers=headers)
            log_api_call(response)
            if response.status_code == 200:
                data = response.json()
                for loc in data.get('locations', []):
                    loc_id = loc.get('id')
                    loc_name = loc.get('name')
                    locations[loc_id] = loc_name
                    logging.info(f"Location ID: {loc_id}, Nombre original: {loc_name}")
                logging.info(f"Obtenidas {len(locations)} ubicaciones.")
                return locations
            elif response.status_code == 429:
                logging.error(f"Error al obtener ubicaciones: {response.status_code} {response.text}")
                if handle_rate_limiting(response, attempt, backoff_factor, max_wait_time):
                    continue
            else:
                logging.error(f"Error al obtener ubicaciones: {response.status_code} {response.text}")
                wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                logging.info(f"Esperando {wait_time} segundos antes de reintentar.")
                time.sleep(wait_time)
        except requests.RequestException as e:
            wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
            logging.warning(f"Error en la solicitud HTTP para ubicaciones (intento {attempt+1}): {e}. Reintentando después de {wait_time} segundos.")
            time.sleep(wait_time)

    logging.error("Máximo número de intentos alcanzado para obtener ubicaciones. No se obtuvieron ubicaciones.")
    return locations  # Devolverá vacío


def fetch_shopify_products():
    # Función para obtener productos activos desde Shopify
    credentials = get_credentials()
    base_url = f"{credentials['base_url']}/products.json"
    headers = credentials["headers"]
    session = requests.Session()
    products = []
    limit = 250  # Máximo permitido por Shopify
    url = f"{base_url}?limit={limit}"  # &status=active"
    rate_limiter = RateLimiter(max_calls=4, period=1)  # Ajustar para 4 llamadas por segundo
    max_retries = 5
    backoff_factor = 2
    max_wait_time = 60

    while url:
        for attempt in range(max_retries):
            try:
                rate_limiter.wait()
                response = session.get(url, headers=headers)
                log_api_call(response)
                if response.status_code == 200:
                    data = response.json()
                    fetched_products = data.get('products', [])
                    products.extend(fetched_products)
                    logging.info(f"Se han obtenido {len(fetched_products)} productos.")
                    # Manejar paginación
                    link_header = response.headers.get('Link')
                    if link_header:
                        links = link_header.split(',')
                        url = None
                        for link in links:
                            if 'rel="next"' in link:
                                start = link.find('<') + 1
                                end = link.find('>')
                                if start > 0 and end > start:
                                    next_url = link[start:end]
                                    url = next_url
                                break
                    else:
                        url = None
                    break
                elif response.status_code == 429:
                    logging.error(f"Error inesperado al obtener productos: {response.status_code} {response.text}")
                    if handle_rate_limiting(response, attempt, backoff_factor, max_wait_time):
                        continue
                else:
                    logging.warning(f"Error inesperado al obtener productos (intento {attempt+1}): {response.status_code} {response.text}. Reintentando.")
                    wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                    logging.info(f"Esperando {wait_time} segundos antes de reintentar.")
                    time.sleep(wait_time)
            except requests.RequestException as e:
                wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                logging.warning(f"Error en la solicitud HTTP para productos (intento {attempt+1}): {e}. Reintentando después de {wait_time} segundos.")
                time.sleep(wait_time)
        else:
            logging.error("Máximo número de intentos alcanzado. Saliendo del fetch de productos.")
            break

        logging.info(f"Procesado lote de productos. Total hasta ahora: {len(products)}")

    session.close()
    logging.info(f"Total de productos obtenidos: {len(products)}")
    return products


# Función para obtener niveles de inventario desde Shopify
def fetch_inventory_levels(inventory_item_ids, location_ids):
    """
    Obtiene los niveles de inventario para una lista de inventory_item_ids y location_ids,
    retornando un diccionario de {inventory_item_id: {location_id: available, ...}, ...}.
    """
    if not inventory_item_ids:
        logging.warning("No hay inventory_item_ids para obtener niveles de inventario.")
        return {}

    credentials = get_credentials()
    base_url = f"{credentials['base_url']}/inventory_levels.json"
    headers = credentials["headers"]
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
                response = session.get(base_url, headers=headers, params=params)
                log_api_call(response)
                if response.status_code == 200:
                    data = response.json()
                    inventory_levels = data.get('inventory_levels', [])
                    if not inventory_levels:
                        logging.warning(f"No se encontraron niveles de inventario para el lote {i+1}/{total_batches}.")
                    for level in inventory_levels:
                        inventory_item_id = level['inventory_item_id']
                        location_id = level['location_id']
                        available = level.get('available', 0)
                        if inventory_item_id not in inventory_dict:
                            inventory_dict[inventory_item_id] = {}
                        inventory_dict[inventory_item_id][location_id] = available
                        logging.debug(f"Inventory Item ID: {inventory_item_id}, Location ID: {location_id}, Available: {available}")
                    logging.info(f"Niveles de inventario obtenidos para el lote {i+1}/{total_batches}.")
                    break
                elif response.status_code == 429:
                    logging.error(f"Error al obtener niveles de inventario: {response.status_code} {response.text}")
                    if handle_rate_limiting(response, attempt, backoff_factor, max_wait_time):
                        continue
                else:
                    logging.warning(f"Error al obtener niveles de inventario (intento {attempt+1}): {response.status_code} {response.text}. Reintentando.")
                    wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                    logging.info(f"Esperando {wait_time} segundos antes de reintentar.")
                    time.sleep(wait_time)
            except requests.RequestException as e:
                wait_time = min(backoff_factor ** attempt * 5, max_wait_time)
                logging.warning(f"Error en la solicitud HTTP para inventarios (intento {attempt+1}): {e}. Reintentando después de {wait_time} segundos.")
                time.sleep(wait_time)
        else:
            logging.error(f"Máximo número de intentos alcanzado para el lote {i+1}/{total_batches}. Saliendo del fetch de inventarios.")
            continue

        logging.info(f"Procesado lote de inventarios. Total hasta ahora: {len(inventory_dict)}")

    session.close()
    return inventory_dict


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
#         logging.error("No se encontraron las ubicaciones deseadas. Verifica los nombres de las ubicaciones en Shopify.")
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
#                 logging.warning(f"Variante sin variant_id para el producto {product_id}")
#                 continue
#             variant_title = clean_string(variant.get('title', 'Unknown'))
#             variant_sku = clean_string(variant.get('sku', 'Unknown'))
#             variant_price = variant.get('price', '0.00')
#             variant_barcode_original = variant.get('barcode', 'Unknown')
#             variant_barcode = clean_string(variant_barcode_original)
#             inventory_item_id = variant.get('inventory_item_id')  # No usaremos esta variable para la base de datos

#             # Validar el barcode
#             if not validate_barcode(variant_barcode):
#                 logging.warning(f"Barcode inválido para la variante ID {variant_id}: '{variant_barcode}'. Se establecerá como 'Unknown'.")
#                 variant_barcode = 'Unknown'

#             # Comprobar si el barcode está duplicado
#             if variant_barcode in barcodes_set:
#                 duplicate_barcodes.add(variant_barcode)
#                 logging.warning(f"Barcode duplicado para la variante ID {variant_id}: '{variant_barcode}'. Se establecerá como 'Unknown'.")
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
#         logging.info(f"{cursor.rowcount} productos insertados o actualizados.")
#     except mysql.connector.Error as err:
#         logging.error(f"Error al insertar o actualizar productos: {err}")


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
#         logging.info(f"{cursor.rowcount} variantes insertadas o actualizadas.")
#     except mysql.connector.Error as err:
#         logging.error(f"Error al insertar o actualizar variantes: {err}")

#     # Obtener los inventory_item_ids para los niveles de inventario
#     inventory_item_ids = list(inventory_item_to_variant.keys())

#     # Obtener los niveles de inventario
#     inventory_levels_fetched = inventory_levels  # Ya se ha obtenido fuera de esta función

#     # Procesar los niveles de inventario
#     for inventory_item_id, loc_dict in inventory_levels_fetched.items():
#         variant_id = inventory_item_to_variant.get(inventory_item_id)
#         if not variant_id:
#             logging.warning(f"No se encontró variant_id para inventory_item_id {inventory_item_id}")
#             continue

#         variant_barcode = variant_id_to_barcode.get(variant_id, 'Unknown')

#         for location_id, available in loc_dict.items():
#             # Obtener el nombre de la ubicación
#             location_name = locations.get(location_id, 'Unknown')

#             if location_name == 'Unknown':
#                 logging.error(f"Location ID {location_id} no tiene un nombre asociado. Verifica las ubicaciones obtenidas.")
#             else:
#                 logging.debug(f"Location ID {location_id} mapeado a {location_name}")

#             # Obtener el stock anterior para esta variante y ubicación
#             try:
#                 cursor.execute("""
#                     SELECT stock FROM product_variants 
#                     WHERE variant_id = %s AND location_id = %s
#                 """, (variant_id, location_id))
#                 result = cursor.fetchone()
#                 previous_stock = result[0] if result else None
#             except mysql.connector.Error as err:
#                 logging.error(f"Error al obtener el stock anterior para variant_id {variant_id}, location_id {location_id}: {err}")
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
#                 logging.debug(f"Actualizado stock para variant_id {variant_id}, location_id {location_id} a {available}.")
#             except mysql.connector.Error as err:
#                 logging.error(f"Error al actualizar stock para variant_id {variant_id}, location_id {location_id}: {err}")

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
#             logging.info(f"{cursor.rowcount} registros de logs de inventario insertados.")
#         except mysql.connector.Error as err:
#             logging.error(f"Error al insertar logs de inventario: {err}")

#     try:
#         conn.commit()
#         logging.info("Transacción de base de datos confirmada.")
#     except mysql.connector.Error as err:
#         logging.error(f"Error al confirmar la transacción: {err}")
#         conn.rollback()
#         logging.info("Transacción revertida debido a un error.")

#     cursor.close()
