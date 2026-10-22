"""
IncidentMind AI — Health and Status Schemas.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for application and database health status response."""

    status: str = Field(
        ...,
        description="Overall service health state (e.g., 'healthy', 'unhealthy').",
        examples=["healthy"],
    )
    database: str = Field(
        ...,
        description="Database connectivity status (e.g., 'connected', 'disconnected').",
        examples=["connected"],
    )
    environment: str = Field(
        ...,
        description="Deployment environment name.",
        examples=["development"],
    )
    version: str = Field(
        ...,
        description="Application semantic version.",
        examples=["0.1.0"],
    )


class RootResponse(BaseModel):
    """Schema for root API discovery endpoint."""

    service: str = Field(
        ...,
        description="Name of the service.",
        examples=["IncidentMind AI"],
    )
    version: str = Field(
        ...,
        description="Service semantic version.",
        examples=["0.1.0"],
    )
    status: str = Field(
        ...,
        description="High-level operational status.",
        examples=["online"],
    )
    docs_url: str = Field(
        ...,
        description="Path to interactive OpenAPI documentation.",
        examples=["/docs"],
    )
    health_url: str = Field(
        ...,
        description="Path to database-aware health check endpoint.",
        examples=["/health"],
    )
