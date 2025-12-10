"Tests for the Vapi API proxy endpoints."
import pytest
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi.testclient import TestClient
from httpx import Response, HTTPStatusError, Request

from app.main import app

# Create a test client
client = TestClient(app)

# Mock token data
MOCK_TOKEN = "test-token-123"
MOCK_INTERVIEW_ID = "interview-456"
MOCK_TOKEN_INFO = {"role": "host", "interview_id": MOCK_INTERVIEW_ID}
MOCK_TOKEN_RECORD = {"id": "token-id", "role": "host", "interview_id": MOCK_INTERVIEW_ID}


@pytest.fixture(autouse=True)
def mock_auth_and_db():
    """Mock authentication and database dependencies to prevent actual DB calls."""
    with patch("app.api.vapi.validate_token_dependency", return_value=MOCK_TOKEN_INFO), \
         patch("app.api.vapi.validate_token_flexible", return_value=MOCK_TOKEN_INFO), \
         patch("app.api.auth.get_token_by_hash", return_value=MOCK_TOKEN_RECORD), \
         patch("app.db.get_supabase_client"):  # Also mock the supabase client just in case
        yield

@pytest.fixture
def mock_httpx_client():
    """Mock the httpx.AsyncClient."""
    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = mock_client_class.return_value.__aenter__.return_value
        mock_client.request = AsyncMock()
        mock_client.post = AsyncMock()
        yield mock_client

# ===================================
# Tests for GET /api/vapi/public-key
# ===================================

def test_get_public_key_success(monkeypatch):
    """Test successful retrieval of the Vapi public key."""
    monkeypatch.setattr("app.api.vapi.VAPI_PUBLIC_KEY", "test-public-key")
    response = client.get("/api/vapi/public-key", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
    assert response.status_code == 200
    assert response.json() == {"public_key": "test-public-key"}

def test_get_public_key_not_configured(monkeypatch):
    """Test error when VAPI_PUBLIC_KEY is not set."""
    monkeypatch.setattr("app.api.vapi.VAPI_PUBLIC_KEY", None)
    response = client.get("/api/vapi/public-key", headers={"Authorization": f"Bearer {MOCK_TOKEN}"})
    assert response.status_code == 500
    assert "Vapi public key is not configured" in response.json()["detail"]

# ===================================
# Tests for POST /api/vapi/call
# ===================================

def test_create_call_success(mock_httpx_client, monkeypatch):
    """Test successful creation of a Vapi call."""
    monkeypatch.setattr("app.api.vapi.VAPI_API_KEY", "test-api-key")
    # Create a realistic response with a request object to allow raise_for_status() to be called
    request = Request("POST", "https://api.vapi.ai/call")
    success_response = Response(200, json={"id": "call-123"}, request=request)
    mock_httpx_client.post.return_value = success_response
    
    request_body = {"assistantId": "asst-abc"}
    response = client.post("/api/vapi/call", headers={"Authorization": f"Bearer {MOCK_TOKEN}"}, json=request_body)

    assert response.status_code == 200
    assert response.json() == {"id": "call-123"}
    
    mock_httpx_client.post.assert_called_once()
    call_args = mock_httpx_client.post.call_args
    assert call_args.args[0] == "https://api.vapi.ai/call"
    assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-api-key"
    assert call_args.kwargs["json"]["assistantOverrides"]["variableValues"]["interviewId"] == MOCK_INTERVIEW_ID

# =======================================
# Tests for the proxy endpoint
# =======================================

@pytest.mark.parametrize("method", ["GET", "POST", "PUT", "DELETE"])
def test_proxy_vapi_request_success(method, mock_httpx_client, monkeypatch):
    """Test successful proxying of a request to Vapi."""
    monkeypatch.setattr("app.api.vapi.VAPI_API_KEY", "test-api-key")
    monkeypatch.setattr("app.api.vapi.VAPI_PUBLIC_KEY", "test-public-key")
    
    mock_httpx_client.request.return_value = Response(200, json={"status": "ok"}, headers={"Content-Type": "application/json"})
    
    proxy_path = "call/web"
    url = f"/api/vapi/proxy/{MOCK_TOKEN}/{proxy_path}?param1=value1"
    
    json_body = {"key": "value"} if method in ["POST", "PUT"] else None
    
    response = client.request(method, url, json=json_body)
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    
    mock_httpx_client.request.assert_called_once()
    call_args = mock_httpx_client.request.call_args
    assert call_args.kwargs["method"] == method
    assert call_args.kwargs["url"] == f"https://api.vapi.ai/{proxy_path}"
    assert call_args.kwargs["params"] == {"param1": "value1"}
    assert call_args.kwargs["json"] == json_body
    assert call_args.kwargs["headers"]["Authorization"] == "Bearer test-public-key"

def test_proxy_vapi_request_vapi_error(mock_httpx_client, monkeypatch):
    """Test error handling when the Vapi API returns an error."""
    monkeypatch.setattr("app.api.vapi.VAPI_API_KEY", "test-api-key")
    monkeypatch.setattr("app.api.vapi.VAPI_PUBLIC_KEY", "test-public-key")
    
    # Mock a 400 error response from Vapi
    error_response = Response(400, json={"error": "Bad Request"})
    # The httpx client raises an exception for 4xx/5xx responses
    mock_httpx_client.request.side_effect = HTTPStatusError(
        message="Bad Request", request=MagicMock(spec=Request), response=error_response
    )
    
    proxy_path = "call/web"
    url = f"/api/vapi/proxy/{MOCK_TOKEN}/{proxy_path}"
    
    response = client.post(url, json={"invalid": "payload"})
    
    assert response.status_code == 400
    # FastAPI wraps the detail in a "detail" key
    assert response.json()["detail"] == "Vapi API error: {'error': 'Bad Request'}"

def test_proxy_vapi_request_no_public_key(monkeypatch):
    """Test error when VAPI_PUBLIC_KEY is not set for the proxy."""
    monkeypatch.setattr("app.api.vapi.VAPI_API_KEY", "test-api-key")
    monkeypatch.setattr("app.api.vapi.VAPI_PUBLIC_KEY", None)
    
    proxy_path = "call/web"
    url = f"/api/vapi/proxy/{MOCK_TOKEN}/{proxy_path}"
    
    response = client.post(url, json={})
    
    assert response.status_code == 500
    assert "public key is not configured" in response.json()["detail"]