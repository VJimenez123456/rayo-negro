# Usamos una imagen más completa en lugar de slim
FROM python:3.11-bullseye

# Establece el directorio de trabajo
WORKDIR /app

# Instalamos herramientas esenciales para manejar certificados
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    openssl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Actualiza los certificados del sistema
RUN update-ca-certificates --fresh

# Copia el archivo de dependencias y el script de inicio
COPY requirements.txt start.sh ./

# Asegura que el script tiene permisos de ejecución
RUN chmod +x /app/start.sh

# Actualiza pip e instala las dependencias
RUN pip install --no-cache-dir --upgrade pip setuptools wheel \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir --upgrade certifi

# Configura variables de entorno para SSL
ENV SSL_CERT_DIR=/etc/ssl/certs
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

# Crea un script de verificación para certificados
RUN echo '#!/usr/bin/env python\n\
import requests\n\
import certifi\n\
import ssl\n\
print("Python SSL version:", ssl.OPENSSL_VERSION)\n\
print("Certifi path:", certifi.where())\n\
print("Testing SSL connection...")\n\
try:\n\
    resp = requests.get("https://shopify.com", timeout=5)\n\
    print("Connection test successful:", resp.status_code)\n\
except Exception as e:\n\
    print("Connection test failed:", e)\n\
' > /usr/local/bin/check-ssl && chmod +x /usr/local/bin/check-ssl

# Verifica que la configuración SSL funciona
RUN /usr/local/bin/check-ssl

# Copia el código de la aplicación
COPY app/ app/

# Expone el puerto de la aplicación
EXPOSE 8000

# Usa el script de inicio como comando
CMD ["bash", "/app/start.sh"]