"""
Client that calls open-ministry-miner API
instead of running scrapers locally.
"""
import logging
import httpx
import os
from sqlalchemy.orm import Session

from database.models.article import Article
from database.models.minister import Minister
from database.models.statement import Statement
from nlp.statement_store import StatementStore

logger = logging.getLogger(__name__)

MINER_URL = os.environ.get("MINER_URL", "http://localhost:8001")


def find_minister(name: str, db: Session) -> Minister | None:
    """Find minister by name — exact then partial."""
    if not name:
        return None
    minister = db.query(Minister).filter(
        Minister.name.ilike(name)
    ).first()
    if minister:
        return minister
    parts = name.strip().split()
    for part in reversed(parts):
        if len(part) > 4 and "." not in part:
            minister = db.query(Minister).filter(
                Minister.name.ilike(f"%{part}%")
            ).first()
            if minister:
                return minister
    return None


def map_topic(topic_tag: str) -> str | None:
    mapping = {
        "education": "Education",
        "health": "Health",
        "transport": "Transport",
        "budget": "Finance",
        "finance": "Finance",
        "election": "Politics",
        "law_order": "Law & Order",
        "agriculture": "Agriculture",
        "welfare": "Social Welfare",
        "environment": "Environment",
        "infrastructure": "Infrastructure",
        "tourism": "Tourism",
    }
    return mapping.get(topic_tag.lower()) if topic_tag else None


def fetch_and_process(source: str = "thehindu", limit: int = 20, db: Session = None) -> dict:
    """
    Call the miner API to scrape and extract statements.
    Save results directly to the database.
    """
    store = StatementStore()

    try:
        with httpx.Client(timeout=300.0) as client:
            res = client.post(
                f"{MINER_URL}/batch",
                json={"source": source, "limit": limit},
            )
            res.raise_for_status()
            data = res.json()
    except Exception as e:
        logger.error(f"Miner API call failed: {e}")
        return {"error": str(e), "statements": 0}

    results = data.get("results", [])
    total_statements = 0

    for item in results:
        url = item.get("url")
        title = item.get("title")
        published_at = item.get("published_at")
        speaker_briefs = item.get("speaker_briefs", [])

        # Check if article already exists
        from database.models.source import Source
        existing = db.query(Article).filter(
            Article.url == url
        ).first()

        if not existing:
            # Get or create source
            source_record = db.query(Source).filter(
                Source.name == "The Hindu - Kerala"
            ).first()

            if source_record:
                article = Article(
                    source_id=source_record.id,
                    url=url,
                    url_hash=__import__("hashlib").sha256(
                        url.encode()
                    ).hexdigest(),
                    title=title,
                    language="en",
                    scrape_status="processed",
                )
                db.add(article)
                db.commit()
                db.refresh(article)
            else:
                continue
        else:
            article = existing

        # Save statements from each speaker brief
        for brief in speaker_briefs:
            speaker_name = brief.get("speaker_name", "")
            quality_stars = brief.get("extraction_quality_stars", 1)

            if quality_stars < 2:
                continue

            minister = find_minister(speaker_name, db)
            if not minister:
                logger.debug(f"Minister not found: {speaker_name}")
                continue

            for stmt in brief.get("statements", []):
                text = stmt.get("snippet", "").strip()
                topic_tag = stmt.get("topic_tag", "")

                if not text or len(text) < 20:
                    continue

                result = store.save_statement(
                    minister_id=minister.id,
                    article_id=article.id,
                    text=text,
                    confidence=quality_stars / 5.0,
                    quote_type="direct",
                    statement_date=None,
                    db=db,
                )

                if result["saved"]:
                    stmt_obj = db.query(Statement).filter(
                        Statement.id == result["statement_id"]
                    ).first()
                    if stmt_obj:
                        stmt_obj.topic = map_topic(topic_tag)
                        db.commit()
                    total_statements += 1

    return {
        "articles_processed": data.get("processed", 0),
        "articles_with_statements": data.get("articles_with_statements", 0),
        "statements_saved": total_statements,
    }