"""
Database initialization script for SprintMind.
This script creates all tables defined in the models using SQLAlchemy.
Run this script once to set up the database schema.
"""
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import engine, Base
from app.models import Analysis, Session


def init_db():
    """
    Initialize the database by creating all tables.
    This will create the uuid-ossp extension if needed and all tables.
    """
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
        sys.exit(1)


if __name__ == "__main__":
    from sqlalchemy import text
    init_db()

# Made with Bob
