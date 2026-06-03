from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class ArticleQueue(Base):
    __tablename__ = "article_queue"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String(1000), nullable=False, unique=True)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=True)
    source_name = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    language = Column(String(10), default="en")

    # Status flow:
    # pending_review → mining → mined → rejected → deleted
    status = Column(String(50), default="pending_review", index=True)

    # Who reviewed it
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Mining results
    mining_started_at = Column(DateTime(timezone=True), nullable=True)
    mining_completed_at = Column(DateTime(timezone=True), nullable=True)
    mining_error = Column(Text, nullable=True)
    statements_found = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    mined_results = relationship(
        "MinedResult", back_populates="queue_item", cascade="all, delete-orphan"
    )
    reviewer = relationship("User", foreign_keys=[reviewed_by])