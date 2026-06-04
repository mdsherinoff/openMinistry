from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class QueueItemCreate(BaseModel):
    url: str
    title: Optional[str] = None
    source_name: Optional[str] = None
    published_at: Optional[datetime] = None
    language: str = "en"

class QueueItemResponse(BaseModel):
    id: int
    url: str
    title: Optional[str]
    source_name: Optional[str]
    published_at: Optional[datetime]
    language: str
    status: str
    statements_found: int
    mining_error: Optional[str]
    created_at: datetime
    reviewed_at: Optional[datetime]
    review_notes: Optional[str]

    class Config:
        from_attributes = True

class MinedResultResponse(BaseModel):
    id: int
    queue_item_id: int
    speaker_name: Optional[str]
    speaker_role: Optional[str]
    minister_id: Optional[int]
    statement_text: str
    context_description: Optional[str]
    topic_tag: Optional[str]
    confidence_stars: int
    status: str
    edited_speaker_name: Optional[str]
    edited_statement_text: Optional[str]
    edited_topic: Optional[str]
    statement_id: Optional[int]

    class Config:
        from_attributes = True

class MinedResultUpdate(BaseModel):
    edited_speaker_name: Optional[str] = None
    edited_statement_text: Optional[str] = None
    edited_topic: Optional[str] = None
    minister_id: Optional[int] = None

class ApproveStatementRequest(BaseModel):
    mined_result_id: Optional[int] = None
    statement_text: Optional[str] = None
    minister_id: Optional[int] = None
    topic: Optional[str] = None
    context_text: Optional[str] = None

class NewStatementRequest(BaseModel):
    """For manually adding a statement the miner missed."""
    minister_id: int
    statement_text: str
    topic: Optional[str] = None
    context_text: Optional[str] = None
