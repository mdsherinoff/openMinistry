from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class StatementResponse(BaseModel):
    id: int
    minister_id: int
    article_id: int
    statement_text: str
    statement_summary: Optional[str]
    topic: Optional[str]
    confidence_score: Optional[float]
    statement_date: Optional[datetime]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

class StatementUpdate(BaseModel):
    statement_text: Optional[str] = None
    statement_summary: Optional[str] = None
    topic: Optional[str] = None
    status: Optional[str] = None


class StatementFlagRequest(BaseModel):
    reason: Optional[str] = None