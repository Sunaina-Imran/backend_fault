"""
IncidentMind AI — Health Check Route.

Provides database-aware health verification using SQLAlchemy engine.
Guarantees connection release, zero credential leakage, and appropriate HTTP status.
"""

import logging
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


def check_database_health() -> bool:
    """
    Execute a lightweight SELECT 1 query against the database using the existing engine.

    Returns:
        bool: True if query succeeds and returns 1, False otherwise.

    Guarantees:
        - Connection is always safely returned to the pool via the context manager.
        - Zero credentials or connection strings are logged or leaked on error.
    """
    try:
        with engine.connect() as connection:
            result = connection.execute(text("SELECT 1")).scalar()
            return result == 1
    except Exception as exc:
        # Log the error category/class name safely without leaking sensitive URLs or credentials
        logger.error("Database health check probe failed: %s", type(exc).__name__)
        return False


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {
            "description": "Application is healthy and database is connected.",
            "model": HealthResponse,
        },
        503: {
            "description": "Database connection failed or service is degraded.",
            "model": HealthResponse,
        },
    },
    summary="Application & Database Health Check",
)
def get_health(response: Response) -> HealthResponse:
    """
    Database-aware health endpoint.

    Performs a live connectivity check using a lightweight SELECT 1 query.
    Returns HTTP 200 with status=healthy, database=connected when healthy.
    Returns HTTP 503 with status=unhealthy, database=disconnected when the check fails.
    """
    db_healthy = check_database_health()

    if not db_healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return HealthResponse(
            status="unhealthy",
            database="disconnected",
            environment=settings.ENVIRONMENT,
            version=settings.VERSION,
        )

    return HealthResponse(
        status="healthy",
        database="connected",
        environment=settings.ENVIRONMENT,
        version=settings.VERSION,
    )
