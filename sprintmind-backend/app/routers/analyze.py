import asyncio
import json
from datetime import datetime, timedelta
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Analysis
from app.schemas import AnalyzeRequest, AnalyzeResponse, AnalysisOutput
from app.pipeline import run_consensus_pipeline

router = APIRouter()


async def check_rate_limit(user_email: str, db: Session) -> None:
    """
    Check if user has exceeded rate limit (3 analyses per 60 seconds).
    
    Args:
        user_email: User's email address
        db: Database session
        
    Raises:
        HTTPException: If rate limit is exceeded
    """
    sixty_seconds_ago = datetime.utcnow() - timedelta(seconds=60)
    
    recent_count = db.query(func.count(Analysis.id)).filter(
        Analysis.user_email == user_email,
        Analysis.created_at >= sixty_seconds_ago
    ).scalar()
    
    if recent_count >= 3:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait 60 seconds between analyses."
        )


async def run_analysis_with_timeout(request: AnalyzeRequest) -> AnalysisOutput:
    """
    Run the consensus pipeline with a 120-second timeout.
    
    Args:
        request: Analysis request
        
    Returns:
        AnalysisOutput from the pipeline
        
    Raises:
        HTTPException: If analysis times out
    """
    try:
        # Run pipeline in executor to avoid blocking
        loop = asyncio.get_event_loop()
        output = await asyncio.wait_for(
            loop.run_in_executor(None, run_consensus_pipeline, request),
            timeout=120.0
        )
        return output
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Analysis took too long. Try with shorter inputs."
        )


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze user research data and generate feature recommendations.
    
    This endpoint:
    1. Checks rate limiting (max 3 analyses per 60 seconds per email)
    2. Runs the AI analysis pipeline with 120-second timeout
    3. Saves results to database
    4. Returns analysis with recommendations and challenges
    
    Args:
        request: AnalyzeRequest with user inputs
        db: Database session (injected)
        
    Returns:
        AnalyzeResponse with analysis results
        
    Raises:
        HTTPException 429: Rate limit exceeded
        HTTPException 408: Analysis timeout
    """
    # Check rate limit
    await check_rate_limit(request.user_email, db)
    
    # Run analysis with timeout
    output = await run_analysis_with_timeout(request)
    
    # Determine status based on results
    if not output.top_features:
        analysis_status: Literal["success", "partial", "failed"] = "failed"
    elif len(output.top_features) < 3:
        analysis_status = "partial"
    else:
        analysis_status = "success"
    
    # Convert output to dict for JSON storage
    output_dict = output.model_dump(mode='json')
    
    # Create Analysis record
    analysis = Analysis(
        user_email=request.user_email,
        raw_interviews=request.interviews,
        raw_jira=request.jira_backlog,
        raw_analytics=request.analytics_data,
        output_json=output_dict,
        processing_time_ms=output.processing_time_ms
    )
    
    db.add(analysis)
    db.commit()
    db.refresh(analysis)
    
    # Create response
    response = AnalyzeResponse(
        analysis_id=analysis.id,
        output=output,
        status=analysis_status
    )
    
    return response


# Made with Bob