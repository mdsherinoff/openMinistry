import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models.article import Article
from database.models.statement import Statement
from nlp.name_detector import NameDetector
from nlp.quote_extractor import QuoteExtractor
from nlp.statement_store import StatementStore

logger = logging.getLogger(__name__)


def process_article(
    article: Article,
    detector: NameDetector,
    extractor: QuoteExtractor,
    store: StatementStore,
    db: Session,
) -> dict:
    """
    Full pipeline for a single article:
    1. Detect minister mentions
    2. Extract quotes for each mention
    3. Quality check and store
    """
    text = article.cleaned_content or article.raw_content or ""
    if not text:
        return {"statements": 0, "skipped": True, "reason": "no content"}

    full_text = f"{article.title or ''}\n\n{text}"

    # Step 1 — Detect ministers
    mentions = detector.detect_mentions(full_text)
    if not mentions:
        article.scrape_status = "no_mentions"
        db.commit()
        return {"statements": 0, "skipped": True, "reason": "no mentions"}

    # Step 2 — Extract and store quotes
    statements_to_save = []

    for mention in mentions:
        quotes = extractor.extract_quotes(
            text=full_text,
            minister_name=mention["minister_name"],
            minister_context=mention["context"],
        )

        for quote in quotes:
            statements_to_save.append({
                "minister_id": mention["minister_id"],
                "article_id": article.id,
                "text": quote.text,
                "confidence": quote.confidence,
                "quote_type": quote.quote_type,
                "statement_date": article.published_at,
            })

    # Step 3 — Save with quality checks
    result = store.save_batch(statements_to_save, db)

    if result["saved"] > 0:
        article.scrape_status = "processed"
    else:
        article.scrape_status = "no_quotes"
    db.commit()

    logger.info(
        f"Article '{(article.title or '')[:50]}': "
        f"saved={result['saved']} rejected={result['rejected']}"
    )

    return {
        "statements": result["saved"],
        "rejected": result["rejected"],
        "skipped": False,
    }


def run_pipeline(db: Session) -> dict:
    """
    Run the full statement extraction pipeline
    on all detected/cleaned articles.
    """
    detector = NameDetector()
    detector.load_ministers(db)
    extractor = QuoteExtractor()
    store = StatementStore()

    # Find articles ready for processing
    articles = db.query(Article).filter(
        Article.scrape_status.in_(["detected", "cleaned"])
    ).all()

    logger.info(f"Processing {len(articles)} articles")

    total_saved = 0
    total_rejected = 0
    processed = 0
    skipped = 0

    for article in articles:
        result = process_article(article, detector, extractor, store, db)
        if result["skipped"]:
            skipped += 1
        else:
            processed += 1
            total_saved += result["statements"]
            total_rejected += result.get("rejected", 0)

    # Get queue stats
    store_obj = StatementStore()
    queue_stats = store_obj.get_queue_stats(db)

    summary = {
        "articles_processed": processed,
        "articles_skipped": skipped,
        "statements_saved": total_saved,
        "statements_rejected": total_rejected,
        "queue": queue_stats,
    }
    logger.info(f"Pipeline complete: {summary}")
    return summary