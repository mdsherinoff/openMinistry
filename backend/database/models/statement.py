from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class Statement(Base):
    __tablename__ = "statements"

    id = Column(Integer, primary_key=True, index=True)
    minister_id = Column(Integer, ForeignKey("ministers.id"), nullable=False)
    article_id = Column(Integer, ForeignKey("articles.id"), nullable=False)
    statement_text = Column(Text, nullable=False)
    statement_text_malayalam = Column(Text, nullable=True)
    statement_summary = Column(Text, nullable=True)
    topic = Column(String(100), nullable=True)
    sentiment = Column(String(50), nullable=True)  # positive/neutral/negative
    confidence_score = Column(Float, nullable=True)  # 0.0 to 1.0
    context_text = Column(Text, nullable=True)      # surrounding paragraph
    article_context = Column(Text, nullable=True)   # broader article context
    queue_item_id = Column(Integer, ForeignKey("article_queue.id"), nullable=True)
    statement_date = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), default="pending")
    # pending | approved | rejected | needs_review
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    minister = relationship("Minister", back_populates="statements")
    article = relationship("Article", back_populates="statements")
    reviewer = relationship("User", back_populates="reviewed_statements")
    moderation_logs = relationship("ModerationLog", back_populates="statement")