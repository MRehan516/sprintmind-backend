from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models import Analysis
from app.schemas import FeedbackRequest

router = APIRouter()


@router.post("/feedback")
async def submit_feedback(
    request: FeedbackRequest,
    db: Session = Depends(get_db)
):
    """
    Submit feedback for an analysis.
    
    Args:
        request: FeedbackRequest with analysis_id, score, and optional text
        db: Database session (injected)
        
    Returns:
        Status confirmation with analysis_id
        
    Raises:
        HTTPException 404: Analysis not found
    """
    # Find analysis by ID
    analysis = db.query(Analysis).filter(Analysis.id == request.analysis_id).first()
    
    if not analysis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis with id {request.analysis_id} not found"
        )
    
    # Update feedback
    analysis.feedback_score = request.score
    analysis.feedback_text = request.feedback_text
    
    db.commit()
    
    return {
        "status": "saved",
        "analysis_id": str(analysis.id)
    }


# Made with Bob