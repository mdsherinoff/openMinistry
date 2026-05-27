from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class Article(Base):
    __tablename__ = "articles"

    id = Column(Integer, primary_key=True, index=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    url = Column(String(1000), nullable=False, unique=True)
    url_hash = Column(String(64), nullable=False, unique=True, index=True)
    title = Column(String(500), nullable=True)
    author = Column(String(255), nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    raw_content = Column(Text, nullable=True)
    cleaned_content = Column(Text, nullable=True)
    language = Column(String(10), nullable=True)
    scrape_status = Column(String(50), default="pending")
    # pending | scraped | failed | skipped
    scraped_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    source = relationship("Source", back_populates="articles")
    statements = relationship("Statement", back_populates="article")