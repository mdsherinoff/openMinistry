import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models.article import Article
from database.models.source import Source
from scrapers.duplicate_detector import DuplicateDetector

logger = logging.getLogger(__name__)
detector = DuplicateDetector()


def save_articles(articles: list[dict], db: Session) -> dict:
    """
    Save scraped articles to the database.
    Uses full duplicate detection before saving.
    """
    saved = 0
    skipped_duplicate = 0
    skipped_short = 0
    failed = 0

    for article_data in articles:
        try:
            url = article_data.get("url", "")
            title = article_data.get("title", "")
            content = article_data.get("raw_content", "")

            # Run full duplicate check
            dup_result = detector.check_duplicate(url, title, content, db)

            if dup_result["is_duplicate"]:
                logger.debug(
                    f"Duplicate ({dup_result['reason']}): {title[:50]}"
                )
                skipped_duplicate += 1
                continue

            # Skip articles with very little content
            if content and len(content.split()) < 30:
                logger.debug(f"Too short, skipping: {title[:50]}")
                skipped_short += 1
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
                url=url,
                url_hash=dup_result["url_hash"],
                title=title,
                author=article_data.get("author"),
                published_at=article_data.get("published_at"),
                raw_content=content,
                cleaned_content=article_data.get("cleaned_content"),
                language=article_data.get("language", "en"),
                scrape_status="scraped",
                scraped_at=datetime.now(timezone.utc),
            )
            db.add(article)
            db.commit()
            saved += 1
            logger.info(f"Saved: {title[:60]}...")

        except Exception as e:
            db.rollback()
            logger.error(
                f"Failed to save article {article_data.get('url')}: {e}"
            )
            failed += 1

    summary = {
        "saved": saved,
        "skipped_duplicate": skipped_duplicate,
        "skipped_short": skipped_short,
        "failed": failed,
    }
    logger.info(f"Save summary: {summary}")
    return summary