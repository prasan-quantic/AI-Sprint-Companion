"""Unit tests for AI service."""
import os
import pytest
from unittest.mock import AsyncMock, patch

# Force mock mode for tests
os.environ["AI_PROVIDER"] = "mock"

from app.ai import AIService, get_ai_service
from app.schemas import StandupEntry


class TestAIServiceMock:
    """Tests for AI service with mock responses."""

    @pytest.fixture
    def ai_service(self):
        """Create AI service instance."""
        return AIService()

    @pytest.mark.asyncio
    async def test_summarize_standup_returns_response(self, ai_service):
        """Summarize standup should return valid response."""
        entries = [
            StandupEntry(
                name="Alice",
                yesterday="Completed API",
                today="Testing",
                blockers=None
            )
        ]

        result = await ai_service.summarize_standup(entries)

        assert result.summary
        assert isinstance(result.key_blockers, list)
        assert isinstance(result.action_items, list)

    @pytest.mark.asyncio
    async def test_generate_user_stories_returns_response(self, ai_service):
        """Generate user stories should return valid response."""
        notes = "Users need password reset functionality with email verification"

        result = await ai_service.generate_user_stories(notes)

        assert result.stories
        assert len(result.stories) > 0
        assert result.stories[0].title
        assert result.stories[0].description

    @pytest.mark.asyncio
    async def test_suggest_sprint_tasks_returns_response(self, ai_service):
        """Suggest sprint tasks should return valid response."""
        stories = ["As a user, I want to login securely"]

        result = await ai_service.suggest_sprint_tasks(stories)

        assert result.tasks
        assert len(result.tasks) > 0
        assert result.tasks[0].title
        assert result.tasks[0].description


class TestAIServiceSingleton:
    """Tests for AI service singleton pattern."""

    def test_get_ai_service_returns_same_instance(self):
        """Get AI service should return singleton."""
        service1 = get_ai_service()
        service2 = get_ai_service()

        assert service1 is service2
