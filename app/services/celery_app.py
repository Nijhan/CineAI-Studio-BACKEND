from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "cineai",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.services.tasks"],
)
celery_app.conf.task_track_started = True
celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
