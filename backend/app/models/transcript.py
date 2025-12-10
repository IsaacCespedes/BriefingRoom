"""Transcript models."""

from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any, List

from pydantic import BaseModel, Field


class TranscriptSegment(BaseModel):
    """A single segment of transcript with speaker information."""
    
    speaker: Optional[str] = None
    text: str
    start_time: float
    end_time: float


class TranscriptBase(BaseModel):
    """Base transcript model with common fields."""

    interview_id: UUID
    daily_room_name: str
    transcript_text: str
    transcript_webvtt: Optional[str] = None
    transcript_data: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Structured transcript data with speaker segments. Format: {'segments': [{'speaker': 'Speaker 0', 'text': '...', 'start_time': 0.0, 'end_time': 5.0}, ...]}"
    )
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    participant_count: Optional[int] = None
    status: str = Field(default="pending", description="Transcript status: pending, processing, completed, failed")


class TranscriptCreate(TranscriptBase):
    """Model for creating a new transcript."""

    pass


class Transcript(TranscriptBase):
    """Full transcript model with database fields."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TranscriptResponse(TranscriptBase):
    """Transcript response model for API responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime
