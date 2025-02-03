import base64
import hmac
import hashlib
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import settings


class VerifyWebhookMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        hmac_header = request.headers.get("X-Shopify-Hmac-SHA256")
        if not hmac_header:
            return JSONResponse(
                {"error": "Encabezado 'X-Shopify-Hmac-SHA256' faltante"},
                status_code=401
            )
        body = await request.body()
        secret = settings.SHOPIFY_SECRET.encode("utf-8")
        calculated_hmac = base64.b64encode(
            hmac.new(secret, body, hashlib.sha256).digest()
        ).decode("utf-8")
        print("calculated_hmac", calculated_hmac, "hmac_header", hmac_header)
        print("calculated_hmac == hmac_header", calculated_hmac == hmac_header)
        if calculated_hmac != hmac_header:
            return JSONResponse(
                {"error": "Firma HMAC inválida"}, status_code=401
            )
        return await call_next(request)
