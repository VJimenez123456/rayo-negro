from celery import Celery
from celery.schedules import crontab
import os

BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
TIMEZONE = os.getenv("CELERY_TIMEZONE", "America/Mexico_City")
TIMEZONE = "America/Bogota"

celery = Celery(
    "rayo_negro",
    broker=BROKER_URL,
    backend=RESULT_BACKEND,
    include=["app.tasks.daily"],
)

celery.conf.update(
    task_track_started=True,
    timezone="America/Bogota",
    enable_utc=False,
    # si NO usas rutas/colas personalizadas, la cola por defecto es "celery"
    task_default_queue="celery",
    worker_hijack_root_logger=False,  # para ver bien tus logs
    worker_log_format="%(asctime)s %(levelname)s [%(processName)s] %(name)s: %(message)s",
    worker_task_log_format="%(asctime)s %(levelname)s [%(processName)s] %(name)s[%(task_name)s:%(task_id)s]: %(message)s",
)

# Programación periódica (Beat)
celery.conf.beat_schedule = {
    "update-inventory": {
        "task": "app.tasks.daily.tarea_diaria",
        "schedule": crontab(minute=32, hour=2),
        "options": {"queue": "default"},
    }
}
