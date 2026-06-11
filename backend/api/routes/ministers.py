from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from database.config import get_db
from database.models.minister import Minister
from database.models.user import User
from api.auth import require_admin, require_moderator
from api.schemas.minister import MinisterCreate, MinisterUpdate, MinisterResponse

router = APIRouter(prefix="/api/ministers", tags=["ministers"])


@router.get("/", response_model=list[MinisterResponse])
def list_ministers(
    active_only: bool = True,
    db: Session = Depends(get_db),
):
    """Public endpoint — list all ministers."""
    query = db.query(Minister)
    if active_only:
        query = query.filter(Minister.is_active == 1)
    return query.order_by(Minister.name).all()

@router.post("/", response_model=MinisterResponse)
def create_minister(
    payload: MinisterCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — create a new minister."""
    minister = Minister(**payload.model_dump())
    db.add(minister)
    db.commit()
    db.refresh(minister)
    return minister


@router.patch("/{minister_id}", response_model=MinisterResponse)
def update_minister(
    minister_id: int,
    payload: MinisterUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — update minister details."""
    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(minister, field, value)
    db.commit()
    db.refresh(minister)
    return minister


@router.delete("/{minister_id}")
def delete_minister(
    minister_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    """Admin only — delete a minister."""
    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")
    db.delete(minister)
    db.commit()
    return {"message": "Minister deleted"}

@router.get("/{minister_id}/statements")
def get_minister_statements(
    minister_id: int,
    status: str = "approved",
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    order: str = "desc",
    db: Session = Depends(get_db),
):
    print(f"DEBUG order={order}")
    """Get all statements for a specific minister."""
    from database.models.statement import Statement
    from database.models.article import Article
    from database.models.source import Source

    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")

    query = db.query(Statement).filter(
        Statement.minister_id == minister_id,
        Statement.status == status,
    )

    total = query.count()
    sort = (
    Statement.statement_date.asc().nullslast()
    if order == "asc"
    else Statement.statement_date.desc().nullslast())
    statements = query.order_by(sort).offset(offset).limit(limit).all()

    results = []
    for stmt in statements:
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
            "text": stmt.statement_text,        # was "statement_text"
            "topic": stmt.topic,
            "confidence_score": stmt.confidence_score,
            "date": stmt.statement_date.isoformat()  # was "statement_date"
                if stmt.statement_date else None,
            "status": stmt.status,
            "minister": {
                "id": minister.id,
                "name": minister.name,
                "portfolio": minister.portfolio,
                "image_url": minister.image_url,
            },
            "source": {
                "name": source.name if source else None,
                "url": article.url if article else None,
                "title": article.title if article else None,
                "published_at": article.published_at.isoformat()
                    if article and article.published_at else None,
            },
        })

    return {
        "minister": {
            "id": minister.id,
            "name": minister.name,
            "name_malayalam": minister.name_malayalam,
            "portfolio": minister.portfolio,
            "image_url": minister.image_url,
            "party": minister.party,
            "constituency": minister.constituency,
            "bio": minister.bio,
            "is_active": minister.is_active,
        },
        "total": total,
        "offset": offset,
        "limit": limit,
        "statements": results,
    }


@router.get("/{minister_id}/stats")
def get_minister_stats(
    minister_id: int,
    db: Session = Depends(get_db),
):
    """Get statement statistics for a minister."""
    from database.models.statement import Statement
    from sqlalchemy import func

    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")

    total = db.query(Statement).filter(
        Statement.minister_id == minister_id,
        Statement.status == "approved",
    ).count()

    # Topic breakdown
    topics = db.query(
        Statement.topic,
        func.count(Statement.id).label("count")
    ).filter(
        Statement.minister_id == minister_id,
        Statement.status == "approved",
        Statement.topic.isnot(None),
    ).group_by(Statement.topic).order_by(
        func.count(Statement.id).desc()
    ).limit(5).all()

    return {
        "total_statements": total,
        "topics": [
            {"topic": t, "count": c} for t, c in topics
        ],
    }

@router.get("/{minister_id}", response_model=MinisterResponse)
def get_minister(
    minister_id: int,
    db: Session = Depends(get_db),
):
    """Public endpoint — get a single minister."""
    minister = db.query(Minister).filter(
        Minister.id == minister_id
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")
    return minister