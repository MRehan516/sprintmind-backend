from sqlalchemy import Column, String, Text, Integer, DateTime, JSON, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func, text
from app.database import Base
import uuid


class Analysis(Base):
    """
    Analysis model for storing sprint analysis data.
    """
    __tablename__ = "analysis"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()")
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    user_email = Column(String(255), nullable=False)
    raw_interviews = Column(Text, nullable=True)
    raw_jira = Column(Text, nullable=True)
    raw_analytics = Column(Text, nullable=True)
    output_json = Column(JSON, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    feedback_score = Column(Integer, nullable=True)
    feedback_text = Column(Text, nullable=True)
    
    __table_args__ = (
        Index('ix_analysis_user_email', 'user_email'),
    )


class Session(Base):
    """
    Session model for tracking user sessions.
    """
    __tablename__ = "session"
    
    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("uuid_generate_v4()")
    )
    user_email = Column(String(255), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_active = Column(
        DateTime(timezone=True),
        nullable=True
    )
    
    __table_args__ = (
        Index('ix_session_user_email', 'user_email'),
    )

# Made with Bob
