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
    """Request model for generating a briefing."""

    job_description: str
    resume_text: str


class GenerateBriefingResponse(BaseModel):
    """Response model for briefing generation."""

    interview_id: UUID
    briefing: str


@router.post("/generate-briefing", response_model=GenerateBriefingResponse)
async def generate_briefing(request: GenerateBriefingRequest):
    """Generate an interview briefing using CrewAI."""
    try:
        # Log input snippets for debugging
        job_desc_snippet = (
            request.job_description[:200] + "..."
            if len(request.job_description) > 200
            else request.job_description
        )
        resume_snippet = (
            request.resume_text[:200] + "..."
            if len(request.resume_text) > 200
            else request.resume_text
        )
        
        logger.info("Generating briefing with inputs:")
        logger.info(f"Job description length: {len(request.job_description)} chars")
        logger.info(f"Job description snippet: {job_desc_snippet}")
        logger.info(f"Resume length: {len(request.resume_text)} chars")
        logger.info(f"Resume snippet: {resume_snippet}")

        # Create the briefing crew
        crew = create_briefing_crew()

        # Prepare inputs for the crew
        inputs = {
            "job_description": request.job_description,
            "resume_text": request.resume_text,
        }

        logger.info(f"Passing inputs to crew: job_description ({len(inputs['job_description'])} chars), resume_text ({len(inputs['resume_text'])} chars)")

        # Run the crew to generate the briefing
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

    except Exception as e:
        logger.error(f"Failed to generate briefing: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")



