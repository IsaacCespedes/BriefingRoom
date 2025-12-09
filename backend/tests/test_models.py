"""Tests for Pydantic models."""

from datetime import datetime
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from app.models.interview import (
    InterviewBase,
    InterviewCreate,
    Interview,
    InterviewResponse,
)
from app.models.interview_note import (
    InterviewNoteBase,
    InterviewNoteCreate,
    InterviewNote,
    InterviewNoteResponse,
)


class TestInterviewModels:
    """Tests for interview-related models."""

    def test_interview_base_creation(self):
        """Test creating an InterviewBase instance."""
        interview = InterviewBase(
            job_description="Software Engineer position",
            resume_text="John Doe resume",
        )
        
        assert interview.job_description == "Software Engineer position"
        assert interview.resume_text == "John Doe resume"
        assert interview.status == "pending"  # Default value

    def test_interview_base_custom_status(self):
        """Test InterviewBase with custom status."""
        interview = InterviewBase(
            job_description="Software Engineer position",
            resume_text="John Doe resume",
            status="completed",
        )
        
        assert interview.status == "completed"

    def test_interview_base_missing_fields(self):
        """Test that InterviewBase requires job_description and resume_text."""
        with pytest.raises(ValidationError):
            InterviewBase(job_description="Software Engineer position")
        
        with pytest.raises(ValidationError):
            InterviewBase(resume_text="John Doe resume")

    def test_interview_create(self):
        """Test creating an InterviewCreate instance."""
        interview = InterviewCreate(
            job_description="Software Engineer position",
            resume_text="John Doe resume",
        )
        
        assert interview.job_description == "Software Engineer position"
        assert interview.resume_text == "John Doe resume"
        assert isinstance(interview, InterviewBase)

    def test_interview_full_model(self):
        """Test creating a full Interview model with database fields."""
        interview_id = uuid4()
        created_at = datetime.now()
        
        interview = Interview(
            id=interview_id,
            job_description="Software Engineer position",
            resume_text="John Doe resume",
            status="pending",
            created_at=created_at,
        )
        
        assert interview.id == interview_id
        assert interview.created_at == created_at
        assert interview.job_description == "Software Engineer position"

    def test_interview_response(self):
        """Test creating an InterviewResponse model."""
        interview_id = uuid4()
        created_at = datetime.now()
        
        response = InterviewResponse(
            id=interview_id,
            job_description="Software Engineer position",
            resume_text="John Doe resume",
            status="pending",
            created_at=created_at,
        )
        
        assert response.id == interview_id
        assert response.created_at == created_at


class TestInterviewNoteModels:
    """Tests for interview note-related models."""

    def test_interview_note_base_creation(self):
        """Test creating an InterviewNoteBase instance."""
        note = InterviewNoteBase(
            note="Interview went well",
            source="Host",
        )
        
        assert note.note == "Interview went well"
        assert note.source == "Host"

    def test_interview_note_base_missing_fields(self):
        """Test that InterviewNoteBase requires note and source."""
        with pytest.raises(ValidationError):
            InterviewNoteBase(note="Interview went well")
        
        with pytest.raises(ValidationError):
            InterviewNoteBase(source="Host")

    def test_interview_note_create(self):
        """Test creating an InterviewNoteCreate instance."""
        interview_id = uuid4()
        
        note = InterviewNoteCreate(
            interview_id=interview_id,
            note="Interview went well",
            source="Host",
        )
        
        assert note.interview_id == interview_id
        assert note.note == "Interview went well"
        assert note.source == "Host"
        assert isinstance(note, InterviewNoteBase)

    def test_interview_note_full_model(self):
        """Test creating a full InterviewNote model with database fields."""
        note_id = uuid4()
        interview_id = uuid4()
        created_at = datetime.now()
        
        note = InterviewNote(
            id=note_id,
            interview_id=interview_id,
            note="Interview went well",
            source="Host",
            created_at=created_at,
        )
        
        assert note.id == note_id
        assert note.interview_id == interview_id
        assert note.created_at == created_at
        assert note.note == "Interview went well"

    def test_interview_note_response(self):
        """Test creating an InterviewNoteResponse model."""
        note_id = uuid4()
        interview_id = uuid4()
        created_at = datetime.now()
        
        response = InterviewNoteResponse(
            id=note_id,
            interview_id=interview_id,
            note="Interview went well",
            source="Host",
            created_at=created_at,
        )
        
        assert response.id == note_id
        assert response.interview_id == interview_id
        assert response.created_at == created_at

    def test_interview_note_source_variations(self):
        """Test InterviewNoteBase with different source values."""
        sources = ["Host", "Candidate", "System", "CrewAI"]
        
        for source in sources:
            note = InterviewNoteBase(
                note="Test note",
                source=source,
            )
            assert note.source == source


class TestModelSerialization:
    """Tests for model serialization and JSON conversion."""

    def test_interview_base_to_dict(self):
        """Test converting InterviewBase to dictionary."""
        interview = InterviewBase(
            job_description="Software Engineer position",
            resume_text="John Doe resume",
            status="pending",
        )
        
        data = interview.model_dump()
        
        assert data["job_description"] == "Software Engineer position"
        assert data["resume_text"] == "John Doe resume"
        assert data["status"] == "pending"

    def test_interview_to_json(self):
        """Test converting Interview to JSON string."""
        interview_id = uuid4()
        created_at = datetime.now()
        
        interview = Interview(
            id=interview_id,
            job_description="Software Engineer position",
            resume_text="John Doe resume",
            status="pending",
            created_at=created_at,
        )
        
        json_str = interview.model_dump_json()
        
        assert isinstance(json_str, str)
        assert str(interview_id) in json_str
        assert "Software Engineer position" in json_str

    def test_interview_note_to_dict(self):
        """Test converting InterviewNoteBase to dictionary."""
        note = InterviewNoteBase(
            note="Interview went well",
            source="Host",
        )
        
        data = note.model_dump()
        
        assert data["note"] == "Interview went well"
        assert data["source"] == "Host"

