"""Transcript retrieval and download endpoints."""

from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query, Body
from fastapi.responses import Response
from pydantic import BaseModel

from app.api.auth import validate_token_dependency, TokenInfoResponse
from app.db import get_transcript_by_interview_id, create_transcript, update_transcript
from app.models.transcript import TranscriptResponse
import json

router = APIRouter()


class SaveTranscriptRequest(BaseModel):
    """Request model for saving transcript from frontend."""
    
    transcript_data: Dict[str, Any]  # Structured transcript data with segments
    source: str = "local_storage"  # Source of transcript (local_storage, daily_co, etc.)


@router.get("/transcripts/{interview_id}", response_model=TranscriptResponse)
async def get_transcript(
    interview_id: str,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Retrieve transcript for an interview.
    
    This endpoint:
    1. Validates authentication and interview_id ownership
    2. Retrieves transcript from database
    3. Returns full transcript with metadata
    
    Returns 404 if transcript is not found.
    """
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        transcript = get_transcript_by_interview_id(interview_id)
        
        if not transcript:
            raise HTTPException(
                status_code=404,
                detail="Transcript not found. The transcript may not be available yet. Try fetching it first.",
            )
        
        # Convert database dict to response model
        return TranscriptResponse(**transcript)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve transcript: {str(e)}",
        )


@router.get("/transcripts/{interview_id}/download")
async def download_transcript(
    interview_id: str,
    format: str = Query(default="txt", regex="^(txt|vtt|json)$"),
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Download transcript for an interview in various formats.
    
    Supported formats:
    - txt: Plain text transcript
    - vtt: WebVTT format (original format from Daily.co)
    - json: Structured JSON format with speaker segments and metadata
    
    Query parameter:
    - format: One of 'txt', 'vtt', or 'json' (default: 'txt')
    """
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        transcript = get_transcript_by_interview_id(interview_id)
        
        if not transcript:
            raise HTTPException(
                status_code=404,
                detail="Transcript not found. The transcript may not be available yet.",
            )
        
        # Determine content type and generate content based on format
        if format == "txt":
            content = transcript.get("transcript_text", "")
            if not content:
                raise HTTPException(
                    status_code=404,
                    detail="Transcript text not available",
                )
            media_type = "text/plain"
            filename = f"transcript-{interview_id}.txt"
            
        elif format == "vtt":
            content = transcript.get("transcript_webvtt", "")
            if not content:
                raise HTTPException(
                    status_code=404,
                    detail="WebVTT transcript not available",
                )
            media_type = "text/vtt"
            filename = f"transcript-{interview_id}.vtt"
            
        elif format == "json":
            # Create structured JSON response
            json_data = {
                "id": str(transcript.get("id")),
                "interview_id": str(transcript.get("interview_id")),
                "transcript_text": transcript.get("transcript_text", ""),
                "transcript_data": transcript.get("transcript_data"),
                "transcript_webvtt": transcript.get("transcript_webvtt"),
                "started_at": transcript.get("started_at"),
                "ended_at": transcript.get("ended_at"),
                "duration_seconds": transcript.get("duration_seconds"),
                "participant_count": transcript.get("participant_count"),
                "status": transcript.get("status"),
                "created_at": transcript.get("created_at"),
                "updated_at": transcript.get("updated_at"),
            }
            content = json.dumps(json_data, indent=2, default=str)
            media_type = "application/json"
            filename = f"transcript-{interview_id}.json"
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {format}. Supported formats: txt, vtt, json",
            )
        
        # Return file download response
        return Response(
            content=content,
            media_type=media_type,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
            },
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to download transcript: {str(e)}",
        )


@router.post("/transcripts/{interview_id}/save", response_model=TranscriptResponse)
async def save_transcript(
    interview_id: str,
    request: SaveTranscriptRequest = Body(...),
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Save transcript from frontend (local storage) to backend.
    
    This endpoint:
    1. Receives transcript data from frontend (captured during the call)
    2. Converts structured segments to plain text
    3. Stores in database
    4. Can be merged with Daily.co transcript if available later
    
    This is useful for:
    - Immediate transcript availability (no waiting for Daily.co processing)
    - Handling sudden browser closures
    - Providing redundancy
    """
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        transcript_data = request.transcript_data
        segments = transcript_data.get("segments", [])
        
        if not segments:
            raise HTTPException(
                status_code=400,
                detail="No transcript segments provided",
            )
        
        # Convert segments to plain text
        transcript_lines = []
        for segment in segments:
            text = segment.get("text", "").strip()
            if not text:
                continue
            
            speaker = segment.get("speaker")
            if speaker:
                transcript_lines.append(f"{speaker}: {text}")
            else:
                transcript_lines.append(text)
        
        transcript_text = "\n".join(transcript_lines)
        
        # Parse timestamps
        started_at = None
        ended_at = None
        duration_seconds = None
        
        if transcript_data.get("started_at"):
            try:
                started_at = datetime.fromisoformat(transcript_data["started_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        if transcript_data.get("ended_at"):
            try:
                ended_at = datetime.fromisoformat(transcript_data["ended_at"].replace("Z", "+00:00"))
            except Exception:
                pass
        
        if transcript_data.get("duration_seconds"):
            duration_seconds = transcript_data["duration_seconds"]
        
        # Count unique participants/speakers
        participant_count = None
        speakers = set()
        for segment in segments:
            speaker = segment.get("speaker")
            participant_id = segment.get("participantId")
            if speaker:
                speakers.add(speaker)
            if participant_id:
                speakers.add(f"participant_{participant_id}")
        if speakers:
            participant_count = len(speakers)
        
        room_name = f"interview-{interview_id}"
        
        # Check if transcript already exists
        existing_transcript = get_transcript_by_interview_id(interview_id)
        
        if existing_transcript:
            # Update existing transcript, but prefer Daily.co version if it's complete
            # If Daily.co transcript is complete, merge the data
            if existing_transcript.get("status") == "completed" and existing_transcript.get("transcript_text"):
                # Daily.co transcript exists and is complete
                # We can still update with local storage version as a backup
                # Or merge them - for now, keep Daily.co version but update structured data
                return TranscriptResponse(**existing_transcript)
            else:
                # Update with local storage version
                updated = update_transcript(
                    transcript_id=existing_transcript["id"],
                    transcript_text=transcript_text,
                    transcript_data={"segments": segments, "source": request.source},
                    started_at=started_at,
                    ended_at=ended_at,
                    duration_seconds=duration_seconds,
                    participant_count=participant_count,
                    status="completed",
                )
                return TranscriptResponse(**updated)
        else:
            # Create new transcript
            new_transcript = create_transcript(
                interview_id=interview_id,
                daily_room_name=room_name,
                transcript_text=transcript_text,
                transcript_data={"segments": segments, "source": request.source},
                started_at=started_at,
                ended_at=ended_at,
                duration_seconds=duration_seconds,
                participant_count=participant_count,
                status="completed",
            )
            return TranscriptResponse(**new_transcript)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save transcript: {str(e)}",
        )
