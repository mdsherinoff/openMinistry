from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class SourceCreate(BaseModel):
    name: str
    website: str
    language: str  # 'ml' or 'en'
    credibility_score: float = 1.0
    scrape_frequency_minutes: int = 60
    is_active: int = 1


class SourceUpdate(BaseModel):
    name: Optional[str] = None
    credibility_score: Optional[float] = None
    scrape_frequency_minutes: Optional[int] = None
    is_active: Optional[int] = None


class SourceResponse(BaseModel):
    id: int
    name: str
    website: str
    language: str
    credibility_score: float
    scrape_frequency_minutes: int
    is_active: int
    created_at: datetime

    class Config:
        from_attributes = True