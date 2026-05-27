from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class Source(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    website = Column(String(500), nullable=False, unique=True)
    language = Column(String(10), nullable=False)  # 'ml' or 'en'
    credibility_score = Column(Float, default=1.0)  # 0.0 to 1.0
    is_active = Column(Integer, default=1)
    scrape_frequency_minutes = Column(Integer, default=60)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    articles = relationship("Article", back_populates="source")