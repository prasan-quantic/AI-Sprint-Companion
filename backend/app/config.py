"""Configuration settings for AI Sprint Companion."""
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic import ConfigDict
from pydantic_settings import BaseSettings

# Find the .env file - check both backend dir and project root
BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
ENV_FILE = PROJECT_ROOT / ".env" if (PROJECT_ROOT / ".env").exists() else BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = ConfigDict(
        env_file=str(ENV_FILE),
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra fields in .env file
    )

    # Application
    app_name: str = "AI Sprint Companion"
    debug: bool = False

    # AI Provider Configuration
    ai_provider: Literal["openai", "azure", "mock"] = "mock"

    # OpenAI Configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"

    # OpenRouter Configuration (alternative)
    openrouter_api_key: Optional[str] = None

    # Azure OpenAI Configuration
    azure_openai_endpoint: Optional[str] = None
    azure_openai_key: Optional[str] = None
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-05-01-preview"

    # Jira Configuration
    jira_url: Optional[str] = None  # e.g., https://your-domain.atlassian.net
    jira_email: Optional[str] = None
    jira_api_token: Optional[str] = None
    jira_project_key: Optional[str] = None  # e.g., PROJ


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
