"""Pydantic schemas for request/response validation."""
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Standup Summary Schemas
# ============================================================================

class StandupEntry(BaseModel):
    """Individual standup entry from a team member."""
    name: str = Field(..., description="Team member name")
    yesterday: str = Field(..., description="What was accomplished yesterday")
    today: str = Field(..., description="What is planned for today")
    blockers: Optional[str] = Field(None, description="Any blockers or impediments")


class StandupSummaryRequest(BaseModel):
    """Request to summarize standup notes."""
    entries: List[StandupEntry] = Field(..., min_length=1, description="List of standup entries")
    sprint_goal: Optional[str] = Field(None, description="Current sprint goal for context")


class StandupSummaryResponse(BaseModel):
    """Summarized standup response."""
    summary: str = Field(..., description="AI-generated summary of the standup")
    key_blockers: List[str] = Field(default_factory=list, description="Highlighted blockers")
    action_items: List[str] = Field(default_factory=list, description="Suggested action items")
    suggested_tasks: List["SprintTask"] = Field(default_factory=list, description="Suggested tasks based on standup")
    suggested_stories: List["UserStory"] = Field(default_factory=list, description="Suggested user stories based on standup")


# ============================================================================
# User Story Schemas
# ============================================================================

class MeetingNotesRequest(BaseModel):
    """Request to generate user stories from meeting notes."""
    notes: str = Field(..., min_length=10, description="Raw meeting notes text")
    context: Optional[str] = Field(None, description="Additional context about the project")


class UserStory(BaseModel):
    """A user story in standard format."""
    title: str = Field(..., description="Brief title for the story")
    description: str = Field(..., description="As a... I want... So that... format")
    acceptance_criteria: List[str] = Field(default_factory=list, description="List of acceptance criteria")
    story_points: Optional[int] = Field(None, ge=1, le=21, description="Estimated story points")


class UserStoriesResponse(BaseModel):
    """Response containing generated user stories."""
    stories: List[UserStory] = Field(..., description="List of generated user stories")
    raw_insights: Optional[str] = Field(None, description="Additional insights from the notes")


# ============================================================================
# Sprint Task Schemas
# ============================================================================

class SprintTaskRequest(BaseModel):
    """Request to suggest sprint tasks."""
    user_stories: List[str] = Field(..., min_length=1, description="List of user story descriptions")
    team_capacity: Optional[int] = Field(None, ge=1, description="Team capacity in story points")
    sprint_duration_days: int = Field(default=14, ge=1, le=30, description="Sprint duration")


class SprintTask(BaseModel):
    """A suggested sprint task."""
    title: str = Field(..., description="Task title")
    description: str = Field(..., description="Task description")
    estimated_hours: Optional[float] = Field(None, ge=0.5, description="Estimated hours")
    priority: Literal["high", "medium", "low"] = Field(default="medium", description="Task priority")
    parent_story: Optional[str] = Field(None, description="Related user story")


class SprintTasksResponse(BaseModel):
    """Response containing suggested sprint tasks."""
    tasks: List[SprintTask] = Field(..., description="List of suggested tasks")
    total_estimated_hours: Optional[float] = Field(None, description="Total estimated hours")
    recommendations: List[str] = Field(default_factory=list, description="Sprint planning recommendations")


# ============================================================================
# Health Check Schema
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    ai_provider: str = Field(..., description="Configured AI provider")


# ============================================================================
# Jira Integration Schemas
# ============================================================================

class JiraConfigStatus(BaseModel):
    """Jira configuration status."""
    configured: bool = Field(..., description="Whether Jira is configured")
    jira_url: Optional[str] = Field(None, description="Jira instance URL")
    project_key: Optional[str] = Field(None, description="Jira project key")
    user_email: Optional[str] = Field(None, description="Connected user email")


class JiraTicketRequest(BaseModel):
    """Request to create a Jira ticket."""
    summary: str = Field(..., min_length=1, max_length=255, description="Ticket summary/title")
    description: str = Field(..., description="Ticket description")
    issue_type: Literal["Story", "Task", "Bug"] = Field(default="Task", description="Issue type")
    priority: Optional[Literal["Highest", "High", "Medium", "Low", "Lowest"]] = Field(None, description="Priority")
    labels: Optional[List[str]] = Field(default=None, description="Labels to add")
    acceptance_criteria: Optional[List[str]] = Field(default=None, description="Acceptance criteria for stories")


class JiraTicketResponse(BaseModel):
    """Response after creating a Jira ticket."""
    success: bool = Field(..., description="Whether the ticket was created")
    key: Optional[str] = Field(None, description="Jira ticket key (e.g., PROJ-123)")
    url: Optional[str] = Field(None, description="URL to the created ticket")
    summary: Optional[str] = Field(None, description="Ticket summary")
    error: Optional[str] = Field(None, description="Error message if failed")


class JiraBulkCreateRequest(BaseModel):
    """Request to create multiple Jira tickets."""
    tickets: List[JiraTicketRequest] = Field(..., min_length=1, description="List of tickets to create")


class JiraBulkCreateResponse(BaseModel):
    """Response after creating multiple Jira tickets."""
    success: bool = Field(..., description="Whether all tickets were created")
    created: List[JiraTicketResponse] = Field(default_factory=list, description="Successfully created tickets")
    failed: List[JiraTicketResponse] = Field(default_factory=list, description="Failed tickets")
    total_created: int = Field(default=0, description="Number of tickets created")
    total_failed: int = Field(default=0, description="Number of tickets that failed")
