"""
Clean public API endpoints with full documentation.
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from api.cache import get_cached, set_cached

from database.config import get_db
from database.models.statement import Statement
from database.models.minister import Minister
from database.models.article import Article
from database.models.source import Source

router = APIRouter(prefix="/api/v1", tags=["Public API v1"])

def build_statement(stmt: Statement, db: Session) -> dict:
    minister = db.query(Minister).filter(
        Minister.id == stmt.minister_id
    ).first()
    article = db.query(Article).filter(
        Article.id == stmt.article_id
    ).first()
    source = db.query(Source).filter(
        Source.id == article.source_id
    ).first() if article else None

    return {
        "id": stmt.id,
        "text": stmt.statement_text,
        "topic": stmt.topic,
        "context_text": stmt.context_text,
        "queue_item_id": stmt.queue_item_id,
        "date": stmt.statement_date.isoformat()
            if stmt.statement_date else None,
        "minister": {
            "id": minister.id if minister else None,
            "name": minister.name if minister else None,
            "portfolio": minister.portfolio if minister else None,
            "party": minister.party if minister else None,
            "constituency": minister.constituency if minister else None,
            "image_url": minister.image_url if minister else None,
        },
        "source": {
            "publication": source.name if source else None,
            "url": article.url if article else None,
            "title": article.title if article else None,
            "published_at": article.published_at.isoformat()
                if article and article.published_at else None,
        },
        "verified_at": stmt.reviewed_at.isoformat()
            if stmt.reviewed_at else None,
    }

@router.get(
    "/statements",
    summary="List verified statements",
    description="""
Returns a list of verified statements from Kerala ministers and MLAs.

All statements are human-verified before publication.

**Filters:**
- `minister_id` — filter by a specific minister
- `topic` — filter by topic (Health, Education, Transport, etc.)
- `limit` — results per page (max 100)
- `offset` — pagination offset
    """,
)
def list_statements(
    minister_id: Optional[int] = None,
    topic: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    cache_key = f"statements:{minister_id}:{topic}:{limit}:{offset}"
    cached = get_cached(cache_key)
    if cached:
        return cached

    query = db.query(Statement).filter(Statement.status == "approved")
    if minister_id:
        query = query.filter(Statement.minister_id == minister_id)
    if topic:
        query = query.filter(Statement.topic == topic)

    total = query.count()
    statements = query.order_by(
        Statement.statement_date.desc().nullslast()
    ).offset(offset).limit(limit).all()

    result = {
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [build_statement(s, db) for s in statements],
    }

    set_cached(cache_key, result, ttl=300)
    return result

@router.get(
    "/ministers",
    summary="List all ministers and MLAs",
    description="Returns all active members of the 16th Kerala Legislative Assembly.",
)
def list_ministers(
    role: Optional[str] = Query(
        default=None,
        description="Filter by role: 'minister' or 'mla'"
    ),
    db: Session = Depends(get_db),
):
    query = db.query(Minister).filter(Minister.is_active == 1)
    ministers = query.order_by(Minister.name).all()

    results = []
    for m in ministers:
        is_minister = (
            m.portfolio and
            not m.portfolio.startswith("MLA") and
            "Minister" in (m.bio or "")
        )
        member_role = "minister" if is_minister else "mla"

        if role and role.lower() != member_role:
            continue

        results.append({
            "id": m.id,
            "name": m.name,
            "name_malayalam": m.name_malayalam,
            "role": member_role,
            "portfolio": m.portfolio,
            "party": m.party,
            "constituency": m.constituency,
        })

    return {"total": len(results), "results": results}

@router.get(
    "/ministers/{minister_id}",
    summary="Get minister profile with statements",
)
def get_minister(
    minister_id: int,
    limit: int = Query(default=10, le=50),
    db: Session = Depends(get_db),
):
    minister = db.query(Minister).filter(
        Minister.id == minister_id,
        Minister.is_active == 1,
    ).first()
    if not minister:
        raise HTTPException(status_code=404, detail="Minister not found")

    statements = db.query(Statement).filter(
        Statement.minister_id == minister_id,
        Statement.status == "approved",
    ).order_by(
        Statement.statement_date.desc().nullslast()
    ).limit(limit).all()

    total = db.query(Statement).filter(
        Statement.minister_id == minister_id,
        Statement.status == "approved",
    ).count()

    return {
        "id": minister.id,
        "name": minister.name,
        "name_malayalam": minister.name_malayalam,
        "portfolio": minister.portfolio,
        "party": minister.party,
        "constituency": minister.constituency,
        "total_statements": total,
        "recent_statements": [
            build_statement(s, db) for s in statements
        ],
    }

@router.get(
    "/search",
    summary="Search statements",
    description="""
Search across all verified statements by keyword.

Searches statement text, minister names, and topics.
    """,
)
def search(
    q: str = Query(..., min_length=2, description="Search query"),
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    db: Session = Depends(get_db),
):
    query_clean = q.strip()

    query = db.query(Statement).join(
        Minister, Statement.minister_id == Minister.id
    ).filter(
        Statement.status == "approved",
        (
            Statement.statement_text.ilike(f"%{query_clean}%") |
            Minister.name.ilike(f"%{query_clean}%") |
            Statement.topic.ilike(f"%{query_clean}%")
        )
    )

    total = query.count()
    statements = query.order_by(
        Statement.statement_date.desc().nullslast()
    ).offset(offset).limit(limit).all()

    return {
        "query": q,
        "total": total,
        "limit": limit,
        "offset": offset,
        "results": [build_statement(s, db) for s in statements],
    }

@router.get("/topics")
def list_topics(db: Session = Depends(get_db)):
    cached = get_cached("topics:all")
    if cached:
        return cached

    from sqlalchemy import func
    results = db.query(
        Statement.topic,
        func.count(Statement.id).label("count")
    ).filter(
        Statement.status == "approved",
        Statement.topic.isnot(None),
    ).group_by(Statement.topic).order_by(
        func.count(Statement.id).desc()
    ).all()

    result = {"topics": [{"topic": t, "count": c} for t, c in results]}
    set_cached("topics:all", result, ttl=600)
    return result

@router.get(
    "/statements/{statement_id}",
    summary="Get a single statement with full context",
)
def get_statement_detail(
    statement_id: int,
    db: Session = Depends(get_db),
):
    stmt = db.query(Statement).filter(
        Statement.id == statement_id,
        Statement.status == "approved",
    ).first()
    if not stmt:
        raise HTTPException(status_code=404, detail="Statement not found")

    # Get related statements from same article
    related = []
    if stmt.article_id:
        related_stmts = db.query(Statement).filter(
            Statement.article_id == stmt.article_id,
            Statement.status == "approved",
            Statement.id != stmt.id,
        ).limit(10).all()
        related = [build_statement(s, db) for s in related_stmts]

    # Also get related from same queue item
    if not related and stmt.queue_item_id:
        related_stmts = db.query(Statement).filter(
            Statement.queue_item_id == stmt.queue_item_id,
            Statement.status == "approved",
            Statement.id != stmt.id,
        ).limit(10).all()
        related = [build_statement(s, db) for s in related_stmts]

    result = build_statement(stmt, db)
    result["context_text"] = stmt.context_text
    result["related_statements"] = related

    return result
