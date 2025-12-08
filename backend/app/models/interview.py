"""Interview models."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewBase(BaseModel):
    """Base interview model with common fields."""

    job_description: str
    resume_text: str
    status: str = Field(default="pending", description="Interview status")


class InterviewCreate(InterviewBase):
    """Model for creating a new interview."""

    pass


class Interview(InterviewBase):
    """Full interview model with database fields."""

    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewResponse(InterviewBase):
    """Interview response model for API responses."""

    id: UUID
    created_at: datetime

