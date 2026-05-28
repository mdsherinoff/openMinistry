import logging
from sqlalchemy.orm import Session
from database.models.article import Article
from database.models.minister import Minister
from nlp.name_detector import NameDetector

logger = logging.getLogger(__name__)

# Single detector instance — loaded once and reused
_detector = None


def get_detector(db: Session) -> NameDetector:
    """Get or create the name detector with ministers loaded."""
    global _detector
    if _detector is None or len(_detector.ministers) == 0:
        _detector = NameDetector()
        _detector.load_ministers(db)
    return _detector


def detect_ministers_in_article(
    article: Article,
    db: Session
) -> list[dict]:
    """Run name detection on a single article."""
    detector = get_detector(db)

    text = article.cleaned_content or article.raw_content or ""
    if not text:
        return []

    # Combine title and content for detection
    full_text = f"{article.title or ''}\n\n{text}"
    mentions = detector.detect_mentions(full_text)

    return mentions


def process_undetected_articles(db: Session) -> dict:
    """
    Find all cleaned articles that haven't had
    name detection run yet and process them.
    """
    articles = db.query(Article).filter(
        Article.scrape_status == "cleaned"
    ).all()

    processed = 0
    skipped = 0
    total_mentions = 0

    for article in articles:
        mentions = detect_ministers_in_article(article, db)

        if mentions:
            # Mark as detected
            article.scrape_status = "detected"
            db.commit()
            total_mentions += len(mentions)
            processed += 1
            logger.info(
                f"Detected {len(mentions)} mentions in: "
                f"{article.title[:60] if article.title else 'untitled'}..."
            )
        else:
            # No ministers mentioned — mark as no_mentions
            article.scrape_status = "no_mentions"
            db.commit()
            skipped += 1

    return {
        "processed": processed,
        "skipped": skipped,
        "total_mentions": total_mentions,
    }