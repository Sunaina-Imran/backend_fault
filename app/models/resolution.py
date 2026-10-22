import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.root_cause import RootCause


class Resolution(Base):
    __tablename__ = "resolutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    root_cause_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("root_causes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., 'ROLLBACK', 'RESTART_SERVICE', 'SCALE_UP', 'PATCH_CONFIG', 'EXECUTE_RUNBOOK'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="PROPOSED",
        server_default="PROPOSED",
        index=True,
    )  # e.g., 'PROPOSED', 'IN_PROGRESS', 'SUCCESSFUL', 'FAILED', 'DISCARDED'
    execution_output: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    suggested_by: Mapped[str] = mapped_column(
        String(50),
        default="AI",
        nullable=False,
        server_default="AI",
    )  # 'AI', 'HUMAN'
    executed_at: Mapped[Optional[datetime]] = mapped_column(
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
    incident: Mapped["Incident"] = relationship(
        "Incident",
        back_populates="resolutions",
    )
    root_cause: Mapped[Optional["RootCause"]] = relationship(
        "RootCause",
        back_populates="resolutions",
    )

    def __repr__(self) -> str:
        return (
            f"<Resolution(id={self.id}, action_type='{self.action_type}', "
            f"status='{self.status}')>"
        )
