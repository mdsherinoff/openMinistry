import hashlib
import logging
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from database.models.statement import Statement
from database.models.article import Article
from database.models.minister import Minister

logger = logging.getLogger(__name__)


class StatementStore:
    """
    Handles deduplication and storage of extracted statements.
    Ensures only quality statements reach the moderation queue.
    """

    # Minimum confidence to store a statement
    MIN_CONFIDENCE = 0.45

    # Minimum statement length in words
    MIN_WORDS = 8

    # Maximum statement length in words
    MAX_WORDS = 300

    # Phrases that indicate junk statements
    JUNK_PHRASES = [
        "click here",
        "subscribe",
        "follow us",
        "read more",
        "also read",
        "advertisement",
        "download the app",
        "breaking news",
        "live updates",
        "photo gallery",
        "video",
        "watch",
    ]

    def make_statement_hash(
        self, minister_id: int, text: str
    ) -> str:
        """Create a hash for deduplication."""
        normalized = " ".join(text.lower().split())
        content = f"{minister_id}:{normalized}"
        return hashlib.sha256(content.encode()).hexdigest()

    def is_quality_statement(self, text: str, confidence: float) -> tuple[bool, str]:
        """
        Check if a statement meets quality standards.
        Returns (is_quality, reason).
        """
        if not text or not text.strip():
            return False, "empty text"

        words = text.split()
        word_count = len(words)

        if word_count < self.MIN_WORDS:
            return False, f"too short ({word_count} words)"

        if word_count > self.MAX_WORDS:
            return False, f"too long ({word_count} words)"

        if confidence < self.MIN_CONFIDENCE:
            return False, f"low confidence ({confidence:.2f})"

        text_lower = text.lower()
        for phrase in self.JUNK_PHRASES:
            if phrase in text_lower:
                return False, f"junk phrase: '{phrase}'"

        # Must contain at least one verb-like word
        # (basic check — proper NLP comes later)
        verb_indicators = [
            "said", "will", "would", "has", "have", "is", "are",
            "was", "were", "should", "must", "announced", "stated",
            "told", "added", "noted", "explained", "confirmed",
        ]
        has_verb = any(v in text_lower.split() for v in verb_indicators)
        if not has_verb:
            return False, "no verb detected"

        return True, "ok"

    def save_statement(
        self,
        minister_id: int,
        article_id: int,
        text: str,
        confidence: float,
        quote_type: str,
        statement_date: datetime | None,
        db: Session,
    ) -> dict:
        """
        Save a single statement with full quality checks.
        Returns result dict.
        """
        # Quality check
        is_quality, reason = self.is_quality_statement(text, confidence)
        if not is_quality:
            return {"saved": False, "reason": reason}

        # Deduplication check
        stmt_hash = self.make_statement_hash(minister_id, text)
        existing = db.query(Statement).filter(
            Statement.minister_id == minister_id,
            Statement.statement_text == text,
        ).first()

        if existing:
            return {"saved": False, "reason": "duplicate"}

        # Also check for very similar statements from same article
        same_article = db.query(Statement).filter(
            Statement.minister_id == minister_id,
            Statement.article_id == article_id,
        ).all()

        for stmt in same_article:
            similarity = self._text_similarity(text, stmt.statement_text)
            if similarity > 0.85:
                return {"saved": False, "reason": "near-duplicate"}

        # Save
        statement = Statement(
            minister_id=minister_id,
            article_id=article_id,
            statement_text=text.strip(),
            confidence_score=confidence,
            statement_date=statement_date,
            status="pending",
        )
        db.add(statement)
        db.commit()
        db.refresh(statement)

        return {"saved": True, "statement_id": statement.id}

    def save_batch(
        self,
        statements: list[dict],
        db: Session,
    ) -> dict:
        """
        Save a batch of extracted statements.
        Returns summary of what was saved/rejected.
        """
        saved = 0
        rejected = 0
        rejection_reasons = {}

        for stmt_data in statements:
            result = self.save_statement(
                minister_id=stmt_data["minister_id"],
                article_id=stmt_data["article_id"],
                text=stmt_data["text"],
                confidence=stmt_data["confidence"],
                quote_type=stmt_data.get("quote_type", "indirect"),
                statement_date=stmt_data.get("statement_date"),
                db=db,
            )

            if result["saved"]:
                saved += 1
            else:
                rejected += 1
                reason = result["reason"]
                rejection_reasons[reason] = rejection_reasons.get(reason, 0) + 1

        return {
            "saved": saved,
            "rejected": rejected,
            "rejection_reasons": rejection_reasons,
        }

    def _text_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    def get_queue_stats(self, db: Session) -> dict:
        """Get moderation queue statistics."""
        total = db.query(Statement).count()
        pending = db.query(Statement).filter(
            Statement.status == "pending"
        ).count()
        approved = db.query(Statement).filter(
            Statement.status == "approved"
        ).count()
        rejected = db.query(Statement).filter(
            Statement.status == "rejected"
        ).count()
        needs_review = db.query(Statement).filter(
            Statement.status == "needs_review"
        ).count()

        return {
            "total": total,
            "pending": pending,
            "approved": approved,
            "rejected": rejected,
            "needs_review": needs_review,
            "approval_rate": (
                round(approved / total * 100, 1) if total > 0 else 0
            ),
        }