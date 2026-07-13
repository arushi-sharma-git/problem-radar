from celery import Celery

app = Celery(
    "problem_radar",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

app.conf.imports = ["tasks"]

from celery.schedules import crontab

app.conf.beat_schedule = {
    "run-ingestion-every-30-minutes": {
        "task": "tasks.run_ingestion",
        "schedule": crontab(minute="*/30"),
    },
}