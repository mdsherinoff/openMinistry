import logging
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
from database.models.article import Article
from database.models.source import Source

logger = logging.getLogger(__name__)


class ScraperMonitor:
    """
    Monitors scraper health and tracks failures.
    Helps identify sources that are broken or blocked.
    """

    def get_source_stats(self, db: Session) -> list[dict]:
        """Get scraping stats per source."""
        sources = db.query(Source).filter(Source.is_active == 1).all()
        stats = []

        for source in sources:
            # Count articles in last 24 hours
            since = datetime.now(timezone.utc) - timedelta(hours=24)
            recent_count = db.query(Article).filter(
                Article.source_id == source.id,
                Article.created_at >= since,
            ).count()

            # Count total articles
            total_count = db.query(Article).filter(
                Article.source_id == source.id
            ).count()

            # Get last scraped article
            last_article = db.query(Article).filter(
                Article.source_id == source.id
            ).order_by(Article.created_at.desc()).first()

            stats.append({
                "source_id": source.id,
                "source_name": source.name,
                "language": source.language,
                "total_articles": total_count,
                "articles_last_24h": recent_count,
                "last_scraped": (
                    last_article.created_at.isoformat()
                    if last_article else None
                ),
                "status": "active" if recent_count > 0 else "stale",
            })

        return stats

    def get_failed_articles(self, db: Session, limit: int = 20) -> list:
        """Get articles that failed to scrape or clean."""
        return db.query(Article).filter(
            Article.scrape_status == "failed"
        ).order_by(Article.created_at.desc()).limit(limit).all()

    def get_pipeline_summary(self, db: Session) -> dict:
        """Get overall pipeline health summary."""
        total = db.query(Article).count()
        scraped = db.query(Article).filter(
            Article.scrape_status == "scraped"
        ).count()
        cleaned = db.query(Article).filter(
            Article.scrape_status == "cleaned"
        ).count()
        failed = db.query(Article).filter(
            Article.scrape_status == "failed"
        ).count()
        skipped = db.query(Article).filter(
            Article.scrape_status == "skipped"
        ).count()

        return {
            "total_articles": total,
            "scraped": scraped,
            "cleaned": cleaned,
            "failed": failed,
            "skipped": skipped,
            "health": "good" if failed < total * 0.1 else "degraded",
        }