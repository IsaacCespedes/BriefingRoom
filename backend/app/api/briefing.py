"""Briefing generation endpoint."""

from uuid import UUID

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.crew.briefing import create_briefing_crew
from app.models.interview import InterviewCreate

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
        # Create the briefing crew
        crew = create_briefing_crew()

        # Prepare inputs for the crew
        inputs = {
            "job_description": request.job_description,
            "resume_text": request.resume_text,
        }

        # Run the crew to generate the briefing
        result = crew.kickoff(inputs=inputs)

        # Extract briefing from result
        briefing = result.output if hasattr(result, "output") else str(result)

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
        raise HTTPException(status_code=500, detail=f"Failed to generate briefing: {str(e)}")



