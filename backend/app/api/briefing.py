"""Briefing generation endpoint."""

import logging
from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.crew.briefing import create_briefing_crew
from app.models.interview import InterviewCreate

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateBriefingRequest(BaseModel):
    """Request model for generating a briefing.
    
    Supports multiple input types:
    - job_description/resume_text: Plain text (backward compatible)
    - job_description_path/resume_path: File path or URL (for file/URL inputs)
    - job_description_source/resume_source: Source type ("text", "pdf", "docx", "url")
    """

    job_description: str | None = None
    resume_text: str | None = None
    job_description_path: str | None = None
    resume_path: str | None = None
    job_description_source: str = "text"
    resume_source: str = "text"


class GenerateBriefingResponse(BaseModel):
    """Response model for briefing generation."""

    interview_id: UUID
    briefing: str


@router.post("/generate-briefing", response_model=GenerateBriefingResponse)
async def generate_briefing(request: GenerateBriefingRequest):
    """Generate an interview briefing using CrewAI.
    
    The crew will automatically extract text from files/URLs using tools.
    """
    try:
        # Create the briefing crew
        crew = create_briefing_crew()

        # Prepare inputs for the crew
        # Pass file paths/URLs if available, otherwise pass text
        inputs = {}
        
        # Handle job description
        # Check if it's a file (pdf, docx, or generic "file" source)
        is_file_source = (
            request.job_description_source in ("pdf", "docx", "file") 
            and request.job_description_path
        )
        # Also check file extension if source is "file"
        if request.job_description_source == "file" and request.job_description_path:
            path_lower = request.job_description_path.lower()
            if path_lower.endswith(".pdf"):
                is_file_source = True
            elif path_lower.endswith((".doc", ".docx")):
                is_file_source = True
        
        if is_file_source:
            # Determine file type from path or source
            path_lower = request.job_description_path.lower()
            if path_lower.endswith(".pdf") or ".pdf" in path_lower.split("?")[0]:
                # Prepend prefix so CrewAI knows it's a PDF file
                inputs["job_description"] = f"PDF_FILE:{request.job_description_path}"
                logger.info(f"Using job description from PDF file: {request.job_description_path}")
            elif path_lower.endswith((".docx", ".doc")) or any(ext in path_lower.split("?")[0] for ext in [".docx", ".doc"]):
                # Prepend prefix so CrewAI knows it's a DOCX file
                inputs["job_description"] = f"DOCX_FILE:{request.job_description_path}"
                logger.info(f"Using job description from DOCX file: {request.job_description_path}")
            else:
                # Generic file - try to infer from source type
                if request.job_description_source == "pdf":
                    inputs["job_description"] = f"PDF_FILE:{request.job_description_path}"
                elif request.job_description_source == "docx":
                    inputs["job_description"] = f"DOCX_FILE:{request.job_description_path}"
                else:
                    inputs["job_description"] = f"FILE:{request.job_description_path}"
                logger.info(f"Using job description from file: {request.job_description_path}")
        elif request.job_description_source == "url" and request.job_description_path:
            # Pass URL with prefix so CrewAI knows it's a website
            inputs["job_description"] = f"WEBSITE_URL:{request.job_description_path}"
            logger.info(f"Using job description from URL: {request.job_description_path}")
        elif request.job_description:
            # Plain text
            inputs["job_description"] = request.job_description
            job_desc_snippet = (
                request.job_description[:200] + "..."
                if len(request.job_description) > 200
                else request.job_description
            )
            logger.info(f"Using job description as text (length: {len(request.job_description)} chars)")
            logger.info(f"Job description snippet: {job_desc_snippet}")
        else:
            raise HTTPException(
                status_code=400,
                detail="Job description is required (text, file path, or URL)",
            )
        
        # Handle resume
        # Check if it's a file (pdf, docx, or generic "file" source)
        is_file_source = (
            request.resume_source in ("pdf", "docx", "file") 
            and request.resume_path
        )
        # Also check file extension if source is "file"
        if request.resume_source == "file" and request.resume_path:
            path_lower = request.resume_path.lower()
            if path_lower.endswith(".pdf"):
                is_file_source = True
            elif path_lower.endswith((".doc", ".docx")):
                is_file_source = True
        
        if is_file_source:
            # Determine file type from path or source
            path_lower = request.resume_path.lower()
            if path_lower.endswith(".pdf") or ".pdf" in path_lower.split("?")[0]:
                # Prepend prefix so CrewAI knows it's a PDF file
                inputs["resume_text"] = f"PDF_FILE:{request.resume_path}"
                logger.info(f"Using resume from PDF file: {request.resume_path}")
            elif path_lower.endswith((".docx", ".doc")) or any(ext in path_lower.split("?")[0] for ext in [".docx", ".doc"]):
                # Prepend prefix so CrewAI knows it's a DOCX file
                inputs["resume_text"] = f"DOCX_FILE:{request.resume_path}"
                logger.info(f"Using resume from DOCX file: {request.resume_path}")
            else:
                # Generic file - try to infer from source type
                if request.resume_source == "pdf":
                    inputs["resume_text"] = f"PDF_FILE:{request.resume_path}"
                elif request.resume_source == "docx":
                    inputs["resume_text"] = f"DOCX_FILE:{request.resume_path}"
                else:
                    inputs["resume_text"] = f"FILE:{request.resume_path}"
                logger.info(f"Using resume from file: {request.resume_path}")
        elif request.resume_source == "url" and request.resume_path:
            # Pass URL with prefix so CrewAI knows it's a website
            inputs["resume_text"] = f"WEBSITE_URL:{request.resume_path}"
            logger.info(f"Using resume from URL: {request.resume_path}")
        elif request.resume_text:
            # Plain text
            inputs["resume_text"] = request.resume_text
            resume_snippet = (
                request.resume_text[:200] + "..."
                if len(request.resume_text) > 200
                else request.resume_text
            )
            logger.info(f"Using resume as text (length: {len(request.resume_text)} chars)")
            logger.info(f"Resume snippet: {resume_snippet}")
        else:
            raise HTTPException(
                status_code=400,
                detail="Resume is required (text, file path, or URL)",
            )

        logger.info(f"Passing inputs to crew: job_description ({len(str(inputs.get('job_description', '')))} chars/path), resume_text ({len(str(inputs.get('resume_text', '')))} chars/path)")

        # Run the crew to generate the briefing
        # Agents will extract text from files/URLs automatically using tools
        result = crew.kickoff(inputs=inputs)

        # Extract briefing from result
        briefing = result.output if hasattr(result, "output") else str(result)
        
        logger.info(f"Briefing generated successfully. Length: {len(briefing)} chars")
        logger.info(f"Briefing snippet: {briefing[:300]}...")

        # TODO: Store interview in database
        # For now, return a mock interview_id
        # In production, this should:
        # 1. Create an interview record in the database
        # 2. Store the briefing as an interview_note
        # 3. Return the actual interview_id

        from uuid import uuid4

        interview_id = uuid4()

        return GenerateBriefingResponse(interview_id=interview_id, briefing=briefing)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate briefing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")



