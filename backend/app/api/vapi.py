"""Vapi voice AI proxy endpoints for secure API access."""

import os
from typing import Optional, Dict, Any, Annotated
from fastapi import APIRouter, HTTPException, Depends, Request, Body, Query, Header

import httpx
from fastapi.responses import StreamingResponse, Response
from pydantic import BaseModel

from app.api.auth import validate_token_dependency, TokenInfoResponse, get_token_from_header, hash_token, get_token_by_hash

router = APIRouter()

# Vapi API configuration
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
VAPI_API_URL = os.getenv("VAPI_API_URL", "https://api.vapi.ai")
VAPI_PUBLIC_KEY = os.getenv("VAPI_PUBLIC_KEY")  # For frontend SDK initialization


def check_vapi_api_key():
    """Check if Vapi API key is configured."""
    if not VAPI_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Vapi API key is not configured. Please set VAPI_API_KEY environment variable.",
        )


class VapiProxyRequest(BaseModel):
    """Generic request model for Vapi API proxy."""
    method: str = "POST"
    path: str
    body: Optional[Dict[str, Any]] = None
    params: Optional[Dict[str, str]] = None


class VapiPublicKeyResponse(BaseModel):
    """Response model for Vapi public key (for frontend SDK)."""
    public_key: str


async def validate_token_flexible(
    authorization: Annotated[Optional[str], Header()] = None,
    token: Annotated[Optional[str], Query()] = None,
) -> TokenInfoResponse:
    """
    Validate a token from either Authorization header or query parameter.
    
    This is useful for proxy endpoints where the client SDK might not send
    Authorization headers but can include tokens in query parameters.
    """
    # Try to get token from header first
    auth_token = None
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            auth_token = parts[1]
    
    # Fall back to query parameter if no header token
    token_value = auth_token or token
    
    if not token_value:
        raise HTTPException(
            status_code=401,
            detail="Authorization token required. Provide via Authorization header or 'token' query parameter.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Hash the token
    token_hash = hash_token(token_value)
    
    # Look up the token in the database
    token_record = get_token_by_hash(token_hash)
    
    if not token_record:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Return the role and interview_id
    return TokenInfoResponse(
        role=token_record["role"],
        interview_id=str(token_record["interview_id"])
    )


@router.get("/vapi/public-key", response_model=VapiPublicKeyResponse)
async def get_public_key(
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Get the Vapi public key for frontend SDK initialization.
    
    This endpoint returns the public key that can be safely used in the frontend.
    The public key has limited permissions and cannot be used to make server-side API calls.
    """
    if not VAPI_PUBLIC_KEY:
        raise HTTPException(
            status_code=500,
            detail="Vapi public key is not configured. Please set VAPI_PUBLIC_KEY environment variable.",
        )
    
    return VapiPublicKeyResponse(public_key=VAPI_PUBLIC_KEY)


@router.post("/vapi/proxy/{token}/{path:path}")
@router.get("/vapi/proxy/{token}/{path:path}")
@router.put("/vapi/proxy/{token}/{path:path}")
@router.delete("/vapi/proxy/{token}/{path:path}")
async def proxy_vapi_request(
    token: str,
    path: str,
    request: Request,
):
    """
    Proxy requests to the Vapi API.
    
    This endpoint forwards authenticated requests to Vapi's API while keeping
    the API key secure on the server side. It supports all HTTP methods and
    forwards headers, query parameters, and request body.
    
    The token is embedded in the URL path to avoid issues with SDK URL construction.
    The path parameter should be the Vapi API endpoint path (e.g., "call/web", "assistant", etc.)
    """
    check_vapi_api_key()
    
    # Validate the token from the path
    try:
        token_info = await validate_token_flexible(token=token, authorization=None)
    except HTTPException as e:
        raise e
    
    # Get the HTTP method from the request
    method = request.method
    
    # Build the full URL
    url = f"{VAPI_API_URL}/{path}"
    
    # Get query parameters
    params = dict(request.query_params)
    
    # Get request body if present
    body = None
    content_type = request.headers.get("content-type", "")
    if method in ("POST", "PUT", "PATCH") and "application/json" in content_type:
        try:
            body = await request.json()
        except Exception:
            # If body parsing fails, pass None
            pass
    
    # Prepare headers for Vapi API
    # For SDK proxy requests, we need to use the PUBLIC key, not the private API key
    # The SDK authenticates using the public key that was provided during initialization
    headers = {
        "Content-Type": "application/json",
    }
    
    # Use public key for SDK requests (not the private API key)
    # The SDK was initialized with the public key, so proxy requests must use it too
    if not VAPI_PUBLIC_KEY:
        raise HTTPException(
            status_code=500,
            detail="Vapi public key is not configured. Required for SDK proxy requests. Please set VAPI_PUBLIC_KEY environment variable.",
        )
    
    # Use the public key for authentication
    headers["Authorization"] = f"Bearer {VAPI_PUBLIC_KEY}"
    
    # Forward relevant headers from the original request
    forward_headers = ["x-vapi-version", "x-request-id"]
    for header in forward_headers:
        if header in request.headers:
            headers[header] = request.headers[header]
    
    async with httpx.AsyncClient() as client:
        try:
            # Make the request to Vapi API
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=body,
                timeout=30.0,
            )
            
            # Forward the response
            response_headers = dict(response.headers)
            # Remove headers that shouldn't be forwarded
            response_headers.pop("content-encoding", None)
            response_headers.pop("transfer-encoding", None)
            
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get("content-type"),
            )
        except httpx.HTTPStatusError as e:
            # Log the error details for debugging
            import logging
            logger = logging.getLogger(__name__)
            error_text = e.response.text
            try:
                error_json = e.response.json()
                error_text = str(error_json)
            except:
                pass
            logger.error(f"Vapi API error: Status={e.response.status_code}, URL={url}, Body={body}, Error={error_text}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Vapi API error: {error_text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Vapi API: {str(e)}",
            )


@router.post("/vapi/call")
async def create_call(
    request_body: Dict[str, Any] = Body(...),
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Create a Vapi call (convenience endpoint).
    
    This is a convenience endpoint that proxies to the Vapi /call endpoint
    with proper authentication. The request body should match Vapi's call creation format.
    """
    check_vapi_api_key()
    
    url = f"{VAPI_API_URL}/call"
    headers = {
        "Authorization": f"Bearer {VAPI_API_KEY}",
        "Content-Type": "application/json",
    }
    
    # Optionally add interview_id to the call context
    if "assistantOverrides" not in request_body:
        request_body["assistantOverrides"] = {}
    if "variableValues" not in request_body.get("assistantOverrides", {}):
        request_body["assistantOverrides"]["variableValues"] = {}
    request_body["assistantOverrides"]["variableValues"]["interviewId"] = token_info.interview_id
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=request_body, timeout=30.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Vapi API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Vapi API: {str(e)}",
            )

