import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.model_version import ModelVersion
    from app.models.service import Service


class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    incident_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model_version_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("model_versions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    prediction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # e.g., 'incident_severity', 'time_to_mitigate', 'anomaly_detection', 'root_cause_ranking'
    prediction_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )  # confidence score or probability (0.0 - 1.0)
    prediction_payload: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # explanation, SHAP values, feature vectors, class probabilities
    is_correct: Mapped[Optional[bool]] = mapped_column(
        Boolean,
        nullable=True,
    )  # feedback flag for evaluation loop
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="predictions",
    )
    incident: Mapped[Optional["Incident"]] = relationship(
        "Incident",
        back_populates="predictions",
    )
    model_version: Mapped[Optional["ModelVersion"]] = relationship(
        "ModelVersion",
        back_populates="predictions",
    )

    __table_args__ = (
        Index("ix_predictions_service_type", "service_id", "prediction_type"),
    )

    def __repr__(self) -> str:
        return (
            f"<Prediction(id={self.id}, type='{self.prediction_type}', "
            f"score={self.prediction_score})>"
        )
