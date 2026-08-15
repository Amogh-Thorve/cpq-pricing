from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

# Resolve the .env file relative to this module file.
# This makes the path work regardless of where the process is invoked from.
_ENV_FILE = Path(__file__).parent.parent.parent / ".env"  # backend/.env

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or .env file.
    Includes configuration for database connection, security, and external services.
    """
    model_config = SettingsConfigDict(
        env_file=str(_ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    PROJECT_NAME: str = "AI-Native Enterprise CPQ Platform"
    API_V1_STR: str = "/api/v1"

    # Database Settings
    # Default to an async PostgreSQL URL (asyncpg driver)
    DATABASE_URL: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/cpq_db",
        description="Async database connection string"
    )

    # JWT Authentication Settings
    # WARNING: Change this key in production environment
    SECRET_KEY: str = Field(
        default="super_secret_key_for_development_purposes_only_1234567890",
        description="Secret key used for signing JWT tokens"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Google Gemini AI Settings
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API key for AI copilot functionality"
    )

    # Salesforce Integration
    SALESFORCE_CLIENT_ID: str = ""
    SALESFORCE_CLIENT_SECRET: str = ""
    SALESFORCE_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/salesforce/callback"

settings = Settings()
