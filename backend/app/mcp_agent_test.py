"""AI Agent for testing MCP Server connectivity and functionality.

This agent connects to the AI Sprint Companion MCP Server and tests all available tools
to verify the server is working correctly.

Usage:
    python -m app.mcp_agent_test

    Or from the project root:
    cd backend
    python -m app.mcp_agent_test
"""

import asyncio
import json
import sys
from typing import Any, Dict, List, Optional
from datetime import datetime


class MCPAgentTester:
    """AI Agent that tests MCP Server connectivity and all tools."""

    def __init__(self):
        """Initialize the agent tester."""
        self.client = None
        self.test_results: List[Dict[str, Any]] = []
        self.start_time: Optional[datetime] = None

    def _log(self, message: str, level: str = "INFO"):
        """Log a message with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        prefix = {
            "INFO": "ℹ️ ",
            "SUCCESS": "✅",
            "ERROR": "❌",
            "WARNING": "⚠️ ",
            "TEST": "🧪",
        }.get(level, "")
        print(f"[{timestamp}] {prefix} {message}")

    def _record_test(self, test_name: str, success: bool, details: str = "", data: Any = None):
        """Record a test result."""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)

        if success:
            self._log(f"PASS: {test_name} - {details}", "SUCCESS")
        else:
            self._log(f"FAIL: {test_name} - {details}", "ERROR")

    async def initialize(self):
        """Initialize the MCP client."""
        self._log("Initializing MCP Agent Tester...")
        self.start_time = datetime.now()

        # Import and create the direct client
        try:
            from .mcp_client import DirectMCPClient
            self.client = DirectMCPClient()
            self._log("DirectMCPClient initialized successfully", "SUCCESS")
            return True
        except ImportError as e:
            self._log(f"Failed to import MCP client: {e}", "ERROR")
            return False

    async def test_health_check(self) -> bool:
        """Test the health check endpoint."""
        self._log("Testing health_check tool...", "TEST")

        try:
            result = await self.client.health_check()

            if result.get("status") == "healthy":
                self._record_test(
                    "health_check",
                    True,
                    f"Service is healthy, version: {result.get('version')}, AI provider: {result.get('ai_provider')}",
                    result
                )
                return True
            else:
                self._record_test("health_check", False, f"Unexpected status: {result}", result)
                return False
        except Exception as e:
            self._record_test("health_check", False, f"Exception: {str(e)}")
            return False

    async def test_summarize_standup(self) -> bool:
        """Test the summarize_standup tool."""
        self._log("Testing summarize_standup tool...", "TEST")

        test_entries = [
            {
                "name": "Alice",
                "yesterday": "Completed user authentication API endpoints",
                "today": "Working on dashboard UI components",
                "blockers": "Waiting for design mockups from UX team"
            },
            {
                "name": "Bob",
                "yesterday": "Fixed critical login bug affecting mobile users",
                "today": "Code review for Alice's PR and starting payment integration",
                "blockers": None
            },
            {
                "name": "Carol",
                "yesterday": "Sprint planning meeting and backlog grooming",
                "today": "Starting database optimization for search feature",
                "blockers": "Need access credentials for staging database"
            }
        ]

        try:
            result = await self.client.summarize_standup(
                entries=test_entries,
                sprint_goal="Complete user authentication and dashboard MVP"
            )

            if "error" in result and result.get("error"):
                self._record_test("summarize_standup", False, f"Error: {result.get('message')}", result)
                return False

            has_summary = bool(result.get("summary"))
            has_blockers = "key_blockers" in result
            has_actions = "action_items" in result
            has_tasks = "suggested_tasks" in result
            has_stories = "suggested_stories" in result

            all_fields = has_summary and has_blockers and has_actions and has_tasks and has_stories

            if all_fields:
                self._record_test(
                    "summarize_standup",
                    True,
                    f"Generated summary with {len(result.get('suggested_tasks', []))} tasks and {len(result.get('suggested_stories', []))} stories",
                    {
                        "summary_length": len(result.get("summary", "")),
                        "blockers_count": len(result.get("key_blockers", [])),
                        "action_items_count": len(result.get("action_items", [])),
                        "tasks_count": len(result.get("suggested_tasks", [])),
                        "stories_count": len(result.get("suggested_stories", []))
                    }
                )
                return True
            else:
                self._record_test(
                    "summarize_standup",
                    False,
                    f"Missing fields: summary={has_summary}, blockers={has_blockers}, actions={has_actions}, tasks={has_tasks}, stories={has_stories}",
                    result
                )
                return False
        except Exception as e:
            self._record_test("summarize_standup", False, f"Exception: {str(e)}")
            return False

    async def test_generate_user_stories(self) -> bool:
        """Test the generate_user_stories tool."""
        self._log("Testing generate_user_stories tool...", "TEST")

        test_notes = """
        Product Planning Meeting Notes - February 8, 2026
        
        Key discussions:
        1. Users need the ability to reset their passwords securely via email
        2. Admin team wants to view all registered users and manage account status
        3. Customers requested a wishlist feature to save products for later
        4. Mobile app needs push notifications for order status updates
        5. Search functionality should support filters by price, category, and ratings
        
        Priority items for next sprint:
        - Password reset is critical for reducing support tickets
        - Admin user management will help with fraud prevention
        - Wishlist has high customer demand based on survey results
        """

        try:
            result = await self.client.generate_user_stories(
                notes=test_notes,
                context="E-commerce platform enhancement project"
            )

            if "error" in result and result.get("error"):
                self._record_test("generate_user_stories", False, f"Error: {result.get('message')}", result)
                return False

            stories = result.get("stories", [])

            if len(stories) > 0:
                # Verify story structure
                first_story = stories[0]
                has_title = "title" in first_story
                has_description = "description" in first_story
                has_criteria = "acceptance_criteria" in first_story

                if has_title and has_description and has_criteria:
                    self._record_test(
                        "generate_user_stories",
                        True,
                        f"Generated {len(stories)} user stories with proper structure",
                        {
                            "stories_count": len(stories),
                            "first_story_title": first_story.get("title"),
                            "raw_insights": result.get("raw_insights")
                        }
                    )
                    return True
                else:
                    self._record_test(
                        "generate_user_stories",
                        False,
                        f"Story missing fields: title={has_title}, description={has_description}, criteria={has_criteria}",
                        first_story
                    )
                    return False
            else:
                self._record_test("generate_user_stories", False, "No stories generated", result)
                return False
        except Exception as e:
            self._record_test("generate_user_stories", False, f"Exception: {str(e)}")
            return False

    async def test_suggest_sprint_tasks(self) -> bool:
        """Test the suggest_sprint_tasks tool."""
        self._log("Testing suggest_sprint_tasks tool...", "TEST")

        test_stories = [
            "As a user, I want to reset my password via email so that I can regain access to my account",
            "As an admin, I want to view all users so that I can manage accounts and prevent fraud",
            "As a customer, I want to save items to a wishlist so that I can purchase them later"
        ]

        try:
            result = await self.client.suggest_sprint_tasks(
                user_stories=test_stories,
                team_capacity=40,
                sprint_duration_days=14
            )

            if "error" in result and result.get("error"):
                self._record_test("suggest_sprint_tasks", False, f"Error: {result.get('message')}", result)
                return False

            tasks = result.get("tasks", [])

            if len(tasks) > 0:
                # Verify task structure
                first_task = tasks[0]
                has_title = "title" in first_task
                has_description = "description" in first_task
                has_hours = "estimated_hours" in first_task
                has_priority = "priority" in first_task

                if has_title and has_description:
                    self._record_test(
                        "suggest_sprint_tasks",
                        True,
                        f"Generated {len(tasks)} tasks, total hours: {result.get('total_estimated_hours', 'N/A')}",
                        {
                            "tasks_count": len(tasks),
                            "total_hours": result.get("total_estimated_hours"),
                            "recommendations": result.get("recommendations", [])
                        }
                    )
                    return True
                else:
                    self._record_test(
                        "suggest_sprint_tasks",
                        False,
                        f"Task missing fields: title={has_title}, description={has_description}",
                        first_task
                    )
                    return False
            else:
                self._record_test("suggest_sprint_tasks", False, "No tasks generated", result)
                return False
        except Exception as e:
            self._record_test("suggest_sprint_tasks", False, f"Exception: {str(e)}")
            return False

    async def test_jira_status(self) -> bool:
        """Test the get_jira_status tool."""
        self._log("Testing get_jira_status tool...", "TEST")

        try:
            result = await self.client.get_jira_status()

            # This test passes whether Jira is configured or not - we just verify the response format
            has_configured = "configured" in result

            if has_configured:
                configured = result.get("configured")
                if configured:
                    self._record_test(
                        "get_jira_status",
                        True,
                        f"Jira is configured: URL={result.get('jira_url')}, Project={result.get('project_key')}",
                        result
                    )
                else:
                    self._record_test(
                        "get_jira_status",
                        True,
                        "Jira is not configured (expected if credentials not set)",
                        result
                    )
                return True
            else:
                self._record_test("get_jira_status", False, "Response missing 'configured' field", result)
                return False
        except Exception as e:
            self._record_test("get_jira_status", False, f"Exception: {str(e)}")
            return False

    async def test_with_sample_file(self) -> bool:
        """Test using the sample user stories file."""
        self._log("Testing with sample user stories file...", "TEST")

        try:
            # Read the sample file
            import os
            sample_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "samples",
                "user_stories_sample.txt"
            )

            if not os.path.exists(sample_path):
                self._record_test(
                    "sample_file_test",
                    False,
                    f"Sample file not found at {sample_path}"
                )
                return False

            with open(sample_path, "r", encoding="utf-8") as f:
                sample_content = f.read()

            self._log(f"Loaded sample file: {len(sample_content)} characters")

            # Extract a subset of user stories for testing
            # Get the first 5 user stories from the file
            lines = sample_content.split("\n")
            user_stories = []
            for line in lines:
                if line.strip().startswith("As a "):
                    user_stories.append(line.strip())
                    if len(user_stories) >= 5:
                        break

            if not user_stories:
                self._record_test("sample_file_test", False, "No user stories found in sample file")
                return False

            self._log(f"Extracted {len(user_stories)} user stories for task generation")

            # Generate tasks from sample stories
            result = await self.client.suggest_sprint_tasks(
                user_stories=user_stories,
                team_capacity=50,
                sprint_duration_days=14
            )

            if "error" in result and result.get("error"):
                self._record_test("sample_file_test", False, f"Error: {result.get('message')}", result)
                return False

            tasks = result.get("tasks", [])

            self._record_test(
                "sample_file_test",
                True,
                f"Successfully generated {len(tasks)} tasks from {len(user_stories)} sample stories",
                {
                    "input_stories": len(user_stories),
                    "output_tasks": len(tasks),
                    "total_hours": result.get("total_estimated_hours"),
                    "recommendations_count": len(result.get("recommendations", []))
                }
            )
            return True

        except Exception as e:
            self._record_test("sample_file_test", False, f"Exception: {str(e)}")
            return False

    async def test_end_to_end_workflow(self) -> bool:
        """Test a complete end-to-end workflow: notes -> stories -> tasks."""
        self._log("Testing end-to-end workflow...", "TEST")

        try:
            # Step 1: Generate user stories from meeting notes
            meeting_notes = """
            Sprint Planning Meeting - New Feature Discussion
            
            The team discussed implementing a new customer loyalty program:
            1. Customers should earn points for every purchase
            2. Points can be redeemed for discounts on future orders
            3. VIP tiers based on annual spending (Silver, Gold, Platinum)
            4. Special birthday rewards and early access to sales
            5. Referral bonuses when customers bring new users
            """

            self._log("Step 1: Generating user stories from meeting notes...")
            stories_result = await self.client.generate_user_stories(
                notes=meeting_notes,
                context="Customer loyalty program for e-commerce platform"
            )

            if "error" in stories_result and stories_result.get("error"):
                self._record_test("end_to_end_workflow", False, f"Story generation failed: {stories_result.get('message')}")
                return False

            stories = stories_result.get("stories", [])
            self._log(f"Generated {len(stories)} user stories")

            if not stories:
                self._record_test("end_to_end_workflow", False, "No stories generated in step 1")
                return False

            # Step 2: Convert stories to task input format
            story_descriptions = [s.get("description", s.get("title", "")) for s in stories]

            self._log("Step 2: Generating sprint tasks from user stories...")
            tasks_result = await self.client.suggest_sprint_tasks(
                user_stories=story_descriptions[:5],  # Use first 5 stories
                team_capacity=40,
                sprint_duration_days=14
            )

            if "error" in tasks_result and tasks_result.get("error"):
                self._record_test("end_to_end_workflow", False, f"Task generation failed: {tasks_result.get('message')}")
                return False

            tasks = tasks_result.get("tasks", [])
            self._log(f"Generated {len(tasks)} sprint tasks")

            # Step 3: Create a mock standup based on the tasks
            standup_entries = []
            task_titles = [t.get("title", "Task") for t in tasks[:3]]

            standup_entries = [
                {
                    "name": "Developer 1",
                    "yesterday": f"Completed: {task_titles[0] if task_titles else 'Initial setup'}",
                    "today": f"Working on: {task_titles[1] if len(task_titles) > 1 else 'Next task'}",
                    "blockers": None
                },
                {
                    "name": "Developer 2",
                    "yesterday": "Code review and testing",
                    "today": f"Starting: {task_titles[2] if len(task_titles) > 2 else 'Documentation'}",
                    "blockers": "Waiting for API specifications"
                }
            ]

            self._log("Step 3: Generating standup summary...")
            standup_result = await self.client.summarize_standup(
                entries=standup_entries,
                sprint_goal="Implement customer loyalty program MVP"
            )

            if "error" in standup_result and standup_result.get("error"):
                self._record_test("end_to_end_workflow", False, f"Standup summary failed: {standup_result.get('message')}")
                return False

            self._record_test(
                "end_to_end_workflow",
                True,
                f"Complete workflow: {len(stories)} stories -> {len(tasks)} tasks -> standup summary",
                {
                    "stories_generated": len(stories),
                    "tasks_generated": len(tasks),
                    "standup_blockers": len(standup_result.get("key_blockers", [])),
                    "standup_actions": len(standup_result.get("action_items", []))
                }
            )
            return True

        except Exception as e:
            self._record_test("end_to_end_workflow", False, f"Exception: {str(e)}")
            return False

    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all MCP server tests."""
        self._log("=" * 60)
        self._log("AI SPRINT COMPANION - MCP SERVER TEST SUITE")
        self._log("=" * 60)
        self._log("")

        # Initialize client
        if not await self.initialize():
            return {
                "success": False,
                "error": "Failed to initialize MCP client",
                "tests_run": 0,
                "tests_passed": 0
            }

        # Run all tests
        tests = [
            ("Health Check", self.test_health_check),
            ("Summarize Standup", self.test_summarize_standup),
            ("Generate User Stories", self.test_generate_user_stories),
            ("Suggest Sprint Tasks", self.test_suggest_sprint_tasks),
            ("Jira Status", self.test_jira_status),
            ("Sample File Test", self.test_with_sample_file),
            ("End-to-End Workflow", self.test_end_to_end_workflow),
        ]

        self._log("")
        self._log("Running tests...")
        self._log("-" * 40)

        for test_name, test_func in tests:
            self._log("")
            await test_func()

        # Calculate results
        passed = sum(1 for r in self.test_results if r["success"])
        failed = len(self.test_results) - passed
        duration = (datetime.now() - self.start_time).total_seconds() if self.start_time else 0

        # Print summary
        self._log("")
        self._log("=" * 60)
        self._log("TEST RESULTS SUMMARY")
        self._log("=" * 60)
        self._log(f"Total Tests: {len(self.test_results)}")
        self._log(f"Passed: {passed}", "SUCCESS" if passed > 0 else "INFO")
        self._log(f"Failed: {failed}", "ERROR" if failed > 0 else "INFO")
        self._log(f"Duration: {duration:.2f} seconds")
        self._log("")

        if failed == 0:
            self._log("🎉 ALL TESTS PASSED! MCP Server is working correctly.", "SUCCESS")
        else:
            self._log(f"⚠️  {failed} test(s) failed. Check the logs above for details.", "WARNING")

        self._log("")
        self._log("=" * 60)

        return {
            "success": failed == 0,
            "tests_run": len(self.test_results),
            "tests_passed": passed,
            "tests_failed": failed,
            "duration_seconds": duration,
            "results": self.test_results
        }


async def main():
    """Main entry point for the MCP agent tester."""
    agent = MCPAgentTester()
    results = await agent.run_all_tests()

    # Exit with appropriate code
    sys.exit(0 if results["success"] else 1)


if __name__ == "__main__":
    asyncio.run(main())

