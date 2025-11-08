#!/usr/bin/env bash
set -euo pipefail

# ===== Config =====
: "${APP_LOG_LEVEL:=INFO}"             # INFO/DEBUG/WARNING/ERROR
: "${APP_ACCESS_LOG:=0}"               # 0 = sin access log, 1 = con access log
: "${CHECK_SHOPIFY:=1}"                # 1 = corre check de conexión
: "${SHOPIFY_SHOP_DOMAIN:=rayo-negro-mx.myshopify.com}"
: "${SHOPIFY_CHECK_RETRIES:=2}"        # reintentos si falla
: "${SHOPIFY_CHECK_TIMEOUT:=5}"        # timeout por intento (s)
: "${FAIL_ON_SHOPIFY_CHECK:=0}"        # 1 = abortar si falla; 0 = solo warn

# ===== Check de conexión a Shopify (sin temas de SSL) =====
if [[ "${CHECK_SHOPIFY}" == "1" ]]; then
  echo "==== Prueba de conexión a Shopify ===="
  python - <<PYCODE || { [[ "$FAIL_ON_SHOPIFY_CHECK" == "1" ]] && exit 1 || echo "WARN: Falla en check Shopify, continuando..."; }
import time, sys
import requests

shop = "${SHOPIFY_SHOP_DOMAIN}"
retries = int("${SHOPIFY_CHECK_RETRIES}")
timeout = int("${SHOPIFY_CHECK_TIMEOUT}")

def try_get(url):
    try:
        r = requests.get(url, timeout=timeout)
        print(f"OK {url} -> {r.status_code}")
        return True
    except Exception as e:
        print(f"ERR {url}: {e}")
        return False

ok = try_get("https://shopify.com")
if not ok:
    for i in range(retries):
        time.sleep(1*(i+1))
        if try_get("https://shopify.com"):
            ok = True
            break

shop_ok = try_get(f"https://{shop}")
if not shop_ok:
    for i in range(retries):
        time.sleep(1*(i+1))
        if try_get(f"https://{shop}"):
            shop_ok = True
            break

sys.exit(0 if (ok and shop_ok) else 1)
PYCODE
fi

# ===== Iniciar aplicación =====
echo "==== Iniciando aplicación ===="
EXTRA_ARGS="--host 0.0.0.0 --port 8000 --log-level ${APP_LOG_LEVEL}"
if [[ "${APP_ACCESS_LOG}" != "1" ]]; then
  EXTRA_ARGS="${EXTRA_ARGS} --no-access-log"
fi

# En prod: sin --reload para no spamear logs ni duplicar procesos
exec uvicorn app.main:app ${EXTRA_ARGS}
