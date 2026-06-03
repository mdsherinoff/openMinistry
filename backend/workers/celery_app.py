import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from celery import Celery
from celery.schedules import crontab
from dotenv import load_dotenv
load_dotenv()

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "openministry",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.tasks"],
)

celery_app.conf.update(
    # Timezone
    timezone="Asia/Kolkata",
    enable_utc=True,

    # Task settings
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    task_acks_late=True,

    # Result expiry
    result_expires=3600,  # 1 hour

    # Retry settings
    task_max_retries=3,
    task_default_retry_delay=60,  # 1 minute

    # Scheduled tasks
    beat_schedule={
        # "scrape-the-hindu-every-30-minutes": {
        #     "task": "workers.tasks.scrape_source",
        #     "schedule": 30 * 60,  # every 30 minutes
        #     "args": ["thehindu.com"],
        # },
        # "scrape-mathrubhumi-every-15-minutes": {
        #     "task": "workers.tasks.scrape_source",
        #     "schedule": 15 * 60,  # every 15 minutes
        #     "args": ["mathrubhumi.com"],
        # },
        # "scrape-manorama-every-15-minutes": {
        #     "task": "workers.tasks.scrape_source",
        #     "schedule": 15 * 60,
        #     "args": ["onmanorama.com"],
        # },
        "collect-urls-every-30-minutes": {
        "task": "workers.tasks.collect_urls",
        "schedule": 30 * 60,
        "args": ["thehindu.com"],
        },
        "tag-statements-every-hour": {
            "task": "workers.tasks.tag_statements",
            "schedule": 60 * 60,
        },
        "run-miner-every-30-minutes": {
            "task": "workers.tasks.run_miner",
            "schedule": 30 * 60,
            "args": ["thehindu", 20],
        },
        "clean-articles-every-hour": {
            "task": "workers.tasks.clean_articles",
            "schedule": 60 * 60,  # every hour
        },
        "detect-ministers-every-hour": {
            "task": "workers.tasks.detect_ministers",
            "schedule": 60 * 60,
        },
        "run-pipeline-every-2-hours": {
            "task": "workers.tasks.run_statement_pipeline",
            "schedule": 2 * 60 * 60,
        },
        "tag-statements-every-hour": {
            "task": "workers.tasks.tag_statements",
            "schedule": 60 * 60,
        },
    },
)