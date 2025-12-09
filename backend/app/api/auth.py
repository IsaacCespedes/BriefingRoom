"""Authentication and token validation endpoints."""

import hashlib

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.db import get_token_by_hash

router = APIRouter()


class TokenInfoResponse(BaseModel):
    """Response model for token validation."""

    role: str
    interview_id: str


def hash_token(token: str) -> str:
    """Hash a token using SHA-256."""
    return hashlib.sha256(token.encode()).hexdigest()


@router.get("/validate-token", response_model=TokenInfoResponse)
async def validate_token(token: str = Query(..., description="Token to validate")):
    """
    Validate a token and return the associated role and interview_id.
    
    This implementation:
    1. Hashes the incoming token
    2. Looks up the token hash in the Supabase database
    3. Checks if the token is active and not expired
    4. Returns the role and interview_id from the token record
    """
    # Hash the incoming token
    token_hash = hash_token(token)
    
    # Look up the token in the database
    token_record = get_token_by_hash(token_hash)
    
    if not token_record:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    # Return the role and interview_id
    return TokenInfoResponse(
        role=token_record["role"],
        interview_id=str(token_record["interview_id"])
    )

