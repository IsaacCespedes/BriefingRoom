"""Interview creation and management endpoints."""

import secrets
from uuid import UUID, uuid4

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.api.auth import hash_token
from app.models.interview import InterviewCreate, InterviewResponse
from app.storage import interviews_store, tokens_store

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
    1. Creates an interview record
    2. Generates two tokens (host and candidate)
    3. Stores token hashes in the database
    4. Returns the interview ID and plain tokens
    """
    try:
        # Generate interview ID
        interview_id = str(uuid4())
        
        # Generate tokens
        host_token = generate_token()
        candidate_token = generate_token()
        
        # Hash tokens for storage
        host_token_hash = hash_token(host_token)
        candidate_token_hash = hash_token(candidate_token)
        
        # Store interview (mock - replace with database in production)
        interviews_store[interview_id] = {
            "id": interview_id,
            "job_description": request.job_description,
            "resume_text": request.resume_text,
            "status": request.status,
        }
        
        # Store tokens (mock - replace with database in production)
        tokens_store[host_token_hash] = {
            "interview_id": interview_id,
            "role": "host",
            "token_hash": host_token_hash,
            "is_active": True,
        }
        
        tokens_store[candidate_token_hash] = {
            "interview_id": interview_id,
            "role": "candidate",
            "token_hash": candidate_token_hash,
            "is_active": True,
        }
        
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
    # Mock implementation - replace with database lookup in production
    if interview_id not in interviews_store:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    interview = interviews_store[interview_id]
    # Return dict instead of InterviewResponse since created_at is required
    # In production, this would come from the database
    from datetime import datetime
    
    return {
        "id": interview["id"],
        "job_description": interview["job_description"],
        "resume_text": interview["resume_text"],
        "status": interview["status"],
        "created_at": datetime.now().isoformat(),
    }

