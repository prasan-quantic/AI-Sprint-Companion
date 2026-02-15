"""Comprehensive tests for configuration module."""
import os
import pytest
from unittest.mock import patch


class TestSettings:
    """Tests for Settings class."""

    def test_default_settings(self):
        """Test default settings values."""
        # Clear cache first
        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.app_name == "AI Sprint Companion"
        assert settings.debug is False
        assert settings.ai_provider in ["openai", "azure", "mock"]
        assert settings.openai_model == "gpt-4o-mini"
        assert settings.openai_base_url == "https://api.openai.com/v1"
        assert settings.azure_openai_deployment == "gpt-4o-mini"
        assert settings.azure_openai_api_version == "2024-05-01-preview"

    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        from app.config import get_settings
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2

    def test_settings_with_env_override(self):
        """Test settings can be overridden by environment variables."""
        from app.config import get_settings
        get_settings.cache_clear()

        with patch.dict(os.environ, {"AI_PROVIDER": "mock", "DEBUG": "true"}):
            from app.config import Settings
            settings = Settings()
            assert settings.ai_provider == "mock"

    def test_jira_settings_optional(self):
        """Test that Jira settings are optional."""
        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        # These can be None
        assert settings.jira_url is None or isinstance(settings.jira_url, str)
        assert settings.jira_email is None or isinstance(settings.jira_email, str)
        assert settings.jira_api_token is None or isinstance(settings.jira_api_token, str)
        assert settings.jira_project_key is None or isinstance(settings.jira_project_key, str)

    def test_openai_settings_optional(self):
        """Test that OpenAI settings are optional."""
        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        # API key can be None
        assert settings.openai_api_key is None or isinstance(settings.openai_api_key, str)

    def test_azure_settings_optional(self):
        """Test that Azure settings are optional."""
        from app.config import get_settings
        get_settings.cache_clear()

        settings = get_settings()

        assert settings.azure_openai_endpoint is None or isinstance(settings.azure_openai_endpoint, str)
        assert settings.azure_openai_key is None or isinstance(settings.azure_openai_key, str)

