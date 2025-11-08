import time, random
import requests
from app.core.config import settings
from collections import deque
from requests import Response
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from email.utils import parsedate_to_datetime


def get_auth_headers_shopify(api_key: str, password: str):
    return {
        'Content-Type': 'application/json',
        'X-Shopify-Access-Token': password
    }


def get_credentials_shopify() -> dict:
    api_version = '2025-01'
    api_key = settings.SHOPIFY_API_KEY
    password = settings.SHOPIFY_API_PASSWORD
    store_url = settings.SHOPIFY_STORE_URL
    base_url = f"https://{store_url}/admin/api/{api_version}"
    headers = get_auth_headers_shopify(api_key, password)
    return base_url, headers


MAX_CALLS_PER_SECOND = 4
SAFE_RPS = 4   # margen por debajo de 4 rps
MIN_INTERVAL = 1.0 / SAFE_RPS


class RateLimiter:
    """
    Limita a N llamadas en 'period' segundos, y además impone un intervalo mínimo
    entre llamadas para evitar ráfagas que crucen la ventana.
    """
    def __init__(self, max_calls=MAX_CALLS_PER_SECOND, period=1.0, min_interval=MIN_INTERVAL):
        self.calls = deque()
        self.max_calls = max_calls
        self.period = period
        self.min_interval = min_interval
        self._last_call_ts = 0.0

    def wait(self):
        now = time.time()

        # 1) Espaciado mínimo entre llamadas
        elapsed = now - self._last_call_ts
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
            now = time.time()

        # 2) Ventana deslizante (max N por periodo)
        while self.calls and self.calls[0] <= now - self.period:
            self.calls.popleft()

        if len(self.calls) >= self.max_calls:
            wait_time = self.period - (now - self.calls[0])
            # Jitter para evitar sincronía con otros procesos
            wait_time *= (0.85 + random.random() * 0.5)  # ~0.85x–1.35x
            if wait_time > 0:
                # print(f"Rate limit alcanzado. Esperando {wait_time:.2f}s")
                time.sleep(wait_time)

        self.calls.append(time.time())
        self._last_call_ts = time.time()

# ====== Session con reintentos ======
def make_session() -> requests.Session:
    retry = Retry(
        total=5,
        backoff_factor=0.35,  # exponencial: 0.35, 0.7, 1.4, ...
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS"),
        respect_retry_after_header=False,
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry, pool_connections=20, pool_maxsize=20)
    s = requests.Session()
    s.mount("https://", adapter)
    s.mount("http://", adapter)
    return s


def parse_call_limit(headers):
    """
    Shopify suele enviar:
    - X-Shopify-API-Call-Limit: '10/40' (uso/bucket)
    - o X-Shopify-Shop-Api-Call-Limit (variantes)
    Devuelve (used, bucket) o (None, None) si no viene.
    """
    for k in ("X-Shopify-API-Call-Limit", "X-Shopify-Shop-Api-Call-Limit"):
        v = headers.get(k)
        if v and "/" in v:
            try:
                used, bucket = v.split("/", 1)
                return int(used.strip()), int(bucket.strip())
            except Exception:
                pass
    return None, None


def backoff_from_bucket(headers):
    """
    Si el bucket está muy usado (p.ej. >80%), duerme un poco
    para evitar topar el 429.
    """
    used, bucket = parse_call_limit(headers)
    if used is not None and bucket:
        ratio = used / bucket
        if ratio >= 0.8:
            # Dormir proporcional al uso, con jitter
            sleep_for = (ratio - 0.8) * 2.0  # hasta ~0.4s extra
            sleep_for *= (0.8 + random.random() * 0.6)
            if sleep_for > 0:
                time.sleep(sleep_for)


def get_retry_after(headers, default_seconds: float = 1.0) -> float:
    """
    Acepta Retry-After en:
      - segundos (entero o '4.0')
      - fecha HTTP (RFC 7231), p.ej. 'Wed, 21 Oct 2015 07:28:00 GMT'
    """
    ra = headers.get("Retry-After")
    if not ra:
        return default_seconds
    ra = ra.strip()
    # 1) número en segundos (int o float)
    try:
        return float(ra)
    except ValueError:
        pass
    # 2) fecha HTTP -> segundos desde ahora
    try:
        dt = parsedate_to_datetime(ra)
        if dt:
            # convertir a tz-aware UTC si viene naive
            if dt.tzinfo is None:
                from datetime import timezone
                dt = dt.replace(tzinfo=timezone.utc)
            wait_s = (dt - parsedate_to_datetime(
                parsedate_to_datetime(time.strftime("%a, %d %b %Y %H:%M:%S GMT")).ctime()
            )).total_seconds()  # <- evitamos dependencias; pero mejor usa time.time()
    except Exception:
        return default_seconds
    # fallback final
    now = time.time()
    wait_s = max(0.0, dt.timestamp() - now)
    return wait_s if wait_s > 0 else default_seconds

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
