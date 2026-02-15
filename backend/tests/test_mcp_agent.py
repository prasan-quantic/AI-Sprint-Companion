"""
Test Suite for MCP Agent Test Module
====================================

This module contains unit tests for the MCP Agent Tester that validates
the connectivity and functionality of the MCP Server.

Test Coverage:
    - MCPAgentTester initialization
    - Logging methods (_log) with various levels
    - Test result recording (_record_test)
    - Individual test methods:
        - test_health_check
        - test_summarize_standup
        - test_generate_user_stories
        - test_suggest_sprint_tasks
        - test_jira_status
        - test_end_to_end_workflow
    - Error handling for failed tests
    - Result format validation
    - Full test suite execution (run_all_tests)

Dependencies:
    - pytest
    - pytest-asyncio
    - unittest.mock

Usage:
    Run tests with: pytest tests/test_mcp_agent.py -v

Author: AI Sprint Companion Team
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.mcp_agent_test import MCPAgentTester


class TestMCPAgentTester:
    """
    Test suite for MCPAgentTester class.

    Tests the agent tester that validates MCP server
    connectivity and tool functionality.
    """

    @pytest.fixture
    def tester(self):
        """
        Create an MCPAgentTester instance for testing.

        Returns:
            MCPAgentTester: Fresh tester instance.
        """
        return MCPAgentTester()

    def test_initialization(self, tester):
        """
        Test tester initializes with correct default values.

        Verifies client is None, test_results is empty,
        and start_time is None before initialization.
        """
        assert tester.client is None
        assert tester.test_results == []
        assert tester.start_time is None

    def test_log_info(self, tester, capsys):
        """
        Test _log method with INFO level.

        Verifies INFO messages are printed with correct format.
        """
        tester._log("Test message", "INFO")
        captured = capsys.readouterr()
        assert "Test message" in captured.out

    def test_log_success(self, tester, capsys):
        """
        Test _log method with SUCCESS level.

        Verifies SUCCESS messages include checkmark emoji.
        """
        tester._log("Success message", "SUCCESS")
        captured = capsys.readouterr()
        assert "Success message" in captured.out
        assert "✅" in captured.out

    def test_log_error(self, tester, capsys):
        """
        Test _log method with ERROR level.

        Verifies ERROR messages include X emoji.
        """
        tester._log("Error message", "ERROR")
        captured = capsys.readouterr()
        assert "Error message" in captured.out
        assert "❌" in captured.out

    def test_log_warning(self, tester, capsys):
        """
        Test _log method with WARNING level.

        Verifies WARNING messages are printed correctly.
        """
        tester._log("Warning message", "WARNING")
        captured = capsys.readouterr()
        assert "Warning message" in captured.out

    def test_log_test(self, tester, capsys):
        """
        Test _log method with TEST level.

        Verifies TEST messages include test tube emoji.
        """
        tester._log("Test message", "TEST")
        captured = capsys.readouterr()
        assert "Test message" in captured.out
        assert "🧪" in captured.out

    def test_record_test_success(self, tester):
        """
        Test _record_test with successful test.

        Verifies test result is recorded with correct
        structure and success flag.
        """
        tester._record_test("test_name", True, "Test passed", {"key": "value"})

        assert len(tester.test_results) == 1
        assert tester.test_results[0]["test"] == "test_name"
        assert tester.test_results[0]["success"] is True
        assert tester.test_results[0]["details"] == "Test passed"

    def test_record_test_failure(self, tester):
        """
        Test _record_test with failed test.

        Verifies failed tests are recorded with success=False.
        """
        tester._record_test("test_name", False, "Test failed")

        assert len(tester.test_results) == 1
        assert tester.test_results[0]["success"] is False

    @pytest.mark.asyncio
    async def test_initialize_success(self, tester):
        """
        Test successful initialization of tester.

        Verifies client is created and start_time is set.
        """
        result = await tester.initialize()

        assert result is True
        assert tester.client is not None
        assert tester.start_time is not None

    @pytest.mark.asyncio
    async def test_test_health_check(self, tester):
        """
        Test health_check test execution.

        Verifies health check test runs and records result.
        """
        await tester.initialize()
        result = await tester.test_health_check()

        assert result is True
        assert any(r["test"] == "health_check" for r in tester.test_results)

    @pytest.mark.asyncio
    async def test_test_summarize_standup(self, tester):
        """
        Test summarize_standup test execution.

        Verifies standup test runs and records result.
        """
        await tester.initialize()
        result = await tester.test_summarize_standup()

        assert result is True
        assert any(r["test"] == "summarize_standup" for r in tester.test_results)

    @pytest.mark.asyncio
    async def test_test_generate_user_stories(self, tester):
        """
        Test generate_user_stories test execution.

        Verifies story generation test runs and records result.
        """
        await tester.initialize()
        result = await tester.test_generate_user_stories()

        assert result is True
        assert any(r["test"] == "generate_user_stories" for r in tester.test_results)

    @pytest.mark.asyncio
    async def test_test_suggest_sprint_tasks(self, tester):
        """
        Test suggest_sprint_tasks test execution.

        Verifies task suggestion test runs and records result.
        """
        await tester.initialize()
        result = await tester.test_suggest_sprint_tasks()

        assert result is True
        assert any(r["test"] == "suggest_sprint_tasks" for r in tester.test_results)

    @pytest.mark.asyncio
    async def test_test_jira_status(self, tester):
        """
        Test Jira status test execution.

        Verifies Jira status test runs and records result.
        """
        await tester.initialize()
        result = await tester.test_jira_status()

        assert result is True
        assert any(r["test"] == "get_jira_status" for r in tester.test_results)

    @pytest.mark.asyncio
    async def test_test_end_to_end_workflow(self, tester):
        """
        Test end-to-end workflow test execution.

        Verifies complete workflow test runs successfully.
        """
        await tester.initialize()
        result = await tester.test_end_to_end_workflow()

        assert result is True
        assert any(r["test"] == "end_to_end_workflow" for r in tester.test_results)

    @pytest.mark.asyncio
    async def test_run_all_tests(self, tester):
        """
        Test running complete test suite.

        Verifies all tests are executed and results summarized.
        """
        results = await tester.run_all_tests()

        assert "success" in results
        assert "tests_run" in results
        assert "tests_passed" in results
        assert "tests_failed" in results
        assert "duration_seconds" in results
        assert results["tests_run"] > 0

    @pytest.mark.asyncio
    async def test_test_with_sample_file_missing(self, tester):
        """
        Test sample file test when file doesn't exist.

        Verifies graceful handling of missing sample files.
        """
        await tester.initialize()

        with patch('os.path.exists', return_value=False):
            result = await tester.test_with_sample_file()
            assert isinstance(result, bool)


class TestMCPAgentTesterErrorHandling:
    """
    Test suite for error handling in MCPAgentTester.

    Tests graceful handling of various error conditions.
    """

    @pytest.fixture
    def tester(self):
        """
        Create an MCPAgentTester instance for error testing.

        Returns:
            MCPAgentTester: Fresh tester instance.
        """
        return MCPAgentTester()

    @pytest.mark.asyncio
    async def test_health_check_exception(self, tester):
        """
        Test health check handles client exceptions.

        Verifies test fails gracefully when client raises error.
        """
        await tester.initialize()
        tester.client.health_check = AsyncMock(side_effect=Exception("Test error"))

        result = await tester.test_health_check()
        assert result is False

    @pytest.mark.asyncio
    async def test_summarize_standup_exception(self, tester):
        """
        Test summarize standup handles client exceptions.

        Verifies test fails gracefully when summarization fails.
        """
        await tester.initialize()
        tester.client.summarize_standup = AsyncMock(side_effect=Exception("Test error"))

        result = await tester.test_summarize_standup()
        assert result is False

    @pytest.mark.asyncio
    async def test_generate_stories_exception(self, tester):
        """
        Test generate stories handles client exceptions.

        Verifies test fails gracefully when story generation fails.
        """
        await tester.initialize()
        tester.client.generate_user_stories = AsyncMock(side_effect=Exception("Test error"))

        result = await tester.test_generate_user_stories()
        assert result is False

    @pytest.mark.asyncio
    async def test_suggest_tasks_exception(self, tester):
        """
        Test suggest tasks handles client exceptions.

        Verifies test fails gracefully when task suggestion fails.
        """
        await tester.initialize()
        tester.client.suggest_sprint_tasks = AsyncMock(side_effect=Exception("Test error"))

        result = await tester.test_suggest_sprint_tasks()
        assert result is False

    @pytest.mark.asyncio
    async def test_jira_status_exception(self, tester):
        """
        Test Jira status handles client exceptions.

        Verifies test fails gracefully when Jira status check fails.
        """
        await tester.initialize()
        tester.client.get_jira_status = AsyncMock(side_effect=Exception("Test error"))

        result = await tester.test_jira_status()
        assert result is False


class TestMCPAgentTesterResultFormats:
    """
    Test suite for result format validation.

    Tests handling of various response formats from client.
    """

    @pytest.fixture
    def tester(self):
        """
        Create an MCPAgentTester for format testing.

        Returns:
            MCPAgentTester: Fresh tester instance.
        """
        return MCPAgentTester()

    @pytest.mark.asyncio
    async def test_standup_missing_fields(self, tester):
        """
        Test standup result with missing required fields.

        Verifies test fails when response is incomplete.
        """
        await tester.initialize()
        tester.client.summarize_standup = AsyncMock(return_value={
            "summary": "Test summary"
        })

        result = await tester.test_summarize_standup()
        assert result is False

    @pytest.mark.asyncio
    async def test_stories_empty_result(self, tester):
        """
        Test stories with empty result list.

        Verifies test fails when no stories are generated.
        """
        await tester.initialize()
        tester.client.generate_user_stories = AsyncMock(return_value={
            "stories": [],
            "raw_insights": None
        })

        result = await tester.test_generate_user_stories()
        assert result is False

    @pytest.mark.asyncio
    async def test_tasks_empty_result(self, tester):
        """
        Test tasks with empty result list.

        Verifies test fails when no tasks are generated.
        """
        await tester.initialize()
        tester.client.suggest_sprint_tasks = AsyncMock(return_value={
            "tasks": [],
            "total_estimated_hours": 0,
            "recommendations": []
        })

        result = await tester.test_suggest_sprint_tasks()
        assert result is False

    @pytest.mark.asyncio
    async def test_jira_status_missing_configured(self, tester):
        """
        Test Jira status without configured field.

        Verifies test fails when response format is invalid.
        """
        await tester.initialize()
        tester.client.get_jira_status = AsyncMock(return_value={})

        result = await tester.test_jira_status()
        assert result is False

    @pytest.mark.asyncio
    async def test_error_in_result(self, tester):
        """
        Test handling error flag in result.

        Verifies test fails when result contains error.
        """
        await tester.initialize()
        tester.client.summarize_standup = AsyncMock(return_value={
            "error": True,
            "message": "Something went wrong"
        })

        result = await tester.test_summarize_standup()
        assert result is False

