import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.service import Service


class Telemetry(Base):
    __tablename__ = "telemetry"

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
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    metric_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # e.g., 'cpu_utilization', 'memory_usage_pct', 'p99_latency_ms', 'http_5xx_rate'
    metric_value: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )
    unit: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # e.g., 'percent', 'ms', 'count', 'bytes'
    dimensions: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # e.g., {'region': 'us-east-1', 'host': 'node-42', 'cluster': 'prod-k8s'}
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="telemetry",
    )

    __table_args__ = (
        Index("ix_telemetry_service_timestamp", "service_id", "timestamp"),
        Index(
            "ix_telemetry_service_metric_timestamp",
            "service_id",
            "metric_name",
            "timestamp",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Telemetry(id={self.id}, service_id={self.service_id}, "
            f"metric='{self.metric_name}', value={self.metric_value}, timestamp={self.timestamp})>"
        )
