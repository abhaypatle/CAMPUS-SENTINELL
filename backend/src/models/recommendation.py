from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, ForeignKey, Boolean, Float
from sqlalchemy.orm import Mapped, mapped_column

from src.db.session import Base


class Recommendation(Base):
    __tablename__ = "recommendations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))

    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incident_reports.id"), nullable=False, index=True)

    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    provider_version: Mapped[str] = mapped_column(String(50), nullable=True)
    calculation_version: Mapped[str] = mapped_column(String(20), nullable=False, default="v1")

    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    recommendation_type: Mapped[str] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float] = mapped_column(Float, nullable=True)

    provider_response_raw: Mapped[str] = mapped_column(Text, nullable=True)
    evidence_anchors: Mapped[str] = mapped_column(Text, nullable=True)

    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    created_by: Mapped[str] = mapped_column(String(36), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
