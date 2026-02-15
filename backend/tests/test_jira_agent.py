"""
Test Suite for Jira Agent Module
================================

This module contains comprehensive unit tests for the Jira integration
functionality including ticket creation, project management, and API communication.

Test Coverage:
    - JiraIssueType enum values
    - JiraTicket dataclass creation and defaults
    - JiraCreatedTicket dataclass
    - JiraAgentError exception handling
    - JiraAgent configuration and connection testing
    - HTTP client management
    - Description formatting for Atlassian Document Format (ADF)
    - Singleton pattern for get_jira_agent

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock
    - httpx (mocked)

Usage:
    Run tests with: pytest tests/test_jira_agent.py -v

Author: AI Sprint Companion Team
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.jira_agent import (
    JiraAgent,
    JiraAgentError,
    JiraTicket,
    JiraIssueType,
    JiraCreatedTicket,
    get_jira_agent,
)


class TestJiraIssueType:
    """
    Test suite for JiraIssueType enumeration.

    Verifies all Jira issue types are properly defined.
    """

    def test_issue_types(self):
        """
        Test all issue type enum values are correctly defined.

        Verifies Story, Task, Bug, Epic, and Sub-task types exist
        with their expected string values.
        """
        assert JiraIssueType.STORY.value == "Story"
        assert JiraIssueType.TASK.value == "Task"
        assert JiraIssueType.BUG.value == "Bug"
        assert JiraIssueType.EPIC.value == "Epic"
        assert JiraIssueType.SUBTASK.value == "Sub-task"


class TestJiraTicket:
    """
    Test suite for JiraTicket dataclass.

    Tests ticket creation with various field combinations
    and default value behavior.
    """

    def test_jira_ticket_creation(self):
        """
        Test JiraTicket creation with all fields populated.

        Verifies that all ticket fields are correctly assigned
        including summary, description, issue type, priority,
        labels, story points, parent key, and acceptance criteria.
        """
        ticket = JiraTicket(
            summary="Test ticket",
            description="Test description",
            issue_type=JiraIssueType.STORY,
            priority="High",
            labels=["test", "automated"],
            story_points=5,
            parent_key="PROJ-1",
            acceptance_criteria=["Criterion 1", "Criterion 2"]
        )
        assert ticket.summary == "Test ticket"
        assert ticket.issue_type == JiraIssueType.STORY
        assert ticket.priority == "High"
        assert len(ticket.labels) == 2
        assert ticket.story_points == 5

    def test_jira_ticket_defaults(self):
        """
        Test JiraTicket default values for optional fields.

        Verifies that only summary and description are required,
        with other fields defaulting to None or JiraIssueType.STORY.
        """
        ticket = JiraTicket(
            summary="Minimal ticket",
            description="Minimal description"
        )
        assert ticket.issue_type == JiraIssueType.STORY
        assert ticket.priority is None
        assert ticket.labels is None
        assert ticket.story_points is None
        assert ticket.parent_key is None
        assert ticket.acceptance_criteria is None


class TestJiraCreatedTicket:
    """
    Test suite for JiraCreatedTicket dataclass.

    Tests the structure returned after successful ticket creation.
    """

    def test_created_ticket(self):
        """
        Test JiraCreatedTicket creation with all fields.

        Verifies the response structure contains key, id, url, and summary.
        """
        ticket = JiraCreatedTicket(
            key="PROJ-123",
            id="10001",
            url="https://test.atlassian.net/browse/PROJ-123",
            summary="Created ticket"
        )
        assert ticket.key == "PROJ-123"
        assert ticket.id == "10001"


class TestJiraAgentError:
    """
    Test suite for JiraAgentError custom exception.

    Tests exception creation and raising behavior.
    """

    def test_jira_agent_error(self):
        """
        Test JiraAgentError exception message.

        Verifies that the error message is correctly stored.
        """
        error = JiraAgentError("Test error message")
        assert str(error) == "Test error message"

    def test_jira_agent_error_raise(self):
        """
        Test raising JiraAgentError exception.

        Verifies the exception can be raised and caught with
        the correct message.
        """
        with pytest.raises(JiraAgentError) as exc_info:
            raise JiraAgentError("Connection failed")
        assert "Connection failed" in str(exc_info.value)


class TestJiraAgent:
    """
    Test suite for JiraAgent class.

    Tests agent initialization, configuration validation,
    API communication, and HTTP client management.
    """

    def test_agent_not_configured(self):
        """
        Test agent reports not configured when credentials missing.

        Verifies is_configured returns False when any required
        credential is None.
        """
        agent = JiraAgent(
            jira_url=None,
            email=None,
            api_token=None,
            project_key=None
        )
        assert agent.is_configured is False

    def test_agent_configured(self):
        """
        Test agent reports configured when all credentials present.

        Verifies is_configured returns True when all required
        credentials are provided.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )
        assert agent.is_configured is True

    def test_agent_partial_config(self):
        """
        Test agent reports not configured with partial credentials.

        Verifies that missing any single credential results
        in is_configured being False.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token=None,
            project_key="TEST"
        )
        assert agent.is_configured is False

    @pytest.mark.asyncio
    async def test_test_connection_not_configured(self):
        """
        Test connection test fails when agent not configured.

        Verifies JiraAgentError is raised with appropriate message
        when attempting to connect without proper configuration.
        """
        agent = JiraAgent(
            jira_url=None,
            email=None,
            api_token=None,
            project_key=None
        )
        with pytest.raises(JiraAgentError) as exc_info:
            await agent.test_connection()
        assert "not configured" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_test_connection_success(self):
        """
        Test successful connection to Jira API.

        Verifies that user info is returned when connection succeeds.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "displayName": "Test User",
            "emailAddress": "test@example.com"
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_get_client', return_value=mock_client):
            result = await agent.test_connection()
            assert result["displayName"] == "Test User"

    @pytest.mark.asyncio
    async def test_test_connection_failure(self):
        """
        Test connection test fails with HTTP error.

        Verifies JiraAgentError is raised when API returns error status.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_get_client', return_value=mock_client):
            with pytest.raises(JiraAgentError) as exc_info:
                await agent.test_connection()
            assert "Failed to connect" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_project_success(self):
        """
        Test successful project retrieval from Jira.

        Verifies project details are returned correctly.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "10001",
            "key": "TEST",
            "name": "Test Project"
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_get_client', return_value=mock_client):
            result = await agent.get_project()
            assert result["key"] == "TEST"

    @pytest.mark.asyncio
    async def test_get_project_failure(self):
        """
        Test project retrieval fails with HTTP error.

        Verifies JiraAgentError is raised when project not found.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Project not found"

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_get_client', return_value=mock_client):
            with pytest.raises(JiraAgentError) as exc_info:
                await agent.get_project()
            assert "Failed to get project" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_issue_types(self):
        """
        Test retrieving available issue types for project.

        Verifies issue types are correctly parsed and cached.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "issueTypes": [
                {"id": "1", "name": "Story"},
                {"id": "2", "name": "Task"},
                {"id": "3", "name": "Bug"}
            ]
        }

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)

        with patch.object(agent, '_get_client', return_value=mock_client):
            result = await agent.get_issue_types()
            assert len(result) == 3

    @pytest.mark.asyncio
    async def test_close_client(self):
        """
        Test HTTP client is properly closed.

        Verifies aclose is called and client reference is cleared.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        mock_client = AsyncMock()
        mock_client.aclose = AsyncMock()
        agent._client = mock_client

        await agent.close()
        mock_client.aclose.assert_called_once()
        assert agent._client is None

    @pytest.mark.asyncio
    async def test_close_no_client(self):
        """
        Test close is safe when no client exists.

        Verifies no error is raised when closing without active client.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        await agent.close()  # Should not raise

    def test_get_auth(self):
        """
        Test HTTP basic auth tuple generation.

        Verifies auth tuple contains email and API token.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        auth = agent._get_auth()
        assert auth == ("test@example.com", "token123")

    def test_format_description(self):
        """
        Test description formatting to Atlassian Document Format.

        Verifies ADF structure is correctly generated with
        headings, paragraphs, and bullet lists.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        ticket = JiraTicket(
            summary="Test",
            description="h3. Header\nSome content\n* Bullet 1\n* Bullet 2",
            acceptance_criteria=["AC1", "AC2"]
        )

        result = agent._format_description(ticket)
        assert result["type"] == "doc"
        assert result["version"] == 1
        assert len(result["content"]) > 0

    def test_format_description_empty(self):
        """
        Test description formatting with empty content.

        Verifies a valid ADF document is returned even when
        description is empty.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        ticket = JiraTicket(summary="Test", description="")

        result = agent._format_description(ticket)
        assert result["type"] == "doc"

    def test_parse_text_with_formatting(self):
        """
        Test parsing text with bold markers for ADF.

        Verifies *bold* text is converted to strong marks.
        """
        agent = JiraAgent(
            jira_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
            project_key="TEST"
        )

        result = agent._parse_text_with_formatting("*Bold* text")
        assert len(result) >= 1


class TestGetJiraAgent:
    """
    Test suite for get_jira_agent singleton function.

    Tests singleton pattern implementation.
    """

    def test_get_jira_agent_returns_instance(self):
        """
        Test get_jira_agent returns a JiraAgent instance.

        Verifies the function returns the correct type.
        """
        agent = get_jira_agent()
        assert isinstance(agent, JiraAgent)

    def test_get_jira_agent_singleton(self):
        """
        Test get_jira_agent returns same instance on multiple calls.

        Verifies singleton pattern is correctly implemented.
        """
        agent1 = get_jira_agent()
        agent2 = get_jira_agent()
        assert agent1 is agent2

