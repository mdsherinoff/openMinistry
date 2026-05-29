from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional

from database.config import get_db
from database.models.statement import Statement
from database.models.minister import Minister
from database.models.user import User
from api.auth import require_moderator
from api.schemas.statement import StatementResponse, StatementUpdate

router = APIRouter(prefix="/api/statements", tags=["statements"])


@router.get("/", response_model=list[StatementResponse])
def list_statements(
    status: Optional[str] = "approved",
    minister_id: Optional[int] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Public endpoint — list approved statements."""
    query = db.query(Statement)

    if status:
        query = query.filter(Statement.status == status)
    if minister_id:
        query = query.filter(Statement.minister_id == minister_id)
    if topic:
        query = query.filter(Statement.topic == topic)

    return query.order_by(
        Statement.statement_date.desc()
    ).offset(offset).limit(limit).all()


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


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    """Public endpoint — get statement statistics."""
    from nlp.statement_store import StatementStore
    store = StatementStore()
    return store.get_queue_stats(db)


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