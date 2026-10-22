import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.deployment import Deployment
    from app.models.incident import Incident
    from app.models.prediction import Prediction
    from app.models.telemetry import Telemetry


class Service(Base):
    __tablename__ = "services"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tier: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )  # e.g., 'tier-1', 'tier-2', 'tier-3'
    owner_team: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )  # e.g., 'SRE', 'Core-Platform', 'Checkout'
    repo_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
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
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    incidents: Mapped[List["Incident"]] = relationship(
        "Incident",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    telemetry: Mapped[List["Telemetry"]] = relationship(
        "Telemetry",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    deployments: Mapped[List["Deployment"]] = relationship(
        "Deployment",
        back_populates="service",
        cascade="all, delete-orphan",
    )
    predictions: Mapped[List["Prediction"]] = relationship(
        "Prediction",
        back_populates="service",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Service(id={self.id}, name='{self.name}', tier='{self.tier}')>"
