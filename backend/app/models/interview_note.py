"""Interview note models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewNoteBase(BaseModel):
    """Base interview note model with common fields."""

    note: str
    source: str = Field(description="Origin of the note (e.g., 'CrewAI', 'Host', 'System')")


class InterviewNoteCreate(InterviewNoteBase):
    """Model for creating a new interview note."""

    interview_id: UUID


class InterviewNote(InterviewNoteBase):
    """Full interview note model with database fields."""

    id: UUID
    interview_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewNoteResponse(InterviewNoteBase):
    """Interview note response model for API responses."""

    id: UUID
    interview_id: UUID
    created_at: datetime

