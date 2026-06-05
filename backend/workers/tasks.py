import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)

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