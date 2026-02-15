"""Jira Integration Agent for AI Sprint Companion.

This module provides functionality to create Jira tickets from AI-generated
user stories, tasks, and standup action items.

To use this integration:
1. Create a free Jira Cloud account at https://www.atlassian.com/software/jira/free
2. Generate an API token at https://id.atlassian.com/manage-profile/security/api-tokens
3. Set the environment variables:
   - JIRA_URL: Your Jira instance URL (e.g., https://your-domain.atlassian.net)
   - JIRA_EMAIL: Your Jira account email
   - JIRA_API_TOKEN: Your Jira API token
   - JIRA_PROJECT_KEY: The project key where tickets will be created (e.g., PROJ)
"""

import json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import httpx

from .config import get_settings


class JiraIssueType(str, Enum):
    """Jira issue types."""
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    EPIC = "Epic"
    SUBTASK = "Sub-task"


@dataclass
class JiraTicket:
    """Represents a Jira ticket to be created."""
    summary: str
    description: str
    issue_type: JiraIssueType = JiraIssueType.STORY
    priority: Optional[str] = None  # Highest, High, Medium, Low, Lowest
    labels: Optional[List[str]] = None
    story_points: Optional[int] = None
    parent_key: Optional[str] = None  # For subtasks
    acceptance_criteria: Optional[List[str]] = None


@dataclass
class JiraCreatedTicket:
    """Represents a successfully created Jira ticket."""
    key: str
    id: str
    url: str
    summary: str


class JiraAgentError(Exception):
    """Custom exception for Jira agent errors."""
    pass


class JiraAgent:
    """Agent for interacting with Jira API."""

    def __init__(
        self,
        jira_url: Optional[str] = None,
        email: Optional[str] = None,
        api_token: Optional[str] = None,
        project_key: Optional[str] = None,
    ):
        """Initialize Jira agent with credentials."""
        settings = get_settings()

        self.jira_url = (jira_url or getattr(settings, 'jira_url', None) or "").rstrip('/')
        self.email = email or getattr(settings, 'jira_email', None)
        self.api_token = api_token or getattr(settings, 'jira_api_token', None)
        self.project_key = project_key or getattr(settings, 'jira_project_key', None)

        self._client: Optional[httpx.AsyncClient] = None
        self._project_id: Optional[str] = None
        self._issue_types: Dict[str, str] = {}

    @property
    def is_configured(self) -> bool:
        """Check if Jira is properly configured."""
        return all([self.jira_url, self.email, self.api_token, self.project_key])

    def _get_auth(self) -> tuple:
        """Get HTTP Basic Auth tuple."""
        return (self.email, self.api_token)

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=f"{self.jira_url}/rest/api/3",
                auth=self._get_auth(),
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Jira and return user info."""
        if not self.is_configured:
            raise JiraAgentError(
                "Jira is not configured. Please set JIRA_URL, JIRA_EMAIL, "
                "JIRA_API_TOKEN, and JIRA_PROJECT_KEY environment variables."
            )

        client = await self._get_client()
        response = await client.get("/myself")

        if response.status_code != 200:
            raise JiraAgentError(f"Failed to connect to Jira: {response.text}")

        return response.json()

    async def get_project(self) -> Dict[str, Any]:
        """Get project details."""
        client = await self._get_client()
        response = await client.get(f"/project/{self.project_key}")

        if response.status_code != 200:
            raise JiraAgentError(f"Failed to get project: {response.text}")

        project = response.json()
        self._project_id = project.get("id")
        return project

    async def get_issue_types(self) -> List[Dict[str, Any]]:
        """Get available issue types for the project."""
        client = await self._get_client()
        response = await client.get(f"/project/{self.project_key}")

        if response.status_code != 200:
            raise JiraAgentError(f"Failed to get issue types: {response.text}")

        project = response.json()
        issue_types = project.get("issueTypes", [])

        # Cache issue type IDs
        for it in issue_types:
            self._issue_types[it["name"]] = it["id"]

        return issue_types

    async def _get_issue_type_id(self, issue_type: JiraIssueType) -> str:
        """Get issue type ID by name."""
        if not self._issue_types:
            await self.get_issue_types()

        # Try exact match first
        if issue_type.value in self._issue_types:
            return self._issue_types[issue_type.value]

        # Try case-insensitive match
        for name, id_ in self._issue_types.items():
            if name.lower() == issue_type.value.lower():
                return id_

        # Default to Task if Story not found
        if "Task" in self._issue_types:
            return self._issue_types["Task"]

        # Return first available type
        if self._issue_types:
            return list(self._issue_types.values())[0]

        raise JiraAgentError(f"Issue type '{issue_type.value}' not found in project")

    def _format_description(self, ticket: JiraTicket) -> Dict[str, Any]:
        """Format description in Atlassian Document Format (ADF)."""
        content = []

        # Add main description
        if ticket.description:
            # Split description by newlines and create paragraphs
            paragraphs = ticket.description.strip().split('\n')
            for para in paragraphs:
                para = para.strip()
                if para:
                    # Check if it's a heading (starts with h3. or similar)
                    if para.startswith('h3. '):
                        content.append({
                            "type": "heading",
                            "attrs": {"level": 3},
                            "content": [{"type": "text", "text": para[4:]}]
                        })
                    elif para.startswith('h2. '):
                        content.append({
                            "type": "heading",
                            "attrs": {"level": 2},
                            "content": [{"type": "text", "text": para[4:]}]
                        })
                    elif para.startswith('* '):
                        # Start collecting bullet points
                        # This is handled separately below
                        pass
                    elif para.startswith('----'):
                        # Horizontal rule
                        content.append({"type": "rule"})
                    elif para.startswith('_') and para.endswith('_'):
                        # Italic text
                        content.append({
                            "type": "paragraph",
                            "content": [{
                                "type": "text",
                                "text": para[1:-1],
                                "marks": [{"type": "em"}]
                            }]
                        })
                    else:
                        # Check for bold markers *text*
                        if para.startswith('*') and '*' in para[1:]:
                            # Handle bold text like *Story Points:* 5
                            content.append({
                                "type": "paragraph",
                                "content": self._parse_text_with_formatting(para)
                            })
                        else:
                            content.append({
                                "type": "paragraph",
                                "content": [{"type": "text", "text": para}]
                            })

            # Now handle bullet lists - collect consecutive bullet points
            self._add_bullet_lists(content, ticket.description)

        # Add acceptance criteria if present (from ticket object, not description)
        if ticket.acceptance_criteria:
            content.append({
                "type": "heading",
                "attrs": {"level": 3},
                "content": [{"type": "text", "text": "Acceptance Criteria"}]
            })

            list_items = []
            for criteria in ticket.acceptance_criteria:
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": [{"type": "text", "text": criteria}]
                    }]
                })

            content.append({
                "type": "bulletList",
                "content": list_items
            })

        return {
            "type": "doc",
            "version": 1,
            "content": content if content else [{"type": "paragraph", "content": [{"type": "text", "text": "No description provided."}]}]
        }

    def _parse_text_with_formatting(self, text: str) -> List[Dict[str, Any]]:
        """Parse text with *bold* markers into ADF format."""
        result = []
        parts = text.split('*')
        is_bold = False

        for i, part in enumerate(parts):
            if part:
                if is_bold:
                    result.append({
                        "type": "text",
                        "text": part,
                        "marks": [{"type": "strong"}]
                    })
                else:
                    result.append({"type": "text", "text": part})
            is_bold = not is_bold

        return result if result else [{"type": "text", "text": text}]

    def _add_bullet_lists(self, content: List[Dict], description: str):
        """Extract bullet lists from description and add them to content."""
        lines = description.strip().split('\n')
        i = 0
        insert_positions = []

        while i < len(lines):
            line = lines[i].strip()
            if line.startswith('* '):
                # Found start of a bullet list
                list_items = []
                while i < len(lines) and lines[i].strip().startswith('* '):
                    item_text = lines[i].strip()[2:]  # Remove '* '
                    list_items.append({
                        "type": "listItem",
                        "content": [{
                            "type": "paragraph",
                            "content": [{"type": "text", "text": item_text}]
                        }]
                    })
                    i += 1

                # Find the right position to insert (after the heading before the list)
                insert_positions.append({
                    "type": "bulletList",
                    "content": list_items
                })
            else:
                i += 1

        # Remove any plain text bullet items that were added as paragraphs and add the lists
        # Filter out paragraphs that start with "* "
        filtered_content = [item for item in content if not (
            item.get("type") == "paragraph" and
            item.get("content") and
            item["content"][0].get("text", "").startswith("* ")
        )]
        content.clear()
        content.extend(filtered_content)

        # Add bullet lists at appropriate positions (after headings)
        for bullet_list in insert_positions:
            content.append(bullet_list)

    async def create_ticket(self, ticket: JiraTicket) -> JiraCreatedTicket:
        """Create a single Jira ticket."""
        if not self.is_configured:
            raise JiraAgentError("Jira is not configured")

        client = await self._get_client()
        issue_type_id = await self._get_issue_type_id(ticket.issue_type)

        # Build the issue payload
        fields = {
            "project": {"key": self.project_key},
            "summary": ticket.summary[:255],  # Jira summary limit
            "description": self._format_description(ticket),
            "issuetype": {"id": issue_type_id},
        }

        # Add optional fields
        if ticket.labels:
            fields["labels"] = ticket.labels

        if ticket.priority:
            fields["priority"] = {"name": ticket.priority}

        if ticket.parent_key and ticket.issue_type == JiraIssueType.SUBTASK:
            fields["parent"] = {"key": ticket.parent_key}

        # Note: Story points field name varies by Jira instance
        # Common names: "Story Points", "customfield_10016", etc.

        payload = {"fields": fields}

        response = await client.post("/issue", json=payload)

        if response.status_code not in (200, 201):
            error_msg = response.text
            try:
                error_data = response.json()
                if "errors" in error_data:
                    error_msg = json.dumps(error_data["errors"])
                elif "errorMessages" in error_data:
                    error_msg = ", ".join(error_data["errorMessages"])
            except:
                pass
            raise JiraAgentError(f"Failed to create ticket: {error_msg}")

        result = response.json()
        return JiraCreatedTicket(
            key=result["key"],
            id=result["id"],
            url=f"{self.jira_url}/browse/{result['key']}",
            summary=ticket.summary,
        )

    async def create_tickets_batch(
        self, tickets: List[JiraTicket]
    ) -> List[JiraCreatedTicket]:
        """Create multiple Jira tickets."""
        created = []
        errors = []

        for ticket in tickets:
            try:
                result = await self.create_ticket(ticket)
                created.append(result)
            except JiraAgentError as e:
                errors.append(f"{ticket.summary}: {str(e)}")

        if errors and not created:
            raise JiraAgentError(f"All tickets failed to create: {'; '.join(errors)}")

        return created

    async def create_story_with_tasks(
        self,
        story: JiraTicket,
        tasks: List[JiraTicket],
    ) -> Dict[str, Any]:
        """Create a user story and its sub-tasks."""
        # Create the story first
        created_story = await self.create_ticket(story)

        # Create tasks as sub-tasks of the story
        created_tasks = []
        for task in tasks:
            task.issue_type = JiraIssueType.SUBTASK
            task.parent_key = created_story.key
            try:
                created_task = await self.create_ticket(task)
                created_tasks.append(created_task)
            except JiraAgentError:
                # If subtasks fail, try creating as regular tasks
                task.issue_type = JiraIssueType.TASK
                task.parent_key = None
                task.summary = f"[{created_story.key}] {task.summary}"
                created_task = await self.create_ticket(task)
                created_tasks.append(created_task)

        return {
            "story": created_story,
            "tasks": created_tasks,
        }


# Helper functions for converting AI outputs to Jira tickets

def user_story_to_jira_ticket(
    title: str,
    description: str,
    acceptance_criteria: List[str] = None,
    story_points: int = None,
    labels: List[str] = None,
) -> JiraTicket:
    """Convert an AI-generated user story to a Jira ticket."""
    return JiraTicket(
        summary=title,
        description=description,
        issue_type=JiraIssueType.STORY,
        acceptance_criteria=acceptance_criteria or [],
        story_points=story_points,
        labels=labels or ["ai-generated"],
    )


def sprint_task_to_jira_ticket(
    title: str,
    description: str,
    priority: str = "Medium",
    estimated_hours: float = None,
    labels: List[str] = None,
) -> JiraTicket:
    """Convert an AI-generated sprint task to a Jira ticket."""
    desc = description
    if estimated_hours:
        desc = f"{description}\n\nEstimated: {estimated_hours} hours"

    # Map priority
    priority_map = {
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    }
    jira_priority = priority_map.get(priority.lower(), "Medium")

    return JiraTicket(
        summary=title,
        description=desc,
        issue_type=JiraIssueType.TASK,
        priority=jira_priority,
        labels=labels or ["ai-generated"],
    )


def action_item_to_jira_ticket(
    action_item: str,
    context: str = None,
    labels: List[str] = None,
) -> JiraTicket:
    """Convert a standup action item to a Jira ticket."""
    desc = action_item
    if context:
        desc = f"{action_item}\n\nContext: {context}"

    return JiraTicket(
        summary=action_item[:255],
        description=desc,
        issue_type=JiraIssueType.TASK,
        priority="High",  # Action items are usually urgent
        labels=labels or ["ai-generated", "action-item"],
    )


# Singleton instance
_jira_agent: Optional[JiraAgent] = None


def get_jira_agent() -> JiraAgent:
    """Get or create the Jira agent singleton."""
    global _jira_agent
    if _jira_agent is None:
        _jira_agent = JiraAgent()
    return _jira_agent
