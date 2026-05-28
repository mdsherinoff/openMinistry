from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime


class MinisterCreate(BaseModel):
    name: str
    name_malayalam: Optional[str] = None
    portfolio: Optional[str] = None
    party: Optional[str] = None
    constituency: Optional[str] = None
    start_date: Optional[date] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None
    is_active: int = 1


class MinisterUpdate(BaseModel):
    name: Optional[str] = None
    name_malayalam: Optional[str] = None
    portfolio: Optional[str] = None
    party: Optional[str] = None
    constituency: Optional[str] = None
    is_active: Optional[int] = None
    bio: Optional[str] = None
    image_url: Optional[str] = None


class MinisterResponse(BaseModel):
    id: int
    name: str
    name_malayalam: Optional[str]
    portfolio: Optional[str]
    party: Optional[str]
    constituency: Optional[str]
    is_active: int
    start_date: Optional[date]
    bio: Optional[str]
    image_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True