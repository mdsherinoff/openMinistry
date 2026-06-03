import hashlib
import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.config import get_db
from database.models.article_queue import ArticleQueue
from database.models.mined_result import MinedResult
from database.models.minister import Minister
from database.models.statement import Statement
from database.models.user import User
from api.auth import get_current_user, require_moderator
from api.schemas.queue import (
    QueueItemCreate,
    QueueItemResponse,
    MinedResultResponse,
    MinedResultUpdate,
    ApproveStatementRequest,
    NewStatementRequest,
)

router = APIRouter(prefix="/api/queue", tags=["queue"])
logger = logging.getLogger(__name__)


def make_url_hash(url: str) -> str:
    return hashlib.sha256(url.strip().lower().split("?")[0].encode()).hexdigest()


# ─────────────────────────────────────────
# Queue Management
# ─────────────────────────────────────────

@router.post("/articles", response_model=QueueItemResponse)
def add_to_queue(
    payload: QueueItemCreate,
    db: Session = Depends(get_db),
):
    """Submit a URL to the moderation queue."""
    url_hash = make_url_hash(payload.url)

    existing = db.query(ArticleQueue).filter(
        ArticleQueue.url_hash == url_hash
    ).first()
    if existing:
        return existing

    item = ArticleQueue(
        url=payload.url,
        url_hash=url_hash,
        title=payload.title,
        source_name=payload.source_name,
        published_at=payload.published_at,
        language=payload.language,
        status="pending_review",
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/pending", response_model=list[QueueItemResponse])
def get_pending(
    status: Optional[str] = "pending_review",
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Get queue items by status."""
    query = db.query(ArticleQueue)
    if status:
        query = query.filter(ArticleQueue.status == status)
    return query.order_by(
        ArticleQueue.created_at.desc()
    ).offset(offset).limit(limit).all()


@router.get("/stats")
def get_queue_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Get queue statistics."""
    from sqlalchemy import func
    stats = {}
    for status in [
        "pending_review", "mining", "mined",
        "rejected", "deleted"
    ]:
        stats[status] = db.query(ArticleQueue).filter(
            ArticleQueue.status == status
        ).count()
    return stats


@router.get("/{item_id}", response_model=QueueItemResponse)
def get_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")
    return item


@router.post("/{item_id}/mine")
def approve_for_mining(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Approve a URL for mining — triggers async Celery task."""
    item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    if item.status not in ("pending_review", "mining_failed"):
        raise HTTPException(
            status_code=400,
            detail=f"Cannot mine item with status: {item.status}"
        )

    # Update status
    item.status = "mining"
    item.reviewed_by = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    # Trigger async mining task
    from workers.tasks import mine_queue_item
    task = mine_queue_item.delay(item_id)

    return {
        "message": "Mining started",
        "item_id": item_id,
        "task_id": str(task.id),
    }


@router.post("/mine-batch")
def mine_batch(
    item_ids: list[int],
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Approve multiple URLs for mining simultaneously."""
    results = []
    for item_id in item_ids:
        item = db.query(ArticleQueue).filter(
            ArticleQueue.id == item_id
        ).first()
        if not item:
            results.append({"id": item_id, "error": "not found"})
            continue
        if item.status not in ("pending_review", "mining_failed"):
            results.append({"id": item_id, "error": f"wrong status: {item.status}"})
            continue

        item.status = "mining"
        item.reviewed_by = current_user.id
        item.reviewed_at = datetime.now(timezone.utc)
        db.commit()

        from workers.tasks import mine_queue_item
        task = mine_queue_item.delay(item_id)
        results.append({"id": item_id, "task_id": str(task.id)})

    return {"results": results}


@router.post("/{item_id}/reject")
def reject_queue_item(
    item_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Reject a URL — keeps it for audit."""
    item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    item.status = "rejected"
    item.reviewed_by = current_user.id
    item.reviewed_at = datetime.now(timezone.utc)
    item.review_notes = notes
    db.commit()

    return {"message": "Item rejected", "item_id": item_id}


@router.delete("/{item_id}")
def delete_queue_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Permanently delete a queue item (admin action)."""
    item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    db.delete(item)
    db.commit()
    return {"message": "Item deleted permanently"}


# ─────────────────────────────────────────
# Mined Results
# ─────────────────────────────────────────

@router.get("/{item_id}/mined", response_model=list[MinedResultResponse])
def get_mined_results(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Get all extracted statements for a queue item."""
    item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    return db.query(MinedResult).filter(
        MinedResult.queue_item_id == item_id
    ).all()


@router.patch("/{item_id}/mined/{result_id}")
def update_mined_result(
    item_id: int,
    result_id: int,
    payload: MinedResultUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Edit a mined result before approving."""
    result = db.query(MinedResult).filter(
        MinedResult.id == result_id,
        MinedResult.queue_item_id == item_id,
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    return result


@router.post("/{item_id}/mined/{result_id}/approve")
def approve_mined_result(
    item_id: int,
    result_id: int,
    payload: ApproveStatementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Approve a single mined result — creates a public statement."""
    result = db.query(MinedResult).filter(
        MinedResult.id == result_id,
        MinedResult.queue_item_id == item_id,
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    queue_item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()

    # Use edited values if available, else original
    final_text = (
        payload.statement_text
        or result.edited_statement_text
        or result.statement_text
    )
    final_minister_id = (
        payload.minister_id
        or result.minister_id
    )
    final_topic = (
        payload.topic
        or result.edited_topic
        or result.topic_tag
    )

    if not final_minister_id:
        raise HTTPException(
            status_code=400,
            detail="Minister must be assigned before approving"
        )

    # Find article if exists
    from database.models.article import Article
    article = db.query(Article).filter(
        Article.url == queue_item.url
    ).first()

    # Create the public statement
    statement = Statement(
        minister_id=final_minister_id,
        article_id=article.id if article else None,
        statement_text=final_text,
        topic=final_topic,
        context_text=payload.context_text or result.context_description,
        queue_item_id=item_id,
        confidence_score=result.confidence_stars / 5.0,
        status="approved",
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(statement)
    db.flush()

    # Link back
    result.statement_id = statement.id
    result.status = "approved"
    result.reviewed_by = current_user.id
    result.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "message": "Statement approved and published",
        "statement_id": statement.id,
    }


@router.post("/{item_id}/mined/{result_id}/reject")
def reject_mined_result(
    item_id: int,
    result_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Reject a single mined result."""
    result = db.query(MinedResult).filter(
        MinedResult.id == result_id,
        MinedResult.queue_item_id == item_id,
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="Result not found")

    result.status = "rejected"
    result.reviewed_by = current_user.id
    result.reviewed_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Result rejected"}


@router.post("/{item_id}/statements/add")
def add_manual_statement(
    item_id: int,
    payload: NewStatementRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Manually add a statement the miner missed."""
    queue_item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not queue_item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    from database.models.article import Article
    article = db.query(Article).filter(
        Article.url == queue_item.url
    ).first()

    statement = Statement(
        minister_id=payload.minister_id,
        article_id=article.id if article else None,
        statement_text=payload.statement_text,
        topic=payload.topic,
        context_text=payload.context_text,
        queue_item_id=item_id,
        confidence_score=1.0,  # manually added = highest confidence
        status="approved",
        reviewed_by=current_user.id,
        reviewed_at=datetime.now(timezone.utc),
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)

    return {
        "message": "Statement added manually",
        "statement_id": statement.id,
    }


@router.get("/{item_id}/status")
def get_mining_status(
    item_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Poll mining progress."""
    item = db.query(ArticleQueue).filter(
        ArticleQueue.id == item_id
    ).first()
    if not item:
        raise HTTPException(status_code=404, detail="Queue item not found")

    mined_count = db.query(MinedResult).filter(
        MinedResult.queue_item_id == item_id
    ).count()

    return {
        "id": item_id,
        "status": item.status,
        "statements_found": item.statements_found,
        "mined_results": mined_count,
        "mining_error": item.mining_error,
        "mining_started_at": item.mining_started_at,
        "mining_completed_at": item.mining_completed_at,
    }