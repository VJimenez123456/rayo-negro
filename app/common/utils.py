from app.core.config import settings
from collections import deque
import time
import random
from requests import Response


def get_auth_headers_shopify(api_key: str, password: str):
    return {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': password
    }


def get_credentials_shopify() -> dict:
    api_version = '2023-07'
    api_key = settings.SHOPIFY_API_KEY
    password = settings.SHOPIFY_API_PASSWORD
    store_url = settings.SHOPIFY_STORE_URL
    base_url = f"https://{store_url}/admin/api/{api_version}"
    headers = get_auth_headers_shopify(api_key, password)
    return base_url, headers


class RateLimiter:
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
            print(f"Rate limit alcanzado. Esperando {wait_time:.2f} segundos.")
            time.sleep(wait_time)
        self.calls.append(time.time())


def log_api_call(response: Response):
    # Función para registrar el límite de llamadas a la API
    call_limit = response.headers.get('X-Shopify-Shop-Api-Call-Limit')
    if call_limit:
        used, total = map(int, call_limit.split('/'))
        print(f"API Call Limit: {used}/{total}")


def get_link_next(link_header: str):
    header_links = link_header.split(',')
    url = None
    for link in header_links:
        if 'rel="next"' in link:
            start = link.find('<') + 1
            end = link.find('>')
            if start > 0 and end > start:
                url = link[start:end]
            break
    return url
