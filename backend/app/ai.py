"""AI/LLM integration module for generating Scrum artifacts."""
import json
from typing import Any, Dict, List, Optional
import re

from openai import AsyncAzureOpenAI, AsyncOpenAI

from .config import Settings, get_settings
from .schemas import (
    SprintTask,
    SprintTasksResponse,
    StandupEntry,
    StandupSummaryResponse,
    UserStoriesResponse,
    UserStory,
)


class AIService:
    """Service for AI-powered Scrum assistance."""

    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or get_settings()
        self._client: Optional[AsyncOpenAI] = None

    def _get_client(self) -> Optional[AsyncOpenAI]:
        """Get or create the appropriate AI client."""
        if self._client is not None:
            return self._client

        if self.settings.ai_provider == "openai" and self.settings.openai_api_key:
            self._client = AsyncOpenAI(
                api_key=self.settings.openai_api_key,
                base_url=self.settings.openai_base_url,
            )
        elif self.settings.ai_provider == "azure" and self.settings.azure_openai_key:
            self._client = AsyncAzureOpenAI(
                api_key=self.settings.azure_openai_key,
                azure_endpoint=self.settings.azure_openai_endpoint,
                api_version=self.settings.azure_openai_api_version,
            )
        return self._client

    def _get_model(self) -> str:
        """Get the appropriate model name based on provider."""
        if self.settings.ai_provider == "azure":
            return self.settings.azure_openai_deployment
        return self.settings.openai_model

    async def _chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Make a chat completion request."""
        client = self._get_client()
        if client is None:
            return self._mock_response(messages)

        response = await client.chat.completions.create(
            model=self._get_model(),
            messages=messages,
            temperature=0.7,
            **kwargs,
        )
        return response.choices[0].message.content or ""

    def _clean_text(self, text: str) -> str:
        """Clean text by removing delimiter characters and formatting artifacts."""
        if not text:
            return text

        # Remove common delimiter patterns
        # Remove lines that are mostly delimiter characters
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip lines that are mostly delimiters (=, -, *, #, etc.)
            if stripped and not re.match(r'^[\s=\-\*#_\|~`]+$', stripped):
                # Also remove inline delimiter sequences
                cleaned = re.sub(r'[=]{3,}', '', stripped)
                cleaned = re.sub(r'[-]{3,}', '', cleaned)
                cleaned = re.sub(r'[_]{3,}', '', cleaned)
                cleaned = re.sub(r'[\*]{3,}', '', cleaned)
                cleaned = re.sub(r'[#]{3,}', '', cleaned)
                cleaned = re.sub(r'[~]{3,}', '', cleaned)
                cleaned = re.sub(r'[`]{3,}', '', cleaned)
                cleaned = re.sub(r'[\|]{3,}', '', cleaned)
                cleaned = cleaned.strip()
                if cleaned:
                    cleaned_lines.append(cleaned)

        return '\n'.join(cleaned_lines)

    def _mock_response(self, messages: List[Dict[str, str]]) -> str:
        """Generate mock response when no AI provider is configured.

        This method parses the actual user input to generate relevant mock responses
        based on the content provided, rather than returning static default responses.
        """
        # Check the system message to determine what type of response is needed
        system_message = messages[0]["content"] if messages else ""
        user_message = messages[-1]["content"] if messages else ""

        # Clean the user message to remove delimiters
        user_message = self._clean_text(user_message)

        # Check system message first for more accurate detection
        if "scrum master" in system_message.lower() or "standup" in system_message.lower():
            return self._generate_standup_mock(user_message)
        elif "technical lead" in system_message.lower() or "sprint tasks" in system_message.lower():
            return self._generate_tasks_mock(user_message)
        elif "agile coach" in system_message.lower() or "extract user stories" in system_message.lower():
            return self._generate_stories_mock(user_message)
        else:
            # Default fallback
            return json.dumps({
                "tasks": [
                    {
                        "title": "Analyze requirements",
                        "description": "Review and analyze the provided requirements to identify key deliverables.",
                        "estimated_hours": 2,
                        "priority": "high",
                        "parent_story": "General"
                    }
                ],
                "total_estimated_hours": 2,
                "recommendations": ["Review requirements carefully before implementation"]
            })

    def _create_short_title(self, text: str, max_length: int = 60) -> str:
        """Create a short, complete title from text without cutting words mid-sentence."""
        if not text:
            return "Untitled Task"

        # Clean the text first
        text = text.strip()

        # Remove leading numbers/bullets (e.g., "1. ", "2. ", "- ", "* ")
        text = re.sub(r'^[\d]+\.\s*', '', text)
        text = re.sub(r'^[-\*•]\s*', '', text)
        text = text.strip()

        # If already short enough, return as is
        if len(text) <= max_length:
            return text

        # Extract the key action/subject from the text
        # Look for common patterns and extract meaningful phrases

        # If text starts with common phrases, try to extract the main subject
        lower_text = text.lower()

        # For "Users need to...", "The admin wants to...", etc. - extract the action
        action_patterns = [
            r'^(?:the\s+)?(\w+(?:\s+\w+)?)\s+(?:need|want|should|must|can|will)\s+(?:to\s+)?(.+)',
            r'^(?:we\s+)?(?:need|want|should|must)\s+(?:to\s+)?(.+)',
        ]

        for pattern in action_patterns:
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                groups = match.groups()
                if len(groups) >= 2:
                    subject = groups[0]
                    action = groups[1]
                    # Create a concise title from subject and action
                    action_short = action[:40].rsplit(' ', 1)[0] if len(action) > 40 else action
                    title = f"{subject.title()} - {action_short}"
                    if len(title) <= max_length:
                        return title.strip()

        # Try to find the first complete clause (up to a period that's not a number)
        # Avoid breaking on "1." "2." etc.
        period_match = re.search(r'(?<!\d)\.\s', text[:max_length])
        if period_match and period_match.start() > 15:
            return text[:period_match.start()].strip()

        # Try other natural break points (but not periods after numbers)
        break_patterns = [', ', ' - ', ': ', '; ', ' so that ', ' in order to ']
        for pattern in break_patterns:
            if pattern in text[:max_length].lower():
                idx = text[:max_length].lower().rfind(pattern)
                if idx > 15:  # Ensure we have a reasonable length
                    return text[:idx].strip()

        # If no natural break, find the last complete word before max_length
        if len(text) > max_length:
            # Find the last space before max_length
            last_space = text[:max_length].rfind(' ')
            if last_space > 15:  # Ensure minimum reasonable length
                return text[:last_space].strip()

        # Fallback: just take first max_length chars and ensure no partial word
        truncated = text[:max_length]
        if len(text) > max_length and text[max_length] != ' ':
            last_space = truncated.rfind(' ')
            if last_space > 0:
                truncated = truncated[:last_space]

        return truncated.strip()

    def _extract_key_phrase(self, text: str) -> str:
        """Extract a key phrase or subject from text for use as a title."""
        if not text:
            return "Untitled"

        # Clean the text
        text = text.strip()
        text = re.sub(r'^[\d]+\.\s*', '', text)  # Remove leading numbers
        text = re.sub(r'^[-\*•]\s*', '', text)   # Remove bullets
        text = text.strip()

        # Try to extract the main subject/action
        lower = text.lower()

        # Common patterns to extract meaningful titles
        patterns = [
            # "Users need password reset" -> "Password Reset"
            (r'(?:need|want|require)s?\s+(?:a\s+|the\s+)?(.+?)(?:\s+so\s+that|\s+in\s+order\s+to|$)', 1),
            # "implement two-factor authentication" -> "Two-Factor Authentication"
            (r'(?:implement|create|build|add|develop)\s+(?:a\s+|the\s+)?(.+?)(?:\s+so\s+that|\s+in\s+order\s+to|$)', 1),
            # "ability to view all users" -> "View All Users"
            (r'ability\s+to\s+(.+?)(?:\s+so\s+that|\s+in\s+order\s+to|$)', 1),
            # "be able to reset password" -> "Reset Password"
            (r'be\s+able\s+to\s+(.+?)(?:\s+so\s+that|\s+in\s+order\s+to|$)', 1),
        ]

        for pattern, group in patterns:
            match = re.search(pattern, lower)
            if match:
                extracted = match.group(group).strip()
                # Capitalize words
                if len(extracted) > 5 and len(extracted) < 60:
                    return extracted.title()

        # Fallback: return first few meaningful words
        words = text.split()[:6]
        return ' '.join(words).title() if words else "Untitled"

    def _generate_standup_mock(self, user_message: str) -> str:
        """Generate mock standup summary based on actual input content."""
        lines = user_message.split('\n')

        # Extract names and work items from the standup entries
        names = []
        yesterday_items = []
        today_items = []
        blockers = []

        for line in lines:
            if '**' in line and '**:' in line:
                # Extract name
                name = line.split('**')[1] if '**' in line else ""
                if name:
                    names.append(name)
            elif '- Yesterday:' in line:
                item = line.replace('- Yesterday:', '').strip()
                if item:
                    yesterday_items.append(item)
            elif '- Today:' in line:
                item = line.replace('- Today:', '').strip()
                if item:
                    today_items.append(item)
            elif '- Blockers:' in line:
                item = line.replace('- Blockers:', '').strip()
                if item and item.lower() != 'none':
                    blockers.append(item)

        # Generate summary based on actual content
        team_size = len(names) if names else 1
        summary = f"Team of {team_size} members reported progress. "
        if yesterday_items:
            summary += f"Yesterday's focus included: {self._create_short_title(yesterday_items[0], 80)}. "
        if today_items:
            summary += f"Today's priorities include: {self._create_short_title(today_items[0], 80)}. "
        if blockers:
            summary += f"There are {len(blockers)} blocker(s) requiring attention."

        # Generate tasks from today's work items
        suggested_tasks = []
        for i, item in enumerate(today_items[:5]):  # Limit to 5 tasks
            suggested_tasks.append({
                "title": self._create_short_title(item, 60),
                "description": f"Complete the following work: {item}",
                "estimated_hours": 4,
                "priority": "high" if i < 2 else "medium",
                "parent_story": names[i] if i < len(names) else "Team Task"
            })

        # Generate stories from blockers and today items
        suggested_stories = []
        for i, blocker in enumerate(blockers[:2]):  # Limit to 2 stories from blockers
            blocker_title = self._create_short_title(blocker, 50)
            suggested_stories.append({
                "title": f"Resolve: {blocker_title}",
                "description": f"As a team member, I want to resolve '{blocker}' so that work can proceed without delays.",
                "acceptance_criteria": [
                    f"Blocker is resolved",
                    "Team can continue with planned work",
                    "No further impediments from this issue"
                ],
                "story_points": 3
            })

        # Add stories from today's work if we have room
        for i, item in enumerate(today_items[:2]):
            if len(suggested_stories) < 3:
                item_title = self._create_short_title(item, 50)
                suggested_stories.append({
                    "title": item_title,
                    "description": f"As a developer, I want to {item.lower()} so that the sprint goals are met.",
                    "acceptance_criteria": [
                        "Work is completed as specified",
                        "Code is reviewed and tested",
                        "Documentation is updated"
                    ],
                    "story_points": 5
                })

        return json.dumps({
            "summary": summary,
            "key_blockers": blockers[:5] if blockers else ["No critical blockers reported"],
            "action_items": [f"Follow up on: {self._create_short_title(item, 50)}" for item in today_items[:3]] or ["Review team progress"],
            "suggested_tasks": suggested_tasks if suggested_tasks else [
                {
                    "title": "Review standup outcomes",
                    "description": "Analyze the standup discussion and identify action items",
                    "estimated_hours": 1,
                    "priority": "medium",
                    "parent_story": "Sprint Management"
                }
            ],
            "suggested_stories": suggested_stories if suggested_stories else [
                {
                    "title": "Sprint Progress Tracking",
                    "description": "As a scrum master, I want to track sprint progress so that I can identify risks early.",
                    "acceptance_criteria": ["Daily standups are conducted", "Blockers are identified and addressed"],
                    "story_points": 2
                }
            ]
        })

    def _generate_tasks_mock(self, user_message: str) -> str:
        """Generate mock sprint tasks based on actual user stories input."""
        lines = [line.strip() for line in user_message.split('\n') if line.strip()]

        # Extract user stories from input
        stories = []
        for line in lines:
            if line.startswith('- '):
                stories.append(line[2:])
            elif 'as a' in line.lower() or 'i want' in line.lower():
                stories.append(line)
            elif len(line) > 20:  # Any substantial line could be a story
                stories.append(line)

        # Generate tasks from the actual stories
        tasks = []
        total_hours = 0

        for i, story in enumerate(stories[:10]):  # Limit to 10 stories
            # Create short title for the story
            story_title = self._create_short_title(story, 50)

            # Design task
            tasks.append({
                "title": f"Design: {story_title}",
                "description": f"Create design and technical specification for: {story}",
                "estimated_hours": 3,
                "priority": "high" if i < 3 else "medium",
                "parent_story": story_title
            })
            total_hours += 3

            # Implementation task
            tasks.append({
                "title": f"Implement: {story_title}",
                "description": f"Develop and implement the functionality for: {story}",
                "estimated_hours": 6,
                "priority": "high" if i < 3 else "medium",
                "parent_story": story_title
            })
            total_hours += 6

            # Testing task (for first 5 stories)
            if i < 5:
                tasks.append({
                    "title": f"Test: {story_title}",
                    "description": f"Write and execute tests for: {story}",
                    "estimated_hours": 2,
                    "priority": "medium",
                    "parent_story": story_title
                })
                total_hours += 2

        recommendations = []
        if len(stories) > 5:
            recommendations.append(f"Consider splitting the {len(stories)} stories across multiple sprints")
        if total_hours > 80:
            recommendations.append(f"Total estimated hours ({total_hours}h) may exceed sprint capacity")
        recommendations.append("Prioritize stories based on business value and dependencies")

        return json.dumps({
            "tasks": tasks if tasks else [
                {
                    "title": "Analyze requirements",
                    "description": "Review and analyze the provided requirements",
                    "estimated_hours": 2,
                    "priority": "high",
                    "parent_story": "General"
                }
            ],
            "total_estimated_hours": total_hours if total_hours > 0 else 2,
            "recommendations": recommendations
        })

    def _generate_stories_mock(self, user_message: str) -> str:
        """Generate mock user stories based on actual meeting notes input."""
        # Extract key phrases and requirements from the input
        lines = user_message.split('\n')

        # Look for actionable items in the text
        keywords = ['need', 'want', 'should', 'must', 'require', 'feature', 'user', 'admin', 'customer', 'ability']
        relevant_lines = []

        for line in lines:
            line = line.strip()
            # Remove leading numbers and bullets
            line = re.sub(r'^[\d]+\.\s*', '', line)
            line = re.sub(r'^[-\*•]\s*', '', line)
            line = line.strip()

            if not line:
                continue

            line_lower = line.lower()
            if any(keyword in line_lower for keyword in keywords):
                relevant_lines.append(line)
            elif len(line) > 50:  # Substantial content
                relevant_lines.append(line)

        # Generate stories from the content
        stories = []
        for i, line in enumerate(relevant_lines[:8]):  # Limit to 8 stories
            # Determine the role based on content
            role = "user"
            if 'admin' in line.lower():
                role = "admin"
            elif 'customer' in line.lower():
                role = "customer"
            elif 'manager' in line.lower():
                role = "manager"

            # Create a meaningful title from the line
            feature_title = self._extract_key_phrase(line)
            if len(feature_title) > 45:
                feature_title = self._create_short_title(feature_title, 45)

            # Clean the description - extract the core requirement
            description_text = line.lower()
            # Remove redundant phrases
            description_text = re.sub(r'^(?:the\s+)?(?:admin|user|customer|manager)\s+(?:team\s+)?(?:wants?\s+to\s+|needs?\s+to\s+)?', '', description_text)
            description_text = description_text.strip()

            if len(description_text) > 120:
                description_text = self._create_short_title(description_text, 120)

            stories.append({
                "title": feature_title,
                "description": f"As a {role}, I want to {description_text} so that I can accomplish my goals efficiently.",
                "acceptance_criteria": [
                    f"The {role} can access the feature",
                    "The functionality works as expected",
                    "Appropriate validation and error handling is in place",
                    "The feature is documented"
                ],
                "story_points": 5 if i < 3 else 3
            })

        # If no stories were generated, create a default based on the input
        if not stories:
            input_summary = self._create_short_title(user_message, 100)
            stories.append({
                "title": "Implement Requirements",
                "description": f"As a user, I want the system to handle: {input_summary}",
                "acceptance_criteria": [
                    "Requirements are implemented",
                    "Functionality is tested",
                    "Documentation is complete"
                ],
                "story_points": 5
            })

        return json.dumps({
            "stories": stories,
            "raw_insights": f"Analyzed {len(relevant_lines)} relevant items from the meeting notes. Generated {len(stories)} user stories based on the content provided."
        })

    async def summarize_standup(
        self, entries: List[StandupEntry], sprint_goal: Optional[str] = None
    ) -> StandupSummaryResponse:
        """Summarize standup entries into actionable insights."""
        entries_text = "\n".join(
            f"**{e.name}**:\n- Yesterday: {e.yesterday}\n- Today: {e.today}\n- Blockers: {e.blockers or 'None'}"
            for e in entries
        )

        system_prompt = """You are a Scrum Master assistant. Analyze standup notes and provide:
1. A concise summary of team progress
2. Key blockers that need attention
3. Action items to address issues
4. Suggested tasks derived from the standup entries
5. Suggested user stories based on work mentioned

Respond in JSON format:
{
    "summary": "string",
    "key_blockers": ["string"],
    "action_items": ["string"],
    "suggested_tasks": [
        {
            "title": "string",
            "description": "string",
            "estimated_hours": number,
            "priority": "high" | "medium" | "low",
            "parent_story": "string or null"
        }
    ],
    "suggested_stories": [
        {
            "title": "string",
            "description": "As a... I want... So that...",
            "acceptance_criteria": ["string"],
            "story_points": number (1-21, Fibonacci)
        }
    ]
}"""

        user_prompt = f"Sprint Goal: {sprint_goal or 'Not specified'}\n\nStandup Entries:\n{entries_text}"

        response = await self._chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        try:
            data = json.loads(response)
            # Convert nested dicts to proper model instances
            if "suggested_tasks" in data:
                data["suggested_tasks"] = [SprintTask(**t) for t in data["suggested_tasks"]]
            if "suggested_stories" in data:
                data["suggested_stories"] = [UserStory(**s) for s in data["suggested_stories"]]
            return StandupSummaryResponse(**data)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"[Standup] Error parsing response: {e}")
            return StandupSummaryResponse(
                summary=response,
                key_blockers=[],
                action_items=[],
                suggested_tasks=[],
                suggested_stories=[],
            )

    async def generate_user_stories(
        self, notes: str, context: Optional[str] = None
    ) -> UserStoriesResponse:
        """Generate user stories from meeting notes."""
        system_prompt = """You are an Agile coach. Extract user stories from meeting notes using the format:
"As a [role], I want [feature] so that [benefit]"

Respond in JSON format:
{
    "stories": [
        {
            "title": "string",
            "description": "As a... I want... So that...",
            "acceptance_criteria": ["string"],
            "story_points": number (1-21, Fibonacci)
        }
    ],
    "raw_insights": "string"
}"""

        user_prompt = f"Context: {context or 'General software project'}\n\nMeeting Notes:\n{notes}"

        response = await self._chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        try:
            data = json.loads(response)
            return UserStoriesResponse(**data)
        except (json.JSONDecodeError, ValueError):
            return UserStoriesResponse(
                stories=[
                    UserStory(
                        title="Generated Story",
                        description=response[:500],
                        acceptance_criteria=[],
                    )
                ],
                raw_insights=None,
            )

    async def suggest_sprint_tasks(
        self,
        user_stories: List[str],
        team_capacity: Optional[int] = None,
        sprint_duration_days: int = 14,
    ) -> SprintTasksResponse:
        """Suggest sprint tasks based on user stories."""
        system_prompt = f"""You are a technical lead. Break down user stories into actionable sprint tasks.
Consider a {sprint_duration_days}-day sprint{f' with {team_capacity} story points capacity' if team_capacity else ''}.

Respond in JSON format:
{{
    "tasks": [
        {{
            "title": "string",
            "description": "string",
            "estimated_hours": number,
            "priority": "high" | "medium" | "low",
            "parent_story": "string"
        }}
    ],
    "total_estimated_hours": number,
    "recommendations": ["string"]
}}"""

        stories_text = "\n".join(f"- {story}" for story in user_stories)
        user_prompt = f"User Stories:\n{stories_text}"

        response = await self._chat_completion([
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ])

        try:
            data = json.loads(response)
            return SprintTasksResponse(**data)
        except (json.JSONDecodeError, ValueError):
            return SprintTasksResponse(
                tasks=[
                    SprintTask(
                        title="Review and plan",
                        description="Review user stories and create detailed tasks",
                        estimated_hours=2,
                        priority="high",
                    )
                ],
                total_estimated_hours=2,
                recommendations=["Manual task breakdown recommended"],
            )


# Singleton instance
_ai_service: Optional[AIService] = None


def get_ai_service() -> AIService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = AIService()
    return _ai_service
