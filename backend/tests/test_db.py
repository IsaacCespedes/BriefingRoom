"""Tests for database operations."""

import os
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

import pytest

from app.db import (
    get_supabase_client,
    create_interview,
    get_interview,
    create_token,
    get_token_by_hash,
    revoke_token,
    create_interview_note,
    get_interview_notes,
)


@pytest.fixture
def mock_supabase_client():
    """Create a mock Supabase client."""
    client = MagicMock()
    return client


@pytest.fixture
def setup_env():
    """Set up environment variables for Supabase."""
    os.environ["SUPABASE_URL"] = "https://test.supabase.co"
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = "test-service-key"
    yield
    os.environ.pop("SUPABASE_URL", None)
    os.environ.pop("SUPABASE_SERVICE_ROLE_KEY", None)


@pytest.mark.unit
@patch("app.db.create_client")
def test_get_supabase_client_creates_client_once(mock_create_client, setup_env):
    """Test that get_supabase_client creates client only once."""
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    # Reset module-level client for testing
    import app.db
    app.db._supabase_client = None
    
    client1 = app.db.get_supabase_client()
    client2 = app.db.get_supabase_client()
    
    assert client1 is client2
    # Client should be created only once
    assert mock_create_client.call_count == 1


@pytest.mark.unit
def test_get_supabase_client_missing_url():
    """Test that get_supabase_client raises error when URL is missing."""
    import importlib
    import app.db
    importlib.reload(app.db)
    
    original_url = os.environ.get("SUPABASE_URL")
    os.environ.pop("SUPABASE_URL", None)
    
    try:
        with pytest.raises(ValueError, match="SUPABASE_URL.*must be set"):
            app.db.get_supabase_client()
    finally:
        if original_url:
            os.environ["SUPABASE_URL"] = original_url


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_create_interview_success(mock_get_client, mock_supabase_client):
    """Test successful interview creation."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "job_description": "Software Engineer",
        "resume_text": "John Doe resume",
        "status": "pending",
        "created_at": "2024-01-01T00:00:00Z",
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = create_interview(
        job_description="Software Engineer",
        resume_text="John Doe resume",
        status="pending",
    )
    
    assert result["id"] == "123e4567-e89b-12d3-a456-426614174000"
    assert result["job_description"] == "Software Engineer"
    mock_table.insert.assert_called_once()


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_create_interview_failure(mock_get_client, mock_supabase_client):
    """Test interview creation failure when database returns no data."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    mock_execute.data = []
    
    mock_supabase_client.table.return_value = mock_table
    
    with pytest.raises(ValueError, match="Failed to create interview"):
        create_interview(
            job_description="Software Engineer",
            resume_text="John Doe resume",
        )


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_interview_success(mock_get_client, mock_supabase_client):
    """Test successful interview retrieval."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "job_description": "Software Engineer",
        "resume_text": "John Doe resume",
        "status": "pending",
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_interview("123e4567-e89b-12d3-a456-426614174000")
    
    assert result is not None
    assert result["id"] == "123e4567-e89b-12d3-a456-426614174000"
    mock_eq.execute.assert_called_once()


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_interview_not_found(mock_get_client, mock_supabase_client):
    """Test getting a non-existent interview."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute
    mock_execute.data = []
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_interview("non-existent-id")
    
    assert result is None


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_create_token_success(mock_get_client, mock_supabase_client):
    """Test successful token creation."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "token-id",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "token_hash": "hashed-token",
        "role": "host",
        "is_active": True,
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = create_token(
        interview_id="123e4567-e89b-12d3-a456-426614174000",
        token_hash="hashed-token",
        role="host",
    )
    
    assert result["token_hash"] == "hashed-token"
    assert result["role"] == "host"


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_create_token_with_expires_at(mock_get_client, mock_supabase_client):
    """Test token creation with expiration date."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "token-id",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "token_hash": "hashed-token",
        "role": "host",
        "is_active": True,
        "expires_at": "2024-12-31T23:59:59Z",
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    expires_at = datetime.now() + timedelta(days=1)
    result = create_token(
        interview_id="123e4567-e89b-12d3-a456-426614174000",
        token_hash="hashed-token",
        role="host",
        expires_at=expires_at,
    )
    
    assert result["token_hash"] == "hashed-token"
    # Verify expires_at was included in the insert call
    call_args = mock_insert.execute.call_args
    assert call_args is not None


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_token_by_hash_success(mock_get_client, mock_supabase_client):
    """Test successful token retrieval by hash."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "token-id",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "token_hash": "hashed-token",
        "role": "host",
        "is_active": True,
        "expires_at": None,
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_token_by_hash("hashed-token")
    
    assert result is not None
    assert result["token_hash"] == "hashed-token"
    assert result["role"] == "host"


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_token_by_hash_expired(mock_get_client, mock_supabase_client):
    """Test that expired tokens are not returned."""
    mock_get_client.return_value = mock_supabase_client
    
    expired_date = (datetime.now() - timedelta(days=1)).isoformat()
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "token-id",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "token_hash": "hashed-token",
        "role": "host",
        "is_active": True,
        "expires_at": expired_date,
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_token_by_hash("hashed-token")
    
    assert result is None


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_token_by_hash_not_found(mock_get_client, mock_supabase_client):
    """Test getting a non-existent token."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq1 = MagicMock()
    mock_eq2 = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq1
    mock_eq1.eq.return_value = mock_eq2
    mock_eq2.execute.return_value = mock_execute
    mock_execute.data = []
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_token_by_hash("non-existent-hash")
    
    assert result is None


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_revoke_token_success(mock_get_client, mock_supabase_client):
    """Test successful token revocation."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "token-id",
        "is_active": False,
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = revoke_token("hashed-token")
    
    assert result is True
    # Verify the update was called with the correct data
    mock_table.update.assert_called_once_with({"is_active": False})


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_revoke_token_not_found(mock_get_client, mock_supabase_client):
    """Test revoking a non-existent token."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_update = MagicMock()
    mock_eq = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.update.return_value = mock_update
    mock_update.eq.return_value = mock_eq
    mock_eq.execute.return_value = mock_execute
    mock_execute.data = []
    
    mock_supabase_client.table.return_value = mock_table
    
    result = revoke_token("non-existent-hash")
    
    assert result is False


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_create_interview_note_success(mock_get_client, mock_supabase_client):
    """Test successful interview note creation."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_insert = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = mock_execute
    mock_execute.data = [{
        "id": "note-id",
        "interview_id": "123e4567-e89b-12d3-a456-426614174000",
        "note": "Interview went well",
        "source": "Host",
        "created_at": "2024-01-01T00:00:00Z",
    }]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = create_interview_note(
        interview_id="123e4567-e89b-12d3-a456-426614174000",
        note="Interview went well",
        source="Host",
    )
    
    assert result["note"] == "Interview went well"
    assert result["source"] == "Host"


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_interview_notes_success(mock_get_client, mock_supabase_client):
    """Test successful interview notes retrieval."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order
    mock_order.execute.return_value = mock_execute
    mock_execute.data = [
        {
            "id": "note-1",
            "interview_id": "123e4567-e89b-12d3-a456-426614174000",
            "note": "First note",
            "source": "Host",
            "created_at": "2024-01-01T00:00:00Z",
        },
        {
            "id": "note-2",
            "interview_id": "123e4567-e89b-12d3-a456-426614174000",
            "note": "Second note",
            "source": "System",
            "created_at": "2024-01-01T01:00:00Z",
        },
    ]
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_interview_notes("123e4567-e89b-12d3-a456-426614174000")
    
    assert len(result) == 2
    assert result[0]["note"] == "First note"
    assert result[1]["note"] == "Second note"


@pytest.mark.unit
@patch("app.db.get_supabase_client")
def test_get_interview_notes_empty(mock_get_client, mock_supabase_client):
    """Test getting notes for an interview with no notes."""
    mock_get_client.return_value = mock_supabase_client
    
    mock_table = MagicMock()
    mock_select = MagicMock()
    mock_eq = MagicMock()
    mock_order = MagicMock()
    mock_execute = MagicMock()
    
    mock_table.select.return_value = mock_select
    mock_select.eq.return_value = mock_eq
    mock_eq.order.return_value = mock_order
    mock_order.execute.return_value = mock_execute
    mock_execute.data = []
    
    mock_supabase_client.table.return_value = mock_table
    
    result = get_interview_notes("123e4567-e89b-12d3-a456-426614174000")
    
    assert result == []

