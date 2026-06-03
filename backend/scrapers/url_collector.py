import hashlib
import logging
import httpx
from bs4 import BeautifulSoup
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database.models.article_queue import ArticleQueue

logger = logging.getLogger(__name__)


class BaseURLCollector:
    """
    Lightweight base class for URL collection.
    No content extraction — just finds article URLs
    and submits them to the moderation queue.
    """

    def __init__(self, source_config: dict):
        self.config = source_config
        self.name = source_config["name"]
        self.base_url = source_config["base_url"]
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 Chrome/124.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
        }

    def make_url_hash(self, url: str) -> str:
        return hashlib.sha256(
            url.strip().lower().split("?")[0].encode()
        ).hexdigest()

    def fetch_page(self, url: str) -> str | None:
        try:
            with httpx.Client(
                headers=self.headers,
                follow_redirects=True,
                timeout=30.0,
            ) as client:
                res = client.get(url)
                res.raise_for_status()
                if len(res.text) < 500:
                    return None
                return res.text
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None

    def get_article_urls(self) -> list[dict]:
        """
        Override in subclass.
        Returns list of dicts: {url, title, published_at}
        """
        raise NotImplementedError

    def submit_to_queue(self, db: Session) -> dict:
        """
        Collect URLs and submit new ones to the queue.
        Skips duplicates automatically.
        """
        urls = self.get_article_urls()
        added = 0
        skipped = 0

        for item in urls:
            url = item.get("url", "").split("?")[0]
            if not url:
                continue

            url_hash = self.make_url_hash(url)

            existing = db.query(ArticleQueue).filter(
                ArticleQueue.url_hash == url_hash
            ).first()

            if existing:
                skipped += 1
                continue

            queue_item = ArticleQueue(
                url=url,
                url_hash=url_hash,
                title=item.get("title"),
                source_name=self.name,
                language=self.config.get("language", "en"),
                published_at=item.get("published_at"),
                status="pending_review",
            )
            db.add(queue_item)
            added += 1

        db.commit()
        logger.info(
            f"{self.name}: added {added} new URLs, "
            f"skipped {skipped} duplicates"
        )
        return {"source": self.name, "added": added, "skipped": skipped}