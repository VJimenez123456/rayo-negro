from fastapi import FastAPI
# from app.core.middleware import VerifyWebhookMiddleware
from app.apps.products.routers import router as products_router
from app.apps.orders.routers import router as orders_router
from app.apps.locations.routers import router as location_router
from app.apps.inventories.routers import router as inventory_router


app = FastAPI(
    title="Shopify Integration",
    description="Proyecto modular para Shopify",
    version="1.0.0"
)

# Global middleware
# app.add_middleware(VerifyWebhookMiddleware)

# routes
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(location_router, prefix="/locations", tags=["Locations"])
app.include_router(inventory_router, prefix="/inventories", tags=["Inventories"])  # noqa
