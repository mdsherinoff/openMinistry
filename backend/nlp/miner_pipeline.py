"""
Adapter that connects open-ministry-miner to the openMinistry database.
Replaces the old regex-based NLP pipeline.
"""
import logging
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.orm import Session
from database.models.article import Article
from database.models.minister import Minister
from database.models.statement import Statement
from nlp.statement_store import StatementStore

logger = logging.getLogger(__name__)


def find_minister_by_name(name: str, db: Session) -> Minister | None:
    """
    Find a minister by name using fuzzy matching.
    Tries exact match first, then partial match.
    """
    if not name:
        return None

    # Exact match
    minister = db.query(Minister).filter(
        Minister.name.ilike(name)
    ).first()
    if minister:
        return minister

    # Try matching on last name
    parts = name.strip().split()
    for part in reversed(parts):
        if len(part) > 4 and "." not in part:
            minister = db.query(Minister).filter(
                Minister.name.ilike(f"%{part}%")
            ).first()
            if minister:
                return minister

    return None


def process_article_with_miner(
    article: Article,
    db: Session,
) -> dict:
    """
    Run open-ministry-miner on a single article
    and save extracted statements to the database.
    """
    try:
        from miner_app.extractor import extract_article
        from miner_app.annotator import annotate_article
    except ImportError:
        logger.error("miner_app not found — check path")
        return {"statements": 0, "error": "miner not available"}

    store = StatementStore()

    # Step 1 — Extract article content
    try:
        article_data = extract_article(article.url)
    except Exception as e:
        logger.error(f"Extraction failed for {article.url}: {e}")
        article.scrape_status = "failed"
        db.commit()
        return {"statements": 0, "error": str(e)}

    # Update article with better content if extractor got more
    if article_data.get("text") and len(article_data["text"]) > len(article.raw_content or ""):
        article.cleaned_content = article_data["text"]
        db.commit()

    # Step 2 — Annotate with LLM
    try:
        annotation = annotate_article(article_data)
    except Exception as e:
        logger.error(f"Annotation failed for {article.url}: {e}")
        article.scrape_status = "failed"
        db.commit()
        return {"statements": 0, "error": str(e)}

    # Step 3 — Save speaker briefs as statements
    saved = 0
    speaker_briefs = annotation.get("speaker_briefs", [])

    for brief in speaker_briefs:
        speaker_name = brief.get("speaker_name", "")
        quality_stars = brief.get("extraction_quality_stars", 1)

        # Skip low quality extractions
        if quality_stars < 2:
            logger.debug(f"Skipping low quality brief for {speaker_name}")
            continue

        # Find the minister in our database
        minister = find_minister_by_name(speaker_name, db)
        if not minister:
            logger.debug(f"Minister not found: {speaker_name}")
            continue

        # Save each statement
        for stmt in brief.get("statements", []):
            text = stmt.get("snippet", "").strip()
            topic_tag = stmt.get("topic_tag", "")

            if not text or len(text) < 20:
                continue

            # Map topic_tag from miner to our topic format
            topic = map_topic(topic_tag)

            # Confidence: convert stars (1-5) to float (0-1)
            confidence = quality_stars / 5.0

            result = store.save_statement(
                minister_id=minister.id,
                article_id=article.id,
                text=text,
                confidence=confidence,
                quote_type="direct",
                statement_date=article.published_at,
                db=db,
            )

            if result["saved"]:
                # Also save topic
                stmt_obj = db.query(Statement).filter(
                    Statement.id == result["statement_id"]
                ).first()
                if stmt_obj and topic:
                    stmt_obj.topic = topic
                    db.commit()
                saved += 1

    # Update article status
    if saved > 0:
        article.scrape_status = "processed"
    else:
        article.scrape_status = "no_quotes"
    db.commit()

    logger.info(
        f"Miner processed: {article.title[:60]} "
        f"— {saved} statements from {len(speaker_briefs)} speakers"
    )

    return {
        "statements": saved,
        "speakers_found": len(speaker_briefs),
        "overall_quality": annotation.get("overall_extraction_quality_stars"),
    }


def map_topic(topic_tag: str) -> str | None:
    """Map miner topic tags to our topic format."""
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


def run_miner_pipeline(db: Session) -> dict:
    """
    Run the miner pipeline on all scraped articles
    that haven't been processed yet.
    """
    articles = db.query(Article).filter(
        Article.scrape_status.in_(["scraped", "cleaned"]),
        Article.language == "en",  # English only for now
    ).all()

    logger.info(f"Running miner pipeline on {len(articles)} articles")

    total_statements = 0
    processed = 0
    failed = 0

    for article in articles:
        result = process_article_with_miner(article, db)
        if "error" in result:
            failed += 1
        else:
            processed += 1
            total_statements += result["statements"]

    return {
        "articles_processed": processed,
        "articles_failed": failed,
        "statements_saved": total_statements,
    }