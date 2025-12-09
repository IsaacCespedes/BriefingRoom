"""Integration tests for the /interviews endpoint."""

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
def test_create_interview_success():
    """Test successful interview creation."""
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
def test_create_interview_returns_valid_uuid():
    """Test that interview_id is a valid UUID."""
    import uuid

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
def test_get_interview_success():
    """Test getting an interview by ID."""
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
    interview_id = create_response.json()["interview_id"]
    
    # Then get it
    get_response = client.get(f"/api/interviews/{interview_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == interview_id
    assert data["job_description"] == "Software Engineer position"
    assert data["resume_text"] == "John Doe\nSoftware Engineer\n5 years experience"


@pytest.mark.integration
def test_get_interview_not_found():
    """Test getting a non-existent interview returns 404."""
    client = TestClient(app)
    response = client.get("/api/interviews/non-existent-id")
    assert response.status_code == 404

