"""MCP (Model Context Protocol) Server for AI Sprint Companion.

This module exposes the AI Sprint Companion functionalities as an MCP server,
allowing AI agents to connect and use the Scrum assistance tools.

MCP Server provides the following tools:
1. summarize_standup - Summarize team standup notes
2. generate_user_stories - Generate user stories from meeting notes
3. suggest_sprint_tasks - Suggest sprint tasks from user stories
4. create_jira_ticket - Create a Jira ticket
5. get_jira_status - Check Jira configuration status
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional, Sequence
from contextlib import asynccontextmanager

# MCP SDK imports
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import (
        Tool,
        TextContent,
        CallToolResult,
        CallToolRequest,
        ListToolsResult,
        ListToolsRequest,
    )
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    print("MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)

from .ai import AIService, get_ai_service
from .jira_agent import JiraAgent, JiraTicket, JiraIssueType, JiraAgentError, get_jira_agent
from .schemas import StandupEntry


class MCPSprintCompanionServer:
    """MCP Server exposing AI Sprint Companion functionalities."""

    def __init__(self):
        """Initialize the MCP server."""
        self.ai_service: Optional[AIService] = None
        self.jira_agent: Optional[JiraAgent] = None

        if MCP_AVAILABLE:
            self.server = Server("ai-sprint-companion")
            self._setup_handlers()
        else:
            self.server = None

    def _setup_handlers(self):
        """Setup MCP request handlers."""

        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """Return list of available tools."""
            return [
                Tool(
                    name="summarize_standup",
                    description="Summarize team standup notes into actionable insights. Analyzes what team members did yesterday, what they're doing today, and any blockers they have.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "entries": {
                                "type": "array",
                                "description": "List of standup entries from team members",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string", "description": "Team member name"},
                                        "yesterday": {"type": "string", "description": "What was accomplished yesterday"},
                                        "today": {"type": "string", "description": "What is planned for today"},
                                        "blockers": {"type": "string", "description": "Any blockers or impediments (optional)"}
                                    },
                                    "required": ["name", "yesterday", "today"]
                                }
                            },
                            "sprint_goal": {
                                "type": "string",
                                "description": "Current sprint goal for context (optional)"
                            }
                        },
                        "required": ["entries"]
                    }
                ),
                Tool(
                    name="generate_user_stories",
                    description="Generate user stories from meeting notes or requirements text. Creates stories in 'As a [role], I want [feature] so that [benefit]' format.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "notes": {
                                "type": "string",
                                "description": "Meeting notes or requirements text to extract user stories from"
                            },
                            "context": {
                                "type": "string",
                                "description": "Additional context about the project (optional)"
                            }
                        },
                        "required": ["notes"]
                    }
                ),
                Tool(
                    name="suggest_sprint_tasks",
                    description="Suggest sprint tasks based on user stories. Breaks down stories into actionable development tasks with time estimates.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "user_stories": {
                                "type": "array",
                                "description": "List of user story descriptions",
                                "items": {"type": "string"}
                            },
                            "team_capacity": {
                                "type": "integer",
                                "description": "Team capacity in story points (optional)"
                            },
                            "sprint_duration_days": {
                                "type": "integer",
                                "description": "Sprint duration in days (default: 14)",
                                "default": 14
                            }
                        },
                        "required": ["user_stories"]
                    }
                ),
                Tool(
                    name="create_jira_ticket",
                    description="Create a Jira ticket (Story, Task, or Bug) in the configured project.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "summary": {
                                "type": "string",
                                "description": "Ticket summary/title"
                            },
                            "description": {
                                "type": "string",
                                "description": "Detailed ticket description"
                            },
                            "issue_type": {
                                "type": "string",
                                "enum": ["Story", "Task", "Bug", "Epic"],
                                "description": "Type of Jira issue",
                                "default": "Story"
                            },
                            "priority": {
                                "type": "string",
                                "enum": ["Highest", "High", "Medium", "Low", "Lowest"],
                                "description": "Ticket priority (optional)"
                            },
                            "labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Labels to add to the ticket (optional)"
                            },
                            "story_points": {
                                "type": "integer",
                                "description": "Story points estimate (optional)"
                            },
                            "acceptance_criteria": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "List of acceptance criteria (optional)"
                            }
                        },
                        "required": ["summary", "description"]
                    }
                ),
                Tool(
                    name="get_jira_status",
                    description="Check if Jira is configured and get connection status.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                ),
                Tool(
                    name="parse_standup_text",
                    description="Parse raw standup text into structured entries. Useful for converting free-form standup notes.",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "text": {
                                "type": "string",
                                "description": "Raw standup text in format 'Name: yesterday | today | blockers' (one entry per line)"
                            }
                        },
                        "required": ["text"]
                    }
                ),
                Tool(
                    name="health_check",
                    description="Check the health status of the AI Sprint Companion service.",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                result = await self._execute_tool(name, arguments)
                return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
            except Exception as e:
                error_result = {
                    "error": True,
                    "message": str(e),
                    "tool": name
                }
                return [TextContent(type="text", text=json.dumps(error_result, indent=2))]

    async def _execute_tool(self, name: str, arguments: dict) -> Dict[str, Any]:
        """Execute a tool and return the result."""
        # Lazy initialization of services
        if self.ai_service is None:
            self.ai_service = get_ai_service()
        if self.jira_agent is None:
            self.jira_agent = get_jira_agent()

        if name == "summarize_standup":
            return await self._summarize_standup(arguments)
        elif name == "generate_user_stories":
            return await self._generate_user_stories(arguments)
        elif name == "suggest_sprint_tasks":
            return await self._suggest_sprint_tasks(arguments)
        elif name == "create_jira_ticket":
            return await self._create_jira_ticket(arguments)
        elif name == "get_jira_status":
            return await self._get_jira_status()
        elif name == "parse_standup_text":
            return self._parse_standup_text(arguments)
        elif name == "health_check":
            return self._health_check()
        else:
            raise ValueError(f"Unknown tool: {name}")

    async def _summarize_standup(self, arguments: dict) -> Dict[str, Any]:
        """Summarize standup entries."""
        entries_data = arguments.get("entries", [])
        sprint_goal = arguments.get("sprint_goal")

        entries = [
            StandupEntry(
                name=e.get("name", "Unknown"),
                yesterday=e.get("yesterday", ""),
                today=e.get("today", ""),
                blockers=e.get("blockers")
            )
            for e in entries_data
        ]

        if not entries:
            return {"error": True, "message": "No standup entries provided"}

        result = await self.ai_service.summarize_standup(entries, sprint_goal)

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
            ],
            "suggested_stories": [
                {
                    "title": s.title,
                    "description": s.description,
                    "acceptance_criteria": s.acceptance_criteria,
                    "story_points": s.story_points
                }
                for s in result.suggested_stories
            ]
        }

    async def _generate_user_stories(self, arguments: dict) -> Dict[str, Any]:
        """Generate user stories from meeting notes."""
        notes = arguments.get("notes", "")
        context = arguments.get("context")

        if len(notes) < 10:
            return {"error": True, "message": "Please provide more detailed meeting notes (at least 10 characters)"}

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

    async def _suggest_sprint_tasks(self, arguments: dict) -> Dict[str, Any]:
        """Suggest sprint tasks from user stories."""
        user_stories = arguments.get("user_stories", [])
        team_capacity = arguments.get("team_capacity")
        sprint_duration_days = arguments.get("sprint_duration_days", 14)

        if not user_stories:
            return {"error": True, "message": "No user stories provided"}

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

    async def _create_jira_ticket(self, arguments: dict) -> Dict[str, Any]:
        """Create a Jira ticket."""
        if not self.jira_agent.is_configured:
            return {
                "error": True,
                "message": "Jira is not configured. Please set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY environment variables."
            }

        try:
            issue_type_str = arguments.get("issue_type", "Story")
            issue_type = JiraIssueType(issue_type_str)

            ticket = JiraTicket(
                summary=arguments.get("summary", ""),
                description=arguments.get("description", ""),
                issue_type=issue_type,
                priority=arguments.get("priority"),
                labels=arguments.get("labels"),
                story_points=arguments.get("story_points"),
                acceptance_criteria=arguments.get("acceptance_criteria")
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
        except Exception as e:
            return {"error": True, "message": f"Failed to create ticket: {str(e)}"}

    async def _get_jira_status(self) -> Dict[str, Any]:
        """Get Jira configuration status."""
        from .config import get_settings
        settings = get_settings()

        status = {
            "configured": self.jira_agent.is_configured,
            "jira_url": settings.jira_url if self.jira_agent.is_configured else None,
            "project_key": settings.jira_project_key if self.jira_agent.is_configured else None,
        }

        if self.jira_agent.is_configured:
            try:
                user_info = await self.jira_agent.test_connection()
                status["connected"] = True
                status["user_email"] = user_info.get("emailAddress")
                status["user_name"] = user_info.get("displayName")
            except JiraAgentError as e:
                status["connected"] = False
                status["connection_error"] = str(e)

        return status

    def _parse_standup_text(self, arguments: dict) -> Dict[str, Any]:
        """Parse raw standup text into structured entries."""
        text = arguments.get("text", "")
        entries = []

        for line in text.strip().split("\n"):
            if ":" in line:
                parts = line.split(":", 1)
                name = parts[0].strip()
                details = parts[1].split("|") if "|" in parts[1] else [parts[1], "", ""]
                entries.append({
                    "name": name,
                    "yesterday": details[0].strip() if len(details) > 0 else "",
                    "today": details[1].strip() if len(details) > 1 else "",
                    "blockers": details[2].strip() if len(details) > 2 else None
                })

        return {
            "entries": entries,
            "count": len(entries)
        }

    def _health_check(self) -> Dict[str, Any]:
        """Check service health."""
        from . import __version__
        from .config import get_settings

        settings = get_settings()

        return {
            "status": "healthy",
            "version": __version__,
            "ai_provider": settings.ai_provider,
            "jira_configured": self.jira_agent.is_configured if self.jira_agent else False
        }

    async def run(self):
        """Run the MCP server."""
        if not MCP_AVAILABLE:
            print("Error: MCP SDK not installed. Install with: pip install mcp", file=sys.stderr)
            sys.exit(1)

        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# Singleton instance
_mcp_server: Optional[MCPSprintCompanionServer] = None


def get_mcp_server() -> MCPSprintCompanionServer:
    """Get or create the MCP server instance."""
    global _mcp_server
    if _mcp_server is None:
        _mcp_server = MCPSprintCompanionServer()
    return _mcp_server


async def main():
    """Main entry point for the MCP server."""
    server = get_mcp_server()
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())

