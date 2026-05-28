import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models.article import Article
from database.models.source import Source

logger = logging.getLogger(__name__)


def save_articles(articles: list[dict], db: Session) -> dict:
    """
    Save scraped articles to the database.
    Skips duplicates using URL hash.
    Returns a summary of what happened.
    """
    saved = 0
    skipped = 0
    failed = 0

    for article_data in articles:
        try:
            # Check for duplicate by URL hash
            existing = db.query(Article).filter(
                Article.url_hash == article_data["url_hash"]
            ).first()

            if existing:
                skipped += 1
                continue

            # Find the source record
            source = db.query(Source).filter(
                Source.name == article_data["source_name"]
            ).first()

            if not source:
                logger.warning(
                    f"Source not found: {article_data['source_name']}"
                )
                failed += 1
                continue

            article = Article(
                source_id=source.id,
                url=article_data["url"],
                url_hash=article_data["url_hash"],
                title=article_data.get("title"),
                author=article_data.get("author"),
                published_at=article_data.get("published_at"),
                raw_content=article_data.get("raw_content"),
                cleaned_content=article_data.get("cleaned_content"),
                language=article_data.get("language", "en"),
                scrape_status="scraped",
                scraped_at=datetime.now(timezone.utc),
            )
            db.add(article)
            db.commit()
            saved += 1
            logger.info(f"Saved article: {article_data['title'][:60]}...")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to save article {article_data.get('url')}: {e}")
            failed += 1

    return {"saved": saved, "skipped": skipped, "failed": failed}