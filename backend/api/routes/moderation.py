from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from database.config import get_db
from database.models.statement import Statement
from database.models.minister import Minister
from database.models.article import Article
from database.models.source import Source
from database.models.moderation_log import ModerationLog
from database.models.user import User
from api.auth import get_current_user, require_moderator
from api.schemas.moderation import (
    ModerationAction,
    ModerationLogResponse,
    StatementWithContext,
)

router = APIRouter(prefix="/api/moderation", tags=["moderation"])


def get_statement_with_context(
    statement: Statement, db: Session
) -> dict:
    """Build full context object for a statement."""
    minister = db.query(Minister).filter(
        Minister.id == statement.minister_id
    ).first()

    article = db.query(Article).filter(
        Article.id == statement.article_id
    ).first()

    source = None
    if article:
        source = db.query(Source).filter(
            Source.id == article.source_id
        ).first()

    return {
        "id": statement.id,
        "statement_text": statement.statement_text,
        "statement_summary": statement.statement_summary,
        "topic": statement.topic,
        "confidence_score": statement.confidence_score,
        "statement_date": statement.statement_date,
        "status": statement.status,
        "created_at": statement.created_at,
        # Public flagging
        "flagged": statement.flagged,
        "flag_count": statement.flag_count,
        "flag_reason": statement.flag_reason,
        "flagged_at": statement.flagged_at,
        # Minister
        "minister_id": minister.id if minister else None,
        "minister_name": minister.name if minister else "Unknown",
        "minister_portfolio": minister.portfolio if minister else None,
        # Article
        "article_id": article.id if article else None,
        "article_title": article.title if article else None,
        "article_url": article.url if article else "",
        "article_source": source.name if source else None,
        "article_published_at": article.published_at if article else None,
    }


@router.get("/queue")
def get_review_queue(
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    minister_id: Optional[int] = None,
    min_confidence: Optional[float] = None,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """
    Get pending statements for review.
    Returns statements with full context.
    """
    query = db.query(Statement).filter(
        Statement.status == "pending"
    )

    if minister_id:
        query = query.filter(Statement.minister_id == minister_id)

    if min_confidence:
        query = query.filter(
            Statement.confidence_score >= min_confidence
        )

    total = query.count()
    statements = query.order_by(
        Statement.confidence_score.desc(),
        Statement.created_at.desc(),
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "statements": [
            get_statement_with_context(s, db) for s in statements
        ],
    }


@router.get("/flagged")
def get_flagged_statements(
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """
    Get published statements that the public flagged for re-evaluation.
    Most-flagged and most-recently-flagged first.
    """
    query = db.query(Statement).filter(
        Statement.status == "approved",
        Statement.flagged.is_(True),
    )

    total = query.count()
    statements = query.order_by(
        Statement.flag_count.desc(),
        Statement.flagged_at.desc(),
    ).offset(offset).limit(limit).all()

    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "statements": [
            get_statement_with_context(s, db) for s in statements
        ],
    }


@router.post("/{statement_id}/dismiss-flag")
def dismiss_flag(
    statement_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """
    Dismiss the flag(s) on a statement — the moderator reviewed it and
    decided to keep it published. Clears the flag markers.
    """
    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    statement.flagged = False
    statement.flag_count = 0
    statement.flag_reason = None
    statement.flagged_at = None

    log = ModerationLog(
        statement_id=statement_id,
        reviewer_id=current_user.id,
        action="flag_dismissed",
        notes=notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()

    return {"message": "Flag dismissed", "statement_id": statement_id}


@router.post("/{statement_id}/review")
def review_statement(
    statement_id: int,
    payload: ModerationAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """
    Review a statement — approve, reject, edit, or flag.
    Creates an audit log entry for every action.
    """
    # Validate action
    valid_actions = {"approved", "rejected", "edited", "flagged", "needs_review"}
    if payload.action not in valid_actions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid action. Must be one of: {valid_actions}"
        )

    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    # Store previous text for audit log
    previous_text = statement.statement_text

    # Apply the action
    if payload.action == "edited" and payload.edited_text:
        if len(payload.edited_text.strip()) < 10:
            raise HTTPException(
                status_code=400,
                detail="Edited text too short"
            )
        statement.statement_text = payload.edited_text.strip()
        statement.status = "approved"  # edits auto-approve
    else:
        statement.status = payload.action

    statement.reviewed_by = current_user.id
    statement.reviewed_at = datetime.now(timezone.utc)

    # Create audit log
    log = ModerationLog(
        statement_id=statement_id,
        reviewer_id=current_user.id,
        action=payload.action,
        notes=payload.notes,
        previous_text=previous_text if payload.action == "edited" else None,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()

    return {
        "message": f"Statement {payload.action}",
        "statement_id": statement_id,
        "action": payload.action,
        "reviewed_by": current_user.email,
    }


@router.post("/{statement_id}/approve")
def approve_statement(
    statement_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Quick approve endpoint."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    statement.status = "approved"
    statement.reviewed_by = current_user.id
    statement.reviewed_at = datetime.now(timezone.utc)

    log = ModerationLog(
        statement_id=statement_id,
        reviewer_id=current_user.id,
        action="approved",
        notes=notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()

    return {"message": "Statement approved", "statement_id": statement_id}


@router.post("/{statement_id}/reject")
def reject_statement(
    statement_id: int,
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_moderator),
):
    """Quick reject endpoint."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    statement.status = "rejected"
    statement.reviewed_by = current_user.id
    statement.reviewed_at = datetime.now(timezone.utc)
    # Clear any flags — a rejected statement no longer needs re-evaluation.
    statement.flagged = False
    statement.flag_count = 0
    statement.flag_reason = None
    statement.flagged_at = None

    log = ModerationLog(
        statement_id=statement_id,
        reviewer_id=current_user.id,
        action="rejected",
        notes=notes,
        timestamp=datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()

    return {"message": "Statement rejected", "statement_id": statement_id}


@router.get("/{statement_id}/context")
def get_context(
    statement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Get full context for a statement including original article."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")

    context = get_statement_with_context(statement, db)

    # Also get the article content for side-by-side review
    article = db.query(Article).filter(
        Article.id == statement.article_id
    ).first()

    if article:
        context["article_content"] = (
            article.cleaned_content or article.raw_content or ""
        )[:2000]  # limit to 2000 chars for display

    return context


@router.get("/{statement_id}/logs", response_model=list[ModerationLogResponse])
def get_statement_logs(
    statement_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Get audit log for a statement."""
    return db.query(ModerationLog).filter(
        ModerationLog.statement_id == statement_id
    ).order_by(ModerationLog.timestamp.desc()).all()


@router.get("/stats/overview")
def get_moderation_stats(
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Get moderation statistics overview."""
    total = db.query(Statement).count()
    pending = db.query(Statement).filter(
        Statement.status == "pending"
    ).count()
    approved = db.query(Statement).filter(
        Statement.status == "approved"
    ).count()
    rejected = db.query(Statement).filter(
        Statement.status == "rejected"
    ).count()
    needs_review = db.query(Statement).filter(
        Statement.status == "needs_review"
    ).count()
    flagged = db.query(Statement).filter(
        Statement.status == "approved",
        Statement.flagged.is_(True),
    ).count()

    # Top ministers by pending statements
    from sqlalchemy import func
    top_ministers = db.query(
        Minister.name,
        func.count(Statement.id).label("count")
    ).join(
        Statement, Statement.minister_id == Minister.id
    ).filter(
        Statement.status == "pending"
    ).group_by(
        Minister.name
    ).order_by(
        func.count(Statement.id).desc()
    ).limit(5).all()

    # Recent moderation activity
    recent_logs = db.query(ModerationLog).order_by(
        ModerationLog.timestamp.desc()
    ).limit(10).all()

    return {
        "totals": {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "needs_review": needs_review,
            "flagged": flagged,
            "approval_rate": round(
                approved / total * 100, 1
            ) if total > 0 else 0,
        },
        "top_ministers_pending": [
            {"name": name, "count": count}
            for name, count in top_ministers
        ],
        "recent_activity": [
            {
                "action": log.action,
                "statement_id": log.statement_id,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in recent_logs
        ],
    }