"""
Test Suite for MCP Server Module
================================

This module contains comprehensive unit tests for the MCP (Model Context Protocol)
server that exposes AI Sprint Companion functionality to AI agents.

Test Coverage:
    - MCPSprintCompanionServer initialization
    - Tool execution for all available tools:
        - health_check
        - summarize_standup
        - generate_user_stories
        - suggest_sprint_tasks
        - get_jira_status
        - parse_standup_text
    - Error handling for invalid inputs
    - Singleton pattern for get_mcp_server
    - Jira integration status checking

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock

Usage:
    Run tests with: pytest tests/test_mcp_server.py -v

Author: AI Sprint Companion Team
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.mcp_server import MCPSprintCompanionServer, get_mcp_server


class TestMCPSprintCompanionServer:
    """
    Test suite for MCPSprintCompanionServer class.

    Tests the MCP server implementation including tool
    registration, execution, and error handling.
    """

    @pytest.fixture
    def server(self):
        """
        Create a server instance for testing.

        Returns:
            MCPSprintCompanionServer: Fresh server instance.
        """
        return MCPSprintCompanionServer()

    def test_server_initialization(self, server):
        """
        Test server initializes with None services.

        Verifies lazy initialization pattern where services
        are not created until first use.
        """
        assert server.ai_service is None
        assert server.jira_agent is None

    @pytest.mark.asyncio
    async def test_execute_tool_health_check(self, server):
        """
        Test executing health_check tool.

        Verifies health check returns status, version,
        and AI provider information.
        """
        result = await server._execute_tool("health_check", {})

        assert "status" in result
        assert result["status"] == "healthy"
        assert "version" in result
        assert "ai_provider" in result

    @pytest.mark.asyncio
    async def test_execute_tool_summarize_standup(self, server):
        """
        Test executing summarize_standup tool.

        Verifies standup entries are processed and
        summary with suggestions is returned.
        """
        arguments = {
            "entries": [
                {
                    "name": "Alice",
                    "yesterday": "Completed API",
                    "today": "Testing",
                    "blockers": None
                }
            ],
            "sprint_goal": "MVP release"
        }

        result = await server._execute_tool("summarize_standup", arguments)

        assert "summary" in result
        assert "key_blockers" in result
        assert "action_items" in result
        assert "suggested_tasks" in result
        assert "suggested_stories" in result

    @pytest.mark.asyncio
    async def test_execute_tool_summarize_standup_empty(self, server):
        """
        Test summarize_standup with empty entries returns error.

        Verifies appropriate error response when no entries provided.
        """
        arguments = {"entries": []}

        result = await server._execute_tool("summarize_standup", arguments)

        assert "error" in result
        assert result["error"] is True

    @pytest.mark.asyncio
    async def test_execute_tool_generate_user_stories(self, server):
        """
        Test executing generate_user_stories tool.

        Verifies meeting notes are processed into user stories.
        """
        arguments = {
            "notes": "Users need password reset functionality with email verification",
            "context": "Web application"
        }

        result = await server._execute_tool("generate_user_stories", arguments)

        assert "stories" in result
        assert "raw_insights" in result

    @pytest.mark.asyncio
    async def test_execute_tool_generate_user_stories_short_notes(self, server):
        """
        Test generate_user_stories with insufficient notes.

        Verifies error response when notes are too short.
        """
        arguments = {"notes": "short"}

        result = await server._execute_tool("generate_user_stories", arguments)

        assert "error" in result
        assert result["error"] is True

    @pytest.mark.asyncio
    async def test_execute_tool_suggest_sprint_tasks(self, server):
        """
        Test executing suggest_sprint_tasks tool.

        Verifies user stories are broken down into tasks
        with estimates and recommendations.
        """
        arguments = {
            "user_stories": [
                "As a user, I want to login",
                "As an admin, I want to manage users"
            ],
            "team_capacity": 40,
            "sprint_duration_days": 14
        }

        result = await server._execute_tool("suggest_sprint_tasks", arguments)

        assert "tasks" in result
        assert "total_estimated_hours" in result
        assert "recommendations" in result

    @pytest.mark.asyncio
    async def test_execute_tool_suggest_sprint_tasks_empty(self, server):
        """
        Test suggest_sprint_tasks with empty stories returns error.

        Verifies appropriate error when no user stories provided.
        """
        arguments = {"user_stories": []}

        result = await server._execute_tool("suggest_sprint_tasks", arguments)

        assert "error" in result
        assert result["error"] is True

    @pytest.mark.asyncio
    async def test_execute_tool_get_jira_status(self, server):
        """
        Test executing get_jira_status tool.

        Verifies Jira configuration status is returned.
        """
        result = await server._execute_tool("get_jira_status", {})

        assert "configured" in result

    @pytest.mark.asyncio
    async def test_execute_tool_parse_standup_text(self, server):
        """
        Test executing parse_standup_text tool.

        Verifies raw text is parsed into structured entries.
        """
        arguments = {
            "text": "Alice: Completed API | Testing today | No blockers\nBob: Code review | Bug fixes | Waiting for specs"
        }

        result = await server._execute_tool("parse_standup_text", arguments)

        assert "entries" in result
        assert "count" in result
        assert result["count"] == 2
        assert len(result["entries"]) == 2

    @pytest.mark.asyncio
    async def test_execute_tool_parse_standup_text_empty(self, server):
        """
        Test parse_standup_text with empty text.

        Verifies empty input returns empty entries list.
        """
        arguments = {"text": ""}

        result = await server._execute_tool("parse_standup_text", arguments)

        assert result["count"] == 0
        assert result["entries"] == []

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self, server):
        """
        Test executing unknown tool raises ValueError.

        Verifies appropriate error for unregistered tools.
        """
        with pytest.raises(ValueError) as exc_info:
            await server._execute_tool("unknown_tool", {})

        assert "Unknown tool" in str(exc_info.value)

    def test_parse_standup_text_various_formats(self, server):
        """
        Test parsing standup text with standard format.

        Verifies name, yesterday, today, and blockers
        are correctly extracted from pipe-separated format.
        """
        result = server._parse_standup_text({
            "text": "Alice: yesterday task | today task | blocker"
        })
        assert result["count"] == 1
        assert result["entries"][0]["name"] == "Alice"
        assert result["entries"][0]["yesterday"] == "yesterday task"
        assert result["entries"][0]["today"] == "today task"
        assert result["entries"][0]["blockers"] == "blocker"

    def test_parse_standup_text_no_pipe(self, server):
        """
        Test parsing standup without pipe separators.

        Verifies graceful handling when only name and
        single field are provided.
        """
        result = server._parse_standup_text({
            "text": "Alice: just one field"
        })
        assert result["count"] == 1
        assert result["entries"][0]["yesterday"] == "just one field"

    def test_health_check_method(self, server):
        """
        Test _health_check method directly.

        Verifies internal health check implementation.
        """
        result = server._health_check()

        assert result["status"] == "healthy"
        assert "version" in result
        assert "ai_provider" in result

    @pytest.mark.asyncio
    async def test_summarize_standup_method(self, server):
        """
        Test _summarize_standup method directly.

        Verifies internal standup summarization implementation.
        """
        arguments = {
            "entries": [
                {"name": "Test", "yesterday": "Work", "today": "More work", "blockers": None}
            ],
            "sprint_goal": "Goal"
        }

        result = await server._summarize_standup(arguments)

        assert "summary" in result

    @pytest.mark.asyncio
    async def test_generate_user_stories_method(self, server):
        """
        Test _generate_user_stories method directly.

        Verifies internal story generation implementation.
        """
        arguments = {
            "notes": "This is a detailed meeting note with requirements",
            "context": "Test context"
        }

        result = await server._generate_user_stories(arguments)

        assert "stories" in result

    @pytest.mark.asyncio
    async def test_suggest_sprint_tasks_method(self, server):
        """
        Test _suggest_sprint_tasks method directly.

        Verifies internal task suggestion implementation.
        """
        arguments = {
            "user_stories": ["As a user, I want feature X"],
            "team_capacity": 20,
            "sprint_duration_days": 7
        }

        result = await server._suggest_sprint_tasks(arguments)

        assert "tasks" in result


class TestGetMCPServer:
    """
    Test suite for get_mcp_server singleton function.

    Tests the singleton pattern implementation for server instances.
    """

    def test_get_mcp_server_returns_instance(self):
        """
        Test get_mcp_server returns MCPSprintCompanionServer.

        Verifies the factory returns correct type.
        """
        server = get_mcp_server()
        assert isinstance(server, MCPSprintCompanionServer)

    def test_get_mcp_server_singleton(self):
        """
        Test get_mcp_server returns same instance.

        Verifies singleton pattern is correctly implemented.
        """
        import app.mcp_server
        app.mcp_server._mcp_server = None

        server1 = get_mcp_server()
        server2 = get_mcp_server()
        assert server1 is server2


class TestMCPServerJiraIntegration:
    """
    Test suite for MCP server Jira integration.

    Tests Jira-related tool execution and error handling.
    """

    @pytest.fixture
    def server(self):
        """
        Create a server instance for Jira testing.

        Returns:
            MCPSprintCompanionServer: Fresh server instance.
        """
        return MCPSprintCompanionServer()

    @pytest.mark.asyncio
    async def test_create_jira_ticket_not_configured(self, server):
        """
        Test create_jira_ticket when Jira not configured.

        Verifies appropriate error response when Jira
        credentials are not set.
        """
        await server._execute_tool("health_check", {})

        if server.jira_agent and not server.jira_agent.is_configured:
            result = await server._create_jira_ticket({
                "summary": "Test",
                "description": "Test description"
            })

            assert "error" in result or "message" in result

    @pytest.mark.asyncio
    async def test_get_jira_status_method(self, server):
        """
        Test _get_jira_status method directly.

        Verifies internal Jira status check implementation.
        """
        result = await server._get_jira_status()

        assert "configured" in result
        assert isinstance(result["configured"], bool)

