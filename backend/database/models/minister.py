from sqlalchemy import Column, Integer, String, Text, Date, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database.config import Base


class Minister(Base):
    __tablename__ = "ministers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    name_malayalam = Column(String(255), nullable=True)
    portfolio = Column(String(255), nullable=True)
    party = Column(String(255), nullable=True)
    constituency = Column(String(255), nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    bio = Column(Text, nullable=True)
    image_url = Column(String(500), nullable=True)
    is_active = Column(Integer, default=1)  # 1 = active, 0 = inactive
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    statements = relationship("Statement", back_populates="minister")