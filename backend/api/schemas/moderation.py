from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ModerationAction(BaseModel):
    action: str  # approved | rejected | edited | flagged | needs_review
    notes: Optional[str] = None
    edited_text: Optional[str] = None


class ModerationLogResponse(BaseModel):
    id: int
    statement_id: int
    reviewer_id: int
    action: str
    notes: Optional[str]
    previous_text: Optional[str]
    timestamp: datetime

    class Config:
        from_attributes = True


class StatementWithContext(BaseModel):
    """Full statement with article and minister context for review."""
    id: int
    statement_text: str
    statement_summary: Optional[str]
    topic: Optional[str]
    confidence_score: Optional[float]
    statement_date: Optional[datetime]
    status: str
    created_at: datetime

    # Minister info
    minister_id: int
    minister_name: str
    minister_portfolio: Optional[str]

    # Article info
    article_id: int
    article_title: Optional[str]
    article_url: str
    article_source: Optional[str]
    article_published_at: Optional[datetime]

    class Config:
        from_attributes = True