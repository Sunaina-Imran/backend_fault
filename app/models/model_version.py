import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.prediction import Prediction


class ModelVersion(Base):
    __tablename__ = "model_versions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # e.g., 'incident_severity_classifier', 'root_cause_engine'
    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # e.g., '1.0.0', '2026.10-v2'
    model_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., 'gradient_boosting', 'llm', 'isolation_forest'
    metrics: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # e.g., {'f1': 0.92, 'precision': 0.94, 'accuracy': 0.95}
    parameters: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # hyperparameters, feature lists, threshold configs
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        server_default="true",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="model_version",
    )

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_model_versions_name_version"),
    )

    def __repr__(self) -> str:
        return (
            f"<ModelVersion(id={self.id}, name='{self.name}', "
            f"version='{self.version}', is_active={self.is_active})>"
        )
