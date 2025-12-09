"""Tests for Daily.co room management endpoints."""

import os
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.integration
@patch("app.api.daily.create_daily_room")
@patch("app.api.daily.create_meeting_token")
def test_create_room_success(
    mock_create_token,
    mock_create_room,
    mock_daily_api_key,
    override_auth_dependency,
):
    """Test successful room creation."""
    mock_room_data = {
        "id": "interview-123e4567-e89b-12d3-a456-426614174000",
        "name": "interview-123e4567-e89b-12d3-a456-426614174000",
        "url": "https://test.daily.co/interview-123e4567-e89b-12d3-a456-426614174000",
    }
    mock_create_room.return_value = mock_room_data
    mock_create_token.return_value = "meeting-token-123"
    
    client = TestClient(app)
    response = client.post(
        "/api/daily/create-room",
        json={"interview_id": "123e4567-e89b-12d3-a456-426614174000"},
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "room_url" in data
    assert data["room_url"] == mock_room_data["url"]
    assert "room_token" in data


@pytest.mark.integration
@patch("app.api.daily.DAILY_API_KEY", None)
def test_create_room_missing_api_key(override_auth_dependency):
    """Test that room creation fails when Daily.co API key is missing."""
    client = TestClient(app)
    response = client.post(
        "/api/daily/create-room",
        json={"interview_id": "123e4567-e89b-12d3-a456-426614174000"},
        headers={"Authorization": "Bearer test-token"},
    )
    
    # The endpoint should fail with 500 when API key is missing
    assert response.status_code == 500
    assert "Daily.co API key" in response.json().get("detail", "")


@pytest.mark.integration
def test_create_room_mismatched_interview_id(mock_daily_api_key, override_auth_dependency):
    """Test that room creation fails when interview_id doesn't match token."""
    client = TestClient(app)
    response = client.post(
        "/api/daily/create-room",
        json={"interview_id": "different-interview-id"},
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 403
    assert "Interview ID in request does not match" in response.json()["detail"]


@pytest.mark.integration
@patch("app.api.daily.get_daily_room")
@patch("app.api.daily.create_meeting_token")
def test_get_room_success(
    mock_create_token,
    mock_get_room,
    mock_daily_api_key,
    override_auth_dependency,
):
    """Test successfully getting an existing room."""
    interview_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_room_data = {
        "id": f"interview-{interview_id}",
        "name": f"interview-{interview_id}",
        "url": f"https://test.daily.co/interview-{interview_id}",
    }
    mock_get_room.return_value = mock_room_data
    mock_create_token.return_value = "meeting-token-456"
    
    client = TestClient(app)
    response = client.get(
        f"/api/daily/room/{interview_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "room_url" in data
    assert data["room_url"] == mock_room_data["url"]


@pytest.mark.integration
@patch("app.api.daily.get_daily_room")
def test_get_room_not_found(
    mock_get_room,
    mock_daily_api_key,
    override_auth_dependency,
):
    """Test getting a room that doesn't exist."""
    from fastapi import HTTPException
    
    interview_id = "123e4567-e89b-12d3-a456-426614174000"
    mock_get_room.side_effect = HTTPException(status_code=404, detail="Room not found")
    
    client = TestClient(app)
    response = client.get(
        f"/api/daily/room/{interview_id}",
        headers={"Authorization": "Bearer test-token"},
    )
    
    assert response.status_code == 404


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.daily.DAILY_API_KEY", "test-key")
@patch("app.api.daily.httpx.AsyncClient")
async def test_create_daily_room_function(mock_client_class):
    """Test the create_daily_room helper function."""
    from app.api.daily import create_daily_room
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "test-room",
        "name": "test-room",
        "url": "https://test.daily.co/test-room",
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await create_daily_room("test-room", privacy="public")
    
    assert result["name"] == "test-room"
    assert "url" in result
    mock_client.post.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.daily.DAILY_API_KEY", "test-key")
@patch("app.api.daily.httpx.AsyncClient")
async def test_get_daily_room_function(mock_client_class):
    """Test the get_daily_room helper function."""
    from app.api.daily import get_daily_room
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "id": "test-room",
        "name": "test-room",
        "url": "https://test.daily.co/test-room",
    }
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await get_daily_room("test-room")
    
    assert result["name"] == "test-room"
    assert "url" in result
    mock_client.get.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.daily.DAILY_API_KEY", "test-key")
@patch("app.api.daily.httpx.AsyncClient")
async def test_create_meeting_token_function(mock_client_class):
    """Test the create_meeting_token helper function."""
    from app.api.daily import create_meeting_token
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": "meeting-token-123"}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await create_meeting_token("test-room")
    
    assert result == "meeting-token-123"
    mock_client.post.assert_called_once()


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.daily.DAILY_API_KEY", "test-key")
@patch("app.api.daily.httpx.AsyncClient")
async def test_create_meeting_token_returns_none_on_empty(mock_client_class):
    """Test that create_meeting_token returns None when token is empty."""
    from app.api.daily import create_meeting_token
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"token": ""}
    mock_response.raise_for_status = MagicMock()
    
    mock_client = AsyncMock()
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None
    mock_client.post = AsyncMock(return_value=mock_response)
    mock_client_class.return_value = mock_client
    
    result = await create_meeting_token("test-room")
    
    assert result is None
