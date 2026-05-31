from fastapi import APIRouter, Depends, HTTPException, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from typing import Optional

from database.config import get_db
from database.models.statement import Statement
from database.models.minister import Minister
from database.models.user import User
from api.auth import require_moderator
from api.schemas.statement import StatementResponse, StatementUpdate

router = APIRouter(prefix="/api/statements", tags=["statements"])
limiter = Limiter(key_func=get_remote_address)

@router.get("/", response_model=list[dict])
@limiter.limit("60/minute")
def list_statements(
    request: Request,
    status: Optional[str] = "approved",
    minister_id: Optional[int] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Public endpoint — list approved statements with full context."""
    from database.models.minister import Minister
    from database.models.article import Article
    from database.models.source import Source

    query = db.query(Statement)

    if status:
        query = query.filter(Statement.status == status)
    if minister_id:
        query = query.filter(Statement.minister_id == minister_id)
    if topic:
        query = query.filter(Statement.topic == topic)

    statements = query.order_by(
        Statement.statement_date.desc(),
        Statement.created_at.desc(),
    ).offset(offset).limit(limit).all()

    results = []
    for stmt in statements:
        minister = db.query(Minister).filter(
            Minister.id == stmt.minister_id
        ).first()
        article = db.query(Article).filter(
            Article.id == stmt.article_id
        ).first()
        source = None
        if article:
            source = db.query(Source).filter(
                Source.id == article.source_id
            ).first()

        results.append({
            "id": stmt.id,
            "statement_text": stmt.statement_text,
            "statement_summary": stmt.statement_summary,
            "topic": stmt.topic,
            "confidence_score": stmt.confidence_score,
            "statement_date": stmt.statement_date.isoformat()
                if stmt.statement_date else None,
            "status": stmt.status,
            "created_at": stmt.created_at.isoformat(),
            "minister": {
                "id": minister.id if minister else None,
                "name": minister.name if minister else "Unknown",
                "portfolio": minister.portfolio if minister else None,
            },
            "source": {
                "name": source.name if source else None,
                "url": article.url if article else None,
                "title": article.title if article else None,
                "published_at": article.published_at.isoformat()
                    if article and article.published_at else None,
            },
        })

    return results


@router.get("/count")
@limiter.limit("60/minute")
def get_statement_count(
    request: Request,
    status: Optional[str] = "approved",
    minister_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get total count of statements."""
    query = db.query(Statement)
    if status:
        query = query.filter(Statement.status == status)
    if minister_id:
        query = query.filter(Statement.minister_id == minister_id)
    return {"count": query.count()}

@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Public endpoint — get statement statistics."""
    from nlp.statement_store import StatementStore
    store = StatementStore()
    return store.get_queue_stats(db)

@router.get("/topics")
@limiter.limit("60/minute")
def get_topics(
    request: Request,
    db: Session = Depends(get_db)
):
    """Get all available topics with statement counts."""
    from nlp.tagging_service import get_topic_stats
    return get_topic_stats(db)

@router.post("/tag-all")
def tag_all_statements(
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Tag all untagged statements with topics."""
    from nlp.tagging_service import tag_pending_statements
    result = tag_pending_statements(db)
    return result

@router.get("/pending", response_model=list[StatementResponse])
def list_pending(
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Moderator only — list pending statements."""
    return db.query(Statement).filter(
        Statement.status == "pending"
    ).order_by(
        Statement.created_at.desc()
    ).offset(offset).limit(limit).all()

@router.get("/{statement_id}", response_model=StatementResponse)
def get_statement(
    statement_id: int,
    db: Session = Depends(get_db),
):
    """Get a single statement."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    return statement

@router.patch("/{statement_id}", response_model=StatementResponse)
def update_statement(
    statement_id: int,
    payload: StatementUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_moderator),
):
    """Moderator only — update a statement."""
    statement = db.query(Statement).filter(
        Statement.id == statement_id
    ).first()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(statement, field, value)
    db.commit()
    db.refresh(statement)
    return statement