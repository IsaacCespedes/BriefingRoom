"""Supabase database client and operations.

This module provides database operations using Supabase.
Replaces the temporary in-memory storage from storage.py.
"""

import os
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from supabase import Client, create_client

# Initialize Supabase client
_supabase_client: Optional[Client] = None


def get_supabase_client() -> Client:
    """Get or create the Supabase client instance."""
    global _supabase_client
    
    if _supabase_client is None:
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment variables"
            )
        
        _supabase_client = create_client(supabase_url, supabase_key)
    
    return _supabase_client


# Interview operations
def create_interview(job_description: str, resume_text: str, status: str = "pending") -> dict:
    """Create a new interview record in the database."""
    client = get_supabase_client()
    
    interview_data = {
        "job_description": job_description,
        "resume_text": resume_text,
        "status": status,
    }
    
    result = client.table("interviews").insert(interview_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create interview")
    
    return result.data[0]


def get_interview(interview_id: str) -> Optional[dict]:
    """Get an interview by ID."""
    client = get_supabase_client()
    
    try:
        result = client.table("interviews").select("*").eq("id", interview_id).execute()
    except Exception:
        # Invalid UUID format or database error - treat as not found
        return None
    
    if not result.data:
        return None
    
    return result.data[0]


# Token operations
def create_token(interview_id: str, token_hash: str, role: str, expires_at: Optional[datetime] = None) -> dict:
    """Create a new token record in the database."""
    client = get_supabase_client()
    
    token_data = {
        "interview_id": interview_id,
        "token_hash": token_hash,
        "role": role,
        "is_active": True,
    }
    
    if expires_at:
        token_data["expires_at"] = expires_at.isoformat()
    
    result = client.table("tokens").insert(token_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create token")
    
    return result.data[0]


def get_token_by_hash(token_hash: str) -> Optional[dict]:
    """Get a token by its hash."""
    client = get_supabase_client()
    
    result = (
        client.table("tokens")
        .select("*")
        .eq("token_hash", token_hash)
        .eq("is_active", True)
        .execute()
    )
    
    if not result.data:
        return None
    
    # Check if token is expired
    token = result.data[0]
    if token.get("expires_at"):
        expires_at = datetime.fromisoformat(token["expires_at"].replace("Z", "+00:00"))
        if datetime.now(expires_at.tzinfo) > expires_at:
            return None
    
    return token


def revoke_token(token_hash: str) -> bool:
    """Revoke a token by setting is_active to False."""
    client = get_supabase_client()
    
    result = (
        client.table("tokens")
        .update({"is_active": False})
        .eq("token_hash", token_hash)
        .execute()
    )
    
    return len(result.data) > 0


# Interview note operations
def create_interview_note(interview_id: str, note: str, source: str) -> dict:
    """Create a new interview note."""
    client = get_supabase_client()
    
    note_data = {
        "interview_id": interview_id,
        "note": note,
        "source": source,
    }
    
    result = client.table("interview_notes").insert(note_data).execute()
    
    if not result.data:
        raise ValueError("Failed to create interview note")
    
    return result.data[0]


def get_interview_notes(interview_id: str) -> list[dict]:
    """Get all notes for an interview."""
    client = get_supabase_client()
    
    result = (
        client.table("interview_notes")
        .select("*")
        .eq("interview_id", interview_id)
        .order("created_at", desc=False)
        .execute()
    )
    
    return result.data if result.data else []

