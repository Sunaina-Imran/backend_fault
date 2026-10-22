import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.prediction import Prediction
    from app.models.resolution import Resolution
    from app.models.root_cause import RootCause
    from app.models.service import Service


class Incident(Base):
    __tablename__ = "incidents"

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
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    severity: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )  # e.g., 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW' or 'P1', 'P2', 'P3'
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="OPEN",
        server_default="OPEN",
        index=True,
    )  # e.g., 'TRIGGERED', 'INVESTIGATING', 'IDENTIFIED', 'MITIGATED', 'RESOLVED', 'CLOSED'
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    mitigated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="incidents",
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="incident",
    )
    root_causes: Mapped[List["RootCause"]] = relationship(
        "RootCause",
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    resolutions: Mapped[List["Resolution"]] = relationship(
        "Resolution",
        back_populates="incident",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Incident(id={self.id}, title='{self.title}', "
            f"severity='{self.severity}', status='{self.status}')>"
        )
