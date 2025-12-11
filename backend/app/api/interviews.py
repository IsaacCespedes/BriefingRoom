"""Interview creation and management endpoints."""

import secrets
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

from app.api.auth import hash_token
from app.db import create_interview as db_create_interview
from app.db import create_token as db_create_token
from app.db import get_interview as db_get_interview
from app.models.interview import InterviewCreate, InterviewResponse
from app.services.file_storage import store_file
from app.services.url_handler import validate_and_store_url

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
async def create_interview(
    request: Request,
    # For multipart requests (only used when content-type is multipart/form-data)
    job_description: Optional[UploadFile] = File(None),
    resume_text: Optional[UploadFile] = File(None),
    job_description_text: Optional[str] = Form(None),
    resume_text_value: Optional[str] = Form(None),
    job_description_type: Optional[str] = Form("text"),
    resume_type: Optional[str] = Form("text"),
    status: Optional[str] = Form("pending"),
):
    """
    Create a new interview with flexible input types (text, file, or URL).
    
    This endpoint accepts:
    - JSON body (InterviewCreate model) for backward compatibility
    - Multipart/form-data for file uploads and text/URL inputs
    
    Flow:
    1. Detect input type for each field
    2. Store files in Supabase Storage (if file)
    3. Validate URLs (if URL)
    4. Create interview record with file paths/URLs/metadata
    5. Generate tokens
    6. Return interview ID and tokens
    
    Note: CrewAI agents will extract text from files/URLs during briefing generation.
    """
    try:
        content_type = request.headers.get("content-type", "")
        
        # Initialize variables
        job_description_source = "text"
        resume_source = "text"
        job_description_metadata = None
        resume_metadata = None
        job_description_path = None
        resume_path = None
        job_description_text_final = None
        resume_text_final = None
        status_value = "pending"
        job_description_file = None
        resume_file = None
        
        # Handle JSON request (backward compatibility)
        if "application/json" in content_type:
            body = await request.json()
            json_body = InterviewCreate(**body)
            
            job_description_source = json_body.job_description_source
            resume_source = json_body.resume_source
            job_description_metadata = json_body.job_description_metadata
            resume_metadata = json_body.resume_metadata
            job_description_path = json_body.job_description_path
            resume_path = json_body.resume_path
            job_description_text_final = json_body.job_description
            resume_text_final = json_body.resume_text
            status_value = json_body.status
        else:
            # Handle multipart/form-data
            status_value = status or "pending"
            
            # Process job_description
            if job_description and job_description.filename:
                # File upload
                job_description_source = "file"
                job_description_file = job_description
            elif job_description_text:
                if job_description_type == "url":
                    # URL input
                    job_description_source = "url"
                    url_result = validate_and_store_url(job_description_text, "", "job_description")
                    job_description_path = url_result.url
                    job_description_metadata = url_result.metadata
                else:
                    # Plain text
                    job_description_source = "text"
                    job_description_text_final = job_description_text
            
            # Process resume_text
            if resume_text and resume_text.filename:
                # File upload
                resume_source = "file"
                resume_file = resume_text
            elif resume_text_value:
                if resume_type == "url":
                    # URL input
                    resume_source = "url"
                    url_result = validate_and_store_url(resume_text_value, "", "resume")
                    resume_path = url_result.url
                    resume_metadata = url_result.metadata
                else:
                    # Plain text
                    resume_source = "text"
                    resume_text_final = resume_text_value
        
        # Validate that we have at least one input method for each field
        if not job_description_text_final and not job_description_path and not job_description_file:
            raise HTTPException(
                status_code=400,
                detail="Job description is required (text, file, or URL)",
            )
        if not resume_text_final and not resume_path and not resume_file:
            raise HTTPException(
                status_code=400,
                detail="Resume is required (text, file, or URL)",
            )
        
        # Create interview record first (we need interview_id for file storage)
        interview = db_create_interview(
            job_description=job_description_text_final,
            resume_text=resume_text_final,
            status=status_value,
            job_description_source=job_description_source,
            resume_source=resume_source,
            job_description_metadata=job_description_metadata,
            resume_metadata=resume_metadata,
            job_description_path=job_description_path,
            resume_path=resume_path,
        )
        interview_id = str(interview["id"])
        
        # Handle file uploads (now that we have interview_id)
        if job_description_file:
            try:
                file_result = store_file(
                    job_description_file,
                    interview_id,
                    "job_description",
                )
                # Determine file type from metadata
                file_ext = file_result.metadata.get("file_extension", "").lower()
                if file_ext == ".pdf":
                    job_description_source = "pdf"
                elif file_ext in (".doc", ".docx"):
                    job_description_source = "docx"
                else:
                    job_description_source = "file"  # Fallback
                
                # Update interview with file path, metadata, and correct source type
                from app.db import get_supabase_client
                client = get_supabase_client()
                client.table("interviews").update({
                    "job_description_path": file_result.file_path,
                    "job_description_metadata": file_result.metadata,
                    "job_description_source": job_description_source,
                }).eq("id", interview_id).execute()
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Job description file error: {str(e)}")
        
        if resume_file:
            try:
                file_result = store_file(
                    resume_file,
                    interview_id,
                    "resume",
                )
                # Determine file type from metadata
                file_ext = file_result.metadata.get("file_extension", "").lower()
                if file_ext == ".pdf":
                    resume_source = "pdf"
                elif file_ext in (".doc", ".docx"):
                    resume_source = "docx"
                else:
                    resume_source = "file"  # Fallback
                
                # Update interview with file path, metadata, and correct source type
                from app.db import get_supabase_client
                client = get_supabase_client()
                client.table("interviews").update({
                    "resume_path": file_result.file_path,
                    "resume_metadata": file_result.metadata,
                    "resume_source": resume_source,
                }).eq("id", interview_id).execute()
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Resume file error: {str(e)}")
        
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
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to create interview: {str(e)}"
        )


@router.get("/interviews/{interview_id}")
async def get_interview(interview_id: str):
    """Get interview details by ID.
    
    For files stored in Supabase Storage, generates signed URLs for access.
    """
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
    
    # Generate signed URLs for files stored in Supabase Storage
    job_description_path = interview.get("job_description_path")
    resume_path = interview.get("resume_path")
    job_description_source = interview.get("job_description_source", "text")
    resume_source = interview.get("resume_source", "text")
    
    # If job description is a file, generate signed URL
    if job_description_source in ("pdf", "docx", "file") and job_description_path:
        try:
            from app.db import get_supabase_client
            client = get_supabase_client()
            signed_url_result = client.storage.from_("interview-files").create_signed_url(
                path=job_description_path,
                expires_in=86400,  # 24 hours
            )
            # Handle different response formats
            if isinstance(signed_url_result, dict):
                if "error" not in signed_url_result:
                    signed_url = signed_url_result.get("signedURL") or signed_url_result.get("signed_url") or str(signed_url_result)
                    job_description_path = signed_url  # Replace path with signed URL
            elif hasattr(signed_url_result, "signedURL"):
                job_description_path = signed_url_result.signedURL
            elif hasattr(signed_url_result, "signed_url"):
                job_description_path = signed_url_result.signed_url
        except Exception as e:
            # If URL generation fails, keep the original path
            pass
    
    # If resume is a file, generate signed URL
    if resume_source in ("pdf", "docx", "file") and resume_path:
        try:
            from app.db import get_supabase_client
            client = get_supabase_client()
            signed_url_result = client.storage.from_("interview-files").create_signed_url(
                path=resume_path,
                expires_in=86400,  # 24 hours
            )
            # Handle different response formats
            if isinstance(signed_url_result, dict):
                if "error" not in signed_url_result:
                    signed_url = signed_url_result.get("signedURL") or signed_url_result.get("signed_url") or str(signed_url_result)
                    resume_path = signed_url  # Replace path with signed URL
            elif hasattr(signed_url_result, "signedURL"):
                resume_path = signed_url_result.signedURL
            elif hasattr(signed_url_result, "signed_url"):
                resume_path = signed_url_result.signed_url
        except Exception as e:
            # If URL generation fails, keep the original path
            pass
    
    return {
        "id": str(interview["id"]),
        "job_description": interview.get("job_description"),
        "resume_text": interview.get("resume_text"),
        "status": interview["status"],
        "created_at": created_at,
        "job_description_source": job_description_source,
        "resume_source": resume_source,
        "job_description_metadata": interview.get("job_description_metadata"),
        "resume_metadata": interview.get("resume_metadata"),
        "job_description_path": job_description_path,
        "resume_path": resume_path,
    }

