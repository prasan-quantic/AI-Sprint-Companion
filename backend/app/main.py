"""Main FastAPI application for AI Sprint Companion."""
from fastapi import FastAPI, Request, Form, UploadFile, File
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional

from . import __version__
from .ai import get_ai_service
from .config import get_settings
from .document_parser import extract_text_from_file
from .jira_agent import (
    get_jira_agent,
    JiraAgentError,
    JiraTicket,
    JiraIssueType,
)
from .schemas import (
    HealthResponse,
    MeetingNotesRequest,
    SprintTaskRequest,
    StandupEntry,
    StandupSummaryRequest,
    StandupSummaryResponse,
    UserStoriesResponse,
    SprintTasksResponse,
    JiraConfigStatus,
    JiraTicketRequest,
    JiraTicketResponse,
    JiraBulkCreateRequest,
    JiraBulkCreateResponse,
)

# Initialize FastAPI app
app = FastAPI(
    title="AI Sprint Companion",
    description="An AI-assisted Scrum helper that summarizes standups, drafts user stories, and suggests sprint tasks.",
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")


# ============================================================================
# Health & Info Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check service health and configuration."""
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=__version__,
        ai_provider=settings.ai_provider,
    )


@app.get("/", response_class=HTMLResponse, tags=["Pages"])
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("index.html", {"request": request})


# ============================================================================
# Standup Summary Endpoints
# ============================================================================

@app.post("/api/standup/summarize", response_model=StandupSummaryResponse, tags=["Standup"])
async def summarize_standup(payload: StandupSummaryRequest):
    """Summarize standup entries into actionable insights."""
    ai_service = get_ai_service()
    return await ai_service.summarize_standup(
        entries=payload.entries,
        sprint_goal=payload.sprint_goal,
    )


@app.get("/standup", response_class=HTMLResponse, tags=["Pages"])
async def standup_page(request: Request):
    """Render the standup summary page."""
    return templates.TemplateResponse("standup.html", {"request": request})


@app.post("/standup/summarize", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_summarize_standup(
    request: Request,
    entries_text: str = Form(""),
    sprint_goal: str = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """HTMX endpoint to summarize standup (form submission with file upload)."""
    combined_text = ""

    # Priority: Use textarea content first (it may contain file content loaded by JS for .txt files)
    if entries_text.strip():
        combined_text = entries_text.strip()
        print(f"[Standup] Using textarea content: {len(combined_text)} chars")
    # If textarea is empty but file is uploaded, extract from file (for PDF, DOC, DOCX)
    elif file and file.filename:
        content = await file.read()
        await file.seek(0)
        if content and len(content) > 0:
            print(f"[Standup] File received: {file.filename}, size: {len(content)} bytes")
            file_text = await extract_text_from_file(file) or ""
            print(f"[Standup] Extracted text length: {len(file_text)}")
            if file_text.strip():
                combined_text = file_text.strip()
                print(f"[Standup] Using extracted file content: {len(combined_text)} chars")

    if not combined_text:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": "Please enter standup notes or upload a file."},
        )

    # Parse entries from text (simple format: Name: yesterday | today | blockers)
    entries = []
    for line in combined_text.strip().split("\n"):
        if ":" in line:
            parts = line.split(":", 1)
            name = parts[0].strip()
            details = parts[1].split("|") if "|" in parts[1] else [parts[1], "", ""]
            entries.append(StandupEntry(
                name=name,
                yesterday=details[0].strip() if len(details) > 0 else "",
                today=details[1].strip() if len(details) > 1 else "",
                blockers=details[2].strip() if len(details) > 2 else None,
            ))

    if not entries:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": "No valid standup entries found. Please use the format: Name: yesterday task | today task | blockers"},
        )

    ai_service = get_ai_service()
    result = await ai_service.summarize_standup(entries, sprint_goal or None)

    # Convert Pydantic models to dictionaries for JSON serialization in templates
    result_dict = {
        "summary": result.summary,
        "key_blockers": result.key_blockers,
        "action_items": result.action_items,
        "suggested_tasks": [task.model_dump() for task in result.suggested_tasks] if result.suggested_tasks else [],
        "suggested_stories": [story.model_dump() for story in result.suggested_stories] if result.suggested_stories else [],
    }

    return templates.TemplateResponse(
        "partials/standup_result.html",
        {"request": request, "result": result_dict},
    )


# ============================================================================
# User Story Endpoints
# ============================================================================

@app.post("/api/stories/generate", response_model=UserStoriesResponse, tags=["User Stories"])
async def generate_user_stories(payload: MeetingNotesRequest):
    """Generate user stories from meeting notes."""
    ai_service = get_ai_service()
    return await ai_service.generate_user_stories(
        notes=payload.notes,
        context=payload.context,
    )


@app.get("/stories", response_class=HTMLResponse, tags=["Pages"])
async def stories_page(request: Request):
    """Render the user stories page."""
    return templates.TemplateResponse("stories.html", {"request": request})


@app.post("/stories/generate", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_generate_stories(
    request: Request,
    notes: str = Form(""),
    context: str = Form(None),
    file: Optional[UploadFile] = File(None),
):
    """HTMX endpoint to generate user stories (form submission with file upload)."""
    combined_text = ""

    # Priority: Use textarea content first (it may contain file content loaded by JS for .txt files)
    if notes.strip():
        combined_text = notes.strip()
        print(f"[Stories] Using textarea content: {len(combined_text)} chars")
    # If textarea is empty but file is uploaded, extract from file (for PDF, DOC, DOCX)
    elif file and file.filename:
        content = await file.read()
        await file.seek(0)
        if content and len(content) > 0:
            print(f"[Stories] File received: {file.filename}, size: {len(content)} bytes")
            file_text = await extract_text_from_file(file) or ""
            print(f"[Stories] Extracted text length: {len(file_text)}")
            if file_text.strip():
                combined_text = file_text.strip()
                print(f"[Stories] Using extracted file content: {len(combined_text)} chars")

    if len(combined_text) < 10:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": "Please provide more detailed meeting notes (at least 10 characters) or upload a document."},
        )

    ai_service = get_ai_service()
    result = await ai_service.generate_user_stories(combined_text, context or None)

    return templates.TemplateResponse(
        "partials/stories_result.html",
        {"request": request, "result": result},
    )


# ============================================================================
# Sprint Task Endpoints
# ============================================================================

@app.post("/api/tasks/suggest", response_model=SprintTasksResponse, tags=["Sprint Tasks"])
async def suggest_sprint_tasks(payload: SprintTaskRequest):
    """Suggest sprint tasks based on user stories."""
    ai_service = get_ai_service()
    return await ai_service.suggest_sprint_tasks(
        user_stories=payload.user_stories,
        team_capacity=payload.team_capacity,
        sprint_duration_days=payload.sprint_duration_days,
    )


@app.get("/tasks", response_class=HTMLResponse, tags=["Pages"])
async def tasks_page(request: Request):
    """Render the sprint tasks page."""
    return templates.TemplateResponse("tasks.html", {"request": request})


@app.post("/tasks/suggest", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_suggest_tasks(
    request: Request,
    user_stories: str = Form(""),
    team_capacity: int = Form(None),
    sprint_duration: int = Form(14),
    file: Optional[UploadFile] = File(None),
):
    """HTMX endpoint to suggest sprint tasks (form submission with file upload)."""
    combined_text = ""

    # Priority: Use textarea content first (it may contain file content loaded by JS for .txt files)
    if user_stories.strip():
        combined_text = user_stories.strip()
        print(f"[Tasks] Using textarea content: {len(combined_text)} chars")
    # If textarea is empty but file is uploaded, extract from file (for PDF, DOC, DOCX)
    elif file and file.filename:
        content = await file.read()
        await file.seek(0)
        if content and len(content) > 0:
            print(f"[Tasks] File received: {file.filename}, size: {len(content)} bytes")
            file_text = await extract_text_from_file(file) or ""
            print(f"[Tasks] Extracted text length: {len(file_text)}")
            if file_text.strip():
                combined_text = file_text.strip()
                print(f"[Tasks] Using extracted file content: {len(combined_text)} chars")

    stories = [s.strip() for s in combined_text.split("\n") if s.strip()]

    if not stories:
        return templates.TemplateResponse(
            "partials/error.html",
            {"request": request, "message": "Please provide at least one user story or upload a document containing user stories."},
        )

    ai_service = get_ai_service()
    result = await ai_service.suggest_sprint_tasks(
        user_stories=stories,
        team_capacity=team_capacity,
        sprint_duration_days=sprint_duration,
    )

    return templates.TemplateResponse(
        "partials/tasks_result.html",
        {"request": request, "result": result},
    )


# ============================================================================
# Jira Integration Endpoints
# ============================================================================

@app.get("/api/jira/status", response_model=JiraConfigStatus, tags=["Jira"])
async def jira_status():
    """Check Jira configuration status."""
    agent = get_jira_agent()
    settings = get_settings()

    status = JiraConfigStatus(
        configured=agent.is_configured,
        jira_url=settings.jira_url,
        project_key=settings.jira_project_key,
        user_email=settings.jira_email if agent.is_configured else None,
    )

    return status


@app.get("/api/jira/test", tags=["Jira"])
async def jira_test_connection():
    """Test Jira connection and return user info."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return {
            "success": False,
            "error": "Jira is not configured. Please set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY."
        }

    try:
        user_info = await agent.test_connection()
        project_info = await agent.get_project()
        return {
            "success": True,
            "user": {
                "displayName": user_info.get("displayName"),
                "emailAddress": user_info.get("emailAddress"),
            },
            "project": {
                "key": project_info.get("key"),
                "name": project_info.get("name"),
            }
        }
    except JiraAgentError as e:
        return {"success": False, "error": str(e)}
    finally:
        await agent.close()


@app.post("/api/jira/ticket", response_model=JiraTicketResponse, tags=["Jira"])
async def create_jira_ticket(request: JiraTicketRequest):
    """Create a single Jira ticket."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return JiraTicketResponse(
            success=False,
            error="Jira is not configured. Please set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN, and JIRA_PROJECT_KEY."
        )

    try:
        # Convert request to JiraTicket
        issue_type_map = {
            "Story": JiraIssueType.STORY,
            "Task": JiraIssueType.TASK,
            "Bug": JiraIssueType.BUG,
        }

        ticket = JiraTicket(
            summary=request.summary,
            description=request.description,
            issue_type=issue_type_map.get(request.issue_type, JiraIssueType.TASK),
            priority=request.priority,
            labels=request.labels or ["ai-generated"],
            acceptance_criteria=request.acceptance_criteria,
        )

        result = await agent.create_ticket(ticket)

        return JiraTicketResponse(
            success=True,
            key=result.key,
            url=result.url,
            summary=result.summary,
        )
    except JiraAgentError as e:
        return JiraTicketResponse(success=False, error=str(e))
    finally:
        await agent.close()


@app.post("/api/jira/tickets/bulk", response_model=JiraBulkCreateResponse, tags=["Jira"])
async def create_jira_tickets_bulk(request: JiraBulkCreateRequest):
    """Create multiple Jira tickets at once."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return JiraBulkCreateResponse(
            success=False,
            failed=[JiraTicketResponse(success=False, error="Jira is not configured")]
        )

    created = []
    failed = []

    try:
        issue_type_map = {
            "Story": JiraIssueType.STORY,
            "Task": JiraIssueType.TASK,
            "Bug": JiraIssueType.BUG,
        }

        for req in request.tickets:
            try:
                ticket = JiraTicket(
                    summary=req.summary,
                    description=req.description,
                    issue_type=issue_type_map.get(req.issue_type, JiraIssueType.TASK),
                    priority=req.priority,
                    labels=req.labels or ["ai-generated"],
                    acceptance_criteria=req.acceptance_criteria,
                )

                result = await agent.create_ticket(ticket)
                created.append(JiraTicketResponse(
                    success=True,
                    key=result.key,
                    url=result.url,
                    summary=result.summary,
                ))
            except JiraAgentError as e:
                failed.append(JiraTicketResponse(
                    success=False,
                    summary=req.summary,
                    error=str(e),
                ))

        return JiraBulkCreateResponse(
            success=len(failed) == 0,
            created=created,
            failed=failed,
            total_created=len(created),
            total_failed=len(failed),
        )
    finally:
        await agent.close()


@app.get("/jira", response_class=HTMLResponse, tags=["Pages"])
async def jira_page(request: Request):
    """Render the Jira integration page."""
    agent = get_jira_agent()
    settings = get_settings()
    return templates.TemplateResponse("jira.html", {
        "request": request,
        "jira_configured": agent.is_configured,
        "project_key": settings.jira_project_key,
        "jira_url": settings.jira_url,
    })


@app.post("/jira/create", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_jira_ticket(
    request: Request,
    summary: str = Form(...),
    description: str = Form(...),
    issue_type: str = Form("Task"),
    priority: str = Form("Medium"),
    labels: str = Form(""),
):
    """HTMX endpoint to create a Jira ticket from form."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return templates.TemplateResponse(
            "partials/jira_result.html",
            {
                "request": request,
                "success": False,
                "error": "Jira is not configured. Please add Jira credentials to your .env file.",
            },
        )

    try:
        issue_type_map = {
            "Story": JiraIssueType.STORY,
            "Task": JiraIssueType.TASK,
            "Bug": JiraIssueType.BUG,
        }

        label_list = [l.strip() for l in labels.split(",") if l.strip()]
        label_list.append("ai-generated")

        ticket = JiraTicket(
            summary=summary,
            description=description,
            issue_type=issue_type_map.get(issue_type, JiraIssueType.TASK),
            priority=priority if priority else None,
            labels=label_list,
        )

        result = await agent.create_ticket(ticket)

        return templates.TemplateResponse(
            "partials/jira_result.html",
            {
                "request": request,
                "success": True,
                "ticket_key": result.key,
                "ticket_url": result.url,
                "ticket_summary": result.summary,
            },
        )
    except JiraAgentError as e:
        return templates.TemplateResponse(
            "partials/jira_result.html",
            {
                "request": request,
                "success": False,
                "error": str(e),
            },
        )
    finally:
        await agent.close()


@app.post("/jira/create-from-story", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_jira_from_story(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    acceptance_criteria: str = Form(""),
    story_points: str = Form(""),
):
    """HTMX endpoint to create a Jira Story from a generated user story."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return HTMLResponse('<span class="jira-error">❌ Jira not configured</span>')

    try:
        # Build full description with proper Jira formatting
        full_description = f"h3. User Story\n{description}\n"

        if acceptance_criteria:
            criteria_list = acceptance_criteria.split("||")
            if criteria_list and criteria_list[0]:
                full_description += "\nh3. Acceptance Criteria\n"
                for criteria in criteria_list:
                    if criteria.strip():
                        full_description += f"* {criteria.strip()}\n"

        if story_points:
            full_description += f"\nh3. Estimation\n*Story Points:* {story_points}"

        full_description += "\n\n----\n_This story was generated by AI Sprint Companion_"

        ticket = JiraTicket(
            summary=title[:255],
            description=full_description,
            issue_type=JiraIssueType.STORY,
            priority="Medium",
            labels=["ai-generated", "user-story"],
        )

        result = await agent.create_ticket(ticket)
        return HTMLResponse(
            f'<span class="jira-success">✅ Created <a href="{result.url}" target="_blank">{result.key}</a></span>'
        )
    except JiraAgentError as e:
        return HTMLResponse(f'<span class="jira-error">❌ {str(e)}</span>')
    finally:
        await agent.close()


@app.post("/jira/create-from-task", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_jira_from_task(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    priority: str = Form("medium"),
    estimated_hours: str = Form(""),
    parent_story: str = Form(""),
):
    """HTMX endpoint to create a Jira Task from a generated sprint task."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return HTMLResponse('<span class="jira-error">❌ Jira not configured</span>')

    try:
        # Build full description with proper Jira formatting
        full_description = f"h3. Task Description\n{description}\n"

        if parent_story:
            full_description += f"\nh3. Related User Story\n{parent_story}\n"

        if estimated_hours:
            full_description += f"\nh3. Estimation\n*Estimated Hours:* {estimated_hours}h\n"

        full_description += "\n----\n_This task was generated by AI Sprint Companion_"

        # Map priority
        priority_map = {
            "high": "High",
            "medium": "Medium",
            "low": "Low",
        }

        ticket = JiraTicket(
            summary=title[:255],
            description=full_description,
            issue_type=JiraIssueType.TASK,
            priority=priority_map.get(priority.lower(), "Medium"),
            labels=["ai-generated", "sprint-task"],
        )

        result = await agent.create_ticket(ticket)
        return HTMLResponse(
            f'<span class="jira-success">✅ Created <a href="{result.url}" target="_blank">{result.key}</a></span>'
        )
    except JiraAgentError as e:
        return HTMLResponse(f'<span class="jira-error">❌ {str(e)}</span>')
    finally:
        await agent.close()


@app.post("/jira/create-all-stories", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_all_stories(request: Request):
    """HTMX endpoint to create Jira tickets for all generated stories."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return HTMLResponse('<span class="jira-error">❌ Jira not configured</span>')

    try:
        # Get JSON data from request body
        body = await request.body()
        import json
        stories = json.loads(body) if body else []

        if not stories:
            return HTMLResponse('<span class="jira-error">❌ No stories to create</span>')

        created = []
        failed = []

        for story in stories:
            try:
                # Build full description with proper Jira formatting
                full_description = f"h3. User Story\n{story.get('description', '')}\n"

                acceptance_criteria = story.get("acceptance_criteria", [])
                if acceptance_criteria:
                    full_description += "\nh3. Acceptance Criteria\n"
                    for criteria in acceptance_criteria:
                        full_description += f"* {criteria}\n"

                story_points = story.get("story_points")
                if story_points:
                    full_description += f"\nh3. Estimation\n*Story Points:* {story_points}"

                full_description += "\n\n----\n_This story was generated by AI Sprint Companion_"

                ticket = JiraTicket(
                    summary=story.get("title", "Untitled Story")[:255],
                    description=full_description,
                    issue_type=JiraIssueType.STORY,
                    priority="Medium",
                    labels=["ai-generated", "user-story"],
                )

                result = await agent.create_ticket(ticket)
                created.append(f'<a href="{result.url}" target="_blank">{result.key}</a>')
            except JiraAgentError as e:
                failed.append(story.get("title", "Unknown"))

        if created and not failed:
            return HTMLResponse(
                f'<span class="jira-success">✅ Created {len(created)} tickets: {", ".join(created)}</span>'
            )
        elif created and failed:
            return HTMLResponse(
                f'<span class="jira-success">✅ Created {len(created)} tickets: {", ".join(created)}</span>'
                f'<br><span class="jira-error">❌ Failed: {len(failed)} tickets</span>'
            )
        else:
            return HTMLResponse(f'<span class="jira-error">❌ Failed to create tickets</span>')
    except Exception as e:
        return HTMLResponse(f'<span class="jira-error">❌ Error: {str(e)}</span>')
    finally:
        await agent.close()


@app.post("/jira/create-all-tasks", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_all_tasks(request: Request):
    """HTMX endpoint to create Jira tickets for all generated tasks."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return HTMLResponse('<span class="jira-error">❌ Jira not configured</span>')

    try:
        body = await request.body()
        import json
        tasks = json.loads(body) if body else []

        if not tasks:
            return HTMLResponse('<span class="jira-error">❌ No tasks to create</span>')

        priority_map = {
            "high": "High",
            "medium": "Medium",
            "low": "Low",
        }

        created = []
        failed = []

        for task in tasks:
            try:
                # Build full description with proper Jira formatting
                full_description = f"h3. Task Description\n{task.get('description', '')}\n"

                parent_story = task.get("parent_story")
                if parent_story:
                    full_description += f"\nh3. Related User Story\n{parent_story}\n"

                estimated_hours = task.get("estimated_hours")
                if estimated_hours:
                    full_description += f"\nh3. Estimation\n*Estimated Hours:* {estimated_hours}h\n"

                full_description += "\n----\n_This task was generated by AI Sprint Companion_"

                ticket = JiraTicket(
                    summary=task.get("title", "Untitled Task")[:255],
                    description=full_description,
                    issue_type=JiraIssueType.TASK,
                    priority=priority_map.get(task.get("priority", "medium").lower(), "Medium"),
                    labels=["ai-generated", "sprint-task"],
                )

                result = await agent.create_ticket(ticket)
                created.append(f'<a href="{result.url}" target="_blank">{result.key}</a>')
            except JiraAgentError as e:
                failed.append(task.get("title", "Unknown"))

        if created and not failed:
            return HTMLResponse(
                f'<span class="jira-success">✅ Created {len(created)} tickets: {", ".join(created)}</span>'
            )
        elif created and failed:
            return HTMLResponse(
                f'<span class="jira-success">✅ Created {len(created)} tickets: {", ".join(created)}</span>'
                f'<br><span class="jira-error">❌ Failed: {len(failed)} tickets</span>'
            )
        else:
            return HTMLResponse(f'<span class="jira-error">❌ Failed to create tickets</span>')
    except Exception as e:
        return HTMLResponse(f'<span class="jira-error">❌ Error: {str(e)}</span>')
    finally:
        await agent.close()


@app.post("/jira/create-from-standup", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_jira_from_standup(
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    item_type: str = Form("action"),
    issue_type: str = Form("Task"),
    summary_context: str = Form(""),
):
    """HTMX endpoint to create a Jira ticket from a standup blocker or action item."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return HTMLResponse('<span class="jira-error">❌ Jira not configured</span>')

    try:
        # Build full description with proper Jira formatting
        item_label = "Blocker" if item_type == "blocker" else "Action Item"

        full_description = f"h3. {item_label}\n{description}\n"

        if summary_context:
            full_description += f"\nh3. Standup Context\n{summary_context}\n"

        full_description += "\n----\n_This item was generated from standup summary by AI Sprint Companion_"

        # Map issue type
        issue_type_map = {
            "Story": JiraIssueType.STORY,
            "Task": JiraIssueType.TASK,
            "Bug": JiraIssueType.BUG,
        }

        # Set priority based on item type (blockers are higher priority)
        priority = "High" if item_type == "blocker" else "Medium"

        # Set labels based on item type
        labels = ["ai-generated", "standup"]
        if item_type == "blocker":
            labels.append("blocker")
        else:
            labels.append("action-item")

        ticket = JiraTicket(
            summary=title[:255],
            description=full_description,
            issue_type=issue_type_map.get(issue_type, JiraIssueType.TASK),
            priority=priority,
            labels=labels,
        )

        result = await agent.create_ticket(ticket)
        return HTMLResponse(
            f'<span class="jira-success">✅ Created <a href="{result.url}" target="_blank">{result.key}</a></span>'
        )
    except JiraAgentError as e:
        return HTMLResponse(f'<span class="jira-error">❌ {str(e)}</span>')
    finally:
        await agent.close()


@app.post("/jira/create-all-standup-items", response_class=HTMLResponse, tags=["HTMX"])
async def htmx_create_all_standup_items(request: Request):
    """HTMX endpoint to create Jira tickets for all standup blockers and action items."""
    agent = get_jira_agent()

    if not agent.is_configured:
        return HTMLResponse('<span class="jira-error">❌ Jira not configured</span>')

    try:
        body = await request.body()
        import json
        data = json.loads(body) if body else {}

        blockers = data.get("blockers", [])
        action_items = data.get("action_items", [])
        summary_context = data.get("summary", "")

        if not blockers and not action_items:
            return HTMLResponse('<span class="jira-error">❌ No items to create</span>')

        created = []
        failed = []

        # Create tickets for blockers
        for blocker in blockers:
            try:
                full_description = f"h3. Blocker\n{blocker}\n"
                if summary_context:
                    full_description += f"\nh3. Standup Context\n{summary_context}\n"
                full_description += "\n----\n_This item was generated from standup summary by AI Sprint Companion_"

                ticket = JiraTicket(
                    summary=f"Blocker: {blocker}"[:255],
                    description=full_description,
                    issue_type=JiraIssueType.TASK,
                    priority="High",
                    labels=["ai-generated", "standup", "blocker"],
                )

                result = await agent.create_ticket(ticket)
                created.append(f'<a href="{result.url}" target="_blank">{result.key}</a>')
            except JiraAgentError as e:
                failed.append(blocker[:50])

        # Create tickets for action items
        for item in action_items:
            try:
                full_description = f"h3. Action Item\n{item}\n"
                if summary_context:
                    full_description += f"\nh3. Standup Context\n{summary_context}\n"
                full_description += "\n----\n_This item was generated from standup summary by AI Sprint Companion_"

                ticket = JiraTicket(
                    summary=item[:255],
                    description=full_description,
                    issue_type=JiraIssueType.TASK,
                    priority="Medium",
                    labels=["ai-generated", "standup", "action-item"],
                )

                result = await agent.create_ticket(ticket)
                created.append(f'<a href="{result.url}" target="_blank">{result.key}</a>')
            except JiraAgentError as e:
                failed.append(item[:50])

        if created and not failed:
            return HTMLResponse(
                f'<span class="jira-success">✅ Created {len(created)} tickets: {", ".join(created)}</span>'
            )
        elif created and failed:
            return HTMLResponse(
                f'<span class="jira-success">✅ Created {len(created)} tickets: {", ".join(created)}</span>'
                f'<br><span class="jira-error">❌ Failed: {len(failed)} items</span>'
            )
        else:
            return HTMLResponse(f'<span class="jira-error">❌ Failed to create tickets</span>')
    except Exception as e:
        return HTMLResponse(f'<span class="jira-error">❌ Error: {str(e)}</span>')
    finally:
        await agent.close()

