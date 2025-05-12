#!/bin/bash

echo "Verificando configuración SSL..."
/usr/local/bin/check-ssl

echo "==== Información de certificados ===="
ls -la /etc/ssl/certs | wc -l
echo "Certificados disponibles en el sistema"

echo "==== Configuración del entorno ===="
echo "SSL_CERT_DIR: $SSL_CERT_DIR"
echo "SSL_CERT_FILE: $SSL_CERT_FILE"
echo "REQUESTS_CA_BUNDLE: $REQUESTS_CA_BUNDLE"

echo "==== Prueba de conexión a Shopify ===="
python -c "
import requests
import ssl
import certifi
print('Python SSL version:', ssl.OPENSSL_VERSION)
print('Certifi path:', certifi.where())
try:
    resp = requests.get('https://shopify.com', timeout=5)
    print('Conexión exitosa a shopify.com:', resp.status_code)

    # Intentar conexión a la API de Shopify (reemplaza con tu URL real)
    shop_url = 'rayo-negro-mx.myshopify.com'
    print(f'Intentando conexión a {shop_url}...')
    test_resp = requests.get(f'https://{shop_url}', timeout=5)
    print(f'Conexión exitosa a {shop_url}:', test_resp.status_code)
except Exception as e:
    print('Error de conexión:', e)
"

echo "==== Iniciando aplicación ===="
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
