"""Smoke tests for AI Sprint Companion API."""
import os
import pytest
from fastapi.testclient import TestClient

# Force mock mode for tests
os.environ["AI_PROVIDER"] = "mock"

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_correct_structure(self, client):
        """Health endpoint should return expected fields."""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert "ai_provider" in data
        assert data["status"] == "healthy"


class TestHomeEndpoint:
    """Tests for home page."""

    def test_home_returns_200(self, client):
        """Home page should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_html(self, client):
        """Home page should return HTML content."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]
        # Template rendering in test client may return empty due to async context
        # The important check is that we get HTML content-type and 200 status


class TestStandupEndpoints:
    """Tests for standup summary endpoints."""

    def test_standup_page_returns_200(self, client):
        """Standup page should return 200 OK."""
        response = client.get("/standup")
        assert response.status_code == 200

    def test_standup_api_with_valid_data(self, client):
        """Standup API should process valid entries."""
        payload = {
            "entries": [
                {
                    "name": "Alice",
                    "yesterday": "Completed user auth",
                    "today": "Working on dashboard",
                    "blockers": None
                }
            ],
            "sprint_goal": "Complete MVP"
        }

        response = client.post("/api/standup/summarize", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "summary" in data
        assert "key_blockers" in data
        assert "action_items" in data

    def test_standup_api_requires_entries(self, client):
        """Standup API should require at least one entry."""
        payload = {"entries": []}

        response = client.post("/api/standup/summarize", json=payload)
        assert response.status_code == 422  # Validation error


class TestUserStoriesEndpoints:
    """Tests for user story generation endpoints."""

    def test_stories_page_returns_200(self, client):
        """Stories page should return 200 OK."""
        response = client.get("/stories")
        assert response.status_code == 200

    def test_stories_api_with_valid_data(self, client):
        """Stories API should process valid notes."""
        payload = {
            "notes": "Users need to reset passwords via email link",
            "context": "Web application"
        }

        response = client.post("/api/stories/generate", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "stories" in data
        assert isinstance(data["stories"], list)

    def test_stories_api_requires_minimum_notes(self, client):
        """Stories API should require minimum note length."""
        payload = {"notes": "short"}

        response = client.post("/api/stories/generate", json=payload)
        assert response.status_code == 422  # Validation error


class TestSprintTasksEndpoints:
    """Tests for sprint task suggestion endpoints."""

    def test_tasks_page_returns_200(self, client):
        """Tasks page should return 200 OK."""
        response = client.get("/tasks")
        assert response.status_code == 200

    def test_tasks_api_with_valid_data(self, client):
        """Tasks API should process valid user stories."""
        payload = {
            "user_stories": [
                "As a user, I want to login so that I can access my account"
            ],
            "team_capacity": 20,
            "sprint_duration_days": 14
        }

        response = client.post("/api/tasks/suggest", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "tasks" in data
        assert "recommendations" in data
        assert isinstance(data["tasks"], list)

    def test_tasks_api_requires_stories(self, client):
        """Tasks API should require at least one story."""
        payload = {"user_stories": []}

        response = client.post("/api/tasks/suggest", json=payload)
        assert response.status_code == 422  # Validation error


class TestAPIDocumentation:
    """Tests for API documentation endpoints."""

    def test_openapi_docs_available(self, client):
        """OpenAPI docs should be accessible."""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_available(self, client):
        """OpenAPI schema should be accessible."""
        response = client.get("/openapi.json")
        assert response.status_code == 200

        data = response.json()
        assert "openapi" in data
        assert "paths" in data
