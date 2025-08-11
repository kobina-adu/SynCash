"""
Celery application configuration for SyncCash Orchestrator
"""

from celery import Celery
import structlog
from src.config.settings import get_settings

logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

# Create Celery instance
celery_app = Celery(
    "synccash-orchestrator",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "src.tasks.payment_tasks",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    task_routes={
        "src.tasks.payment_tasks.process_payment": {"queue": "payments"},
        "src.tasks.payment_tasks.validate_transaction": {"queue": "validation"},
        "src.tasks.payment_tasks.cleanup_expired_transactions": {"queue": "cleanup"},
    },
    beat_schedule={
        "cleanup-expired-transactions": {
            "task": "src.tasks.payment_tasks.cleanup_expired_transactions",
            "schedule": 300.0,  # Every 5 minutes
        },
        "generate-daily-report": {
            "task": "src.tasks.payment_tasks.generate_daily_report",
            "schedule": 86400.0,  # Every 24 hours
        },
    },
)

if __name__ == "__main__":
    celery_app.start()
