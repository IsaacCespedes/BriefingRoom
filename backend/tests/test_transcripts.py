"""Tests for transcript storage functionality."""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api.auth import TokenInfoResponse
from app.api.daily import validate_token_dependency
from app.main import app


@pytest.fixture
def mock_daily_api_key():
    """Set up a mock Daily.co API key."""
    original_key = os.environ.get("DAILY_API_KEY")
    os.environ["DAILY_API_KEY"] = "test-daily-api-key"
    yield
    if original_key:
        os.environ["DAILY_API_KEY"] = original_key
    else:
        os.environ.pop("DAILY_API_KEY", None)


@pytest.fixture
def mock_token_record():
    """Create a mock token record for authentication."""
    return {
        "role": "host",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
    }


@pytest.fixture
def override_auth_dependency(mock_token_record):
    """Override the auth dependency for testing."""
    def override_validate_token():
        return TokenInfoResponse(
            role=mock_token_record["role"],
            interview_id=mock_token_record["interview_id"]
        )
    
    app.dependency_overrides[validate_token_dependency] = override_validate_token
    yield
    app.dependency_overrides.clear()


@pytest.mark.unit
def test_parse_webvtt_to_text():
    """Test parsing WebVTT format to plain text."""
    from app.services.transcript_service import parse_webvtt_to_text
    
    webvtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Speaker 1: Hello, this is a test.

00:00:05.000 --> 00:00:10.000
Speaker 2: Hi there!

00:00:10.000 --> 00:00:15.000
Speaker 1: How are you doing today?"""
    
    result = parse_webvtt_to_text(webvtt_content)
    
    assert "Hello, this is a test." in result
    assert "Hi there!" in result
    assert "How are you doing today?" in result
    assert "00:00:00.000" not in result  # Timestamps should be removed
    assert "WEBVTT" not in result  # Header should be removed


@pytest.mark.unit
def test_parse_webvtt_to_text_empty():
    """Test parsing empty WebVTT content."""
    from app.services.transcript_service import parse_webvtt_to_text
    
    assert parse_webvtt_to_text("") == ""
    assert parse_webvtt_to_text("WEBVTT") == ""


@pytest.mark.unit
def test_parse_webvtt_to_text_no_speakers():
    """Test parsing WebVTT without speaker labels."""
    from app.services.transcript_service import parse_webvtt_to_text
    
    webvtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello, this is a test.

00:00:05.000 --> 00:00:10.000
Hi there!"""
    
    result = parse_webvtt_to_text(webvtt_content)
    
    assert "Hello, this is a test." in result
    assert "Hi there!" in result


@pytest.mark.unit
def test_extract_webvtt_metadata():
    """Test extracting metadata from WebVTT."""
    from app.services.transcript_service import extract_webvtt_metadata
    
    webvtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Speaker 1: Hello, this is a test.

00:00:05.000 --> 00:00:10.000
Speaker 2: Hi there!

00:00:10.000 --> 00:00:30.000
Speaker 1: How are you doing today?"""
    
    metadata = extract_webvtt_metadata(webvtt_content)
    
    assert "duration_seconds" in metadata
    assert metadata["duration_seconds"] == 30  # 30 seconds total
    assert "participant_count" in metadata
    assert metadata["participant_count"] == 2  # Two speakers


@pytest.mark.unit
def test_extract_webvtt_metadata_empty():
    """Test extracting metadata from empty WebVTT."""
    from app.services.transcript_service import extract_webvtt_metadata
    
    metadata = extract_webvtt_metadata("")
    
    assert metadata == {}


@pytest.mark.unit
def test_parse_webvtt_to_segments():
    """Test parsing WebVTT into structured segments with speaker information."""
    from app.services.transcript_service import parse_webvtt_to_segments
    
    webvtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Speaker 0: Hello, this is a test.

00:00:05.000 --> 00:00:10.000
Speaker 1: Hi there!

00:00:10.000 --> 00:00:15.000
Speaker 0: How are you doing today?"""
    
    segments = parse_webvtt_to_segments(webvtt_content)
    
    assert len(segments) == 3
    assert segments[0]["speaker"] == "Speaker 0"
    assert segments[0]["text"] == "Hello, this is a test."
    assert segments[0]["start_time"] == 0.0
    assert segments[0]["end_time"] == 5.0
    
    assert segments[1]["speaker"] == "Speaker 1"
    assert segments[1]["text"] == "Hi there!"
    assert segments[1]["start_time"] == 5.0
    assert segments[1]["end_time"] == 10.0
    
    assert segments[2]["speaker"] == "Speaker 0"
    assert segments[2]["text"] == "How are you doing today?"
    assert segments[2]["start_time"] == 10.0
    assert segments[2]["end_time"] == 15.0


@pytest.mark.unit
def test_parse_webvtt_to_segments_no_speakers():
    """Test parsing WebVTT without speaker labels."""
    from app.services.transcript_service import parse_webvtt_to_segments
    
    webvtt_content = """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello, this is a test.

00:00:05.000 --> 00:00:10.000
Hi there!"""
    
    segments = parse_webvtt_to_segments(webvtt_content)
    
    assert len(segments) == 2
    assert segments[0]["speaker"] is None
    assert segments[0]["text"] == "Hello, this is a test."
    assert segments[1]["speaker"] is None
    assert segments[1]["text"] == "Hi there!"


@pytest.mark.unit
def test_parse_webvtt_to_segments_empty():
    """Test parsing empty WebVTT content."""
    from app.services.transcript_service import parse_webvtt_to_segments
    
    assert parse_webvtt_to_segments("") == []
    assert parse_webvtt_to_segments("WEBVTT") == []


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.services.transcript_service.DAILY_API_KEY", "test-key")
@patch("app.services.transcript_service.httpx.AsyncClient")
async def test_get_daily_transcript_success(mock_client_class):
    """Test successfully fetching transcript from Daily.co."""
    from app.services.transcript_service import get_daily_transcript
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "transcript": """WEBVTT

00:00:00.000 --> 00:00:05.000
Hello, this is a test."""
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await get_daily_transcript("interview-123")
    
    assert result is not None
    assert "transcript" in result
    mock_client.get.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.services.transcript_service.DAILY_API_KEY", "test-key")
@patch("app.services.transcript_service.httpx.AsyncClient")
async def test_get_daily_transcript_not_ready(mock_client_class):
    """Test fetching transcript that is not ready yet."""
    from app.services.transcript_service import get_daily_transcript
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "Not Found", request=MagicMock(), response=mock_response
    )
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await get_daily_transcript("interview-123")
    
    assert result is None  # Transcript not ready yet


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.transcript_service.get_daily_transcript")
@patch("app.db.get_transcript_by_room_name")
async def test_fetch_and_store_transcript_new(
    mock_get_by_room,
    mock_get_daily_transcript,
    mock_daily_api_key,
):
    """Test fetching and storing a new transcript."""
    from app.services.transcript_service import fetch_and_store_transcript
    from app.db import create_interview
    
    # Create an interview first (required for foreign key constraint)
    interview = create_interview(
        job_description="Test job description",
        resume_text="Test resume text",
        status="pending",
    )
    interview_id = str(interview["id"])
    room_name = f"interview-{interview_id}"
    
    # Mock Daily.co API response
    mock_get_daily_transcript.return_value = {
        "transcript": """WEBVTT

00:00:00.000 --> 00:00:05.000
Speaker 0: Hello, this is a test.

00:00:05.000 --> 00:00:30.000
Speaker 1: Hi there!"""
    }
    
    # No existing transcript
    mock_get_by_room.return_value = None
    
    result = await fetch_and_store_transcript(room_name, interview_id)
    
    assert result["status"] == "completed"
    assert "transcript_text" in result
    assert interview_id in result["interview_id"] or result["interview_id"] == interview_id
    # Verify speaker information is preserved
    assert "Hello, this is a test" in result["transcript_text"]
    assert "Hi there!" in result["transcript_text"]


@pytest.mark.integration
@pytest.mark.asyncio
@patch("app.services.transcript_service.get_daily_transcript")
@patch("app.db.get_transcript_by_room_name")
async def test_fetch_and_store_transcript_not_ready(
    mock_get_by_room,
    mock_get_daily_transcript,
    mock_daily_api_key,
):
    """Test fetching transcript when it's not ready yet."""
    from app.services.transcript_service import fetch_and_store_transcript
    from app.db import create_interview
    
    # Create an interview first (required for foreign key constraint)
    interview = create_interview(
        job_description="Test job description",
        resume_text="Test resume text",
        status="pending",
    )
    interview_id = str(interview["id"])
    room_name = f"interview-{interview_id}"
    
    # Transcript not ready yet
    mock_get_daily_transcript.return_value = None
    
    # No existing transcript
    mock_get_by_room.return_value = None
    
    result = await fetch_and_store_transcript(room_name, interview_id)
    
    assert result["status"] == "pending"
    assert result["transcript_text"] == ""  # Empty until transcript is available
    assert interview_id in result["interview_id"] or result["interview_id"] == interview_id


@pytest.mark.integration
@patch("app.api.daily.fetch_and_store_transcript")
def test_fetch_transcript_endpoint_success(
    mock_fetch_transcript,
    mock_daily_api_key,
):
    """Test the fetch transcript endpoint."""
    from datetime import datetime
    from app.db import create_interview
    from app.api.auth import TokenInfoResponse
    from app.api.daily import validate_token_dependency
    
    # Create an interview first (required for foreign key constraint)
    interview = create_interview(
        job_description="Test job description",
        resume_text="Test resume text",
        status="pending",
    )
    interview_id = str(interview["id"])
    
    # Override auth dependency to use the created interview_id
    def override_validate_token():
        return TokenInfoResponse(
            role="host",
            interview_id=interview_id
        )
    
    app.dependency_overrides[validate_token_dependency] = override_validate_token
    
    try:
        # Mock the async function to return a coroutine with all required fields
        # Note: Database returns UUIDs as strings, which Pydantic will parse
        from uuid import uuid4
        
        transcript_uuid = str(uuid4())
        now = datetime.now()
        
        async def mock_fetch(*args, **kwargs):
            return {
                "id": transcript_uuid,
                "interview_id": interview_id,  # String UUID from database
                "daily_room_name": f"interview-{interview_id}",
                "transcript_text": "Hello, this is a test.",
                "transcript_webvtt": None,
                "transcript_data": None,
                "started_at": None,
                "ended_at": None,
                "duration_seconds": None,
                "participant_count": None,
                "status": "completed",
                "created_at": now.isoformat(),
                "updated_at": now.isoformat(),
            }
        
        mock_fetch_transcript.side_effect = mock_fetch
        
        client = TestClient(app)
        response = client.post(
            f"/api/daily/fetch-transcript/{interview_id}",
            headers={"Authorization": "Bearer test-token"},
        )
        
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.text}")
            # Re-raise to see the actual error
            raise AssertionError(f"Expected 200, got {response.status_code}: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert "transcript_text" in data
        mock_fetch_transcript.assert_called_once()
    finally:
        app.dependency_overrides.clear()


@pytest.mark.integration
def test_fetch_transcript_endpoint_mismatched_interview_id(
    mock_daily_api_key,
    override_auth_dependency,
):
    """Test that fetch transcript fails when interview_id doesn't match token."""
    client = TestClient(app)
    response = client.post(
        "/api/daily/fetch-transcript/different-interview-id",
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 403
    assert "Interview ID in path does not match" in response.json()["detail"]


@pytest.mark.integration
@patch("app.services.transcript_service.DAILY_API_KEY", None)
def test_fetch_transcript_endpoint_missing_api_key(override_auth_dependency):
    """Test that fetch transcript fails when Daily.co API key is missing."""
    interview_id = "123e4567-e89b-12d3-a456-426614174000"
    
    client = TestClient(app)
    response = client.post(
        f"/api/daily/fetch-transcript/{interview_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 500
    assert "Daily.co API key" in response.json().get("detail", "")
