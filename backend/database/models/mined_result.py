from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class MinedResult(Base):
    __tablename__ = "mined_results"

    id = Column(Integer, primary_key=True, index=True)
    queue_item_id = Column(
        Integer, ForeignKey("article_queue.id", ondelete="CASCADE"),
        nullable=False, index=True
    )

    # Speaker info from miner
    speaker_name = Column(String(255), nullable=True)
    speaker_role = Column(String(255), nullable=True)

    # Matched minister from our database
    minister_id = Column(Integer, ForeignKey("ministers.id"), nullable=True)

    # Statement details
    statement_text = Column(Text, nullable=False)
    context_description = Column(Text, nullable=True)
    topic_tag = Column(String(100), nullable=True)
    confidence_stars = Column(Integer, default=3)  # 1-5 from miner

    # Status
    # awaiting_review → approved → rejected
    status = Column(String(50), default="awaiting_review", index=True)

    # If approved → links to the actual statement
    statement_id = Column(
        Integer, ForeignKey("statements.id"), nullable=True
    )

    # Moderator edits
    edited_speaker_name = Column(String(255), nullable=True)
    edited_statement_text = Column(Text, nullable=True)
    edited_topic = Column(String(100), nullable=True)

    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    queue_item = relationship("ArticleQueue", back_populates="mined_results")
    minister = relationship("Minister", foreign_keys=[minister_id])
    statement = relationship("Statement", foreign_keys=[statement_id])
    reviewer = relationship("User", foreign_keys=[reviewed_by])