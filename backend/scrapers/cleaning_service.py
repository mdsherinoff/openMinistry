import logging
from sqlalchemy.orm import Session
from database.models.article import Article
from scrapers.cleaner import ArticleCleaner

logger = logging.getLogger(__name__)
cleaner = ArticleCleaner()


def clean_pending_articles(db: Session) -> dict:
    """
    Find all scraped articles that haven't been
    cleaned yet and run them through the cleaner.
    """
    # Find articles with raw content but no cleaned content
    articles = db.query(Article).filter(
        Article.scrape_status == "scraped",
        Article.raw_content.isnot(None),
    ).all()

    cleaned = 0
    skipped = 0
    failed = 0

    for article in articles:
        try:
            # Clean the raw content
            clean_text = cleaner.clean_text(article.raw_content)

            if not cleaner.is_content_sufficient(clean_text):
                article.scrape_status = "skipped"
                db.commit()
                skipped += 1
                logger.debug(f"Skipped (too short): {article.title}")
                continue

            # Save cleaned content
            article.cleaned_content = clean_text
            article.scrape_status = "cleaned"
            db.commit()
            cleaned += 1
            logger.info(f"Cleaned: {article.title[:60]}...")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to clean article {article.id}: {e}")
            failed += 1

    return {"cleaned": cleaned, "skipped": skipped, "failed": failed}


def get_article_preview(article: Article) -> str:
    """Get a short preview of an article's content."""
    content = article.cleaned_content or article.raw_content or ""
    return cleaner.extract_first_paragraph(content)