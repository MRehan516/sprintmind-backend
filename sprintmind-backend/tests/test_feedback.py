import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from uuid import uuid4
from app.main import app
from app.database import Base, get_db

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    """Override database dependency for testing."""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_feedback_valid():
    """Test feedback endpoint with valid analysis ID."""
    # First, create an analysis
    analyze_payload = {
        "user_email": "feedback@example.com",
        "interviews": "User mentioned they struggle with task management and need better organization tools.",
        "jira_backlog": "TASK-123: Implement calendar sync feature. TASK-456: Add task prioritization.",
        "analytics_data": "Feature usage: Calendar views 45%, Task creation 78%, Mobile app usage 23%."
    }
    
    analyze_response = client.post("/api/v1/analyze", json=analyze_payload)
    assert analyze_response.status_code == 200
    analysis_data = analyze_response.json()
    analysis_id = analysis_data["analysis_id"]
    
    # Now submit feedback for this analysis
    feedback_payload = {
        "analysis_id": analysis_id,
        "score": 5,
        "feedback_text": "Great analysis, very helpful!"
    }
    
    feedback_response = client.post("/api/v1/feedback", json=feedback_payload)
    
    assert feedback_response.status_code == 200
    feedback_data = feedback_response.json()
    assert feedback_data["status"] == "saved"
    assert feedback_data["analysis_id"] == analysis_id


def test_feedback_invalid_id():
    """Test feedback endpoint with non-existent analysis ID."""
    # Generate a random UUID that doesn't exist in database
    random_uuid = str(uuid4())
    
    feedback_payload = {
        "analysis_id": random_uuid,
        "score": 3,
        "feedback_text": "This should fail"
    }
    
    response = client.post("/api/v1/feedback", json=feedback_payload)
    
    assert response.status_code == 404  # Not found


# Made with Bob