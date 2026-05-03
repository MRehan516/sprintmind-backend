from pydantic import BaseModel, EmailStr, Field
from typing import List, Optional, Literal
from uuid import UUID
from datetime import datetime


class AnalyzeRequest(BaseModel):
    """Request model for analyzing user research data."""
    user_email: EmailStr
    interviews: str = Field(..., min_length=10, max_length=50000)
    jira_backlog: str = Field(..., min_length=10, max_length=50000)
    analytics_data: str = Field(..., min_length=10, max_length=50000)


class SignalItem(BaseModel):
    """Individual signal extracted from user research."""
    type: Literal["pain", "request", "behavior"]
    description: str
    source: Literal["interviews", "jira", "analytics"]
    intensity: int = Field(..., ge=1, le=5)


class FeatureRecommendation(BaseModel):
    """Feature recommendation with supporting evidence."""
    feature_name: str
    problem_it_solves: str
    supporting_evidence: List[str]
    priority_score: int = Field(..., ge=1, le=100)
    estimated_user_impact: str


class Challenge(BaseModel):
    """Challenges associated with a feature."""
    feature_name: str
    challenges: List[str]


class AnalysisOutput(BaseModel):
    """Complete analysis output."""
    top_features: List[FeatureRecommendation]
    challenges_per_feature: List[Challenge]
    consensus_score: float
    generated_at: datetime
    processing_time_ms: int


class AnalyzeResponse(BaseModel):
    """Response model for analysis endpoint."""
    analysis_id: UUID
    output: AnalysisOutput
    status: Literal["success", "partial", "failed"]


class FeedbackRequest(BaseModel):
    """Request model for submitting feedback."""
    analysis_id: UUID
    score: int = Field(..., ge=1, le=5)
    feedback_text: Optional[str] = Field(None, max_length=2000)


class HistoryItem(BaseModel):
    """Individual history item."""
    analysis_id: UUID
    created_at: datetime
    consensus_score: float
    top_feature_name: str
    feedback_score: Optional[int] = None


class HistoryResponse(BaseModel):
    """Response model for history endpoint."""
    user_email: str
    analyses: List[HistoryItem]

# Made with Bob
