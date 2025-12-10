"""Daily.co video call room management endpoints."""

import os
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.auth import validate_token_dependency, TokenInfoResponse
from app.services.transcript_service import fetch_and_store_transcript
from app.models.transcript import TranscriptResponse

router = APIRouter()

# Daily.co API configuration
DAILY_API_KEY = os.getenv("DAILY_API_KEY")
DAILY_API_URL = os.getenv("DAILY_API_URL", "https://api.daily.co/v1")


def check_daily_api_key():
    """Check if Daily.co API key is configured."""
    if not DAILY_API_KEY:
        raise HTTPException(
            status_code=500,
            detail="Daily.co API key is not configured. Please set DAILY_API_KEY environment variable.",
        )


class CreateRoomRequest(BaseModel):
    """Request model for creating a Daily.co room."""

    interview_id: str


class CreateRoomResponse(BaseModel):
    """Response model for Daily.co room creation."""

    room_url: str
    room_token: Optional[str] = None


async def create_daily_room(
    room_name: str,
    privacy: str = "public",
    properties: Optional[dict] = None,
) -> dict:
    """
    Create a Daily.co room using the REST API.
    
    Args:
        room_name: Unique name for the room
        privacy: Room privacy setting ("public" or "private")
        properties: Optional room properties (enable_chat, enable_recording, etc.)
    
    Returns:
        Dictionary containing room details from Daily.co API
    """
    url = f"{DAILY_API_URL}/rooms"
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {"name": room_name, "privacy": privacy}
    if properties:
        payload["properties"] = properties
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Daily.co API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Daily.co: {str(e)}",
            )


async def get_daily_room(room_name: str) -> dict:
    """
    Get details of an existing Daily.co room.
    
    Args:
        room_name: Name of the room to retrieve
    
    Returns:
        Dictionary containing room details from Daily.co API
    """
    url = f"{DAILY_API_URL}/rooms/{room_name}"
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10.0)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise HTTPException(status_code=404, detail="Room not found")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Daily.co API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Daily.co: {str(e)}",
            )


async def create_meeting_token(room_name: str, properties: Optional[dict] = None) -> Optional[str]:
    """
    Create a meeting token for a Daily.co room.
    
    Args:
        room_name: Name of the room
        properties: Optional token properties (exp, is_owner, etc.)
    
    Returns:
        Meeting token string, or None if token is not available
    """
    url = f"{DAILY_API_URL}/meeting-tokens"
    headers = {
        "Authorization": f"Bearer {DAILY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {"properties": {"room_name": room_name}}
    if properties:
        payload["properties"].update(properties)
    
    # Debug: log the payload structure being sent
    import json
    print(f"[DEBUG] Creating meeting token with payload: {json.dumps(payload, indent=2)}")
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()
            data = response.json()
            token = data.get("token")
            print(f"[DEBUG] Token created successfully: {token[:20]}..." if token else "[DEBUG] No token returned")
            # Return None if token is empty string or not present
            return token if token and isinstance(token, str) and token.strip() else None
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Daily.co API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Daily.co: {str(e)}",
            )


@router.post("/daily/create-room", response_model=CreateRoomResponse)
async def create_room(
    request: CreateRoomRequest,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Create a Daily.co room for an interview.
    
    This endpoint:
    1. Creates a Daily.co room with a name based on the interview ID
    2. Optionally generates a meeting token for secure access
    3. Returns the room URL and token
    """
    check_daily_api_key()
    
    # Validate that the interview_id in the request matches the token's interview_id
    if request.interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in request does not match the token's interview ID",
        )
    
    try:
        # Use interview_id as the room name (Daily.co will handle uniqueness)
        room_name = f"interview-{request.interview_id}"
        
        # Create room with default properties
        room_properties = {
            "enable_chat": True,
            "enable_screenshare": True,
            "enable_recording": False,  # Set to True if you want recording
            "enable_transcription_storage": True,  # Store transcripts for retrieval
            # Note: Transcription provider/model are configured at domain level in Daily.co dashboard
            # The room just needs enable_transcription_storage set to True
        }
        
        # Create room with "public" privacy (can be changed to "private" for invite-only)
        room_data = await create_daily_room(room_name, privacy="public", properties=room_properties)
        
        # Generate a meeting token for secure access
        # Note: Transcription admin permission is required to start transcription
        # According to Daily.co docs: use permissions.canAdmin array with "transcription"
        token_properties = {
            "is_owner": True,  # Host has owner privileges
            "exp": 86400,  # Token expires in 24 hours
            "enable_live_captions_ui": True,  # Enable closed captions UI in Daily Prebuilt
            # Transcription admin permission (required to start/stop transcription)
            # Format: permissions.canAdmin must be an array containing "transcription"
            "permissions": {
                "canAdmin": ["transcription"],
            },
        }
        
        try:
            meeting_token = await create_meeting_token(room_name, token_properties)
        except Exception:
            # If token creation fails, continue without token
            meeting_token = None
        
        return CreateRoomResponse(
            room_url=room_data.get("url", ""),
            room_token=meeting_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create Daily.co room: {str(e)}",
        )


@router.post("/daily/start-transcription/{interview_id}")
async def start_transcription(
    interview_id: str,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Start transcription for a Daily.co room using REST API.
    
    This is an alternative to starting transcription client-side.
    Requires transcription admin permissions in the meeting token.
    """
    check_daily_api_key()
    
    # Validate that the interview_id matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        room_name = f"interview-{interview_id}"
        url = f"{DAILY_API_URL}/rooms/{room_name}/transcription/start"
        headers = {
            "Authorization": f"Bearer {DAILY_API_KEY}",
            "Content-Type": "application/json",
        }
        
        # Daily.co transcription start endpoint doesn't require a body
        # Transcription provider is configured at domain level in Daily.co dashboard
        async with httpx.AsyncClient() as client:
            try:
                # Send POST request with no body (Daily.co transcription start endpoint)
                response = await client.post(url, headers=headers, timeout=10.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                # Check if transcription is already active - this is fine, treat as success
                error_text = e.response.text.lower()
                if "active stream" in error_text or "already" in error_text:
                    # Transcription is already active, return success
                    return {"status": "already_active", "message": "Transcription is already active"}
                
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Daily.co API error: {e.response.text}",
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to connect to Daily.co: {str(e)}",
                )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to start transcription: {str(e)}",
        )


@router.get("/daily/room/{interview_id}", response_model=CreateRoomResponse)
async def get_room(
    interview_id: str,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Get the Daily.co room URL for an existing interview.
    
    If the room doesn't exist, returns 404.
    """
    check_daily_api_key()
    
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        room_name = f"interview-{interview_id}"
        room_data = await get_daily_room(room_name)
        
        # Optionally generate a new token
        meeting_token = None
        try:
            token_properties = {
                "is_owner": True,
                "exp": 86400,
                "enable_live_captions_ui": True,  # Enable closed captions UI in Daily Prebuilt
                # Transcription admin permission (required to start/stop transcription)
                # Format: permissions.canAdmin must be an array containing "transcription"
                "permissions": {
                    "canAdmin": ["transcription"],
                },
            }
            meeting_token = await create_meeting_token(room_name, token_properties)
        except Exception:
            # If token creation fails, continue without token
            pass
        
        return CreateRoomResponse(
            room_url=room_data.get("url", ""),
            room_token=meeting_token,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get Daily.co room: {str(e)}",
        )


@router.post("/daily/fetch-transcript/{interview_id}", response_model=TranscriptResponse)
async def fetch_transcript(
    interview_id: str,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Fetch transcript from Daily.co and store in database.
    
    This endpoint:
    1. Calls Daily.co API to get transcript for the room
    2. Parses WebVTT format to plain text
    3. Extracts metadata (duration, timestamps, etc.)
    4. Stores transcript in database
    
    Note: Transcripts may not be immediately available after a call ends.
    Daily.co processes transcripts asynchronously (may take 1-5 minutes).
    If transcript is not ready, returns a pending transcript record.
    """
    check_daily_api_key()
    
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        room_name = f"interview-{interview_id}"
        transcript_data = await fetch_and_store_transcript(room_name, interview_id)
        
        # Convert database dict to response model
        return TranscriptResponse(**transcript_data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch transcript: {str(e)}",
        )

