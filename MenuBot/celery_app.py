from celery import Celery

celery_app = Celery("menu-bot")
celery_app.config_from_object("django.conf:settings", namespace="CELERY")
celery_app.autodiscover_tasks()
celery_app.conf.beat_schedule = {}
