import uuid
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.service import Service


class Deployment(Base):
    __tablename__ = "deployments"

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
    version: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )  # e.g., 'v2.1.0' or git commit SHA
    environment: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="production",
        server_default="production",
    )  # e.g., 'production', 'staging'
    deployed_by: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )  # e.g., 'ci-pipeline', 'engineer@company.com'
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="SUCCESS",
        server_default="SUCCESS",
    )  # e.g., 'SUCCESS', 'FAILED', 'ROLLED_BACK'
    deployed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )
    change_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    commit_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    service: Mapped["Service"] = relationship(
        "Service",
        back_populates="deployments",
    )

    __table_args__ = (
        Index("ix_deployments_service_deployed_at", "service_id", "deployed_at"),
    )

    def __repr__(self) -> str:
        return (
            f"<Deployment(id={self.id}, service_id={self.service_id}, "
            f"version='{self.version}', status='{self.status}', deployed_at={self.deployed_at})>"
        )
