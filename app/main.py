"""
IncidentMind AI — FastAPI Application Entry Point.
"""

from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.schemas.health import RootResponse

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="IncidentMind AI — Incident detection, severity prediction, root-cause analysis, and remediation recommendations.",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


@app.get(
    "/",
    response_model=RootResponse,
    tags=["Root"],
    summary="API Root Information",
)
def root() -> RootResponse:
    """Return basic service metadata and documentation links."""
    return RootResponse(
        service=settings.PROJECT_NAME,
        version=settings.VERSION,
        status="online",
        docs_url="/docs",
        health_url="/health",
    )


# Mount health router directly at root (/health) and under versioned prefix (/api/v1/health)
app.include_router(health_router)
app.include_router(health_router, prefix=settings.API_V1_STR)
