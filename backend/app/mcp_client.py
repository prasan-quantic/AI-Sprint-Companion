"""MCP (Model Context Protocol) Client for AI Sprint Companion.

This module provides a client to connect to the AI Sprint Companion MCP server
and use its tools programmatically.

Usage:
    from app.mcp_client import DirectMCPClient
    
    async def main():
        client = DirectMCPClient()
        result = await client.summarize_standup([...])
"""

import asyncio
import json
from typing import Any, Dict, List, Optional


class DirectMCPClient:
    """Direct client that calls the AI Sprint Companion services directly.
    
    Use this client when you want to use the AI Sprint Companion functionality
    without setting up the full MCP server/client infrastructure.
    """

    def __init__(self):
        """Initialize the direct client."""
        self.ai_service = None
        self.jira_agent = None

    async def _ensure_services(self):
        """Ensure services are initialized."""
        if self.ai_service is None:
            from .ai import get_ai_service
            self.ai_service = get_ai_service()
        if self.jira_agent is None:
            from .jira_agent import get_jira_agent
            self.jira_agent = get_jira_agent()

    async def summarize_standup(
        self,
        entries: List[Dict[str, Any]],
        sprint_goal: Optional[str] = None
    ) -> Dict[str, Any]:
        """Summarize standup entries.
        
        Args:
            entries: List of standup entries, each with keys:
                - name: Team member name
                - yesterday: What was done yesterday
                - today: What's planned for today
                - blockers: Any blockers (optional)
            sprint_goal: Current sprint goal for context (optional)
            
        Returns:
            Dictionary with summary, key_blockers, action_items, 
            suggested_tasks, and suggested_stories
        """
        await self._ensure_services()
        from .schemas import StandupEntry as SchemaStandupEntry

        standup_entries = [
            SchemaStandupEntry(
                name=e.get("name", "Unknown"),
                yesterday=e.get("yesterday", ""),
                today=e.get("today", ""),
                blockers=e.get("blockers")
            )
            for e in entries
        ]

        result = await self.ai_service.summarize_standup(standup_entries, sprint_goal)
        
        return {
            "summary": result.summary,
            "key_blockers": result.key_blockers,
            "action_items": result.action_items,
            "suggested_tasks": [
                {
                    "title": t.title,
                    "description": t.description,
                    "estimated_hours": t.estimated_hours,
                    "priority": t.priority,
                    "parent_story": t.parent_story
                }
                for t in result.suggested_tasks
            ] if result.suggested_tasks else [],
            "suggested_stories": [
                {
                    "title": s.title,
                    "description": s.description,
                    "acceptance_criteria": s.acceptance_criteria,
                    "story_points": s.story_points
                }
                for s in result.suggested_stories
            ] if result.suggested_stories else []
        }

    async def generate_user_stories(
        self,
        notes: str,
        context: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate user stories from meeting notes.
        
        Args:
            notes: Meeting notes or requirements text
            context: Additional project context (optional)
            
        Returns:
            Dictionary with stories list and raw_insights
        """
        await self._ensure_services()

        result = await self.ai_service.generate_user_stories(notes, context)
        
        return {
            "stories": [
                {
                    "title": s.title,
                    "description": s.description,
                    "acceptance_criteria": s.acceptance_criteria,
                    "story_points": s.story_points
                }
                for s in result.stories
            ],
            "raw_insights": result.raw_insights
        }

    async def suggest_sprint_tasks(
        self,
        user_stories: List[str],
        team_capacity: Optional[int] = None,
        sprint_duration_days: int = 14
    ) -> Dict[str, Any]:
        """Suggest sprint tasks from user stories.
        
        Args:
            user_stories: List of user story descriptions
            team_capacity: Team capacity in story points (optional)
            sprint_duration_days: Sprint duration (default: 14)
            
        Returns:
            Dictionary with tasks list, total_estimated_hours, and recommendations
        """
        await self._ensure_services()

        result = await self.ai_service.suggest_sprint_tasks(
            user_stories=user_stories,
            team_capacity=team_capacity,
            sprint_duration_days=sprint_duration_days
        )
        
        return {
            "tasks": [
                {
                    "title": t.title,
                    "description": t.description,
                    "estimated_hours": t.estimated_hours,
                    "priority": t.priority,
                    "parent_story": t.parent_story
                }
                for t in result.tasks
            ],
            "total_estimated_hours": result.total_estimated_hours,
            "recommendations": result.recommendations
        }

    async def create_jira_ticket(
        self,
        summary: str,
        description: str,
        issue_type: str = "Story",
        priority: Optional[str] = None,
        labels: Optional[List[str]] = None,
        story_points: Optional[int] = None,
        acceptance_criteria: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Create a Jira ticket.
        
        Args:
            summary: Ticket title
            description: Ticket description
            issue_type: Type of issue (Story, Task, Bug, Epic)
            priority: Priority level (Highest, High, Medium, Low, Lowest)
            labels: List of labels
            story_points: Story points estimate
            acceptance_criteria: List of acceptance criteria
            
        Returns:
            Dictionary with success status and ticket details
        """
        await self._ensure_services()
        from .jira_agent import JiraTicket, JiraIssueType, JiraAgentError

        if not self.jira_agent.is_configured:
            return {
                "error": True,
                "message": "Jira is not configured"
            }

        try:
            ticket = JiraTicket(
                summary=summary,
                description=description,
                issue_type=JiraIssueType(issue_type),
                priority=priority,
                labels=labels,
                story_points=story_points,
                acceptance_criteria=acceptance_criteria
            )

            created = await self.jira_agent.create_ticket(ticket)
            
            return {
                "success": True,
                "ticket": {
                    "key": created.key,
                    "id": created.id,
                    "url": created.url,
                    "summary": created.summary
                }
            }
        except JiraAgentError as e:
            return {"error": True, "message": str(e)}

    async def get_jira_status(self) -> Dict[str, Any]:
        """Get Jira configuration status.
        
        Returns:
            Dictionary with configured status, connection info
        """
        await self._ensure_services()
        from .config import get_settings
        
        settings = get_settings()
        return {
            "configured": self.jira_agent.is_configured,
            "jira_url": settings.jira_url if self.jira_agent.is_configured else None,
            "project_key": settings.jira_project_key if self.jira_agent.is_configured else None
        }

    async def health_check(self) -> Dict[str, Any]:
        """Check service health.
        
        Returns:
            Dictionary with status, version, ai_provider, and jira_configured
        """
        await self._ensure_services()
        from . import __version__
        from .config import get_settings
        
        settings = get_settings()
        return {
            "status": "healthy",
            "version": __version__,
            "ai_provider": settings.ai_provider,
            "jira_configured": self.jira_agent.is_configured
        }


def get_client() -> DirectMCPClient:
    """Get an AI Sprint Companion client.
    
    Returns:
        DirectMCPClient instance
    """
    return DirectMCPClient()


async def demo():
    """Demo function showing how to use the client."""
    print("AI Sprint Companion MCP Client Demo")
    print("=" * 50)
    
    client = DirectMCPClient()
    
    # Health check
    print("\n1. Health Check:")
    health = await client.health_check()
    print(f"   Status: {health['status']}")
    print(f"   Version: {health['version']}")
    print(f"   AI Provider: {health['ai_provider']}")
    
    # Summarize standup
    print("\n2. Summarize Standup:")
    standup_result = await client.summarize_standup([
        {
            "name": "Alice",
            "yesterday": "Completed user authentication API",
            "today": "Working on dashboard components",
            "blockers": "Waiting for design mockups"
        },
        {
            "name": "Bob",
            "yesterday": "Fixed critical login bug",
            "today": "Code review for Alice's PR",
            "blockers": None
        }
    ], sprint_goal="Complete user authentication and dashboard MVP")
    
    print(f"   Summary: {standup_result['summary'][:100]}...")
    print(f"   Blockers: {standup_result['key_blockers']}")
    print(f"   Tasks suggested: {len(standup_result['suggested_tasks'])}")
    
    # Generate user stories
    print("\n3. Generate User Stories:")
    stories_result = await client.generate_user_stories(
        "Users need to be able to reset their passwords. The admin team wants to view all registered users."
    )
    print(f"   Stories generated: {len(stories_result['stories'])}")
    for story in stories_result['stories'][:2]:
        print(f"   - {story['title']}")
    
    # Suggest tasks
    print("\n4. Suggest Sprint Tasks:")
    tasks_result = await client.suggest_sprint_tasks([
        "As a user, I want to reset my password so I can regain access to my account",
        "As an admin, I want to view all users so I can manage the user base"
    ])
    print(f"   Tasks suggested: {len(tasks_result['tasks'])}")
    print(f"   Total hours: {tasks_result['total_estimated_hours']}")
    
    print("\n" + "=" * 50)
    print("Demo complete!")


if __name__ == "__main__":
    asyncio.run(demo())

