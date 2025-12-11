"""Emotion detection endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Body

from app.api.auth import validate_token_dependency, TokenInfoResponse
from app.db import create_emotion_detections, get_emotion_detections_by_interview_id
from pydantic import BaseModel

router = APIRouter()


class SaveEmotionsRequest(BaseModel):
    """Request model for saving emotion detections from frontend."""
    
    emotion_data: Dict[str, Any]  # Structured emotion data with detections
    source: str = "local_storage"  # Source of emotions (local_storage, api, etc.)


@router.post("/emotions/{interview_id}/save")
async def save_emotions(
    interview_id: str,
    request: SaveEmotionsRequest = Body(...),
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Save emotion detections from frontend (local storage) to backend.
    
    This endpoint:
    1. Receives emotion detection data from frontend (captured during the call)
    2. Stores all detections in database
    3. Associates them with the interview
    
    This is useful for:
    - Storing emotion analytics for interviews
    - Providing emotion timeline data
    - Post-interview analysis
    """
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        emotion_data = request.emotion_data
        detections = emotion_data.get("detections", [])
        
        if not detections:
            raise HTTPException(
                status_code=400,
                detail="No emotion detections provided",
            )
        
        # Create emotion detection records
        created = create_emotion_detections(
            interview_id=interview_id,
            detections=detections,
            source=request.source,
        )
        
        return {
            "status": "success",
            "interview_id": interview_id,
            "detections_saved": len(created),
            "message": f"Successfully saved {len(created)} emotion detections",
        }
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save emotion detections: {str(e)}",
        )


@router.get("/emotions/{interview_id}")
async def get_emotions(
    interview_id: str,
    token_info: TokenInfoResponse = Depends(validate_token_dependency),
):
    """
    Retrieve emotion detections for an interview.
    
    This endpoint:
    1. Validates authentication and interview_id ownership
    2. Retrieves all emotion detections from database
    3. Returns detections ordered by timestamp
    
    Returns empty list if no detections are found.
    """
    # Validate that the interview_id in the path matches the token's interview_id
    if interview_id != token_info.interview_id:
        raise HTTPException(
            status_code=403,
            detail="Interview ID in path does not match the token's interview ID",
        )
    
    try:
        detections = get_emotion_detections_by_interview_id(interview_id)
        
        return {
            "interview_id": interview_id,
            "detections": detections,
            "count": len(detections),
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve emotion detections: {str(e)}",
        )
