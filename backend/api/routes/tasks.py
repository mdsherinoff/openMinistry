import os

from fastapi import APIRouter, Depends
from database.models.user import User
from api.auth import require_moderator

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("/status/{task_id}")
def get_task_status(
    task_id: str,
    _: User = Depends(require_moderator),
):
    """Check the status of a running task."""
    from workers.celery_app import celery_app
    task = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": task.status,
        "result": str(task.result) if task.ready() else None,
    }

@router.post("/collect-urls")
def trigger_url_collection(
    source_key: str = "thehindu.com",
    _: User = Depends(require_moderator),
):
    """Manually trigger URL collection for a source."""
    from workers.tasks import collect_urls
    task = collect_urls.delay(source_key)
    return {
        "message": f"URL collection triggered for {source_key}",
        "task_id": str(task.id),
    }

@router.get("/miner/health")
def check_miner_health(_: User = Depends(require_moderator)):
    """Check if the open-ministry-miner service is available."""
    from nlp.miner_client import is_miner_available
    available = is_miner_available()
    return {
        "available": available,
        "miner_url": os.environ.get("MINER_URL", "http://miner:8001"),
    }
