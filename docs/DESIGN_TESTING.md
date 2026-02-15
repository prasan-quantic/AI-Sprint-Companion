# Design & Testing Document

## AI Sprint Companion

**Version:** 1.1.0  
**Date:** February 8, 2026

### Project Overview

AI Sprint Companion is an AI-assisted Scrum helper application that helps agile teams by:
- Summarizing daily standup notes into actionable insights
- Generating user stories from meeting notes
- Suggesting sprint tasks based on user stories
- Creating Jira tickets from generated artifacts
- Providing MCP protocol support for AI agent integration

---

## 1. System Architecture

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Browser   │  │  API Client │  │  MCP Agent  │              │
│  │   (HTMX)    │  │   (REST)    │  │  (Claude)   │              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
          ▼                ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Application                    │    │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │    │
│  │  │  Routes  │  │ Schemas  │  │    AI    │  │   MCP    │ │    │
│  │  │  (API)   │  │(Pydantic)│  │ Service  │  │  Server  │ │    │
│  │  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
          │                │
          ▼                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      External Services                           │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  OpenAI API     │  │  Azure OpenAI   │  │   Jira Cloud    │  │
│  │  (GPT-4o-mini)  │  │   Service       │  │   REST API      │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 Component Diagram

```
┌─────────────────────────────────────────────┐
│              main.py (FastAPI)              │
│  - Health endpoints                         │
│  - Page routes (HTML)                       │
│  - API routes (JSON)                        │
│  - HTMX endpoints (HTML partials)           │
│  - Jira integration endpoints               │
└──────────────────┬──────────────────────────┘
                   │
    ┌──────────────┼──────────────┬───────────────┐
    ▼              ▼              ▼               ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│schemas.py│  │  ai.py   │  │jira_agent│  │mcp_server│
│- DTOs    │  │- AIServ. │  │- JiraAgt │  │- MCP API │
│- Valid.  │  │- LLM API │  │- Tickets │  │- 7 Tools │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
                   │              │
                   ▼              ▼
             ┌──────────┐  ┌──────────┐
             │config.py │  │ External │
             │- Settings│  │   APIs   │
             │- Env Vars│  │          │
             └──────────┘  └──────────┘
```

### 1.3 Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| Backend Framework | FastAPI | High-performance async API |
| Templating | Jinja2 | Server-side HTML rendering |
| Frontend Enhancement | HTMX | Dynamic updates without JS framework |
| Validation | Pydantic | Request/response validation |
| AI Integration | OpenAI SDK | LLM communication |
| HTTP Client | HTTPX | Async HTTP for Jira API |
| Protocol | MCP SDK | AI agent integration |
| Testing | Pytest | Unit and integration tests |
| CI/CD | GitHub Actions | Automated testing and deployment |
| Deployment | Render.com | Cloud hosting (free tier) |

---

## 2. Data Flow

### 2.1 Standup Summary Flow

```
User Input          API Processing           AI Service            Response
    │                    │                       │                    │
    │  POST /api/        │                       │                    │
    │  standup/summarize │                       │                    │
    ├───────────────────►│                       │                    │
    │                    │  Validate request     │                    │
    │                    │  (Pydantic)           │                    │
    │                    ├──────────────────────►│                    │
    │                    │                       │  Build prompt      │
    │                    │                       │  Call LLM API      │
    │                    │                       │  Parse response    │
    │                    │◄──────────────────────┤                    │
    │                    │  Return structured    │                    │
    │◄───────────────────┤  summary + tasks      │                    │
    │                    │  + stories            │                    │
```

### 2.2 MCP Agent Flow

```
AI Agent            MCP Server              DirectMCPClient         Services
    │                    │                       │                    │
    │  Tool Call         │                       │                    │
    │  (summarize_       │                       │                    │
    │   standup)         │                       │                    │
    ├───────────────────►│                       │                    │
    │                    │  Parse tool request   │                    │
    │                    ├──────────────────────►│                    │
    │                    │                       │  Call AIService    │
    │                    │                       ├───────────────────►│
    │                    │                       │◄───────────────────┤
    │                    │◄──────────────────────┤  Return result     │
    │◄───────────────────┤  JSON response        │                    │
```

### 2.3 Request/Response Models

**StandupSummaryRequest:**
```json
{
  "entries": [
    {
      "name": "string",
      "yesterday": "string",
      "today": "string",
      "blockers": "string | null"
    }
  ],
  "sprint_goal": "string | null"
}
```

**StandupSummaryResponse:**
```json
{
  "summary": "string",
  "key_blockers": ["string"],
  "action_items": ["string"],
  "suggested_tasks": [
    {
      "title": "string",
      "description": "string",
      "estimated_hours": 4.0,
      "priority": "high|medium|low",
      "parent_story": "string | null"
    }
  ],
  "suggested_stories": [
    {
      "title": "string",
      "description": "string",
      "acceptance_criteria": ["string"],
      "story_points": 5
    }
  ]
}
```

---

## 3. API Design

### 3.1 Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Service health check |
| GET | `/` | Home page |
| GET | `/standup` | Standup summary page |
| GET | `/stories` | User stories page |
| GET | `/tasks` | Sprint tasks page |
| GET | `/jira` | Jira integration page |
| POST | `/api/standup/summarize` | Summarize standup entries |
| POST | `/api/stories/generate` | Generate user stories |
| POST | `/api/tasks/suggest` | Suggest sprint tasks |
| GET | `/api/jira/status` | Check Jira configuration |
| GET | `/api/jira/test` | Test Jira connection |
| POST | `/api/jira/ticket` | Create single Jira ticket |
| POST | `/api/jira/tickets/bulk` | Create multiple Jira tickets |

### 3.2 MCP Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `health_check` | Check service health | (none) |
| `summarize_standup` | Summarize standup notes | `entries`, `sprint_goal` |
| `generate_user_stories` | Generate user stories | `notes`, `context` |
| `suggest_sprint_tasks` | Suggest sprint tasks | `user_stories`, `team_capacity` |
| `create_jira_ticket` | Create Jira ticket | `summary`, `description`, `issue_type` |
| `get_jira_status` | Check Jira config | (none) |
| `parse_standup_text` | Parse raw standup text | `text` |

---

## 4. Testing Strategy

### 4.1 Test Files

| Test File | Purpose | Tests |
|-----------|---------|-------|
| `test_smoke.py` | Basic smoke tests | Health check, imports |
| `test_config.py` | Configuration tests | Settings loading, defaults |
| `test_schemas.py` | Schema validation | Pydantic model validation |
| `test_ai.py` | AI service tests | Basic AI functionality |
| `test_ai_comprehensive.py` | Comprehensive AI tests | All AI methods, edge cases |
| `test_main_endpoints.py` | API endpoint tests | All REST endpoints |
| `test_jira_agent.py` | Jira integration tests | Jira API interactions |
| `test_document_parser.py` | Document parsing tests | File upload handling |
| `test_mcp_server.py` | MCP server tests | MCP protocol handling |
| `test_mcp_client.py` | MCP client tests | DirectMCPClient methods |
| `test_mcp_agent.py` | MCP agent tests | End-to-end MCP testing |

### 4.2 Test Categories

#### Unit Tests
- Schema validation
- Configuration loading
- Text processing utilities
- Mock response generation

#### Integration Tests
- API endpoint responses
- AI service with mock provider
- Jira agent with mock responses
- MCP tool execution

#### End-to-End Tests
- Complete workflows (notes → stories → tasks)
- MCP agent test suite
- File upload processing

### 4.3 Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_ai_comprehensive.py -v

# Run with coverage
pytest --cov=app --cov-report=html

# Run MCP agent tests (interactive)
python -m app.mcp_agent_test

# Run MCP tests via batch file (Windows)
run_mcp_test.bat
```

### 4.4 MCP Agent Test Suite

The MCP Agent Test runs 7 comprehensive tests:

| Test | Description |
|------|-------------|
| Health Check | Verify service health and version |
| Summarize Standup | Test standup summarization with sample data |
| Generate User Stories | Test story generation from meeting notes |
| Suggest Sprint Tasks | Test task breakdown from stories |
| Jira Status | Verify Jira configuration status |
| Sample File Test | Test with actual sample data files |
| End-to-End Workflow | Complete flow: notes → stories → tasks → standup |

**Sample Output:**
```
[2026-02-08 21:14:47] ✅ PASS: health_check - Service healthy, version: 1.0.0
[2026-02-08 21:14:49] ✅ PASS: summarize_standup - Generated 3 tasks, 3 stories
[2026-02-08 21:14:49] ✅ PASS: generate_user_stories - Generated 8 user stories
[2026-02-08 21:14:49] ✅ PASS: suggest_sprint_tasks - Generated 9 tasks, 33 hours
[2026-02-08 21:14:49] ✅ PASS: get_jira_status - Jira configured
[2026-02-08 21:14:49] ✅ PASS: sample_file_test - 15 tasks from 5 stories
[2026-02-08 21:14:49] ✅ PASS: end_to_end_workflow - Complete workflow success
============================================================
Total Tests: 7 | Passed: 7 | Failed: 0 | Duration: 1.20s
🎉 ALL TESTS PASSED! MCP Server is working correctly.
```

### 4.5 Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| AI Service | 90% | ✅ |
| API Endpoints | 95% | ✅ |
| Schemas | 100% | ✅ |
| Configuration | 100% | ✅ |
| Jira Agent | 85% | ✅ |
| MCP Server | 90% | ✅ |
| MCP Client | 90% | ✅ |

---

## 5. Quality Assurance

### 5.1 Code Quality Tools

| Tool | Purpose |
|------|---------|
| Ruff | Linting and formatting |
| Pytest | Testing framework |
| Pydantic | Runtime type validation |
| Type hints | Static type checking |

### 5.2 CI/CD Pipeline

```yaml
# GitHub Actions workflow
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - run: pip install -r requirements.txt
      - run: pytest --cov=app
      - run: ruff check app/
```

### 5.3 Pre-Deployment Checklist

- [ ] All tests passing
- [ ] Linting passes
- [ ] Environment variables documented
- [ ] API documentation updated
- [ ] MCP tools tested
- [ ] Sample files working

---

## 6. Deployment Configuration

### 6.1 Render.com Settings

| Setting | Value |
|---------|-------|
| Runtime | Python 3.11 |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Root Directory | `backend` |
| Plan | Free |

### 6.2 Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AI_PROVIDER` | Yes | `mock`, `openai`, or `azure` |
| `OPENAI_API_KEY` | If OpenAI | OpenAI API key |
| `OPENAI_MODEL` | No | Model name (default: gpt-4o-mini) |
| `JIRA_URL` | If Jira | Jira instance URL |
| `JIRA_EMAIL` | If Jira | Account email |
| `JIRA_API_TOKEN` | If Jira | API token |
| `JIRA_PROJECT_KEY` | If Jira | Project key |

---

## 7. Troubleshooting

### 7.1 Common Issues

| Issue | Solution |
|-------|----------|
| "MCP SDK not installed" | Run `pip install mcp` |
| "Could not find platform independent libraries" | Clear `PYTHONHOME` environment variable |
| "Jira not configured" | Set all JIRA_* environment variables |
| Tests failing with AI errors | Set `AI_PROVIDER=mock` |

### 7.2 Debug Commands

```bash
# Check Python environment
python --version
pip list | grep -E "fastapi|openai|mcp"

# Test health endpoint
curl http://localhost:8000/health

# Run with debug logging
DEBUG=true python -m uvicorn app.main:app --reload

# Test MCP server directly
python -m app.mcp_agent_test
```
