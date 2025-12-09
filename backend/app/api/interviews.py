"""Interview creation and management endpoints."""

import secrets

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.auth import hash_token
from app.db import create_interview as db_create_interview
from app.db import create_token as db_create_token
from app.db import get_interview as db_get_interview
from app.models.interview import InterviewCreate, InterviewResponse

router = APIRouter()


class CreateInterviewResponse(BaseModel):
    """Response model for interview creation."""

    interview_id: str
    host_token: str
    candidate_token: str


def generate_token() -> str:
    """Generate a cryptographically secure random token."""
    # Generate a URL-safe token (32 bytes = 256 bits of entropy)
    return secrets.token_urlsafe(32)


@router.post("/interviews", response_model=CreateInterviewResponse)
async def create_interview(request: InterviewCreate):
    """
    Create a new interview and generate host and candidate tokens.
    
    This endpoint:
    1. Creates an interview record in Supabase
    2. Generates two tokens (host and candidate)
    3. Stores token hashes in the database
    4. Returns the interview ID and plain tokens
    """
    try:
        # Create interview in database
        interview = db_create_interview(
            job_description=request.job_description,
            resume_text=request.resume_text,
            status=request.status,
        )
        interview_id = str(interview["id"])
        
        # Generate tokens
        host_token = generate_token()
        candidate_token = generate_token()
        
        # Hash tokens for storage
        host_token_hash = hash_token(host_token)
        candidate_token_hash = hash_token(candidate_token)
        
        # Store tokens in database
        db_create_token(
            interview_id=interview_id,
            token_hash=host_token_hash,
            role="host",
        )
        
        db_create_token(
            interview_id=interview_id,
            token_hash=candidate_token_hash,
            role="candidate",
        )
        
        return CreateInterviewResponse(
            interview_id=interview_id,
            host_token=host_token,
            candidate_token=candidate_token,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create interview: {str(e)}"
        )


@router.get("/interviews/{interview_id}")
async def get_interview(interview_id: str):
    """Get interview details by ID."""
    interview = db_get_interview(interview_id)
    
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    # Convert created_at to ISO format if it's a string
    created_at = interview.get("created_at")
    if isinstance(created_at, str):
        # Already in ISO format
        pass
    else:
        # Convert datetime to ISO format
        created_at = created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at)
    
    return {
        "id": str(interview["id"]),
        "job_description": interview["job_description"],
        "resume_text": interview["resume_text"],
        "status": interview["status"],
        "created_at": created_at,
    }

