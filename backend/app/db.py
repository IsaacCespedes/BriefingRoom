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


# Transcript operations
def create_transcript(
    interview_id: str,
    daily_room_name: str,
    transcript_text: str,
    transcript_webvtt: Optional[str] = None,
    transcript_data: Optional[dict] = None,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    participant_count: Optional[int] = None,
    status: str = "pending",
) -> dict:
    """Create a new transcript record in the database."""
    client = get_supabase_client()
    
    transcript_record = {
        "interview_id": interview_id,
        "daily_room_name": daily_room_name,
        "transcript_text": transcript_text,
        "status": status,
    }
    
    if transcript_webvtt:
        transcript_record["transcript_webvtt"] = transcript_webvtt
    if transcript_data:
        transcript_record["transcript_data"] = transcript_data
    if started_at:
        transcript_record["started_at"] = started_at.isoformat()
    if ended_at:
        transcript_record["ended_at"] = ended_at.isoformat()
    if duration_seconds is not None:
        transcript_record["duration_seconds"] = duration_seconds
    if participant_count is not None:
        transcript_record["participant_count"] = participant_count
    
    result = client.table("interview_transcripts").insert(transcript_record).execute()
    
    if not result.data:
        raise ValueError("Failed to create transcript")
    
    return result.data[0]


def get_transcript_by_interview_id(interview_id: str) -> Optional[dict]:
    """Retrieve transcript for a given interview."""
    client = get_supabase_client()
    
    try:
        result = (
            client.table("interview_transcripts")
            .select("*")
            .eq("interview_id", interview_id)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        # Invalid UUID format or database error - treat as not found
        return None
    
    if not result.data:
        return None
    
    return result.data[0]


def get_transcript_by_room_name(daily_room_name: str) -> Optional[dict]:
    """Retrieve transcript by Daily.co room name."""
    client = get_supabase_client()
    
    try:
        result = (
            client.table("interview_transcripts")
            .select("*")
            .eq("daily_room_name", daily_room_name)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
    except Exception:
        return None
    
    if not result.data:
        return None
    
    return result.data[0]


def update_transcript_status(transcript_id: str, status: str) -> dict:
    """Update transcript status."""
    client = get_supabase_client()
    
    result = (
        client.table("interview_transcripts")
        .update({"status": status, "updated_at": datetime.now().isoformat()})
        .eq("id", transcript_id)
        .execute()
    )
    
    if not result.data:
        raise ValueError(f"Failed to update transcript {transcript_id}")
    
    return result.data[0]


def update_transcript(
    transcript_id: str,
    transcript_text: Optional[str] = None,
    transcript_webvtt: Optional[str] = None,
    transcript_data: Optional[dict] = None,
    started_at: Optional[datetime] = None,
    ended_at: Optional[datetime] = None,
    duration_seconds: Optional[int] = None,
    participant_count: Optional[int] = None,
    status: Optional[str] = None,
) -> dict:
    """Update an existing transcript record."""
    client = get_supabase_client()
    
    update_data: dict = {"updated_at": datetime.now().isoformat()}
    
    if transcript_text is not None:
        update_data["transcript_text"] = transcript_text
    if transcript_webvtt is not None:
        update_data["transcript_webvtt"] = transcript_webvtt
    if transcript_data is not None:
        update_data["transcript_data"] = transcript_data
    if started_at is not None:
        update_data["started_at"] = started_at.isoformat()
    if ended_at is not None:
        update_data["ended_at"] = ended_at.isoformat()
    if duration_seconds is not None:
        update_data["duration_seconds"] = duration_seconds
    if participant_count is not None:
        update_data["participant_count"] = participant_count
    if status is not None:
        update_data["status"] = status
    
    result = (
        client.table("interview_transcripts")
        .update(update_data)
        .eq("id", transcript_id)
        .execute()
    )
    
    if not result.data:
        raise ValueError(f"Failed to update transcript {transcript_id}")
    
    return result.data[0]

