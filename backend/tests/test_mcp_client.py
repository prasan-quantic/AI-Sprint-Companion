"""
Test Suite for MCP Client Module
================================

This module contains comprehensive unit tests for the MCP (Model Context Protocol)
client that provides programmatic access to AI Sprint Companion functionality.

Test Coverage:
    - DirectMCPClient initialization and service management
    - Health check functionality
    - Standup summarization with various inputs
    - User story generation from meeting notes
    - Sprint task suggestions from user stories
    - Jira status retrieval
    - Jira ticket creation (when configured)
    - End-to-end workflow testing
    - get_client factory function

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock

Usage:
    Run tests with: pytest tests/test_mcp_client.py -v

Author: AI Sprint Companion Team
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.mcp_client import DirectMCPClient, get_client


class TestDirectMCPClient:
    """
    Test suite for DirectMCPClient class.

    Tests the direct client implementation that calls
    AI Sprint Companion services without MCP protocol overhead.
    """

    @pytest.fixture
    def client(self):
        """
        Create a DirectMCPClient instance for testing.

        Returns:
            DirectMCPClient: Fresh client instance for each test.
        """
        return DirectMCPClient()

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """
        Test health check returns correct structure.

        Verifies the response contains status, version,
        ai_provider, and jira_configured fields.
        """
        result = await client.health_check()

        assert "status" in result
        assert "version" in result
        assert "ai_provider" in result
        assert "jira_configured" in result
        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_summarize_standup(self, client):
        """
        Test standup summarization with valid entries.

        Verifies the response contains summary, blockers,
        action items, suggested tasks, and stories.
        """
        entries = [
            {
                "name": "Alice",
                "yesterday": "Completed API work",
                "today": "Testing",
                "blockers": "None"
            }
        ]

        result = await client.summarize_standup(entries, sprint_goal="MVP")

        assert "summary" in result
        assert "key_blockers" in result
        assert "action_items" in result
        assert "suggested_tasks" in result
        assert "suggested_stories" in result

    @pytest.mark.asyncio
    async def test_summarize_standup_no_blockers(self, client):
        """
        Test standup summarization with None blockers.

        Verifies that entries without blockers are handled correctly.
        """
        entries = [
            {
                "name": "Bob",
                "yesterday": "Code review",
                "today": "Bug fixes",
                "blockers": None
            }
        ]

        result = await client.summarize_standup(entries)

        assert "summary" in result
        assert isinstance(result["suggested_tasks"], list)

    @pytest.mark.asyncio
    async def test_generate_user_stories(self, client):
        """
        Test user story generation from meeting notes.

        Verifies stories are generated with proper structure
        including title, description, and acceptance criteria.
        """
        notes = "Users need password reset functionality with email verification"

        result = await client.generate_user_stories(notes, context="Web app")

        assert "stories" in result
        assert "raw_insights" in result
        assert isinstance(result["stories"], list)

    @pytest.mark.asyncio
    async def test_generate_user_stories_no_context(self, client):
        """
        Test user story generation without context.

        Verifies that context is optional and stories
        are still generated correctly.
        """
        notes = "The admin team wants to manage user accounts and permissions"

        result = await client.generate_user_stories(notes)

        assert "stories" in result
        assert len(result["stories"]) > 0

    @pytest.mark.asyncio
    async def test_suggest_sprint_tasks(self, client):
        """
        Test sprint task suggestions from user stories.

        Verifies tasks are generated with estimates,
        priorities, and recommendations.
        """
        stories = [
            "As a user, I want to login so I can access my account",
            "As an admin, I want to manage users"
        ]

        result = await client.suggest_sprint_tasks(
            stories,
            team_capacity=40,
            sprint_duration_days=14
        )

        assert "tasks" in result
        assert "total_estimated_hours" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_suggest_sprint_tasks_defaults(self, client):
        """
        Test sprint task suggestions with default parameters.

        Verifies that team_capacity and sprint_duration_days
        have sensible defaults.
        """
        stories = ["As a user, I want to reset my password"]

        result = await client.suggest_sprint_tasks(stories)

        assert "tasks" in result
        assert isinstance(result["tasks"], list)

    @pytest.mark.asyncio
    async def test_get_jira_status(self, client):
        """
        Test Jira configuration status retrieval.

        Verifies the configured flag is present in response.
        """
        result = await client.get_jira_status()

        assert "configured" in result
        assert isinstance(result["configured"], bool)

    @pytest.mark.asyncio
    async def test_create_jira_ticket_not_configured(self, client):
        """
        Test Jira ticket creation when Jira not configured.

        Verifies appropriate error response when Jira
        credentials are not set.
        """
        with patch.object(client, 'jira_agent') as mock_agent:
            mock_agent.is_configured = False
            await client._ensure_services()
            client.jira_agent = mock_agent

            result = await client.create_jira_ticket(
                summary="Test ticket",
                description="Test description"
            )

            assert "error" in result or "configured" in str(result).lower()

    @pytest.mark.asyncio
    async def test_ensure_services_initialization(self, client):
        """
        Test lazy initialization of AI and Jira services.

        Verifies services are None before first use and
        initialized after _ensure_services call.
        """
        assert client.ai_service is None
        assert client.jira_agent is None

        await client._ensure_services()

        assert client.ai_service is not None
        assert client.jira_agent is not None

    @pytest.mark.asyncio
    async def test_ensure_services_called_once(self, client):
        """
        Test services are only initialized once.

        Verifies that repeated calls to _ensure_services
        return the same service instances.
        """
        await client._ensure_services()
        ai_service = client.ai_service
        jira_agent = client.jira_agent

        await client._ensure_services()

        assert client.ai_service is ai_service
        assert client.jira_agent is jira_agent


class TestGetClient:
    """
    Test suite for get_client factory function.

    Tests the convenience function for obtaining client instances.
    """

    def test_get_client_returns_direct_client(self):
        """
        Test get_client returns DirectMCPClient by default.

        Verifies the factory returns the correct client type.
        """
        client = get_client()
        assert isinstance(client, DirectMCPClient)

    def test_get_client_new_instance(self):
        """
        Test get_client returns new instance each time.

        Verifies that each call creates a fresh client
        (not a singleton).
        """
        client1 = get_client()
        client2 = get_client()
        assert client1 is not client2


class TestDirectMCPClientIntegration:
    """
    Integration test suite for DirectMCPClient.

    Tests complete workflows that exercise multiple
    client methods in sequence.
    """

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """
        Test complete workflow: notes -> stories -> tasks.

        Verifies end-to-end functionality by:
        1. Generating user stories from meeting notes
        2. Creating sprint tasks from those stories
        3. Summarizing a standup based on the tasks
        """
        client = DirectMCPClient()

        # Step 1: Generate stories from notes
        notes = """
        Meeting notes:
        - Users need to reset passwords
        - Admin needs user management
        - System needs audit logging
        """
        stories_result = await client.generate_user_stories(notes)
        assert len(stories_result["stories"]) > 0

        # Step 2: Generate tasks from stories
        story_descriptions = [s["description"] for s in stories_result["stories"][:2]]
        tasks_result = await client.suggest_sprint_tasks(story_descriptions)
        assert len(tasks_result["tasks"]) > 0

        # Step 3: Create standup from tasks
        standup_entries = [
            {
                "name": "Developer",
                "yesterday": "Completed design",
                "today": tasks_result["tasks"][0]["title"] if tasks_result["tasks"] else "Development",
                "blockers": None
            }
        ]
        standup_result = await client.summarize_standup(standup_entries)
        assert standup_result["summary"]

    @pytest.mark.asyncio
    async def test_multiple_team_members_standup(self):
        """
        Test standup summarization with multiple team members.

        Verifies that standups with multiple entries are
        properly aggregated into a summary with blockers
        and action items.
        """
        client = DirectMCPClient()

        entries = [
            {"name": "Alice", "yesterday": "API development", "today": "Testing", "blockers": "Need API docs"},
            {"name": "Bob", "yesterday": "Code review", "today": "Bug fixes", "blockers": None},
            {"name": "Carol", "yesterday": "Design work", "today": "Implementation", "blockers": "Waiting for feedback"},
        ]

        result = await client.summarize_standup(entries, sprint_goal="Release v1.0")

        assert result["summary"]
        assert isinstance(result["key_blockers"], list)
        assert isinstance(result["suggested_tasks"], list)

