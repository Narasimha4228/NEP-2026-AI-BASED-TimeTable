from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    # API config
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "AI Timetable Generator"
    
    # CORS Configuration
    ALLOWED_ORIGINS: List[AnyHttpUrl] = []

    @field_validator("ALLOWED_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v

    # Database Configuration
    MONGODB_URL: str
    DATABASE_NAME: str

    # Security Configuration
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 days
    
    # AI Configuration
    GEMINI_API_KEY: Optional[str] = None
    
    # File Storage
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    # Pagination
    DEFAULT_PAGE_SIZE: int = 20
    MAX_PAGE_SIZE: int = 100
    
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"
    }

# Create settings instance
settings = Settings()
