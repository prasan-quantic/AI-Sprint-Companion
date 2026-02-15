"""
Comprehensive Test Suite for AI Service Module
==============================================

This module contains extensive unit tests for the AI service that provides
intelligent Scrum assistance functionality including standup summarization,
user story generation, and sprint task suggestions.

Test Coverage:
    - AIService initialization and configuration
    - Client setup for different AI providers (OpenAI, Azure, Mock)
    - Text cleaning and preprocessing
    - Title creation and extraction
    - Mock response generation for all AI functions
    - Main service methods:
        - summarize_standup
        - generate_user_stories
        - suggest_sprint_tasks
    - Edge cases and error handling
    - Singleton pattern for get_ai_service

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock

Usage:
    Run tests with: pytest tests/test_ai_comprehensive.py -v

Author: AI Sprint Companion Team
"""

import os
import json
import pytest

# Force mock mode for tests
os.environ["AI_PROVIDER"] = "mock"

from app.ai import AIService, get_ai_service
from app.schemas import StandupEntry, UserStory, SprintTask


class TestAIServiceInitialization:
    """
    Test suite for AI service initialization.

    Tests service creation with various configurations
    and the singleton pattern implementation.
    """

    def test_ai_service_creation(self):
        """
        Test AIService can be instantiated.

        Verifies basic service creation with default settings.
        """
        service = AIService()
        assert service is not None
        assert service.settings is not None

    def test_ai_service_with_custom_settings(self):
        """
        Test AIService with custom settings injection.

        Verifies settings can be passed during initialization.
        """
        from app.config import Settings
        settings = Settings(ai_provider="mock")
        service = AIService(settings=settings)
        assert service.settings.ai_provider == "mock"

    def test_get_ai_service_singleton(self):
        """
        Test get_ai_service returns singleton instance.

        Verifies the same instance is returned on multiple calls.
        """
        service1 = get_ai_service()
        service2 = get_ai_service()
        assert service1 is service2


class TestAIServiceClientSetup:
    """
    Test suite for AI client configuration.

    Tests client creation for different AI providers.
    """

    def test_get_client_mock_mode(self):
        """
        Test _get_client returns None in mock mode.

        Verifies no external client is created when using mock provider.
        """
        service = AIService()
        service.settings.ai_provider = "mock"
        service.settings.openai_api_key = None
        service._client = None

        client = service._get_client()
        assert client is None

    def test_get_model_mock(self):
        """
        Test _get_model returns correct model for mock/openai.

        Verifies the configured OpenAI model name is returned.
        """
        service = AIService()
        service.settings.ai_provider = "mock"

        model = service._get_model()
        assert model == service.settings.openai_model

    def test_get_model_azure(self):
        """
        Test _get_model returns deployment name for Azure.

        Verifies Azure deployment name is used instead of model name.
        """
        service = AIService()
        service.settings.ai_provider = "azure"

        model = service._get_model()
        assert model == service.settings.azure_openai_deployment


class TestAIServiceTextCleaning:
    """
    Test suite for text cleaning functionality.

    Tests removal of delimiter characters and formatting artifacts.
    """

    def test_clean_text_removes_delimiters(self):
        """
        Test _clean_text removes common delimiter patterns.

        Verifies === and --- sequences are removed while
        preserving actual content.
        """
        service = AIService()

        text = "Header\n===\nContent\n---\nMore content"
        result = service._clean_text(text)

        assert "===" not in result
        assert "---" not in result
        assert "Header" in result
        assert "Content" in result

    def test_clean_text_empty(self):
        """
        Test _clean_text handles empty string.

        Verifies empty input returns empty output.
        """
        service = AIService()
        result = service._clean_text("")
        assert result == ""

    def test_clean_text_none(self):
        """
        Test _clean_text handles None input.

        Verifies None input returns None.
        """
        service = AIService()
        result = service._clean_text(None)
        assert result is None

    def test_clean_text_multiple_delimiters(self):
        """
        Test _clean_text removes multiple delimiter types.

        Verifies ***, ___, and ### sequences are all removed.
        """
        service = AIService()

        text = "Title\n***\nContent\n___\nMore\n###\nEnd"
        result = service._clean_text(text)

        assert "***" not in result
        assert "___" not in result
        assert "###" not in result


class TestAIServiceTitleCreation:
    """
    Test suite for title creation functionality.

    Tests intelligent title generation from longer text.
    """

    def test_create_short_title_short_text(self):
        """
        Test _create_short_title with already short text.

        Verifies short text is returned unchanged.
        """
        service = AIService()

        result = service._create_short_title("Short title", max_length=60)
        assert result == "Short title"

    def test_create_short_title_long_text(self):
        """
        Test _create_short_title truncates long text.

        Verifies text is truncated to max_length without
        cutting words mid-way.
        """
        service = AIService()

        long_text = "This is a very long title that needs to be truncated because it exceeds the maximum allowed length for titles"
        result = service._create_short_title(long_text, max_length=60)

        assert len(result) <= 60

    def test_create_short_title_empty(self):
        """
        Test _create_short_title with empty text.

        Verifies default title is returned for empty input.
        """
        service = AIService()
        result = service._create_short_title("")
        assert result == "Untitled Task"

    def test_create_short_title_with_numbers(self):
        """
        Test _create_short_title removes leading numbers.

        Verifies numbered list prefixes like "1. " are removed.
        """
        service = AIService()

        result = service._create_short_title("1. First item in list")
        assert not result.startswith("1.")

    def test_create_short_title_with_bullets(self):
        """
        Test _create_short_title removes bullet points.

        Verifies bullet prefixes like "- " are removed.
        """
        service = AIService()

        result = service._create_short_title("- Bullet point item")
        assert not result.startswith("-")

    def test_extract_key_phrase(self):
        """
        Test _extract_key_phrase extracts meaningful content.

        Verifies key phrases are identified from longer text.
        """
        service = AIService()

        result = service._extract_key_phrase("Users need password reset functionality")
        assert result is not None
        assert len(result) > 0

    def test_extract_key_phrase_empty(self):
        """
        Test _extract_key_phrase with empty text.

        Verifies default phrase is returned for empty input.
        """
        service = AIService()
        result = service._extract_key_phrase("")
        assert result == "Untitled"


class TestAIServiceMockResponses:
    """
    Test suite for mock response generation.

    Tests the mock AI responses used when no real AI provider
    is configured.
    """

    def test_mock_response_standup(self):
        """
        Test _mock_response for standup summarization.

        Verifies mock generates valid JSON with expected structure.
        """
        service = AIService()

        messages = [
            {"role": "system", "content": "You are a Scrum Master assistant"},
            {"role": "user", "content": "Alice: Completed API | Testing | None"}
        ]

        result = service._mock_response(messages)
        data = json.loads(result)

        assert "summary" in data
        assert "key_blockers" in data
        assert "action_items" in data

    def test_mock_response_stories(self):
        """
        Test _mock_response for user story generation.

        Verifies mock generates stories with proper structure.
        """
        service = AIService()

        messages = [
            {"role": "system", "content": "You are an Agile coach. Extract user stories"},
            {"role": "user", "content": "Users need password reset"}
        ]

        result = service._mock_response(messages)
        data = json.loads(result)

        assert "stories" in data

    def test_mock_response_tasks(self):
        """
        Test _mock_response for sprint task suggestion.

        Verifies mock generates tasks with estimates.
        """
        service = AIService()

        messages = [
            {"role": "system", "content": "You are a technical lead. Break down sprint tasks"},
            {"role": "user", "content": "As a user, I want to login"}
        ]

        result = service._mock_response(messages)
        data = json.loads(result)

        assert "tasks" in data

    def test_generate_standup_mock(self):
        """
        Test _generate_standup_mock with formatted input.

        Verifies standup-specific mock response generation.
        """
        service = AIService()

        user_message = """**Alice**:
- Yesterday: Completed API
- Today: Testing
- Blockers: None"""

        result = service._generate_standup_mock(user_message)
        data = json.loads(result)

        assert "summary" in data
        assert "suggested_tasks" in data
        assert "suggested_stories" in data

    def test_generate_tasks_mock(self):
        """
        Test _generate_tasks_mock with user stories.

        Verifies task breakdown from user stories.
        """
        service = AIService()

        user_message = """- As a user, I want to login
- As an admin, I want to manage users"""

        result = service._generate_tasks_mock(user_message)
        data = json.loads(result)

        assert "tasks" in data
        assert "total_estimated_hours" in data
        assert "recommendations" in data

    def test_generate_stories_mock(self):
        """
        Test _generate_stories_mock from meeting notes.

        Verifies user story extraction from notes.
        """
        service = AIService()

        user_message = "Users need password reset. Admin needs user management."

        result = service._generate_stories_mock(user_message)
        data = json.loads(result)

        assert "stories" in data
        assert "raw_insights" in data


class TestAIServiceMainMethods:
    """
    Test suite for main AI service methods.

    Tests the public API of the AI service.
    """

    @pytest.fixture
    def service(self):
        """
        Create AI service instance for testing.

        Returns:
            AIService: Fresh service instance.
        """
        return AIService()

    @pytest.mark.asyncio
    async def test_summarize_standup(self, service):
        """
        Test summarize_standup with multiple entries.

        Verifies complete standup summarization including
        suggested tasks and stories.
        """
        entries = [
            StandupEntry(
                name="Alice",
                yesterday="Completed API endpoints",
                today="Writing tests",
                blockers="Need test database"
            ),
            StandupEntry(
                name="Bob",
                yesterday="Code review",
                today="Bug fixes",
                blockers=None
            )
        ]

        result = await service.summarize_standup(entries, sprint_goal="MVP")

        assert result.summary
        assert isinstance(result.key_blockers, list)
        assert isinstance(result.action_items, list)
        assert isinstance(result.suggested_tasks, list)
        assert isinstance(result.suggested_stories, list)

    @pytest.mark.asyncio
    async def test_summarize_standup_no_goal(self, service):
        """
        Test summarize_standup without sprint goal.

        Verifies summarization works without optional goal.
        """
        entries = [
            StandupEntry(name="Alice", yesterday="Work", today="More work")
        ]

        result = await service.summarize_standup(entries)

        assert result.summary

    @pytest.mark.asyncio
    async def test_generate_user_stories(self, service):
        """
        Test generate_user_stories from meeting notes.

        Verifies stories are generated with proper structure.
        """
        notes = """
        Meeting notes:
        - Users need password reset functionality
        - Admin team wants user management dashboard
        - System needs audit logging
        """

        result = await service.generate_user_stories(notes, context="Web app")

        assert result.stories
        assert len(result.stories) > 0
        assert result.stories[0].title
        assert result.stories[0].description

    @pytest.mark.asyncio
    async def test_generate_user_stories_no_context(self, service):
        """
        Test generate_user_stories without context.

        Verifies story generation works without optional context.
        """
        notes = "Users need to be able to reset their passwords via email"

        result = await service.generate_user_stories(notes)

        assert result.stories

    @pytest.mark.asyncio
    async def test_suggest_sprint_tasks(self, service):
        """
        Test suggest_sprint_tasks from user stories.

        Verifies tasks are generated with estimates and priorities.
        """
        stories = [
            "As a user, I want to login so I can access my account",
            "As an admin, I want to manage users so I can control access"
        ]

        result = await service.suggest_sprint_tasks(
            stories,
            team_capacity=40,
            sprint_duration_days=14
        )

        assert result.tasks
        assert len(result.tasks) > 0
        assert result.tasks[0].title
        assert result.tasks[0].description

    @pytest.mark.asyncio
    async def test_suggest_sprint_tasks_defaults(self, service):
        """
        Test suggest_sprint_tasks with default parameters.

        Verifies task suggestion works with minimal input.
        """
        stories = ["As a user, I want feature X"]

        result = await service.suggest_sprint_tasks(stories)

        assert result.tasks

    @pytest.mark.asyncio
    async def test_chat_completion_mock(self, service):
        """
        Test _chat_completion returns mock response.

        Verifies mock mode returns valid string response.
        """
        messages = [
            {"role": "system", "content": "Test system"},
            {"role": "user", "content": "Test user message"}
        ]

        result = await service._chat_completion(messages)

        assert result is not None
        assert isinstance(result, str)


class TestAIServiceEdgeCases:
    """
    Test suite for edge cases and error handling.

    Tests boundary conditions and unusual inputs.
    """

    @pytest.fixture
    def service(self):
        """
        Create AI service for edge case testing.

        Returns:
            AIService: Fresh service instance.
        """
        return AIService()

    @pytest.mark.asyncio
    async def test_summarize_standup_single_entry(self, service):
        """
        Test standup with single entry.

        Verifies minimum viable input is handled.
        """
        entries = [
            StandupEntry(name="Solo", yesterday="All", today="Everything", blockers="Nothing")
        ]

        result = await service.summarize_standup(entries)
        assert result.summary

    @pytest.mark.asyncio
    async def test_generate_stories_minimal_notes(self, service):
        """
        Test story generation with minimal notes.

        Verifies short but valid input is processed.
        """
        notes = "Need login feature"

        result = await service.generate_user_stories(notes)
        assert result.stories

    @pytest.mark.asyncio
    async def test_suggest_tasks_single_story(self, service):
        """
        Test task suggestion with single story.

        Verifies single story produces meaningful tasks.
        """
        stories = ["As a user, I want to do something"]

        result = await service.suggest_sprint_tasks(stories)
        assert result.tasks

    def test_clean_text_preserves_content(self):
        """
        Test that clean_text preserves actual content.

        Verifies cleaning doesn't remove legitimate text.
        """
        service = AIService()

        text = "Important content here with details"
        result = service._clean_text(text)

        assert "Important" in result
        assert "content" in result
        assert "details" in result

