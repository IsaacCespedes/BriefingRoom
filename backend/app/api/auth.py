"""Authentication and token validation endpoints."""

import hashlib
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

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
    
    This is a placeholder implementation. In production, this should:
    1. Hash the incoming token
    2. Look up the token hash in the database
    3. Check if the token is active and not expired
    4. Return the role and interview_id from the token record
    """
    # TODO: Implement actual database lookup
    # For now, this is a mock implementation for testing
    
    # Mock token validation - in production, this would query the database
    # Example: token_hash = hash_token(token)
    # token_record = await db.get_token_by_hash(token_hash)
    
    # For testing purposes, accept tokens that start with "host-" or "candidate-"
    if token.startswith("host-"):
        # Extract interview_id from token (mock)
        interview_id = token.replace("host-", "").split("-")[0] if "-" in token.replace("host-", "") else "mock-interview-123"
        return TokenInfoResponse(role="host", interview_id=interview_id)
    elif token.startswith("candidate-"):
        interview_id = token.replace("candidate-", "").split("-")[0] if "-" in token.replace("candidate-", "") else "mock-interview-456"
        return TokenInfoResponse(role="candidate", interview_id=interview_id)
    else:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

