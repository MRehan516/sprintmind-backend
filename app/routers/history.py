from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models import Analysis
from app.schemas import HistoryResponse, HistoryItem

router = APIRouter()


@router.get("/history/{email}", response_model=HistoryResponse)
async def get_history(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Get analysis history for a user.
    
    Returns last 10 analyses ordered by created_at descending.
    Does not return raw input text for privacy protection.
    
    Args:
        email: User's email address
        db: Database session (injected)
        
    Returns:
        HistoryResponse with list of HistoryItem objects
    """
    # Query last 10 analyses for this email
    analyses = db.query(Analysis).filter(
        Analysis.user_email == email
    ).order_by(
        Analysis.created_at.desc()
    ).limit(10).all()
    
    # Convert to HistoryItem objects
    history_items = []
    for analysis in analyses:
        # Extract top feature name from output_json
        top_feature_name = "N/A"
        if analysis.output_json and isinstance(analysis.output_json, dict):
            top_features = analysis.output_json.get("top_features", [])
            if top_features and len(top_features) > 0:
                top_feature_name = top_features[0].get("feature_name", "N/A")
        
        # Extract consensus score
        consensus_score = 0.0
        if analysis.output_json and isinstance(analysis.output_json, dict):
            consensus_score = analysis.output_json.get("consensus_score", 0.0)
        
        history_item = HistoryItem(
            analysis_id=analysis.id,
            created_at=analysis.created_at,
            consensus_score=consensus_score,
            top_feature_name=top_feature_name,
            feedback_score=analysis.feedback_score
        )
        history_items.append(history_item)
    
    return HistoryResponse(
        user_email=email,
        analyses=history_items
    )


# Made with Bob