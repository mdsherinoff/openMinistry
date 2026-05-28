import logging
from celery import shared_task
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="workers.tasks.scrape_source",
)
def scrape_source(self, source_key: str):
    """
    Scrape all articles from a given source.
    source_key matches keys in SOURCE_CONFIGS.
    """
    logger.info(f"Starting scrape task for: {source_key}")

    try:
        from scrapers.source_config import SOURCE_CONFIGS
        from scrapers.article_store import save_articles
        from database.config import get_session_factory

        if source_key not in SOURCE_CONFIGS:
            logger.error(f"Unknown source key: {source_key}")
            return {"error": f"Unknown source: {source_key}"}

        # Import the right scraper
        scraper = _get_scraper(source_key)
        if not scraper:
            return {"error": f"No scraper for: {source_key}"}

        # Run the scrape
        articles = scraper.scrape_all()

        # Save to database
        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = save_articles(articles, db)
        finally:
            db.close()

        logger.info(f"Scrape complete for {source_key}: {result}")
        return result

    except Exception as e:
        logger.error(f"Scrape task failed for {source_key}: {e}")
        raise self.retry(exc=e)


@celery_app.task(
    name="workers.tasks.clean_articles",
)
def clean_articles():
    """Clean all scraped articles that haven't been cleaned yet."""
    logger.info("Starting article cleaning task")

    try:
        from scrapers.cleaning_service import clean_pending_articles
        from database.config import get_session_factory

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = clean_pending_articles(db)
        finally:
            db.close()

        logger.info(f"Cleaning complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Cleaning task failed: {e}")
        raise


@celery_app.task(
    name="workers.tasks.scrape_all_sources",
)
def scrape_all_sources():
    """Trigger scraping for all active sources at once."""
    from scrapers.source_config import SOURCE_CONFIGS

    results = {}
    for source_key in SOURCE_CONFIGS.keys():
        result = scrape_source.delay(source_key)
        results[source_key] = str(result.id)

    return results


def _get_scraper(source_key: str):
    """Return the right scraper instance for a source key."""
    if source_key == "thehindu.com":
        from scrapers.sources.the_hindu import TheHinduScraper
        return TheHinduScraper()
    elif source_key == "mathrubhumi.com":
        from scrapers.sources.mathrubhumi import MathrubhumiScraper
        return MathrubhumiScraper()
    elif source_key == "onmanorama.com":
        from scrapers.sources.manorama import ManoramaScraper
        return ManoramaScraper()
    logger.warning(f"No scraper implemented for: {source_key}")
    return None