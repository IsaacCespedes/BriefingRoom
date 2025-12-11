"""File storage service for handling PDF/DOCX uploads to Supabase Storage."""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import httpx
from fastapi import UploadFile
from supabase import Client

from app.db import get_supabase_client

# Storage configuration
STORAGE_BUCKET = "interview-files"
MAX_FILE_SIZE_MB = 10
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}
ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


@dataclass
class FileStorageResult:
    """Result of file storage operation."""

    file_path: str  # Storage path
    file_url: str  # Signed URL for CrewAI agents
    metadata: dict  # filename, file_size, file_type


def validate_file(file: UploadFile) -> tuple[bool, Optional[str]]:
    """
    Validate uploaded file (type, size).
    
    Returns:
        (is_valid, error_message)
    """
    # Check file extension
    filename = file.filename or ""
    file_ext = Path(filename).suffix.lower()
    
    if file_ext not in ALLOWED_EXTENSIONS:
        return False, f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
    
    # Check MIME type
    if file.content_type and file.content_type not in ALLOWED_MIME_TYPES:
        return False, f"Invalid MIME type. Allowed: {', '.join(ALLOWED_MIME_TYPES)}"
    
    # Note: File size validation should be done when reading the file
    # We'll check it during upload
    
    return True, None


def store_file(
    file: UploadFile,
    interview_id: str,
    field_type: str,  # "job_description" or "resume"
) -> FileStorageResult:
    """
    Store file in Supabase Storage and return access path/URL.
    
    Args:
        file: Uploaded file
        interview_id: Interview ID
        field_type: "job_description" or "resume"
    
    Returns:
        FileStorageResult with file_path, file_url, and metadata
    
    Raises:
        ValueError: If file validation fails or storage fails
    """
    # Validate file
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        raise ValueError(error_msg or "File validation failed")
    
    # Read file content
    content = file.file.read()
    file_size = len(content)
    
    # Check file size
    if file_size > MAX_FILE_SIZE_BYTES:
        raise ValueError(f"File size exceeds {MAX_FILE_SIZE_MB}MB limit")
    
    if file_size == 0:
        raise ValueError("File is empty")
    
    # Generate storage path: {interview_id}/{field_type}/{filename}
    filename = file.filename or "uploaded_file"
    # Sanitize filename (remove path components)
    safe_filename = Path(filename).name
    storage_path = f"{interview_id}/{field_type}/{safe_filename}"
    
    try:
        # Get Supabase client
        storage_client = get_supabase_client()
        
        # Upload file using Supabase client
        # The client is configured with the service role key, so it should bypass RLS
        response = storage_client.storage.from_(STORAGE_BUCKET).upload(
            path=storage_path,
            file=content,
            file_options={
                "content-type": file.content_type or "application/octet-stream",
                "x-upsert": "true",
            },
        )
        
        # Supabase-py's upload method does not return a traditional response object
        # It raises an exception on failure. If it completes, the upload was successful.
        # We need to manually check if the object exists to be fully sure.
        # However, for simplicity here, we'll assume success if no exception is raised.
        
        # Generate signed URL using the same client
        signed_url_result = storage_client.storage.from_(STORAGE_BUCKET).create_signed_url(
            path=storage_path,
            expires_in=86400,  # 24 hours
        )
        
        # Handle different response formats
        if isinstance(signed_url_result, dict):
            if "error" in signed_url_result:
                raise ValueError(f"Failed to generate signed URL: {signed_url_result['error']}")
            signed_url = signed_url_result.get("signedURL") or signed_url_result.get("signed_url") or str(signed_url_result)
        elif hasattr(signed_url_result, "error") and signed_url_result.error:
            raise ValueError(f"Failed to generate signed URL: {signed_url_result.error}")
        elif hasattr(signed_url_result, "signedURL"):
            signed_url = signed_url_result.signedURL
        elif hasattr(signed_url_result, "signed_url"):
            signed_url = signed_url_result.signed_url
        else:
            signed_url = str(signed_url_result)
        
        # Prepare metadata
        metadata = {
            "filename": safe_filename,
            "file_size": file_size,
            "file_type": file.content_type or "unknown",
            "file_extension": Path(filename).suffix.lower(),
        }
        
        return FileStorageResult(
            file_path=storage_path,
            file_url=signed_url,
            metadata=metadata,
        )
    
    except Exception as e:
        raise ValueError(f"Failed to store file: {str(e)}") from e
