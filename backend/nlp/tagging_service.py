import logging
from sqlalchemy.orm import Session
from database.models.statement import Statement
from nlp.topic_classifier import TopicClassifier

logger = logging.getLogger(__name__)
classifier = TopicClassifier()


def tag_pending_statements(db: Session) -> dict:
    """
    Tag all untagged approved and pending statements with topics.
    """
    statements = db.query(Statement).filter(
        Statement.topic.is_(None),
        Statement.status.in_(["approved", "pending"]),
    ).all()

    tagged = 0
    untagged = 0

    for stmt in statements:
        topic = classifier.classify(stmt.statement_text)
        if topic:
            stmt.topic = topic
            tagged += 1
        else:
            untagged += 1

    db.commit()
    logger.info(f"Tagged {tagged} statements, {untagged} untagged")
    return {"tagged": tagged, "untagged": untagged}


def get_topic_stats(db: Session) -> list[dict]:
    """Get count of statements per topic."""
    from sqlalchemy import func
    results = db.query(
        Statement.topic,
        func.count(Statement.id).label("count")
    ).filter(
        Statement.status == "approved",
        Statement.topic.isnot(None),
    ).group_by(
        Statement.topic
    ).order_by(
        func.count(Statement.id).desc()
    ).all()

    return [{"topic": t, "count": c} for t, c in results]