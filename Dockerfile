FROM python:3.11-bullseye

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl openssl dos2unix \
 && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN update-ca-certificates --fresh

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir --upgrade certifi

# ... tu base y setup
RUN pip install --no-cache-dir celery[redis]==5.3.6
# opcional: pytz o usar zoneinfo (3.9+ ya trae zoneinfo)

COPY start.sh /usr/local/bin/start.sh
RUN dos2unix /usr/local/bin/start.sh && chmod +x /usr/local/bin/start.sh

# (opcional) carpeta para logs si decides seguir con archivos
RUN mkdir -p /var/log/app

# Script de verificación SSL (lo dejo si te sirve)
RUN echo '#!/usr/bin/env python\n\
import requests, certifi, ssl\n\
print("Python SSL version:", ssl.OPENSSL_VERSION)\n\
print("Certifi path:", certifi.where())\n\
print("Testing SSL connection...")\n\
try:\n\
    resp = requests.get("https://shopify.com", timeout=5)\n\
    print("Connection test successful:", resp.status_code)\n\
except Exception as e:\n\
    print("Connection test failed:", e)\n' \
> /usr/local/bin/check-ssl && chmod +x /usr/local/bin/check-ssl \
 && /usr/local/bin/check-ssl

# Copia solo el código de la app (el volumen lo sobreescribe en dev)
COPY app/ /app/app/

EXPOSE 8000

# Lanza Uvicorn en modo prod (sin reload y sin access log)
CMD ["bash", "-lc", "exec /usr/local/bin/start.sh"]
