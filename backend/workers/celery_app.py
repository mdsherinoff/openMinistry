import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from celery import Celery
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
    # URL Collection
    "collect-urls-thehindu-every-30-minutes": {
        "task": "workers.tasks.collect_urls",
        "schedule": 30 * 60,
        "args": ["thehindu.com"],
    },
    # Statement tagging
    "tag-statements-every-hour": {
        "task": "workers.tasks.tag_statements",
        "schedule": 60 * 60,
    },
},
)