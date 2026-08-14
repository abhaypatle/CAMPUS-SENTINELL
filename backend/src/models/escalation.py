from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class EscalationEvent(Base):
    __tablename__ = "escalation_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incident_reports.id"), nullable=False, index=True)

    risk_assessment_id: Mapped[str] = mapped_column(String(36), ForeignKey("risk_assessments.id"), nullable=True)

    escalation_key: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

    triggered_rule: Mapped[str] = mapped_column(String(80), nullable=False)

    trigger_values: Mapped[str] = mapped_column(Text, nullable=True)

    evidence: Mapped[str] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")

    created_by: Mapped[str] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    acknowledged_by: Mapped[str] = mapped_column(String(36), nullable=True)
    acknowledged_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    actioned_by: Mapped[str] = mapped_column(String(36), nullable=True)
    actioned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    resolution_note: Mapped[str] = mapped_column(Text, nullable=True)
