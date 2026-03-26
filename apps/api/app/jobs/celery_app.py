"""
הגדרת אפליקציית Celery עבור משימות רקע של מנוע COGNET LDI.
בחירה: Celery (על פני Dramatiq) בזכות אקוסיסטם בוגר ותמיכה ב-Redis broker.
"""
from celery import Celery
import os

# כתובת Redis broker מתוך משתני סביבה
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "cognet_jobs",
    broker=REDIS_URL,
    backend=REDIS_URL,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    # מניעת הרצות חוזרות יקרות
    broker_transport_options={"visibility_timeout": 3600},
)

# גילוי אוטומטי של משימות מתוך מודול jobs
celery_app.autodiscover_tasks(["app.jobs"])
