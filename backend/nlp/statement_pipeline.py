import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models.article import Article
from database.models.statement import Statement
from nlp.name_detector import NameDetector
from nlp.quote_extractor import QuoteExtractor

logger = logging.getLogger(__name__)


def process_article(
    article: Article,
    detector: NameDetector,
    extractor: QuoteExtractor,
    db: Session,
) -> dict:
    """
    Full pipeline for a single article:
    1. Detect minister mentions
    2. Extract quotes for each mention
    3. Save as pending statements
    """
    text = article.cleaned_content or article.raw_content or ""
    if not text:
        return {"statements": 0, "skipped": True}

    full_text = f"{article.title or ''}\n\n{text}"

    # Step 1 — Detect ministers
    mentions = detector.detect_mentions(full_text)
    if not mentions:
        article.scrape_status = "no_mentions"
        db.commit()
        return {"statements": 0, "skipped": True}

    # Step 2 — Extract quotes for each minister
    saved = 0
    extractor_obj = extractor

    for mention in mentions:
        quotes = extractor_obj.extract_quotes(
            text=full_text,
            minister_name=mention["minister_name"],
            minister_context=mention["context"],
        )

        for quote in quotes:
            # Skip very short or low confidence quotes
            if len(quote.text) < 30 or quote.confidence < 0.4:
                continue

            # Check for duplicate statement
            existing = db.query(Statement).filter(
                Statement.article_id == article.id,
                Statement.minister_id == mention["minister_id"],
            ).first()

            if existing:
                continue

            statement = Statement(
                minister_id=mention["minister_id"],
                article_id=article.id,
                statement_text=quote.text,
                topic=None,           # filled on Day 25
                sentiment=None,       # filled later
                confidence_score=quote.confidence,
                statement_date=article.published_at,
                status="pending",     # awaits human moderation
            )
            db.add(statement)
            saved += 1

    if saved > 0:
        article.scrape_status = "processed"
        db.commit()
        logger.info(
            f"Saved {saved} statements from: "
            f"{article.title[:60] if article.title else 'untitled'}..."
        )
    else:
        article.scrape_status = "no_quotes"
        db.commit()

    return {"statements": saved, "skipped": False}


def run_pipeline(db: Session) -> dict:
    """
    Run the full statement extraction pipeline
    on all detected articles.
    """
    # Load detector and extractor
    detector = NameDetector()
    detector.load_ministers(db)
    extractor = QuoteExtractor()

    # Find articles ready for processing
    articles = db.query(Article).filter(
        Article.scrape_status.in_(["detected", "cleaned"])
    ).all()

    logger.info(f"Processing {len(articles)} articles")

    total_statements = 0
    processed = 0
    skipped = 0

    for article in articles:
        result = process_article(article, detector, extractor, db)
        if result["skipped"]:
            skipped += 1
        else:
            processed += 1
            total_statements += result["statements"]

    summary = {
        "articles_processed": processed,
        "articles_skipped": skipped,
        "total_statements_saved": total_statements,
    }
    logger.info(f"Pipeline complete: {summary}")
    return summary