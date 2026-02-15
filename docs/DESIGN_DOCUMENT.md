# AI Sprint Companion - Design Document

**Version:** 1.1.0  
**Date:** February 8, 2026  
**Author:** AI Sprint Companion Team

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [System Overview](#2-system-overview)
3. [Architecture](#3-architecture)
4. [Component Design](#4-component-design)
5. [Data Models](#5-data-models)
6. [API Design](#6-api-design)
7. [AI Integration](#7-ai-integration)
8. [MCP Protocol Integration](#8-mcp-protocol-integration)
9. [External Integrations](#9-external-integrations)
10. [Security Considerations](#10-security-considerations)
11. [Testing Strategy](#11-testing-strategy)
12. [Deployment](#12-deployment)
13. [Future Enhancements](#13-future-enhancements)

---

## 1. Executive Summary

### 1.1 Purpose

AI Sprint Companion is an intelligent Scrum assistance tool that leverages Large Language Models (LLMs) to automate and enhance agile development workflows. The system provides AI-powered capabilities for:

- **Standup Summarization**: Analyzing daily standup notes to extract insights, blockers, and action items
- **User Story Generation**: Converting meeting notes into well-formatted user stories
- **Sprint Task Suggestion**: Breaking down user stories into actionable development tasks
- **Jira Integration**: Automatically creating tickets in Jira from generated artifacts
- **MCP Protocol Support**: AI agent integration via Model Context Protocol

### 1.2 Goals

| Goal | Description |
|------|-------------|
| **Efficiency** | Reduce time spent on administrative Scrum tasks by 50%+ |
| **Consistency** | Ensure user stories and tasks follow best practices and standard formats |
| **Accessibility** | Provide both web UI and programmatic API access |
| **Flexibility** | Support multiple AI providers (OpenAI, Azure OpenAI, Mock) |
| **Integration** | Seamlessly connect with existing project management tools (Jira) |
| **AI Agent Ready** | Support MCP protocol for AI agent integration |

### 1.3 Technology Stack

| Layer | Technology |
|-------|------------|
| **Backend Framework** | Python 3.13, FastAPI |
| **AI/LLM** | OpenAI API, Azure OpenAI |
| **Frontend** | HTML5, HTMX, Jinja2 Templates |
| **HTTP Client** | HTTPX (async) |
| **Document Parsing** | python-docx, lxml |
| **Configuration** | Pydantic Settings |
| **Protocol** | MCP (Model Context Protocol) |
| **Testing** | pytest, pytest-asyncio |
| **Deployment** | Render.com, Docker |

---

## 2. System Overview

### 2.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AI Sprint Companion                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                  │
│  │   Web UI     │    │   REST API   │    │  MCP Server  │                  │
│  │   (HTMX)     │    │   (JSON)     │    │  (Protocol)  │                  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                  │
│         │                   │                   │                          │
│         └───────────────────┼───────────────────┘                          │
│                             │                                              │
│                    ┌────────▼────────┐                                     │
│                    │  FastAPI App    │                                     │
│                    │  (main.py)      │                                     │
│                    └────────┬────────┘                                     │
│                             │                                              │
│         ┌───────────────────┼───────────────────┐                          │
│         │                   │                   │                          │
│  ┌──────▼──────┐    ┌───────▼───────┐   ┌──────▼──────┐                   │
│  │ AI Service  │    │ Document      │   │ Jira Agent  │                   │
│  │ (ai.py)     │    │ Parser        │   │             │                   │
│  └──────┬──────┘    └───────────────┘   └──────┬──────┘                   │
│         │                                       │                          │
│  ┌──────▼──────┐                        ┌──────▼──────┐                   │
│  │ OpenAI /    │                        │ Jira Cloud  │                   │
│  │ Azure API   │                        │ REST API    │                   │
│  └─────────────┘                        └─────────────┘                   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Request Flow

```
User Request → FastAPI Router → Service Layer → AI/External API → Response
     │              │                │                │              │
     │              │                │                │              │
     ▼              ▼                ▼                ▼              ▼
  Web Form      Endpoint         AIService      OpenAI API      JSON/HTML
  or JSON       Handler          Methods        Completion      Response
```

### 2.3 MCP Agent Flow

```
AI Agent → MCP Client → MCP Server → DirectMCPClient → Services → Response
    │          │            │              │              │           │
    │          │            │              │              │           │
    ▼          ▼            ▼              ▼              ▼           ▼
  Claude   stdio/SSE    Tool Call    Direct Call    AIService    Structured
  or other  transport   Handler      to Services    JiraAgent    JSON Result
```

---

## 3. Architecture

### 3.1 Architectural Pattern

The application follows a **Layered Architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────┐
│         Presentation Layer              │
│   (Templates, Static Files, HTMX)       │
├─────────────────────────────────────────┤
│           API Layer                     │
│   (FastAPI Routes, MCP Server)          │
├─────────────────────────────────────────┤
│          Service Layer                  │
│   (AIService, JiraAgent, Parsers)       │
├─────────────────────────────────────────┤
│          Data Layer                     │
│   (Pydantic Schemas, Configuration)     │
└─────────────────────────────────────────┘
```

### 3.2 Design Patterns Used

| Pattern | Implementation | Purpose |
|---------|----------------|---------|
| **Singleton** | `get_ai_service()`, `get_settings()`, `get_jira_agent()` | Ensure single instance of services |
| **Factory** | `_get_client()` in AIService | Create appropriate AI client based on provider |
| **Strategy** | AI provider selection | Support multiple AI backends |
| **Adapter** | JiraAgent | Adapt Jira API to application interface |
| **Template Method** | Mock response generation | Define skeleton for mock responses |
| **Facade** | DirectMCPClient | Simplified interface for MCP tools |

### 3.3 Module Structure

```
backend/
├── app/
│   ├── __init__.py          # Package initialization, version (1.0.0)
│   ├── __main__.py          # Entry point for running as module
│   ├── main.py              # FastAPI application, routes
│   ├── ai.py                # AI service implementation
│   ├── config.py            # Configuration management
│   ├── schemas.py           # Pydantic data models
│   ├── document_parser.py   # File parsing utilities (PDF, DOCX, TXT)
│   ├── jira_agent.py        # Jira Cloud integration
│   ├── mcp_server.py        # MCP protocol server (7 tools)
│   ├── mcp_client.py        # DirectMCPClient for programmatic access
│   ├── mcp_agent_test.py    # MCP server test agent
│   ├── templates/           # Jinja2 HTML templates
│   │   ├── base.html        # Base template with navigation
│   │   ├── index.html       # Home page
│   │   ├── standup.html     # Standup summary page
│   │   ├── stories.html     # User stories page
│   │   ├── tasks.html       # Sprint tasks page
│   │   ├── jira.html        # Jira integration page
│   │   └── partials/        # HTMX partial templates
│   │       ├── standup_result.html
│   │       ├── stories_result.html
│   │       ├── tasks_result.html
│   │       └── error.html
│   └── static/              # CSS, JavaScript assets
│       ├── css/
│       └── js/
├── tests/                   # Comprehensive test suite (11 test files)
│   ├── test_ai.py
│   ├── test_ai_comprehensive.py
│   ├── test_config.py
│   ├── test_document_parser.py
│   ├── test_jira_agent.py
│   ├── test_main_endpoints.py
│   ├── test_mcp_agent.py
│   ├── test_mcp_client.py
│   ├── test_mcp_server.py
│   ├── test_schemas.py
│   └── test_smoke.py
├── requirements.txt         # Python dependencies
├── requirements-prod.txt    # Production dependencies
├── pyproject.toml          # Project configuration
└── Dockerfile              # Container definition
```

---

## 4. Component Design

### 4.1 AI Service (`ai.py`)

The core AI service that handles all LLM interactions.

#### Class: `AIService`

```python
class AIService:
    """Service for AI-powered Scrum assistance."""
    
    def __init__(self, settings: Optional[Settings] = None)
    
    # Client Management
    def _get_client() -> Optional[AsyncOpenAI]
    def _get_model() -> str
    
    # Core AI Methods
    async def _chat_completion(messages, **kwargs) -> str
    async def summarize_standup(entries, sprint_goal) -> StandupSummaryResponse
    async def generate_user_stories(notes, context) -> UserStoriesResponse
    async def suggest_sprint_tasks(stories, capacity, duration) -> SprintTasksResponse
    
    # Text Processing
    def _clean_text(text) -> str
    def _create_short_title(text, max_length) -> str
    def _extract_key_phrase(text) -> str
    
    # Mock Response Generation (for testing without API keys)
    def _mock_response(messages) -> str
    def _generate_standup_mock(user_message) -> str
    def _generate_stories_mock(user_message) -> str
    def _generate_tasks_mock(user_message) -> str
```

#### Provider Selection Logic

```
┌─────────────────┐
│ Check Provider  │
└────────┬────────┘
         │
    ┌────▼────┐
    │ openai? │──Yes──▶ Create AsyncOpenAI Client
    └────┬────┘
         │No
    ┌────▼────┐
    │ azure?  │──Yes──▶ Create AsyncAzureOpenAI Client
    └────┬────┘
         │No
    ┌────▼────┐
    │ mock?   │──Yes──▶ Return None (use intelligent mock responses)
    └─────────┘
```

### 4.2 Configuration (`config.py`)

Centralized configuration using Pydantic Settings.

#### Class: `Settings`

```python
class Settings(BaseSettings):
    # Application
    app_name: str = "AI Sprint Companion"
    debug: bool = False
    
    # AI Provider
    ai_provider: Literal["openai", "azure", "mock"] = "mock"
    
    # OpenAI
    openai_api_key: Optional[str]
    openai_model: str = "gpt-4o-mini"
    openai_base_url: str = "https://api.openai.com/v1"
    
    # Azure OpenAI
    azure_openai_endpoint: Optional[str]
    azure_openai_key: Optional[str]
    azure_openai_deployment: str = "gpt-4o-mini"
    azure_openai_api_version: str = "2024-05-01-preview"
    
    # Jira Integration
    jira_url: Optional[str]
    jira_email: Optional[str]
    jira_api_token: Optional[str]
    jira_project_key: Optional[str]
```

### 4.3 Jira Agent (`jira_agent.py`)

Handles all Jira Cloud API interactions.

#### Class: `JiraAgent`

```python
class JiraAgent:
    """Agent for interacting with Jira API."""
    
    # Properties
    @property is_configured -> bool
    
    # Connection Management
    async def _get_client() -> httpx.AsyncClient
    async def close()
    
    # API Methods
    async def test_connection() -> Dict[str, Any]
    async def get_project() -> Dict[str, Any]
    async def get_issue_types() -> List[Dict]
    async def create_ticket(ticket: JiraTicket) -> JiraCreatedTicket
    async def create_tickets_bulk(tickets: List[JiraTicket]) -> List[JiraCreatedTicket]
    
    # Formatting
    def _format_description(ticket) -> Dict  # Atlassian Document Format
```

#### Data Classes

```python
class JiraIssueType(Enum):
    STORY = "Story"
    TASK = "Task"
    BUG = "Bug"
    EPIC = "Epic"
    SUBTASK = "Sub-task"

@dataclass
class JiraTicket:
    summary: str
    description: str
    issue_type: JiraIssueType = JiraIssueType.STORY
    priority: Optional[str] = None
    labels: Optional[List[str]] = None
    story_points: Optional[int] = None
    acceptance_criteria: Optional[List[str]] = None

@dataclass
class JiraCreatedTicket:
    key: str
    id: str
    url: str
    summary: str
```

### 4.4 MCP Server (`mcp_server.py`)

Model Context Protocol server for AI agent integration.

#### Class: `MCPSprintCompanionServer`

```python
class MCPSprintCompanionServer:
    """MCP Server exposing AI Sprint Companion functionalities."""
    
    def __init__(self)
    def _setup_handlers()
    async def run()
```

#### Available MCP Tools (7 tools)

| Tool | Description | Required Parameters |
|------|-------------|---------------------|
| `summarize_standup` | Summarize team standup notes | `entries` (array) |
| `generate_user_stories` | Generate user stories from notes | `notes` (string) |
| `suggest_sprint_tasks` | Suggest tasks from stories | `user_stories` (array) |
| `create_jira_ticket` | Create a Jira ticket | `summary`, `description` |
| `get_jira_status` | Check Jira configuration | (none) |
| `parse_standup_text` | Parse raw standup text | `text` (string) |
| `health_check` | Check service health | (none) |

### 4.5 MCP Client (`mcp_client.py`)

Direct client for programmatic access to MCP tools.

#### Class: `DirectMCPClient`

```python
class DirectMCPClient:
    """Direct client for AI Sprint Companion services."""
    
    async def summarize_standup(entries, sprint_goal) -> Dict
    async def generate_user_stories(notes, context) -> Dict
    async def suggest_sprint_tasks(user_stories, team_capacity, sprint_duration_days) -> Dict
    async def create_jira_ticket(summary, description, issue_type, ...) -> Dict
    async def get_jira_status() -> Dict
    async def health_check() -> Dict
```

### 4.6 Document Parser (`document_parser.py`)

File parsing utilities for uploading documents.

#### Supported Formats

| Format | Library | Notes |
|--------|---------|-------|
| `.txt` | Built-in | Plain text files |
| `.docx` | python-docx | Microsoft Word documents |
| `.doc` | python-docx | Legacy Word documents |
| `.pdf` | N/A | Text extraction (planned) |

---

## 5. Data Models

### 5.1 Standup Models

```python
class StandupEntry(BaseModel):
    name: str                    # Team member name
    yesterday: str               # What was accomplished
    today: str                   # What is planned
    blockers: Optional[str]      # Any blockers

class StandupSummaryResponse(BaseModel):
    summary: str                 # AI-generated summary
    key_blockers: List[str]      # Highlighted blockers
    action_items: List[str]      # Suggested actions
    suggested_tasks: List[SprintTask]    # Generated tasks
    suggested_stories: List[UserStory]   # Generated stories
```

### 5.2 User Story Models

```python
class UserStory(BaseModel):
    title: str                           # Brief title
    description: str                     # "As a... I want... So that..."
    acceptance_criteria: List[str]       # List of criteria
    story_points: Optional[int]          # 1-21 points

class UserStoriesResponse(BaseModel):
    stories: List[UserStory]             # Generated stories
    raw_insights: Optional[str]          # Additional insights
```

### 5.3 Sprint Task Models

```python
class SprintTask(BaseModel):
    title: str                           # Task title
    description: str                     # Task description
    estimated_hours: Optional[float]     # Time estimate
    priority: Literal["high", "medium", "low"]
    parent_story: Optional[str]          # Related user story

class SprintTasksResponse(BaseModel):
    tasks: List[SprintTask]              # Generated tasks
    total_estimated_hours: Optional[float]
    recommendations: List[str]           # Planning recommendations
```

### 5.4 Jira Models

```python
class JiraConfigStatus(BaseModel):
    configured: bool
    jira_url: Optional[str]
    project_key: Optional[str]
    user_email: Optional[str]

class JiraTicketRequest(BaseModel):
    summary: str
    description: str
    issue_type: str = "Story"
    priority: Optional[str]
    labels: Optional[List[str]]
    story_points: Optional[int]
    acceptance_criteria: Optional[List[str]]

class JiraTicketResponse(BaseModel):
    success: bool
    ticket_key: Optional[str]
    ticket_url: Optional[str]
    error: Optional[str]
```

---

## 6. API Design

### 6.1 REST API Endpoints

#### Health & Info

| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/health` | Service health check | `HealthResponse` |
| GET | `/docs` | OpenAPI documentation | Swagger UI |
| GET | `/redoc` | ReDoc documentation | ReDoc UI |

#### Pages (HTML)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Home page |
| GET | `/standup` | Standup summary page |
| GET | `/stories` | User stories page |
| GET | `/tasks` | Sprint tasks page |
| GET | `/jira` | Jira integration page |

#### Standup API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/standup/summarize` | Summarize standup entries (JSON) |
| POST | `/standup/summarize` | HTMX endpoint with file upload |

#### User Stories API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/stories/generate` | Generate user stories (JSON) |
| POST | `/stories/generate` | HTMX endpoint with file upload |

#### Sprint Tasks API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/tasks/suggest` | Suggest sprint tasks (JSON) |
| POST | `/tasks/suggest` | HTMX endpoint with file upload |

#### Jira API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/jira/status` | Check Jira configuration |
| GET | `/api/jira/test` | Test Jira connection |
| POST | `/api/jira/ticket` | Create single ticket |
| POST | `/api/jira/tickets/bulk` | Create multiple tickets |

### 6.2 Request/Response Examples

#### Standup Summary

**Request:**
```json
POST /api/standup/summarize
{
  "entries": [
    {
      "name": "Alice",
      "yesterday": "Completed user authentication API",
      "today": "Working on dashboard components",
      "blockers": "Waiting for design mockups"
    }
  ],
  "sprint_goal": "Complete MVP"
}
```

**Response:**
```json
{
  "summary": "Team is making progress on authentication and dashboard...",
  "key_blockers": ["Waiting for design mockups from UX team"],
  "action_items": ["Schedule meeting with UX team"],
  "suggested_tasks": [...],
  "suggested_stories": [...]
}
```

---

## 7. AI Integration

### 7.1 Prompt Engineering

Each AI feature uses carefully crafted prompts:

#### Standup Summary Prompt Structure
```
System: You are a Scrum Master assistant...
User: Sprint Goal: {goal}
      Team Updates:
      - {name}: Yesterday: {yesterday}, Today: {today}, Blockers: {blockers}
```

#### User Story Generation Prompt Structure
```
System: You are an Agile coach. Extract user stories from meeting notes using the format:
"As a [role], I want [feature] so that [benefit]"

Respond in JSON format: {...}
```

#### Task Suggestion Prompt Structure
```
System: You are an experienced tech lead...
User: Team Capacity: {capacity} story points
      Sprint Duration: {days} days
      User Stories:
      {stories}
```

### 7.2 Response Parsing

All AI responses are parsed into structured JSON format with validation.

### 7.3 Mock Mode

When `AI_PROVIDER=mock`, the system generates intelligent mock responses based on input content for testing without API keys.

---

## 8. MCP Protocol Integration

### 8.1 Overview

The Model Context Protocol (MCP) enables AI agents (like Claude) to interact with AI Sprint Companion tools programmatically.

### 8.2 MCP Configuration

```json
{
  "mcpServers": {
    "ai-sprint-companion": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "backend"
    }
  }
}
```

### 8.3 MCP Tools Available

1. **summarize_standup** - Summarize team standup notes
2. **generate_user_stories** - Generate stories from meeting notes
3. **suggest_sprint_tasks** - Break down stories into tasks
4. **create_jira_ticket** - Create Jira tickets
5. **get_jira_status** - Check Jira configuration
6. **parse_standup_text** - Parse raw standup text
7. **health_check** - Service health check

### 8.4 Testing MCP Server

```bash
# Run MCP Agent Test
python -m app.mcp_agent_test

# Or use the batch file (Windows)
run_mcp_test.bat
```

---

## 9. External Integrations

### 9.1 Jira Cloud Integration

#### Setup Requirements

1. Create Jira Cloud account (free tier available)
2. Generate API token at https://id.atlassian.com/manage-profile/security/api-tokens
3. Set environment variables:
   - `JIRA_URL`: Your Jira instance URL
   - `JIRA_EMAIL`: Your Jira account email
   - `JIRA_API_TOKEN`: Your API token
   - `JIRA_PROJECT_KEY`: Project key (e.g., "KAN")

#### Supported Operations

- Create Story, Task, Bug, Epic tickets
- Set priority, labels, story points
- Add acceptance criteria
- Bulk ticket creation

### 9.2 Trello Integration (Bootstrap Tool)

A bootstrap tool is available to create a pre-configured Trello board:

```bash
run_trello_bootstrap.bat
```

---

## 10. Security Considerations

### 10.1 API Key Management

- All API keys stored as environment variables
- Never committed to version control
- `.env` file in `.gitignore`

### 10.2 Input Validation

- Pydantic models validate all inputs
- Length limits on text fields
- Type checking enforced

### 10.3 External API Security

- HTTPS for all external calls
- API tokens for Jira authentication
- Rate limiting considerations

---

## 11. Testing Strategy

### 11.1 Test Coverage

| Test File | Coverage Area |
|-----------|---------------|
| `test_ai.py` | AI service basic tests |
| `test_ai_comprehensive.py` | AI service comprehensive tests |
| `test_config.py` | Configuration management |
| `test_document_parser.py` | File parsing |
| `test_jira_agent.py` | Jira integration |
| `test_main_endpoints.py` | API endpoints |
| `test_mcp_agent.py` | MCP agent tests |
| `test_mcp_client.py` | MCP client tests |
| `test_mcp_server.py` | MCP server tests |
| `test_schemas.py` | Data model validation |
| `test_smoke.py` | Smoke tests |

### 11.2 Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=app

# Specific test file
pytest tests/test_ai_comprehensive.py -v

# MCP Agent Test (interactive)
python -m app.mcp_agent_test
```

---

## 12. Deployment

### 12.1 Render.com Deployment

The application is configured for Render.com free tier deployment:

```yaml
# render.yaml
services:
  - type: web
    name: ai-sprint-companion
    runtime: python
    plan: free
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

### 12.2 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_PROVIDER` | Yes | `mock`, `openai`, or `azure` |
| `OPENAI_API_KEY` | If OpenAI | OpenAI API key |
| `JIRA_URL` | If Jira | Jira instance URL |
| `JIRA_EMAIL` | If Jira | Jira account email |
| `JIRA_API_TOKEN` | If Jira | Jira API token |
| `JIRA_PROJECT_KEY` | If Jira | Project key |

### 12.3 Local Development

```bash
# Windows
run.bat

# Unix/Mac
./run.sh

# MCP Server
run_mcp_server.bat  # Windows
./run_mcp_server.sh # Unix/Mac
```

---

## 13. Future Enhancements

### 13.1 Planned Features

- [ ] Sprint retrospective analysis
- [ ] Team velocity tracking
- [ ] Integration with Azure DevOps
- [ ] Slack/Teams notifications
- [ ] Custom prompt templates
- [ ] Multi-language support

### 13.2 Technical Improvements

- [ ] Database persistence (PostgreSQL)
- [ ] User authentication
- [ ] Rate limiting
- [ ] Caching layer
- [ ] WebSocket support for real-time updates

---

## Appendix A: File Structure

```
Capstone AI Project/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── ai.py
│   │   ├── config.py
│   │   ├── document_parser.py
│   │   ├── jira_agent.py
│   │   ├── main.py
│   │   ├── mcp_agent_test.py
│   │   ├── mcp_client.py
│   │   ├── mcp_server.py
│   │   ├── schemas.py
│   │   ├── static/
│   │   └── templates/
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── docs/
├── samples/
├── tools/
├── render.yaml
├── mcp_config.json
├── run.bat
├── run_mcp_server.bat
└── run_mcp_test.bat
```

## Appendix B: API Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Health check |
| `/api/standup/summarize` | POST | Summarize standup |
| `/api/stories/generate` | POST | Generate user stories |
| `/api/tasks/suggest` | POST | Suggest sprint tasks |
| `/api/jira/status` | GET | Jira config status |
| `/api/jira/ticket` | POST | Create Jira ticket |
| `/api/jira/tickets/bulk` | POST | Bulk create tickets |
