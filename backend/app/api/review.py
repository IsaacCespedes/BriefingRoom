"""Interview review generation endpoint."""

import logging

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.auth import validate_token_dependency
from app.api.auth import TokenInfoResponse
from app.crew.review import create_review_crew
from app.db import create_interview_note, get_interview, get_transcript_by_interview_id

logger = logging.getLogger(__name__)

router = APIRouter()


class GenerateReviewRequest(BaseModel):
    """Optional request body for review generation."""

    transcript_text: str | None = None  # Optional: can provide transcript text directly


class GenerateReviewResponse(BaseModel):
    """Response model for review generation."""

    interview_id: str
    review_id: str
    review: str


class GetReviewResponse(BaseModel):
    """Response model for getting a review."""

    interview_id: str
    review_id: str
    review: str
    created_at: str


@router.post("/interviews/{interview_id}/review", response_model=GenerateReviewResponse)
async def generate_review(
    interview_id: str,
    request: GenerateReviewRequest | None = None,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """Generate an interview review based on the transcript using CrewAI.
    
    This endpoint:
    1. Validates the interview exists and user has access
    2. Retrieves the completed transcript for the interview (or uses provided transcript text)
    3. Uses CrewAI to analyze the transcript and generate a review
    4. Stores the review as an interview_note with source="CrewAI Review"
    5. Returns the review
    
    The review includes:
    - Overall assessment
    - Call summary
    - Candidate strengths (with evidence)
    - Candidate weaknesses/concerns (with evidence)
    - Interview quality assessment
    - Evidence-based recommendations
    
    If transcript_text is provided in the request body, it will be used directly.
    Otherwise, the transcript will be fetched from the database.
    """
    try:
        # Validate interview exists and user has access
        interview = get_interview(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Verify the token's interview_id matches (security check)
        if token_info.interview_id != interview_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Token does not match interview ID",
            )
        
        # Get transcript text - either from request body or database
        transcript_text = None
        
        if request and request.transcript_text:
            # Use transcript text provided in request (e.g., from local storage)
            transcript_text = request.transcript_text
            logger.info(f"Using transcript text provided in request (length: {len(transcript_text)} chars)")
        else:
            # Get the transcript from database
            transcript = get_transcript_by_interview_id(interview_id)
            if not transcript:
                raise HTTPException(
                    status_code=404,
                    detail="Transcript not found for this interview. Please ensure the interview has been completed and transcript is available, or provide transcript_text in the request body.",
                )
            
            # Get transcript text from database
            transcript_text = transcript.get("transcript_text")
            if not transcript_text:
                raise HTTPException(
                    status_code=400,
                    detail="Transcript text is empty. Cannot generate review.",
                )
        
        logger.info(
            f"Generating review for interview {interview_id}. Transcript length: {len(transcript_text)} chars"
        )
        
        # Create the review crew
        crew = create_review_crew()
        
        # Prepare inputs for the crew
        inputs = {
            "transcript_text": transcript_text,
        }
        
        # Run the crew to generate the review
        result = crew.kickoff(inputs=inputs)
        
        # Extract review from result
        review = result.output if hasattr(result, "output") else str(result)
        
        logger.info(f"Review generated successfully. Length: {len(review)} chars")
        logger.info(f"Review snippet: {review[:300]}...")
        
        # Store the review as an interview note
        review_note = create_interview_note(
            interview_id=interview_id,
            note=review,
            source="CrewAI Review",
        )
        
        review_id = str(review_note["id"])
        
        logger.info(f"Review stored as interview note with ID: {review_id}")
        
        return GenerateReviewResponse(
            interview_id=interview_id,
            review_id=review_id,
            review=review,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate review: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate review: {str(e)}"
        )


@router.get("/interviews/{interview_id}/review", response_model=GetReviewResponse)
async def get_review(
    interview_id: str,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """Get the interview review if it exists.
    
    Returns the most recent review (interview_note with source="CrewAI Review")
    for the given interview.
    """
    try:
        # Validate interview exists and user has access
        interview = get_interview(interview_id)
        if not interview:
            raise HTTPException(status_code=404, detail="Interview not found")
        
        # Verify the token's interview_id matches (security check)
        if token_info.interview_id != interview_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: Token does not match interview ID",
            )
        
        # Get interview notes and find the review
        from app.db import get_interview_notes
        
        notes = get_interview_notes(interview_id)
        
        # Find the most recent review (CrewAI Review)
        review_notes = [
            note for note in notes if note.get("source") == "CrewAI Review"
        ]
        
        if not review_notes:
            raise HTTPException(
                status_code=404,
                detail="Review not found. Generate a review first using POST /api/interviews/{interview_id}/review",
            )
        
        # Get the most recent review (should be sorted by created_at, but get the last one to be safe)
        review_note = review_notes[-1]
        
        # Format created_at as ISO string
        created_at = review_note["created_at"]
        if isinstance(created_at, str):
            created_at_str = created_at
        elif hasattr(created_at, "isoformat"):
            created_at_str = created_at.isoformat()
        else:
            created_at_str = str(created_at)
        
        return GetReviewResponse(
            interview_id=interview_id,
            review_id=str(review_note["id"]),
            review=review_note["note"],
            created_at=created_at_str,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get review: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to get review: {str(e)}"
        )
