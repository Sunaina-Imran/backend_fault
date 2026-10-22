import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.incident import Incident
    from app.models.resolution import Resolution


class RootCause(Base):
    __tablename__ = "root_causes"

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
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # e.g., 'CODE_DEFECT', 'CONFIG_CHANGE', 'DATABASE_CONTENTION', 'INFRASTRUCTURE_FAILURE'
    description: Mapped[str] = mapped_column(Text, nullable=False)
    confidence_score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )  # AI confidence (0.0 - 1.0)
    is_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        server_default="false",
    )  # Verified by SRE / engineer
    suggested_by: Mapped[str] = mapped_column(
        String(50),
        default="AI",
        nullable=False,
        server_default="AI",
    )  # 'AI', 'HUMAN'
    evidence: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB,
        nullable=True,
    )  # supporting metrics, logs, diffs, stacktraces
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
        back_populates="root_causes",
    )
    resolutions: Mapped[List["Resolution"]] = relationship(
        "Resolution",
        back_populates="root_cause",
    )

    def __repr__(self) -> str:
        return (
            f"<RootCause(id={self.id}, category='{self.category}', "
            f"is_verified={self.is_verified})>"
        )
