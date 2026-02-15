# AI Sprint Companion

An AI-assisted Scrum helper that summarizes standups, drafts user stories from meeting notes, and suggests sprint tasks. Built as a web app using FastAPI + Jinja (HTMX-ready) with CI/CD and a rubric-aligned documentation set.

## 🚀 Quick Start

### One-Command Run (Recommended)

**Windows:**
```bash
run.bat
```

**Linux/macOS:**
```bash
chmod +x run.sh
./run.sh
```

The script will automatically:
- Check for virtual environment
- Start the application at http://127.0.0.1:8000

### Manual Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the application
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 🌐 Access the Application

Once running, access:
- **Web Interface:** http://127.0.0.1:8000
- **API Documentation (Swagger):** http://127.0.0.1:8000/docs
- **API Documentation (ReDoc):** http://127.0.0.1:8000/redoc

## ✨ Features

- **📋 Standup Summaries** - Automatically summarize daily standup notes into actionable insights
- **📝 User Story Generator** - Transform meeting notes into well-formatted user stories with acceptance criteria
- **✅ Sprint Task Suggestions** - Break down user stories into actionable tasks with time estimates
- **📁 Document Upload** - Support for TXT, PDF, DOC, DOCX file uploads
- **🔌 REST API** - Full API access for integration with other tools
- **🎫 Jira Integration** - Create Jira tickets directly from generated stories/tasks

## 📁 Sample Files for Testing

The `samples/` folder contains pre-made test files for each feature:

| File | Use With | Description |
|------|----------|-------------|
| `meeting_notes_sample.txt` | User Stories page | Product planning meeting notes (~1,500 words) |
| `standup_notes_sample.txt` | Standup Summary page | Daily standup entries from 24 team members (~1,400 words) |
| `user_stories_sample.txt` | Sprint Tasks page | 58 user stories organized by category (~1,600 words) |

### How to Use Sample Files

1. Start the application using `run.bat`
2. Navigate to the desired page (Standup, Stories, or Tasks)
3. Click "Upload" and select the corresponding sample file
4. The file content will appear in the textarea
5. Click the action button to generate AI-powered results

## 📁 Project Structure

```
ai-sprint-companion/
├── run.bat                 # Windows run script
├── run.sh                  # Linux/macOS run script
├── Readme.MD               # This file
├── backend/
│   ├── app/
│   │   ├── main.py         # FastAPI application entry point
│   │   ├── ai.py           # AI service integration
│   │   ├── config.py       # Configuration settings
│   │   ├── schemas.py      # Pydantic models
│   │   ├── document_parser.py  # File parsing utilities
│   │   ├── jira_agent.py   # Jira integration
│   │   ├── templates/      # Jinja2 HTML templates
│   │   └── static/         # CSS, JS assets
│   ├── tests/              # Test files
│   ├── requirements.txt    # Python dependencies
│   ├── Dockerfile          # Docker configuration
│   └── pyproject.toml      # Project metadata
├── samples/                # Sample files for testing
│   ├── meeting_notes_sample.txt
│   ├── standup_notes_sample.txt
│   └── user_stories_sample.txt
├── docs/                   # Documentation
│   ├── DESIGN_TESTING.md
│   ├── PRODUCT_BACKLOG.md
│   ├── SPRINT_PLAN.md
│   ├── DEMO_SCRIPT.md
│   ├── PRESENTATION_CHECKLIST.md
│   └── TASKBOARD_LINK.md
├── scripts/                # Utility scripts
│   └── create_repo_and_push.sh
├── mcp_config.json         # MCP server configuration
├── run_mcp_server.bat      # Windows MCP server script
└── run_mcp_server.sh       # Linux/macOS MCP server script
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root or set environment variables:

#### AI Provider (Optional - defaults to mock mode)

**OpenAI:**
```bash
AI_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1
```

**Azure OpenAI:**
```bash
AI_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://YOUR-RESOURCE.openai.azure.com
AZURE_OPENAI_KEY=...
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_API_VERSION=2024-05-01-preview
```

#### Jira Integration (Optional)
```bash
JIRA_URL=https://your-domain.atlassian.net
JIRA_EMAIL=your-email@example.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
```

## 🐳 Docker Deployment

```bash
cd backend
docker build -t ai-sprint-companion .
docker run -p 8000:8000 ai-sprint-companion
```

## ☁️ Cloud Deployment (Render)

1. Create a **Web Service** from this repo
2. Runtime: Python 3.11
3. Build Command: `pip install -r backend/requirements.txt`
4. Start Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT --app-dir backend`
5. Add environment variables from configuration section above

## 🧪 Running Tests

```bash
cd backend
pytest tests/ -v
```

## 📚 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Home page |
| `/standup` | GET | Standup summary page |
| `/standup/summarize` | POST | Generate standup summary |
| `/stories` | GET | User story generator page |
| `/stories/generate` | POST | Generate user stories |
| `/tasks` | GET | Task suggestions page |
| `/tasks/suggest` | POST | Suggest sprint tasks |
| `/health` | GET | Health check endpoint |
| `/docs` | GET | Swagger API documentation |

## 🛠️ Automation Scripts

### Create GitHub Repo & Push
```bash
export REPO_NAME=ai-sprint-companion
export VISIBILITY=private
export GITHUB_TOKEN=ghp_...
./scripts/create_repo_and_push.sh
```

### Bootstrap Trello Board
```bash
export TRELLO_KEY=...
export TRELLO_TOKEN=...
export TRELLO_BOARD_NAME="AI Sprint Companion"
python tools/bootstrap_trello.py
```

## 📋 Capstone Deliverables

| Deliverable | Location |
|-------------|----------|
| Source Code | This repository |
| Deployed App | [Deploy Link] |
| Agile Task Board | `docs/TASKBOARD_LINK.md` |
| Design & Testing Doc | `docs/DESIGN_TESTING.md` |
| Demo Script | `docs/DEMO_SCRIPT.md` |
| Presentation Checklist | `docs/PRESENTATION_CHECKLIST.md` |

## 📄 License

Quantic Capstone License - See LICENSE file for details.

---

**Built with ❤️ using FastAPI, HTMX, and AI**

## 🤖 MCP Server (AI Agent Integration)

The AI Sprint Companion includes a **Model Context Protocol (MCP) Server** that allows AI agents (like Claude Desktop, custom LLM applications, etc.) to connect and use the Scrum assistance tools programmatically.

### Available MCP Tools

| Tool | Description |
|------|-------------|
| `summarize_standup` | Summarize team standup notes into actionable insights |
| `generate_user_stories` | Generate user stories from meeting notes |
| `suggest_sprint_tasks` | Suggest sprint tasks from user stories |
| `create_jira_ticket` | Create a Jira ticket (Story, Task, Bug) |
| `get_jira_status` | Check Jira configuration status |
| `parse_standup_text` | Parse raw standup text into structured entries |
| `health_check` | Check service health status |

### Running the MCP Server

**Windows:**
```bash
run_mcp_server.bat
```

**Linux/macOS:**
```bash
chmod +x run_mcp_server.sh
./run_mcp_server.sh
```

**Or directly with Python:**
```bash
cd backend
python -m app.mcp_server
```

### Configuring Claude Desktop

Add this to your Claude Desktop configuration file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "ai-sprint-companion": {
      "command": "python",
      "args": ["-m", "app.mcp_server"],
      "cwd": "C:/path/to/ai-sprint-companion/backend",
      "env": {
        "OPENAI_API_KEY": "your-openai-key",
        "JIRA_URL": "https://your-domain.atlassian.net",
        "JIRA_EMAIL": "your-email@example.com",
        "JIRA_API_TOKEN": "your-jira-token",
        "JIRA_PROJECT_KEY": "PROJ"
      }
    }
  }
}
```

### Using the MCP Client Programmatically

```python
import asyncio
from app.mcp_client import DirectMCPClient

async def main():
    client = DirectMCPClient()
    
    # Summarize standup
    result = await client.summarize_standup([
        {
            "name": "Alice",
            "yesterday": "Completed user authentication API",
            "today": "Working on dashboard components",
            "blockers": "Waiting for design mockups"
        },
        {
            "name": "Bob", 
            "yesterday": "Fixed critical login bug",
            "today": "Code review",
            "blockers": None
        }
    ], sprint_goal="Complete MVP")
    
    print(f"Summary: {result['summary']}")
    print(f"Blockers: {result['key_blockers']}")
    
    # Generate user stories
    stories = await client.generate_user_stories(
        "Users need password reset functionality. Admins need to manage users."
    )
    for story in stories['stories']:
        print(f"Story: {story['title']}")
    
    # Suggest tasks
    tasks = await client.suggest_sprint_tasks([
        "As a user, I want to reset my password"
    ])
    for task in tasks['tasks']:
        print(f"Task: {task['title']} ({task['estimated_hours']}h)")

asyncio.run(main())
```

### MCP Tool Examples

**Summarize Standup:**
```json
{
  "tool": "summarize_standup",
  "arguments": {
    "entries": [
      {
        "name": "Alice",
        "yesterday": "Completed API endpoints",
        "today": "Writing tests",
        "blockers": "Need test database"
      }
    ],
    "sprint_goal": "Release v1.0"
  }
}
```

**Generate User Stories:**
```json
{
  "tool": "generate_user_stories",
  "arguments": {
    "notes": "Meeting discussed: users need to reset passwords, admins need user management, system needs audit logging",
    "context": "Enterprise SaaS application"
  }
}
```

**Suggest Sprint Tasks:**
```json
{
  "tool": "suggest_sprint_tasks",
  "arguments": {
    "user_stories": [
      "As a user, I want to reset my password so I can regain access",
      "As an admin, I want to view all users so I can manage accounts"
    ],
    "team_capacity": 40,
    "sprint_duration_days": 14
  }
}
```

**Create Jira Ticket:**
```json
{
  "tool": "create_jira_ticket",
  "arguments": {
    "summary": "Implement password reset feature",
    "description": "As a user, I want to reset my password so I can regain access to my account.",
    "issue_type": "Story",
    "priority": "High",
    "story_points": 5,
    "acceptance_criteria": [
      "User can request password reset via email",
      "Reset link expires after 24 hours",
      "User can set new password"
    ]
  }
}
```
