import json
from datetime import datetime, timezone
from typing import List
from sqlalchemy.orm import Session
from pydantic import ValidationError

from src.models.incident import IncidentReport
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.reports.fusion_schemas import FusedIncidentCreate
from src.ai.base import FusionProvider


def _canonical_report_set(report_ids: List[str]) -> str:
    # canonical representation independent of order
    uniq = sorted(set(report_ids))
    return ",".join(uniq)


def run_fusion(report_ids: List[str], db: Session, provider: FusionProvider, created_by: str | None = None) -> FusedIncident:
    # validate unique ids and count
    uniq_ids = list(dict.fromkeys(report_ids))
    if len(uniq_ids) < 2:
        raise ValueError("at least two unique report IDs required")

    # load reports
    reports = db.query(IncidentReport).filter(IncidentReport.id.in_(uniq_ids)).all()
    if len(reports) != len(uniq_ids):
        raise ValueError("one or more report IDs not found")

    report_set_hash = _canonical_report_set(uniq_ids)

    # check duplicate fused incident
    existing = db.query(FusedIncident).filter(FusedIncident.report_set_hash == report_set_hash).first()
    if existing:
        raise ValueError("duplicate fused incident")

    result = provider.analyze(reports)

    # validate provider output
    try:
        validated = FusedIncidentCreate(**{"report_ids": uniq_ids, "provider": result.get("provider")})
    except ValidationError as e:
        raise ValueError(f"invalid provider output: {e}")

    # required parts: confidence, provider
    confidence = result.get("confidence")
    provider_id = result.get("provider")
    reason = result.get("reason")
    evidence = result.get("evidence")
    created_at = result.get("created_at")

    if confidence is None or provider_id is None:
        raise ValueError("provider must return confidence and provider id")

    try:
        confidence = float(confidence)
    except Exception:
        raise ValueError("confidence must be a float")

    if not (0.0 <= confidence <= 1.0):
        raise ValueError("confidence must be between 0.0 and 1.0")

    # persist atomically
    try:
        # prepare fused incident
        fi_kwargs = dict(
            created_by=created_by,
            provider=provider_id,
            confidence=confidence,
            reason=reason,
            evidence=json.dumps(evidence) if evidence is not None else None,
            report_set_hash=report_set_hash,
        )

        if created_at:
            fi_kwargs["created_at"] = created_at

        fused = FusedIncident(**fi_kwargs)
        db.add(fused)
        db.flush()

        # add associations
        for rid in uniq_ids:
            assoc = FusedIncidentReport(fused_incident_id=fused.id, report_id=rid)
            db.add(assoc)

        db.commit()
        db.refresh(fused)
        return fused

    except Exception:
        db.rollback()
        raise
