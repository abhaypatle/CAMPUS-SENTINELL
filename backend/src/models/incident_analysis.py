from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class IncidentAnalysis(Base):
    __tablename__ = "incident_analyses"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid4()),
    )

    incident_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("incident_reports.id"),
        nullable=False,
        unique=True,
    )

    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    assessed_category: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    assessed_severity: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    risk_indicators: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    recommended_action: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    provider: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="mock",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
