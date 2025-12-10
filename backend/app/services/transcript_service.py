"""Transcript processing service.

This service handles fetching transcripts from Daily.co, parsing WebVTT format,
and storing transcripts in the database.
"""

import os
import re
from datetime import datetime
from typing import Optional
from uuid import UUID

import httpx
from fastapi import HTTPException

from app.db import (
    create_transcript,
    get_transcript_by_interview_id,
    get_transcript_by_room_name,
    update_transcript,
    update_transcript_status,
)

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


async def get_daily_transcript(room_name: str) -> Optional[str]:
    """
    Retrieve stored transcript WebVTT content from Daily.co for a room.
    
    This function:
    1. Lists transcripts from Daily.co API
    2. Finds the transcript for the specified room
    3. Gets an access link to the WebVTT file
    4. Fetches the WebVTT content from the access link
    
    Args:
        room_name: Name of the Daily.co room (e.g., "interview-{interview_id}")
    
    Returns:
        WebVTT content as string, or None if not available
    """
    check_daily_api_key()
    
    async with httpx.AsyncClient() as client:
        try:
            # Step 1: List transcripts to find the one for this room
            list_url = f"{DAILY_API_URL}/transcript"
            headers = {
                "Authorization": f"Bearer {DAILY_API_KEY}",
            }
            
            response = await client.get(list_url, headers=headers, timeout=10.0)
            
            # Daily.co returns 404 if no transcripts exist
            if response.status_code == 404:
                return None
            
            response.raise_for_status()
            transcripts_data = response.json()
            
            # Extract the data array from the response
            transcripts_list = transcripts_data.get("data", [])
            if not transcripts_list:
                return None
            
            # Step 2: Find the transcript for this room
            # We need to match by room_id. First, try to get the room details to find room_id
            room_id = None
            try:
                room_url = f"{DAILY_API_URL}/rooms/{room_name}"
                room_response = await client.get(room_url, headers=headers, timeout=10.0)
                
                if room_response.status_code == 200:
                    room_response.raise_for_status()
                    room_data = room_response.json()
                    room_id = room_data.get("id")
            except Exception:
                # If room lookup fails, we'll try to match by room_name directly
                pass
            
            # Find transcript matching this room
            transcript_obj = None
            for transcript in transcripts_list:
                # Match by room_id if we have it
                transcript_room_id = transcript.get("room_id")
                matched = False
                
                if room_id and transcript_room_id == room_id:
                    matched = True
                elif transcript_room_id == room_name:
                    matched = True
                else:
                    # Also check meeting_session_id which might contain room info
                    meeting_session_id = transcript.get("meeting_session_id", "")
                    if meeting_session_id and (room_name in str(meeting_session_id) or (room_id and room_id in str(meeting_session_id))):
                        matched = True
                
                if matched:
                    # Check transcript status - should be "t_finished" for completed transcripts
                    transcript_status = transcript.get("status", "")
                    is_vtt_available = transcript.get("is_vtt_available", False)
                    
                    # If transcript is finished and VTT is available, use it
                    if transcript_status == "t_finished" and is_vtt_available:
                        transcript_obj = transcript
                        break
                    # Otherwise, if we found a match but it's not ready, keep looking for a finished one
                    # but remember this one in case no finished transcript exists
                    elif not transcript_obj:
                        # Store the first matching transcript (even if not finished) as fallback
                        transcript_obj = transcript
            
            if not transcript_obj:
                # Transcript not found for this room
                return None
            
            # Check if transcript is ready
            transcript_status = transcript_obj.get("status", "")
            is_vtt_available = transcript_obj.get("is_vtt_available", False)
            
            # Daily.co transcript statuses:
            # - "t_finished": Transcript processing is complete
            # - Other statuses: Still processing
            if transcript_status != "t_finished":
                # Transcript exists but is still processing
                # Return None so we can create a pending record
                # The status might be something like "t_processing" or similar
                return None
            
            if not is_vtt_available:
                # Transcript is finished but VTT file not available yet
                # This shouldn't happen if status is t_finished, but handle it anyway
                return None
            
            transcript_id = transcript_obj.get("id")
            if not transcript_id:
                return None
            
            # Step 3: Get access link to the WebVTT file
            access_link_url = f"{DAILY_API_URL}/transcript/{transcript_id}/access-link"
            access_response = await client.get(access_link_url, headers=headers, timeout=10.0)
            
            if access_response.status_code == 404:
                return None
            
            access_response.raise_for_status()
            access_data = access_response.json()
            
            # The access link is in the response
            webvtt_url = access_data.get("download_link") or access_data.get("url") or access_data.get("access_link")
            
            if not webvtt_url:
                raise HTTPException(
                    status_code=500,
                    detail="Could not retrieve WebVTT access link from Daily.co",
                )
            
            # Step 4: Fetch the actual WebVTT content from the S3 link
            webvtt_response = await client.get(webvtt_url, timeout=30.0)
            webvtt_response.raise_for_status()
            
            # Return the WebVTT content as string
            return webvtt_response.text
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                # Transcript not available yet
                return None
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Daily.co API error: {e.response.text}",
            )
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to connect to Daily.co: {str(e)}",
            )


def parse_webvtt_to_text(webvtt_content: str) -> str:
    """
    Convert WebVTT format to plain text transcript.
    
    WebVTT format example:
    WEBVTT
    
    00:00:00.000 --> 00:00:05.000
    Speaker 1: Hello, this is a test.
    
    00:00:05.000 --> 00:00:10.000
    Speaker 2: Hi there!
    
    Returns:
        Plain text transcript with speaker labels if available
    """
    if not webvtt_content or not webvtt_content.strip():
        return ""
    
    lines = webvtt_content.split("\n")
    transcript_lines = []
    
    # Skip WEBVTT header and empty lines
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip WEBVTT header
        if line == "WEBVTT" or line.startswith("WEBVTT"):
            i += 1
            continue
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Skip timestamp lines (format: 00:00:00.000 --> 00:00:05.000)
        if re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}", line):
            i += 1
            # Next line(s) should be the transcript text
            if i < len(lines):
                text_line = lines[i].strip()
                if text_line and not re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}", text_line):
                    transcript_lines.append(text_line)
            i += 1
            continue
        
        # Regular text line (not a timestamp)
        if line and not re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}", line):
            transcript_lines.append(line)
        
        i += 1
    
    return "\n".join(transcript_lines)


def parse_webvtt_to_segments(webvtt_content: str) -> list[dict]:
    """
    Parse WebVTT format into structured segments with speaker information.
    
    WebVTT format example:
    WEBVTT
    
    00:00:00.000 --> 00:00:05.000
    Speaker 0: Hello, this is a test.
    
    00:00:05.000 --> 00:00:10.000
    Speaker 1: Hi there!
    
    Returns:
        List of segment dictionaries with speaker, text, start_time, end_time
        Format: [
            {"speaker": "Speaker 0", "text": "Hello, this is a test.", "start_time": 0.0, "end_time": 5.0},
            {"speaker": "Speaker 1", "text": "Hi there!", "start_time": 5.0, "end_time": 10.0},
        ]
    """
    if not webvtt_content or not webvtt_content.strip():
        return []
    
    segments = []
    lines = webvtt_content.split("\n")
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Skip WEBVTT header
        if line == "WEBVTT" or line.startswith("WEBVTT"):
            i += 1
            continue
        
        # Skip empty lines
        if not line:
            i += 1
            continue
        
        # Match timestamp line (format: 00:00:00.000 --> 00:00:05.000)
        timestamp_match = re.match(
            r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})", line
        )
        
        if timestamp_match:
            # Parse timestamps
            def parse_timestamp(h, m, s, ms):
                return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
            
            start_time = parse_timestamp(*timestamp_match.groups()[:4])
            end_time = parse_timestamp(*timestamp_match.groups()[4:])
            
            # Get the text line(s) after the timestamp
            i += 1
            text_lines = []
            while i < len(lines):
                text_line = lines[i].strip()
                # Stop if we hit another timestamp or empty line
                if not text_line or re.match(r"^\d{2}:\d{2}:\d{2}\.\d{3}", text_line):
                    break
                text_lines.append(text_line)
                i += 1
            
            if text_lines:
                # Combine multi-line text
                full_text = " ".join(text_lines)
                
                # Extract speaker label if present (format: "Speaker 0:", "Speaker 1:", etc.)
                speaker = None
                text = full_text
                
                # Match patterns like "Speaker 0:", "Speaker 1:", "Speaker 2:", etc.
                speaker_match = re.match(r"^(Speaker\s+\d+|speaker\s+\d+):\s*(.+)", full_text, re.IGNORECASE)
                if speaker_match:
                    speaker = speaker_match.group(1)
                    text = speaker_match.group(2).strip()
                else:
                    # Try other patterns like "Participant 1:", etc.
                    participant_match = re.match(r"^(Participant\s+\d+|participant\s+\d+):\s*(.+)", full_text, re.IGNORECASE)
                    if participant_match:
                        speaker = participant_match.group(1)
                        text = participant_match.group(2).strip()
                
                segments.append({
                    "speaker": speaker,
                    "text": text,
                    "start_time": start_time,
                    "end_time": end_time,
                })
            continue
        
        i += 1
    
    return segments


def extract_webvtt_metadata(webvtt_content: str) -> dict:
    """
    Extract metadata from WebVTT (duration, participant count, etc.).
    
    Note: WebVTT timestamps are relative (seconds from start), not absolute Unix timestamps.
    Therefore, started_at and ended_at are not populated here. If absolute timestamps
    are required, fetch the recording/session start time from Daily.co's API.
    
    Returns:
        Dictionary with metadata:
        - duration_seconds: Total duration in seconds (calculated from relative timestamps)
        - participant_count: Estimated from speaker labels (if available)
    """
    if not webvtt_content or not webvtt_content.strip():
        return {}
    
    metadata = {}
    
    # Extract timestamps to calculate duration
    timestamp_pattern = r"(\d{2}):(\d{2}):(\d{2})\.(\d{3})\s*-->\s*(\d{2}):(\d{2}):(\d{2})\.(\d{3})"
    timestamps = re.findall(timestamp_pattern, webvtt_content)
    
    if timestamps:
        # Get first and last timestamps
        first_timestamp = timestamps[0]
        last_timestamp = timestamps[-1]
        
        # Parse timestamps (these are relative, not absolute Unix timestamps)
        def parse_timestamp(h, m, s, ms):
            return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000.0
        
        start_seconds = parse_timestamp(*first_timestamp[:4])
        end_seconds = parse_timestamp(*last_timestamp[4:])
        
        # Calculate duration from relative timestamps (this is correct)
        metadata["duration_seconds"] = int(end_seconds - start_seconds)
        # Do not set started_at/ended_at - WebVTT only provides relative timestamps
        # To get absolute timestamps, fetch the recording/session start time from Daily.co API
    
    # Try to extract participant count from speaker labels
    # Look for patterns like "Speaker 1:", "Speaker 2:", etc.
    speaker_pattern = r"(?:Speaker|speaker|Participant|participant)\s*(\d+)"
    speakers = set(re.findall(speaker_pattern, webvtt_content))
    if speakers:
        metadata["participant_count"] = len(speakers)
    
    return metadata


async def fetch_and_store_transcript(room_name: str, interview_id: str) -> dict:
    """
    Fetch transcript from Daily.co and store in database.
    
    This function:
    1. Calls Daily.co API to get transcript
    2. Parses WebVTT to plain text
    3. Extracts metadata
    4. Stores in database
    
    Args:
        room_name: Daily.co room name (e.g., "interview-{interview_id}")
        interview_id: Interview UUID as string
    
    Returns:
        Dictionary containing stored transcript data
    
    Raises:
        HTTPException: If transcript is not available or processing fails
    """
    # Check if transcript already exists
    existing_transcript = get_transcript_by_room_name(room_name)
    if existing_transcript and existing_transcript.get("status") == "completed":
        return existing_transcript
    
    # Fetch transcript WebVTT content from Daily.co
    webvtt_content = await get_daily_transcript(room_name)
    
    if not webvtt_content:
        # Transcript not available yet - create pending record or update existing
        if existing_transcript:
            update_transcript_status(existing_transcript["id"], "pending")
            return existing_transcript
        
        # Create pending transcript record
        return create_transcript(
            interview_id=interview_id,
            daily_room_name=room_name,
            transcript_text="",  # Empty until transcript is available
            status="pending",
        )
    
    # Parse WebVTT to plain text
    transcript_text = parse_webvtt_to_text(webvtt_content)
    
    # Parse WebVTT to structured segments with speaker information
    segments = parse_webvtt_to_segments(webvtt_content)
    
    # Extract metadata
    metadata = extract_webvtt_metadata(webvtt_content)
    
    # Create structured transcript data with speaker segments
    structured_transcript_data = None
    if segments:
        structured_transcript_data = {"segments": segments}
    
    # Update or create transcript record
    if existing_transcript:
        # Update existing transcript
        return update_transcript(
            transcript_id=existing_transcript["id"],
            transcript_text=transcript_text,
            transcript_webvtt=webvtt_content,
            transcript_data=structured_transcript_data,  # Store structured data with speaker segments
            started_at=metadata.get("started_at"),
            ended_at=metadata.get("ended_at"),
            duration_seconds=metadata.get("duration_seconds"),
            participant_count=metadata.get("participant_count"),
            status="completed",
        )
    else:
        # Create new transcript record
        return create_transcript(
            interview_id=interview_id,
            daily_room_name=room_name,
            transcript_text=transcript_text,
            transcript_webvtt=webvtt_content,
            transcript_data=structured_transcript_data,  # Store structured data with speaker segments
            started_at=metadata.get("started_at"),
            ended_at=metadata.get("ended_at"),
            duration_seconds=metadata.get("duration_seconds"),
            participant_count=metadata.get("participant_count"),
            status="completed",
        )
