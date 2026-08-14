from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incident_reports.id"), nullable=False, index=True)

    risk_score: Mapped[float] = mapped_column(Float, nullable=False)

    risk_level: Mapped[str] = mapped_column(String(20), nullable=False)

    risk_factors: Mapped[str] = mapped_column(Text, nullable=False)

    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)

    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
