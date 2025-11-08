from app.core.celery_app import celery

@celery.task(name="app.tasks.daily.tarea_diaria", bind=True, max_retries=3)
def tarea_diaria(self):
    # tu lógica real
    # ejemplo:
    #   - generar un reporte
    #   - llamar una API
    #   - limpiar cachés
    return {"status": "ok"}
