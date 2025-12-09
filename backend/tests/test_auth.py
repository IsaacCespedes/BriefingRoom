"""Tests for authentication endpoints and utilities."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import (
    hash_token,
    get_token_from_header,
    validate_token_dependency,
)
from app.main import app


@pytest.mark.unit
def test_hash_token():
    """Test that hash_token correctly hashes a token using SHA-256."""
    token = "test-token-123"
    expected_hash = hashlib.sha256(token.encode()).hexdigest()
    
    result = hash_token(token)
    
    assert result == expected_hash
    assert len(result) == 64  # SHA-256 produces 64 hex characters


@pytest.mark.unit
def test_hash_token_different_tokens_produce_different_hashes():
    """Test that different tokens produce different hashes."""
    token1 = "token-1"
    token2 = "token-2"
    
    hash1 = hash_token(token1)
    hash2 = hash_token(token2)
    
    assert hash1 != hash2


@pytest.mark.unit
def test_hash_token_same_token_produces_same_hash():
    """Test that the same token always produces the same hash."""
    token = "test-token"
    
    hash1 = hash_token(token)
    hash2 = hash_token(token)
    
    assert hash1 == hash2


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_token_from_header_valid_bearer_token():
    """Test extracting token from valid Authorization header."""
    authorization = "Bearer test-token-123"
    
    token = await get_token_from_header(authorization=authorization)
    
    assert token == "test-token-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_token_from_header_case_insensitive_bearer():
    """Test that Bearer keyword is case-insensitive."""
    authorization = "bearer test-token-123"
    
    token = await get_token_from_header(authorization=authorization)
    
    assert token == "test-token-123"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_token_from_header_missing_authorization():
    """Test that missing Authorization header raises 401."""
    with pytest.raises(HTTPException) as exc_info:
        await get_token_from_header(authorization=None)
    
    assert exc_info.value.status_code == 401
    assert "Authorization header is required" in exc_info.value.detail
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_token_from_header_invalid_format():
    """Test that invalid Authorization header format raises 401."""
    authorization = "InvalidFormat test-token"
    
    with pytest.raises(HTTPException) as exc_info:
        await get_token_from_header(authorization=authorization)
    
    assert exc_info.value.status_code == 401
    assert "Invalid authorization header format" in exc_info.value.detail
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_token_from_header_token_with_spaces():
    """Test that token with spaces is extracted correctly."""
    authorization = "Bearer token with spaces in it"
    
    token = await get_token_from_header(authorization=authorization)
    
    assert token == "token with spaces in it"


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.api.auth.get_token_by_hash")
@patch("app.api.auth.hash_token")
async def test_validate_token_dependency_valid_token(mock_hash_token, mock_get_token):
    """Test validate_token_dependency with a valid token."""
    mock_token_record = {
        "role": "host",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
    }
    mock_get_token.return_value = mock_token_record
    mock_hash_token.return_value = "hashed-token"
    
    token = "valid-token"
    
    result = await validate_token_dependency(token=token)
    
    assert result.role == "host"
    assert result.interview_id == "123e4567-e89b-12d3-a456-426614174000"
    mock_hash_token.assert_called_once_with(token)
    mock_get_token.assert_called_once_with("hashed-token")


@pytest.mark.unit
@pytest.mark.asyncio
@patch("app.db.get_token_by_hash")
async def test_validate_token_dependency_invalid_token(mock_get_token):
    """Test validate_token_dependency with an invalid token."""
    mock_get_token.return_value = None
    
    token = "invalid-token"
    
    with pytest.raises(HTTPException) as exc_info:
        await validate_token_dependency(token=token)
    
    assert exc_info.value.status_code == 401
    assert "Invalid or expired token" in exc_info.value.detail
    assert exc_info.value.headers == {"WWW-Authenticate": "Bearer"}


@pytest.mark.integration
@patch("app.api.auth.get_token_by_hash")
@patch("app.api.auth.hash_token")
def test_validate_token_endpoint_valid_token(mock_hash_token, mock_get_token):
    """Test the /validate-token endpoint with a valid token."""
    mock_token_record = {
        "role": "candidate",
        "interview_id": "456e7890-e89b-12d3-a456-426614174001",
    }
    mock_get_token.return_value = mock_token_record
    mock_hash_token.return_value = "hashed-token-123"
    
    client = TestClient(app)
    response = client.get("/api/validate-token?token=valid-token-123")
    
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "candidate"
    assert data["interview_id"] == "456e7890-e89b-12d3-a456-426614174001"


@pytest.mark.integration
@patch("app.db.get_token_by_hash")
def test_validate_token_endpoint_invalid_token(mock_get_token):
    """Test the /validate-token endpoint with an invalid token."""
    mock_get_token.return_value = None
    
    client = TestClient(app)
    response = client.get("/api/validate-token?token=invalid-token")
    
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["detail"]


@pytest.mark.integration
def test_validate_token_endpoint_missing_token():
    """Test the /validate-token endpoint without a token."""
    client = TestClient(app)
    response = client.get("/api/validate-token")
    
    assert response.status_code == 422  # Validation error

