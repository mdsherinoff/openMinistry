from fastapi import APIRouter, Depends
from database.models.user import User
from api.auth import require_admin, require_moderator

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


@router.post("/scrape/{source_key}")
def trigger_scrape(
    source_key: str,
    _: User = Depends(require_admin),
):
    """Manually trigger a scrape for a specific source."""
    from workers.tasks import scrape_source
    task = scrape_source.delay(source_key)
    return {
        "message": f"Scrape triggered for {source_key}",
        "task_id": str(task.id),
    }


@router.post("/scrape-all")
def trigger_scrape_all(
    _: User = Depends(require_admin),
):
    """Manually trigger scraping for all sources."""
    from workers.tasks import scrape_all_sources
    task = scrape_all_sources.delay()
    return {
        "message": "Scraping triggered for all sources",
        "task_id": str(task.id),
    }


@router.post("/clean")
def trigger_clean(
    _: User = Depends(require_moderator),
):
    """Manually trigger article cleaning."""
    from workers.tasks import clean_articles
    task = clean_articles.delay()
    return {
        "message": "Cleaning task triggered",
        "task_id": str(task.id),
    }


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

@router.post("/detect")
def trigger_detection(
    _: User = Depends(require_moderator),
):
    """Run name detection on all cleaned articles."""
    from workers.tasks import detect_ministers
    task = detect_ministers.delay()
    return {
        "message": "Detection task triggered",
        "task_id": str(task.id),
    }

@router.post("/pipeline")
def trigger_pipeline(
    _: User = Depends(require_moderator),
):
    """Trigger the full statement extraction pipeline."""
    from workers.tasks import run_statement_pipeline
    task = run_statement_pipeline.delay()
    return {
        "message": "Statement pipeline triggered",
        "task_id": str(task.id),
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