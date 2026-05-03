from pydantic_settings import BaseSettings
from pydantic import Field, field_validator


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # WatsonX Configuration
    watsonx_api_key: str = Field(..., alias="WATSONX_API_KEY")
    watsonx_project_id: str = Field(..., alias="WATSONX_PROJECT_ID")
    watsonx_url: str = Field(default="https://us-south.ml.cloud.ibm.com", alias="WATSONX_URL")
    
    # Database Configuration
    database_url: str = Field(..., alias="DATABASE_URL")
    
    # Application Configuration
    environment: str = Field(default="development", alias="ENVIRONMENT")
    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    
    @field_validator("watsonx_api_key")
    @classmethod
    def validate_watsonx_api_key(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("WATSONX_API_KEY is required and cannot be empty")
        return v
    
    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("DATABASE_URL is required and cannot be empty")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()

# Made with Bob
