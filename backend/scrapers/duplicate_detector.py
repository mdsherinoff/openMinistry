import hashlib
import logging
import re
from difflib import SequenceMatcher
from sqlalchemy.orm import Session
from database.models.article import Article

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """
    Detects duplicate articles using multiple strategies:
    1. URL hash — exact URL match
    2. Content hash — exact content match
    3. Title similarity — near-duplicate titles
    """

    def __init__(self, similarity_threshold: float = 0.85):
        # How similar two titles need to be to count as duplicates
        self.similarity_threshold = similarity_threshold

    def make_url_hash(self, url: str) -> str:
        """SHA256 hash of normalized URL."""
        url = url.strip().lower().split("?")[0]  # remove query params
        return hashlib.sha256(url.encode()).hexdigest()

    def make_content_hash(self, content: str) -> str:
        """SHA256 hash of normalized content."""
        # Normalize before hashing
        content = self._normalize_for_hashing(content)
        return hashlib.sha256(content.encode()).hexdigest()

    def _normalize_for_hashing(self, text: str) -> str:
        """Normalize text so minor formatting differences don't create false negatives."""
        if not text:
            return ""
        # Lowercase
        text = text.lower()
        # Remove all whitespace and punctuation
        text = re.sub(r"[\s\W]+", "", text)
        return text

    def _title_similarity(self, title1: str, title2: str) -> float:
        """Calculate similarity ratio between two titles."""
        if not title1 or not title2:
            return 0.0
        t1 = title1.lower().strip()
        t2 = title2.lower().strip()
        return SequenceMatcher(None, t1, t2).ratio()

    def is_url_duplicate(self, url_hash: str, db: Session) -> bool:
        """Check if an article with this URL hash already exists."""
        exists = db.query(Article).filter(
            Article.url_hash == url_hash
        ).first()
        return exists is not None

    def is_content_duplicate(self, content_hash: str, db: Session) -> bool:
        """Check if an article with identical content already exists."""
        # We store content hash in url_hash column for now
        # On Day 3 schema we didn't add content_hash — we'll check by content
        exists = db.query(Article).filter(
            Article.url_hash == content_hash
        ).first()
        return exists is not None

    def is_title_duplicate(self, title: str, db: Session, limit: int = 50) -> bool:
        """
        Check if a very similar title already exists.
        Only checks recent articles for performance.
        """
        if not title:
            return False

        # Get recent articles to compare against
        recent_articles = db.query(Article.title).order_by(
            Article.created_at.desc()
        ).limit(limit).all()

        for (existing_title,) in recent_articles:
            if not existing_title:
                continue
            similarity = self._title_similarity(title, existing_title)
            if similarity >= self.similarity_threshold:
                logger.debug(
                    f"Title duplicate found: '{title[:50]}' "
                    f"matches '{existing_title[:50]}' "
                    f"({similarity:.2f})"
                )
                return True
        return False

    def check_duplicate(
        self,
        url: str,
        title: str,
        content: str,
        db: Session,
    ) -> dict:
        """
        Full duplicate check combining all strategies.
        Returns a result dict explaining why it's a duplicate (or not).
        """
        url_hash = self.make_url_hash(url)

        # Check 1 — URL hash (fastest, check first)
        if self.is_url_duplicate(url_hash, db):
            return {
                "is_duplicate": True,
                "reason": "url_hash",
                "url_hash": url_hash,
            }

        # Check 2 — Content hash
        if content:
            content_hash = self.make_content_hash(content)
            # Check against existing content hashes
            existing = db.query(Article).filter(
                Article.raw_content.isnot(None)
            ).order_by(Article.created_at.desc()).limit(100).all()

            for article in existing:
                if article.raw_content:
                    existing_hash = self.make_content_hash(article.raw_content)
                    if existing_hash == content_hash:
                        return {
                            "is_duplicate": True,
                            "reason": "content_hash",
                            "url_hash": url_hash,
                        }

        # Check 3 — Title similarity
        if self.is_title_duplicate(title, db):
            return {
                "is_duplicate": True,
                "reason": "title_similarity",
                "url_hash": url_hash,
            }

        return {
            "is_duplicate": False,
            "reason": None,
            "url_hash": url_hash,
        }