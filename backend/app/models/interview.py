"""Interview models."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class InterviewBase(BaseModel):
    """Base interview model with common fields."""

    job_description: Optional[str] = None  # Text content OR file path OR URL
    resume_text: Optional[str] = None  # Text content OR file path OR URL
    status: str = Field(default="pending", description="Interview status")
    
    # Source tracking
    job_description_source: str = Field(default="text", description="Source type: text, pdf, docx, url")
    resume_source: str = Field(default="text", description="Source type: text, pdf, docx, url")
    
    # Metadata
    job_description_metadata: Optional[dict] = Field(default=None, description="Metadata about the source")
    resume_metadata: Optional[dict] = Field(default=None, description="Metadata about the source")
    
    # File paths or URLs
    job_description_path: Optional[str] = Field(default=None, description="File path or URL (if not text)")
    resume_path: Optional[str] = Field(default=None, description="File path or URL (if not text)")


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

