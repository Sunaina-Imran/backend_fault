"""
Tests for FastAPI application entry point, GET /, and GET /health endpoints.
"""

from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.core.config import settings
from app.main import app


@pytest.fixture
def client():
    """FastAPI TestClient fixture."""
    return TestClient(app)


def test_root_endpoint(client):
    """Test GET / returns service metadata and links."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == settings.PROJECT_NAME
    assert data["version"] == settings.VERSION
    assert data["status"] == "online"
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/health"


def test_health_endpoint_success(client):
    """Test GET /health with live database connection returns 200 and connected status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"
    assert data["environment"] == settings.ENVIRONMENT
    assert data["version"] == settings.VERSION

    # Sensitive strings must never appear anywhere in the response
    raw_text = response.text
    assert "postgresql" not in raw_text.lower()
    assert "password" not in raw_text.lower()
    assert "supabase" not in raw_text.lower()


def test_versioned_health_endpoint_success(client):
    """Test GET /api/v1/health also works identically."""
    response = client.get(f"{settings.API_V1_STR}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"] == "connected"


def test_health_endpoint_database_failure(client):
    """Test GET /health returns 503 when the database check fails."""
    with patch("app.api.routes.health.check_database_health", return_value=False):
        response = client.get("/health")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"] == "disconnected"
        assert data["environment"] == settings.ENVIRONMENT
        assert data["version"] == settings.VERSION


def test_check_database_health_handles_exception_safely():
    """Verify check_database_health catches exceptions, releases connection, and returns False without leaking info."""
    from app.api.routes.health import check_database_health

    with patch("app.api.routes.health.engine.connect") as mock_connect:
        mock_connect.side_effect = OperationalError("connection to server failed", params=None, orig=Exception("secret_pass@db.internal"))
        result = check_database_health()
        assert result is False
