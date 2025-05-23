from fastapi import FastAPI
# from apscheduler.schedulers.background import BackgroundScheduler
# from app.core.middleware import VerifyWebhookMiddleware
from app.apps.products.routers import router as products_router
from app.apps.orders.routers import router as orders_router
from app.apps.locations.routers import router as location_router
from app.apps.inventories.routers import router as inventory_router
from app.apps.system.routers import router as system_router
# from datetime import datetime


app = FastAPI(
    title="Shopify Integration",
    description="Proyecto modular para Shopify",
    version="1.0.0"
)

# scheduler = BackgroundScheduler()

# Global middleware
# app.add_middleware(VerifyWebhookMiddleware)

# routes
app.include_router(products_router, prefix="/products", tags=["Products"])
app.include_router(orders_router, prefix="/orders", tags=["Orders"])
app.include_router(location_router, prefix="/locations", tags=["Locations"])
app.include_router(inventory_router, prefix="/inventories", tags=["Inventories"])  # noqa
app.include_router(system_router, prefix="/system", tags=["System"])


# # inventarios
# print("datetime->", datetime.now())
# scheduler.add_job(update_inventory, "cron", hour=4, minute=36)


# # start and down scheduler
# async def startup_event():
#     scheduler.start()
# app.add_event_handler("startup", startup_event)


# async def shutdown_event():
#     scheduler.shutdown()
# app.add_event_handler("shutdown", shutdown_event)
