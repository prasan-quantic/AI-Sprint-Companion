"""
Test Suite for Pydantic Schemas
===============================

This module contains comprehensive unit tests for all Pydantic schema models
used in the AI Sprint Companion application.

Test Coverage:
    - StandupEntry: Individual standup entry validation
    - StandupSummaryRequest: Standup summary request validation
    - StandupSummaryResponse: Standup summary response structure
    - MeetingNotesRequest: Meeting notes input validation
    - UserStory: User story model validation
    - UserStoriesResponse: User stories response structure
    - SprintTaskRequest: Sprint task request validation
    - SprintTask: Sprint task model validation
    - SprintTasksResponse: Sprint tasks response structure
    - HealthResponse: Health check response structure
    - JiraConfigStatus: Jira configuration status
    - JiraTicketRequest: Jira ticket creation request
    - JiraTicketResponse: Jira ticket creation response
    - JiraBulkCreateRequest: Bulk Jira ticket creation
    - JiraBulkCreateResponse: Bulk creation response

Usage:
    Run tests with: pytest tests/test_schemas.py -v

Author: AI Sprint Companion Team
"""

import pytest
from pydantic import ValidationError

from app.schemas import (
    StandupEntry,
    StandupSummaryRequest,
    StandupSummaryResponse,
    MeetingNotesRequest,
    UserStory,
    UserStoriesResponse,
    SprintTaskRequest,
    SprintTask,
    SprintTasksResponse,
    HealthResponse,
    JiraConfigStatus,
    JiraTicketRequest,
    JiraTicketResponse,
    JiraBulkCreateRequest,
    JiraBulkCreateResponse,
)


class TestStandupSchemas:
    """
    Test suite for standup-related Pydantic schemas.

    Tests validation rules, required fields, optional fields,
    and default values for standup data models.
    """

    def test_standup_entry_valid(self):
        """
        Test creating a valid StandupEntry with all fields.

        Verifies that a StandupEntry can be created with name,
        yesterday, today, and blockers fields.
        """
        entry = StandupEntry(
            name="Alice",
            yesterday="Completed API",
            today="Testing",
            blockers="None"
        )
        assert entry.name == "Alice"
        assert entry.yesterday == "Completed API"
        assert entry.today == "Testing"
        assert entry.blockers == "None"

    def test_standup_entry_optional_blockers(self):
        """
        Test StandupEntry with optional blockers field omitted.

        Verifies that blockers field defaults to None when not provided.
        """
        entry = StandupEntry(
            name="Bob",
            yesterday="Code review",
            today="Bug fixes"
        )
        assert entry.blockers is None

    def test_standup_entry_missing_required(self):
        """
        Test StandupEntry validation fails without required fields.

        Verifies that ValidationError is raised when required fields
        (yesterday, today) are missing.
        """
        with pytest.raises(ValidationError):
            StandupEntry(name="Alice")

    def test_standup_summary_request_valid(self):
        """
        Test creating a valid StandupSummaryRequest.

        Verifies that request can be created with entries list
        and optional sprint goal.
        """
        entry = StandupEntry(name="Alice", yesterday="API", today="Testing")
        request = StandupSummaryRequest(entries=[entry], sprint_goal="MVP")
        assert len(request.entries) == 1
        assert request.sprint_goal == "MVP"

    def test_standup_summary_request_empty_entries(self):
        """
        Test StandupSummaryRequest validation fails with empty entries.

        Verifies that at least one entry is required (min_length=1).
        """
        with pytest.raises(ValidationError):
            StandupSummaryRequest(entries=[])

    def test_standup_summary_response(self):
        """
        Test creating a StandupSummaryResponse with all fields.

        Verifies response structure including summary, blockers,
        action items, tasks, and stories.
        """
        response = StandupSummaryResponse(
            summary="Team is on track",
            key_blockers=["Design specs needed"],
            action_items=["Follow up with UX"],
            suggested_tasks=[],
            suggested_stories=[]
        )
        assert response.summary == "Team is on track"
        assert len(response.key_blockers) == 1

    def test_standup_summary_response_defaults(self):
        """
        Test StandupSummaryResponse with default values.

        Verifies that lists default to empty when not provided.
        """
        response = StandupSummaryResponse(summary="Summary")
        assert response.key_blockers == []
        assert response.action_items == []
        assert response.suggested_tasks == []
        assert response.suggested_stories == []


class TestUserStorySchemas:
    """
    Test suite for user story-related Pydantic schemas.

    Tests validation rules for meeting notes input and
    user story output models.
    """

    def test_meeting_notes_request_valid(self):
        """
        Test creating a valid MeetingNotesRequest.

        Verifies that notes with sufficient length and
        optional context are accepted.
        """
        request = MeetingNotesRequest(
            notes="Users need password reset functionality",
            context="Web application"
        )
        assert len(request.notes) > 10
        assert request.context == "Web application"

    def test_meeting_notes_request_min_length(self):
        """
        Test MeetingNotesRequest validation for minimum note length.

        Verifies that notes shorter than 10 characters are rejected.
        """
        with pytest.raises(ValidationError):
            MeetingNotesRequest(notes="short")

    def test_meeting_notes_request_optional_context(self):
        """
        Test MeetingNotesRequest without optional context.

        Verifies that context field defaults to None.
        """
        request = MeetingNotesRequest(notes="This is a long enough note for testing")
        assert request.context is None

    def test_user_story_valid(self):
        """
        Test creating a valid UserStory with all fields.

        Verifies story creation with title, description,
        acceptance criteria, and story points.
        """
        story = UserStory(
            title="Password Reset",
            description="As a user, I want to reset my password",
            acceptance_criteria=["Email sent", "Link works"],
            story_points=5
        )
        assert story.title == "Password Reset"
        assert story.story_points == 5

    def test_user_story_points_validation(self):
        """
        Test UserStory story points validation range.

        Verifies that story points must be between 1 and 21 (Fibonacci).
        """
        with pytest.raises(ValidationError):
            UserStory(title="Test", description="Test description", story_points=0)

        with pytest.raises(ValidationError):
            UserStory(title="Test", description="Test description", story_points=22)

    def test_user_story_defaults(self):
        """
        Test UserStory default values.

        Verifies that acceptance_criteria defaults to empty list
        and story_points defaults to None.
        """
        story = UserStory(title="Test", description="Description")
        assert story.acceptance_criteria == []
        assert story.story_points is None

    def test_user_stories_response(self):
        """
        Test UserStoriesResponse structure.

        Verifies response contains stories list and raw insights.
        """
        story = UserStory(title="Test", description="Desc")
        response = UserStoriesResponse(stories=[story], raw_insights="Some insights")
        assert len(response.stories) == 1
        assert response.raw_insights == "Some insights"


class TestSprintTaskSchemas:
    """
    Test suite for sprint task-related Pydantic schemas.

    Tests validation rules for task requests and task models.
    """

    def test_sprint_task_request_valid(self):
        """
        Test creating a valid SprintTaskRequest.

        Verifies request with user stories, team capacity,
        and sprint duration.
        """
        request = SprintTaskRequest(
            user_stories=["As a user, I want to login"],
            team_capacity=20,
            sprint_duration_days=14
        )
        assert len(request.user_stories) == 1
        assert request.team_capacity == 20
        assert request.sprint_duration_days == 14

    def test_sprint_task_request_empty_stories(self):
        """
        Test SprintTaskRequest validation fails with empty stories.

        Verifies that at least one user story is required.
        """
        with pytest.raises(ValidationError):
            SprintTaskRequest(user_stories=[])

    def test_sprint_task_request_defaults(self):
        """
        Test SprintTaskRequest default values.

        Verifies team_capacity defaults to None and
        sprint_duration_days defaults to 14.
        """
        request = SprintTaskRequest(user_stories=["Story"])
        assert request.team_capacity is None
        assert request.sprint_duration_days == 14

    def test_sprint_task_request_duration_validation(self):
        """
        Test SprintTaskRequest sprint duration validation.

        Verifies that sprint duration must be between 1 and 30 days.
        """
        with pytest.raises(ValidationError):
            SprintTaskRequest(user_stories=["Story"], sprint_duration_days=0)

        with pytest.raises(ValidationError):
            SprintTaskRequest(user_stories=["Story"], sprint_duration_days=31)

    def test_sprint_task_valid(self):
        """
        Test creating a valid SprintTask.

        Verifies task creation with all fields including
        title, description, hours, priority, and parent story.
        """
        task = SprintTask(
            title="Implement login",
            description="Create login functionality",
            estimated_hours=8,
            priority="high",
            parent_story="Login story"
        )
        assert task.title == "Implement login"
        assert task.priority == "high"

    def test_sprint_task_priority_validation(self):
        """
        Test SprintTask priority validation.

        Verifies that priority must be 'high', 'medium', or 'low'.
        """
        with pytest.raises(ValidationError):
            SprintTask(title="Test", description="Desc", priority="invalid")

    def test_sprint_task_hours_validation(self):
        """
        Test SprintTask estimated hours validation.

        Verifies that estimated hours must be at least 0.5.
        """
        with pytest.raises(ValidationError):
            SprintTask(title="Test", description="Desc", estimated_hours=0.1)

    def test_sprint_task_defaults(self):
        """
        Test SprintTask default values.

        Verifies default priority is 'medium' and other
        optional fields default to None.
        """
        task = SprintTask(title="Test", description="Desc")
        assert task.estimated_hours is None
        assert task.priority == "medium"
        assert task.parent_story is None

    def test_sprint_tasks_response(self):
        """
        Test SprintTasksResponse structure.

        Verifies response contains tasks, total hours, and recommendations.
        """
        task = SprintTask(title="Test", description="Desc")
        response = SprintTasksResponse(
            tasks=[task],
            total_estimated_hours=8.0,
            recommendations=["Plan carefully"]
        )
        assert len(response.tasks) == 1
        assert response.total_estimated_hours == 8.0


class TestHealthSchema:
    """
    Test suite for health check schema.

    Tests the HealthResponse model structure.
    """

    def test_health_response_valid(self):
        """
        Test creating a valid HealthResponse.

        Verifies response contains status, version, and ai_provider.
        """
        response = HealthResponse(
            status="healthy",
            version="1.0.0",
            ai_provider="mock"
        )
        assert response.status == "healthy"
        assert response.version == "1.0.0"
        assert response.ai_provider == "mock"


class TestJiraSchemas:
    """
    Test suite for Jira integration schemas.

    Tests validation rules for Jira configuration status,
    ticket creation requests, and responses.
    """

    def test_jira_config_status(self):
        """
        Test JiraConfigStatus when Jira is configured.

        Verifies all configuration fields are properly set.
        """
        status = JiraConfigStatus(
            configured=True,
            jira_url="https://test.atlassian.net",
            project_key="TEST",
            user_email="test@example.com"
        )
        assert status.configured is True
        assert status.project_key == "TEST"

    def test_jira_config_status_unconfigured(self):
        """
        Test JiraConfigStatus when Jira is not configured.

        Verifies optional fields can be None.
        """
        status = JiraConfigStatus(configured=False)
        assert status.configured is False
        assert status.jira_url is None

    def test_jira_ticket_request_valid(self):
        """
        Test creating a valid JiraTicketRequest.

        Verifies request with all fields including summary,
        description, issue type, priority, labels, and criteria.
        """
        request = JiraTicketRequest(
            summary="Test ticket",
            description="Test description",
            issue_type="Story",
            priority="High",
            labels=["test"],
            acceptance_criteria=["Criterion 1"]
        )
        assert request.summary == "Test ticket"
        assert request.issue_type == "Story"

    def test_jira_ticket_request_defaults(self):
        """
        Test JiraTicketRequest default values.

        Verifies default issue_type is 'Task' and
        optional fields default to None.
        """
        request = JiraTicketRequest(summary="Test", description="Desc")
        assert request.issue_type == "Task"
        assert request.priority is None
        assert request.labels is None

    def test_jira_ticket_request_summary_length(self):
        """
        Test JiraTicketRequest summary max length validation.

        Verifies summary cannot exceed 255 characters.
        """
        with pytest.raises(ValidationError):
            JiraTicketRequest(summary="x" * 256, description="Desc")

    def test_jira_ticket_request_issue_type_validation(self):
        """
        Test JiraTicketRequest issue type validation.

        Verifies issue_type must be 'Story', 'Task', or 'Bug'.
        """
        with pytest.raises(ValidationError):
            JiraTicketRequest(summary="Test", description="Desc", issue_type="Invalid")

    def test_jira_ticket_response_success(self):
        """
        Test successful JiraTicketResponse.

        Verifies response contains ticket key, URL, and summary.
        """
        response = JiraTicketResponse(
            success=True,
            key="TEST-123",
            url="https://test.atlassian.net/browse/TEST-123",
            summary="Test ticket"
        )
        assert response.success is True
        assert response.key == "TEST-123"

    def test_jira_ticket_response_failure(self):
        """
        Test failed JiraTicketResponse.

        Verifies response contains error message on failure.
        """
        response = JiraTicketResponse(success=False, error="Connection failed")
        assert response.success is False
        assert response.error == "Connection failed"

    def test_jira_bulk_create_request(self):
        """
        Test JiraBulkCreateRequest with multiple tickets.

        Verifies request can contain multiple ticket requests.
        """
        ticket = JiraTicketRequest(summary="Test", description="Desc")
        request = JiraBulkCreateRequest(tickets=[ticket])
        assert len(request.tickets) == 1

    def test_jira_bulk_create_request_empty(self):
        """
        Test JiraBulkCreateRequest validation fails when empty.

        Verifies at least one ticket is required.
        """
        with pytest.raises(ValidationError):
            JiraBulkCreateRequest(tickets=[])

    def test_jira_bulk_create_response(self):
        """
        Test JiraBulkCreateResponse structure.

        Verifies response contains created/failed lists and counts.
        """
        created = JiraTicketResponse(success=True, key="TEST-1")
        failed = JiraTicketResponse(success=False, error="Failed")

        response = JiraBulkCreateResponse(
            success=False,
            created=[created],
            failed=[failed],
            total_created=1,
            total_failed=1
        )
        assert response.total_created == 1
        assert response.total_failed == 1

