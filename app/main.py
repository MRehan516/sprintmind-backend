from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.config import settings
from app.routers import analyze, feedback, history
from app.database import engine, Base, get_db
from app.models import Analysis, Session as SessionModel

# Create FastAPI app
app = FastAPI(
    title="SprintMind API",
    description="AI-powered product priority synthesis engine.",
    version="1.0.0"
)

"""
CORS Configuration for Replit-to-Railway Architecture
======================================================

Why CORS is needed:
-------------------
CORS (Cross-Origin Resource Sharing) is a security mechanism that browsers enforce
to prevent malicious websites from making unauthorized requests to your API.

Our Architecture:
-----------------
- Frontend: React app hosted on Replit (e.g., https://your-app.replit.app)
- Backend: FastAPI hosted on Railway (e.g., https://your-api.railway.app)

The Problem:
------------
When the React frontend (origin A) tries to fetch data from the FastAPI backend
(origin B), the browser blocks the request by default because they're on different
domains. This is the "Failed to fetch" CORS error you're seeing.

The Solution:
-------------
We configure CORSMiddleware to tell the browser: "It's okay for requests from
these origins to access this API." This adds special headers to API responses
that the browser checks before allowing the frontend to read the data.

Configuration Details:
----------------------
- allow_origins=["*"]: Allows requests from ANY domain (use specific domains in production)
- allow_credentials=True: Allows cookies/auth headers to be sent with requests
- allow_methods=["*"]: Allows all HTTP methods (GET, POST, PUT, DELETE, etc.)
- allow_headers=["*"]: Allows all custom headers in requests

Security Note for Hackathon:
-----------------------------
Using ["*"] for allow_origins is acceptable for hackathons and development, but
for production apps, you should specify exact domains like:
allow_origins=["https://your-app.replit.app", "https://yourdomain.com"]

For more info: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS
"""

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - perfect for hackathons!
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods
    allow_headers=["*"],  # Allows all headers
)

# Include routers with /api/v1 prefix
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(feedback.router, prefix="/api/v1", tags=["feedback"])
app.include_router(history.router, prefix="/api/v1", tags=["history"])


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    print("Starting database initialization...")
    try:
        # Create the uuid-ossp extension for PostgreSQL
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"))
            conn.commit()
            print("[OK] UUID extension enabled")
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        print("[OK] All tables created successfully")
        
        # List created tables
        print("\nCreated tables:")
        for table_name in Base.metadata.tables.keys():
            print(f"  - {table_name}")
        
        print("\n[SUCCESS] Database initialization complete!")
        
    except Exception as e:
        print(f"\n[ERROR] Error during database initialization: {e}")


@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "SprintMind API",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health")
async def health(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity test."""
    database_status = "connected"
    try:
        # Attempt a simple SELECT 1 query to check database connectivity
        db.execute(text("SELECT 1"))
    except Exception as e:
        database_status = "error"
        print(f"Database health check failed: {e}")
    
    return {
        "status": "ok",
        "environment": settings.environment,
        "database": database_status
    }


# Made with Bob