"""Integration tests for the /interviews endpoint."""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.mark.integration
def test_create_interview_requires_job_description():
    """Test that creating an interview requires job_description."""
    client = TestClient(app)
    response = client.post(
        "/api/interviews",
        json={"resume_text": "Sample resume"},
    )
    assert response.status_code == 422


@pytest.mark.integration
def test_create_interview_requires_resume_text():
    """Test that creating an interview requires resume_text."""
    client = TestClient(app)
    response = client.post(
        "/api/interviews",
        json={"job_description": "Sample job description"},
    )
    assert response.status_code == 422


@pytest.mark.integration
@patch("app.api.interviews.db_create_interview")
@patch("app.api.interviews.db_create_token")
def test_create_interview_success(mock_create_token, mock_create_interview):
    """Test successful interview creation."""
    import uuid
    
    interview_id = uuid.uuid4()
    mock_create_interview.return_value = {
        "id": str(interview_id),
        "job_description": "Software Engineer position",
        "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        "status": "pending",
    }
    mock_create_token.return_value = {"id": "token-id"}
    
    client = TestClient(app)
    response = client.post(
        "/api/interviews",
        json={
            "job_description": "Software Engineer position",
            "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "interview_id" in data
    assert "host_token" in data
    assert "candidate_token" in data
    assert len(data["host_token"]) > 0
    assert len(data["candidate_token"]) > 0
    assert data["host_token"] != data["candidate_token"]


@pytest.mark.integration
@patch("app.api.interviews.db_create_interview")
@patch("app.api.interviews.db_create_token")
def test_create_interview_returns_valid_uuid(mock_create_token, mock_create_interview):
    """Test that interview_id is a valid UUID."""
    import uuid

    interview_id = uuid.uuid4()
    mock_create_interview.return_value = {
        "id": str(interview_id),
        "job_description": "Software Engineer position",
        "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        "status": "pending",
    }
    mock_create_token.return_value = {"id": "token-id"}
    
    client = TestClient(app)
    response = client.post(
        "/api/interviews",
        json={
            "job_description": "Software Engineer position",
            "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        },
    )

    assert response.status_code == 200
    data = response.json()
    # Should be able to parse as UUID
    uuid.UUID(data["interview_id"])


@pytest.mark.integration
@patch("app.api.interviews.db_get_interview")
@patch("app.api.interviews.db_create_interview")
@patch("app.api.interviews.db_create_token")
def test_get_interview_success(mock_create_token, mock_create_interview, mock_get_interview):
    """Test getting an interview by ID."""
    import uuid
    
    interview_id = uuid.uuid4()
    interview_id_str = str(interview_id)
    
    mock_create_interview.return_value = {
        "id": interview_id_str,
        "job_description": "Software Engineer position",
        "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        "status": "pending",
    }
    mock_create_token.return_value = {"id": "token-id"}
    mock_get_interview.return_value = {
        "id": interview_id_str,
        "job_description": "Software Engineer position",
        "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        "status": "pending",
        "created_at": "2024-01-01T00:00:00Z",
    }
    
    client = TestClient(app)
    
    # First create an interview
    create_response = client.post(
        "/api/interviews",
        json={
            "job_description": "Software Engineer position",
            "resume_text": "John Doe\nSoftware Engineer\n5 years experience",
        },
    )
    assert create_response.status_code == 200
    created_interview_id = create_response.json()["interview_id"]
    
    # Then get it
    get_response = client.get(f"/api/interviews/{created_interview_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == created_interview_id
    assert data["job_description"] == "Software Engineer position"
    assert data["resume_text"] == "John Doe\nSoftware Engineer\n5 years experience"


@pytest.mark.integration
@patch("app.api.interviews.db_get_interview")
def test_get_interview_not_found(mock_get_interview):
    """Test getting a non-existent interview returns 404."""
    mock_get_interview.return_value = None
    
    client = TestClient(app)
    response = client.get("/api/interviews/non-existent-id")
    assert response.status_code == 404

