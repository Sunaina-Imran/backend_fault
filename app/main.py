"""
Fault IQ — FastAPI Application Entry Point.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

from app.api.routes.health import router as health_router
from app.core.config import settings
from app.db.session import engine
from app.observability import configure_observability
from app.schemas.health import RootResponse

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize telemetry without making it a startup dependency."""
    try:
        configure_observability(app, engine)
        logger.info("Fault IQ application started with OpenTelemetry.")
    except Exception:
        logger.exception(
            "OpenTelemetry initialization failed; API will continue."
        )
    try:
        yield
    finally:
        from app.observability import (
            _logger_provider,
            _meter_provider,
            _tracer_provider,
        )
        for name, provider in (
            ("traces", _tracer_provider),
            ("metrics", _meter_provider),
            ("logs", _logger_provider),
        ):
            if provider is None:
                continue
            shutdown = getattr(provider, "shutdown", None)
            if callable(shutdown):
                try:
                    shutdown()
                except Exception:
                    logger.exception(
                        "Error shutting down OpenTelemetry %s provider.",
                        name,
                    )


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=(
        "Fault IQ — Incident detection, severity prediction, "
        "root-cause analysis, and remediation recommendations."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Instrument FastAPI before its middleware stack is initialized.
try:
    FastAPIInstrumentor.instrument_app(app)
except Exception:
    logger.exception(
        "FastAPI instrumentation failed; API will continue."
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


# Preserve the existing root and versioned health routes.
app.include_router(health_router)
app.include_router(health_router, prefix=settings.API_V1_STR)
