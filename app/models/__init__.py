"""
Fault IQ — Central Model Registration Module.

Imports all SQLAlchemy models so that their Table definitions are registered
with Base.metadata. Alembic imports Base.metadata from this package.
"""

from app.db.base import Base
from app.models.deployment import Deployment
from app.models.incident import Incident
from app.models.model_version import ModelVersion
from app.models.prediction import Prediction
from app.models.resolution import Resolution
from app.models.root_cause import RootCause
from app.models.service import Service
from app.models.telemetry import Telemetry

__all__ = [
    "Base",
    "Service",
    "Incident",
    "Telemetry",
    "Deployment",
    "ModelVersion",
    "Prediction",
    "RootCause",
    "Resolution",
]
