from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class ModerationLog(Base):
    __tablename__ = "moderation_logs"

    id = Column(Integer, primary_key=True, index=True)
    statement_id = Column(Integer, ForeignKey("statements.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)
    # approved | rejected | edited | flagged
    notes = Column(Text, nullable=True)
    previous_text = Column(Text, nullable=True)  # stores original before edits
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    statement = relationship("Statement", back_populates="moderation_logs")
    reviewer = relationship("User", back_populates="moderation_logs")