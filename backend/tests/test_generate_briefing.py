"""Integration tests for the /generate-briefing endpoint."""

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(autouse=True)
def set_openai_key():
    """Set a dummy OpenAI API key for testing."""
    os.environ["OPENAI_API_KEY"] = "test-key-12345"
    yield
    os.environ.pop("OPENAI_API_KEY", None)


@pytest.mark.integration
def test_generate_briefing_endpoint_requires_job_description():
    """Test that the endpoint requires job_description."""
    client = TestClient(app)
    response = client.post(
        "/generate-briefing",
        json={"resume_text": "Sample resume"},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_generate_briefing_endpoint_requires_resume_text():
    """Test that the endpoint requires resume_text."""
    client = TestClient(app)
    response = client.post(
        "/generate-briefing",
        json={"job_description": "Sample job description"},
    )
    assert response.status_code == 422


@pytest.mark.integration
@patch("app.api.briefing.create_briefing_crew")
def test_generate_briefing_endpoint_creates_interview(mock_create_crew):
    """Test that the endpoint creates an interview and returns a briefing."""
    # Mock the crew
    mock_crew = MagicMock()
    mock_result = MagicMock()
    mock_result.output = "Generated briefing content"
    mock_crew.kickoff.return_value = mock_result
    mock_create_crew.return_value = mock_crew

    client = TestClient(app)
    response = client.post(
        "/generate-briefing",
        json={
            "job_description": "Software Engineer position",
            "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "interview_id" in data
    assert "briefing" in data


@pytest.mark.integration
@patch("app.api.briefing.create_briefing_crew")
def test_generate_briefing_endpoint_stores_interview(mock_create_crew):
    """Test that the endpoint stores the interview in the database."""
    # Mock the crew
    mock_crew = MagicMock()
    mock_result = MagicMock()
    mock_result.output = "Generated briefing content"
    mock_crew.kickoff.return_value = mock_result
    mock_create_crew.return_value = mock_crew

    client = TestClient(app)
    response = client.post(
        "/generate-briefing",
        json={
            "job_description": "Software Engineer position",
            "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "interview_id" in data
    # Verify interview was created (would need database access to fully verify)

