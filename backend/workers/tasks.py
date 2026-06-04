import logging
from celery import shared_task
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    name="workers.tasks.scrape_source",
    soft_time_limit=300,
    time_limit=360,
)
def scrape_source(self, source_key: str):
    """
    Scrape all articles from a given source.
    source_key matches keys in SOURCE_CONFIGS.
    """
    from celery.exceptions import SoftTimeLimitExceeded

    logger.info(f"Starting scrape task for: {source_key}")

    try:
        from scrapers.source_config import SOURCE_CONFIGS
        from scrapers.article_store import save_articles
        from database.config import get_session_factory

        if source_key not in SOURCE_CONFIGS:
            logger.error(f"Unknown source key: {source_key}")
            return {"error": f"Unknown source: {source_key}"}

        scraper = _get_scraper(source_key)
        if not scraper:
            return {"error": f"No scraper for: {source_key}"}

        articles = scraper.scrape_all()

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = save_articles(articles, db)
        finally:
            db.close()

        logger.info(f"Scrape complete for {source_key}: {result}")
        return result

    except SoftTimeLimitExceeded:
        logger.error(f"Scrape task timed out for {source_key}")
        return {"error": "timeout", "source": source_key}

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

@celery_app.task(name="workers.tasks.detect_ministers")
def detect_ministers():
    """Run name detection on all cleaned articles."""
    logger.info("Starting minister detection task")
    try:
        from nlp.detection_service import process_undetected_articles
        from database.config import get_session_factory

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = process_undetected_articles(db)
        finally:
            db.close()

        logger.info(f"Detection complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Detection task failed: {e}")
        raise

@celery_app.task(name="workers.tasks.run_statement_pipeline")
def run_statement_pipeline():
    """Run full statement extraction pipeline."""
    logger.info("Starting statement pipeline task")
    try:
        from backend.nlp.miner_pipeline import run_pipeline
        from database.config import get_session_factory

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = run_pipeline(db)
        finally:
            db.close()

        logger.info(f"Pipeline complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Pipeline task failed: {e}")
        raise

@celery_app.task(name="workers.tasks.tag_statements")
def tag_statements():
    """Tag all untagged statements with topics."""
    logger.info("Starting tagging task")
    try:
        from nlp.tagging_service import tag_pending_statements
        from database.config import get_session_factory

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = tag_pending_statements(db)
        finally:
            db.close()

        logger.info(f"Tagging complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Tagging task failed: {e}")
        raise

@celery_app.task(name="workers.tasks.run_miner")
def run_miner(source: str = "thehindu", limit: int = 20):
    """Fetch and process articles via open-ministry-miner."""
    logger.info(f"Starting miner task for {source}")
    try:
        from nlp.miner_client import fetch_and_process
        from database.config import get_session_factory

        SessionLocal = get_session_factory()
        db = SessionLocal()
        try:
            result = fetch_and_process(source=source, limit=limit, db=db)
        finally:
            db.close()

        logger.info(f"Miner task complete: {result}")
        return result
    except Exception as e:
        logger.error(f"Miner task failed: {e}")
        raise

@celery_app.task(
    name="workers.tasks.mine_queue_item",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
)
def mine_queue_item(self, queue_item_id: int):
    """
    Mine a single queue item using open-ministry-miner.
    Called when moderator approves a URL for mining.
    """
    logger.info(f"Mining queue item: {queue_item_id}")

    from database.config import get_session_factory
    from database.models.article_queue import ArticleQueue
    from database.models.mined_result import MinedResult
    from database.models.minister import Minister
    from nlp.miner_client import mine_url, parse_speaker_briefs
    from datetime import datetime, timezone

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        # Get queue item
        item = db.query(ArticleQueue).filter(
            ArticleQueue.id == queue_item_id
        ).first()
        if not item:
            logger.error(f"Queue item not found: {queue_item_id}")
            return {"error": "not found"}

        # Mark as mining
        item.status = "mining"
        item.mining_started_at = datetime.now(timezone.utc)
        db.commit()

        # Call the miner
        logger.info(f"Calling miner for: {item.url}")
        data = mine_url(item.url)

        article_data = data.get("article", {})
        annotation = data.get("annotation", {})

        # Update title from miner if we didn't have it
        if article_data.get("title") and not item.title:
            item.title = article_data["title"][:500]

        # Parse statements from speaker briefs
        candidates = parse_speaker_briefs(annotation)
        logger.info(
            f"Miner found {len(candidates)} statement candidates "
            f"for item {queue_item_id}"
        )

        # Match each speaker to our ministers database
        saved_count = 0
        for candidate in candidates:
            speaker_name = candidate["speaker_name"]

            # Try to find minister — exact then partial
            minister = None
            if speaker_name:
                minister = db.query(Minister).filter(
                    Minister.name.ilike(speaker_name)
                ).first()

                if not minister:
                    # Try last name
                    parts = speaker_name.strip().split()
                    for part in reversed(parts):
                        if len(part) > 4 and "." not in part:
                            minister = db.query(Minister).filter(
                                Minister.name.ilike(f"%{part}%")
                            ).first()
                            if minister:
                                break

            mined = MinedResult(
                queue_item_id=queue_item_id,
                speaker_name=speaker_name,
                speaker_role=candidate["speaker_role"],
                minister_id=minister.id if minister else None,
                statement_text=candidate["statement_text"],
                context_description=candidate["context_description"],
                topic_tag=candidate["topic_tag"],
                confidence_stars=candidate["confidence_stars"],
                status="awaiting_review",
            )
            db.add(mined)
            saved_count += 1

        # Update queue item status
        item.status = "mined"
        item.statements_found = saved_count
        item.mining_completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            f"Mining complete for item {queue_item_id}: "
            f"{saved_count} statements found"
        )
        return {
            "queue_item_id": queue_item_id,
            "statements_found": saved_count,
            "overall_quality": annotation.get(
                "overall_extraction_quality_stars"
            ),
        }

    except Exception as e:
        logger.error(f"Mining failed for {queue_item_id}: {e}")
        db.rollback()

        # Update item as failed
        try:
            item = db.query(ArticleQueue).filter(
                ArticleQueue.id == queue_item_id
            ).first()
            if item:
                item.status = "mining_failed"
                item.mining_error = str(e)[:500]
                db.commit()
        except Exception:
            pass

        raise self.retry(exc=e)

    finally:
        db.close()

@celery_app.task(name="workers.tasks.collect_urls")
def collect_urls(source_key: str = "thehindu.com"):
    """
    Collect article URLs from a source and
    add new ones to the moderation queue.
    """
    logger.info(f"Collecting URLs from {source_key}")

    from database.config import get_session_factory

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        collector = _get_collector(source_key)
        if not collector:
            logger.error(f"No collector for: {source_key}")
            return {"error": f"No collector for {source_key}"}

        result = collector.submit_to_queue(db)
        logger.info(f"Collection complete: {result}")
        return result

    except Exception as e:
        logger.error(f"URL collection failed for {source_key}: {e}")
        raise
    finally:
        db.close()


def _get_collector(source_key: str):
    """Return the right collector for a source key."""
    if source_key == "thehindu.com":
        from scrapers.collectors.the_hindu_collector import TheHinduCollector
        return TheHinduCollector()
    logger.warning(f"No collector implemented for: {source_key}")
    return None