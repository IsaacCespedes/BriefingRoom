"""Authentication and token validation endpoints."""

import hashlib
from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, Header, Depends
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


async def get_token_from_header(
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    """
    Extract Bearer token from Authorization header.
    
    This is a dependency function that extracts the token from the
    Authorization header and validates it.
    """
    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>" format
    parts = authorization.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=401,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return parts[1]


async def validate_token_dependency(
    token: Annotated[str, Depends(get_token_from_header)],
) -> TokenInfoResponse:
    """
    Validate a token from the Authorization header and return token info.
    
    This is a dependency function that can be used with Depends() in route handlers.
    It:
    1. Extracts the token from the Authorization header
    2. Hashes the token
    3. Looks up the token hash in the Supabase database
    4. Returns the role and interview_id from the token record
    
    Usage:
        @router.post("/some-endpoint")
        async def some_endpoint(token_info: TokenInfoResponse = Depends(validate_token_dependency)):
            # Use token_info.role and token_info.interview_id
    """
    # Hash the incoming token
    token_hash = hash_token(token)
    
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


@router.get("/validate-token", response_model=TokenInfoResponse)
async def validate_token(token: str = Query(..., description="Token to validate")):
    """
    Validate a token and return the associated role and interview_id.
    
    This endpoint accepts the token as a query parameter for backwards compatibility.
    
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

