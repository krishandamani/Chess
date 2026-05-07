import os

import sentry_sdk
from celery import Celery
from dotenv import load_dotenv

load_dotenv()

sentry_dsn = os.getenv("SENTRY_DSN", "")
if sentry_dsn:
    sentry_sdk.init(dsn=sentry_dsn, environment=os.getenv("ENVIRONMENT", "development"))

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")

celery_app = Celery(
    "chess_worker",
    broker=redis_url,
    backend=redis_url,
    include=[
        "tasks.ingest",
        "tasks.analyze",
        "tasks.patterns",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    # Route CPU-heavy analysis to a dedicated queue
    task_routes={
        "tasks.analyze.*": {"queue": "analysis"},
        "tasks.ingest.*": {"queue": "ingest"},
        "tasks.patterns.*": {"queue": "ingest"},
    },
)
