from app.core.celery_app import celery
from celery import shared_task
from celery.utils.log import get_task_logger
from app.apps.system.services import synchronize_inventory_service

logger = get_task_logger(__name__)

@celery.task(name="app.tasks.daily.tarea_diaria", bind=True, max_retries=3)
def tarea_diaria(self):
    # print("here")
    # logger.info("init")
    # synchronize_inventory_service()
    # logger.info("finish")
    return {"status": "ok"}
