from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class FusedIncident(Base):
    __tablename__ = "fused_incidents"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid4())
    )

    created_by: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id"), nullable=True
    )

    provider: Mapped[str] = mapped_column(String(50), nullable=False, default="mock")

    confidence: Mapped[float] = mapped_column(Float, nullable=False)

    reason: Mapped[str] = mapped_column(Text, nullable=True)

    evidence: Mapped[str] = mapped_column(Text, nullable=True)

    report_set_hash: Mapped[str] = mapped_column(String(1024), nullable=False, unique=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )


class FusedIncidentReport(Base):
    __tablename__ = "fused_incident_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    fused_incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("fused_incidents.id"), nullable=False)

    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("incident_reports.id"), nullable=False)

    contribution_role: Mapped[str] = mapped_column(String(50), nullable=True)

    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (UniqueConstraint("fused_incident_id", "report_id", name="uix_fused_report_pair"),)
