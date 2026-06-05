from fastapi import APIRouter, Depends, Query, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional

from database.config import get_db
from database.models.statement import Statement
from database.models.minister import Minister
from database.models.article import Article
from database.models.source import Source

router = APIRouter(prefix="/api/search", tags=["search"])


def build_statement_result(stmt, db: Session) -> dict:
    """Build full result object for a statement."""
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

    return {
        "id": stmt.id,
        "statement_text": stmt.statement_text,
        "topic": stmt.topic,
        "statement_date": stmt.statement_date.isoformat()
            if stmt.statement_date else None,
        "minister": {
            "id": minister.id if minister else None,
            "name": minister.name if minister else "Unknown",
            "portfolio": minister.portfolio if minister else None,
            "image_url": minister.image_url if minister else None,
        },
        "source": {
            "name": source.name if source else None,
            "url": article.url if article else None,
            "title": article.title if article else None,
        },
    }

limiter = Limiter(key_func=get_remote_address)

@router.get("/")
@limiter.limit("30/minute")
def search(
    request: Request,
    q: str = Query(..., min_length=2),
    minister_id: Optional[int] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """
    Full-text search across approved statements.
    """
    results = []
    total = 0
    query_clean = q.strip()

    if not query_clean:
        return {"total": 0, "results": [], "query": q}

    try:
        query = db.query(Statement).join(
            Minister, Statement.minister_id == Minister.id
        ).filter(
            Statement.status == "approved",
        ).filter(
            (Statement.statement_text.ilike(f"%{query_clean}%")) |
            (Minister.name.ilike(f"%{query_clean}%")) |
            (Minister.portfolio.ilike(f"%{query_clean}%")) |
            (Statement.topic.ilike(f"%{query_clean}%"))
        )

        if minister_id:
            query = query.filter(Statement.minister_id == minister_id)
        if topic:
            query = query.filter(Statement.topic == topic)

        total = query.count()
        statements = query.order_by(
            Statement.statement_date.desc().nullslast()
        ).offset(offset).limit(limit).all()

        results = [build_statement_result(s, db) for s in statements]

    except Exception as e:
        db.rollback()
        return {"total": 0, "results": [], "query": q, "error": str(e)}

    return {
        "total": total,
        "query": q,
        "results": results,
        "offset": offset,
        "limit": limit,
    }

@router.get("/ministers")
def search_ministers(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """Search ministers by name, portfolio, or constituency."""
    query_clean = q.strip()

    ministers = db.query(Minister).filter(
        Minister.is_active == 1,
        (
            Minister.name.ilike(f"%{query_clean}%") |
            Minister.portfolio.ilike(f"%{query_clean}%") |
            Minister.constituency.ilike(f"%{query_clean}%") |
            Minister.party.ilike(f"%{query_clean}%")
        )
    ).order_by(Minister.name).limit(20).all()

    return [
        {
            "id": m.id,
            "name": m.name,
            "portfolio": m.portfolio,
            "constituency": m.constituency,
            "party": m.party,
        }
        for m in ministers
    ]

@router.get("/suggestions")
def get_suggestions(
    q: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
):
    """
    Get search suggestions — minister names and topics
    that match the query.
    """
    query_clean = q.strip()
    suggestions = []

    # Minister name suggestions
    ministers = db.query(Minister.name).filter(
        Minister.is_active == 1,
        Minister.name.ilike(f"%{query_clean}%"),
    ).limit(5).all()

    for (name,) in ministers:
        suggestions.append({
            "type": "minister",
            "label": name,
            "value": name,
        })

    # Topic suggestions
    topics = db.query(Statement.topic).filter(
        Statement.status == "approved",
        Statement.topic.isnot(None),
        Statement.topic.ilike(f"%{query_clean}%"),
    ).distinct().limit(5).all()

    for (topic,) in topics:
        if topic:
            suggestions.append({
                "type": "topic",
                "label": topic,
                "value": topic,
            })

    return suggestions
