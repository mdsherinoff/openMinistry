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
        from nlp.statement_pipeline import run_pipeline
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

@celery_app.task(name="workers.tasks.mine_queue_item")
def mine_queue_item(queue_item_id: int):
    """Mine a single queue item using open-ministry-miner."""
    logger.info(f"Mining queue item: {queue_item_id}")

    from database.config import get_session_factory
    from database.models.article_queue import ArticleQueue
    from database.models.mined_result import MinedResult
    from database.models.minister import Minister
    from datetime import datetime, timezone
    import os

    MINER_URL = os.environ.get("MINER_URL", "http://localhost:8001")

    SessionLocal = get_session_factory()
    db = SessionLocal()

    try:
        item = db.query(ArticleQueue).filter(
            ArticleQueue.id == queue_item_id
        ).first()
        if not item:
            logger.error(f"Queue item not found: {queue_item_id}")
            return

        item.mining_started_at = datetime.now(timezone.utc)
        item.status = "mining"
        db.commit()

        # Call the miner
        import httpx
        with httpx.Client(timeout=120.0) as client:
            res = client.post(
                f"{MINER_URL}/mine",
                json={"url": item.url},
            )
            res.raise_for_status()
            data = res.json()

        annotation = data.get("annotation", {})
        article_data = data.get("article", {})

        # Update article title if we got it
        if article_data.get("title") and not item.title:
            item.title = article_data["title"][:500]

        # Save mined results
        speaker_briefs = annotation.get("speaker_briefs", [])
        saved_count = 0

        for brief in speaker_briefs:
            speaker_name = brief.get("speaker_name", "")
            speaker_role = brief.get("speaker_role", "")
            quality_stars = brief.get("extraction_quality_stars", 3)

            # Try to find minister
            minister = None
            if speaker_name:
                minister = db.query(Minister).filter(
                    Minister.name.ilike(f"%{speaker_name.split()[-1]}%")
                ).first()

            for stmt in brief.get("statements", []):
                text = stmt.get("snippet", "").strip()
                if not text or len(text) < 15:
                    continue

                mined = MinedResult(
                    queue_item_id=queue_item_id,
                    speaker_name=speaker_name,
                    speaker_role=speaker_role,
                    minister_id=minister.id if minister else None,
                    statement_text=text,
                    context_description=stmt.get("context_description"),
                    topic_tag=stmt.get("topic_tag"),
                    confidence_stars=quality_stars,
                    status="awaiting_review",
                )
                db.add(mined)
                saved_count += 1

        item.status = "mined"
        item.statements_found = saved_count
        item.mining_completed_at = datetime.now(timezone.utc)
        db.commit()

        logger.info(
            f"Mining complete for item {queue_item_id}: "
            f"{saved_count} statements found"
        )
        return {"statements_found": saved_count}

    except Exception as e:
        logger.error(f"Mining failed for item {queue_item_id}: {e}")
        item = db.query(ArticleQueue).filter(
            ArticleQueue.id == queue_item_id
        ).first()
        if item:
            item.status = "mining_failed"
            item.mining_error = str(e)
            db.commit()
        raise
    finally:
        db.close()

@celery_app.task(name="workers.tasks.collect_urls")
def collect_urls(source_key: str = "thehindu.com"):
    """Collect URLs from a source and add to the moderation queue."""
    logger.info(f"Collecting URLs from {source_key}")

    import httpx
    import hashlib
    from database.config import get_session_factory
    from database.models.article_queue import ArticleQueue
    from scrapers.source_config import SOURCE_CONFIGS

    config = SOURCE_CONFIGS.get(source_key)
    if not config:
        logger.error(f"Unknown source: {source_key}")
        return

    SessionLocal = get_session_factory()
    db = SessionLocal()
    added = 0

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }

        for list_url in config.get("article_list_urls", []):
            try:
                from bs4 import BeautifulSoup
                res = httpx.get(list_url, headers=headers, timeout=30)
                soup = BeautifulSoup(res.text, "html.parser")

                for a in soup.find_all("a", href=True):
                    href = a["href"]
                    if href.startswith("/"):
                        href = f"{config['base_url']}{href}"

                    if "/article" not in href:
                        continue
                    if config["base_url"].replace("https://www.", "") \
                       not in href:
                        continue

                    url = href.split("?")[0]
                    url_hash = hashlib.sha256(
                        url.strip().lower().encode()
                    ).hexdigest()

                    existing = db.query(ArticleQueue).filter(
                        ArticleQueue.url_hash == url_hash
                    ).first()
                    if existing:
                        continue

                    # Get title from link text
                    title = a.get_text(strip=True)[:500] or None

                    item = ArticleQueue(
                        url=url,
                        url_hash=url_hash,
                        title=title,
                        source_name=config["name"],
                        language=config["language"],
                        status="pending_review",
                    )
                    db.add(item)
                    added += 1

            except Exception as e:
                logger.error(f"Error collecting from {list_url}: {e}")

        db.commit()
        logger.info(f"Collected {added} new URLs from {source_key}")
        return {"added": added}

    finally:
        db.close()