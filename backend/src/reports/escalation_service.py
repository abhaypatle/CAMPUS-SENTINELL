import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional
from sqlalchemy.orm import Session

from src.models.risk_assessment import RiskAssessment
from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.models.escalation import EscalationEvent


PRIORITY = ["ImmediateCritical", "FusionMultiConfirmed", "RisingSeverity", "AIHighSeveritySupport"]


def _make_escalation_key(incident_id: str, calculation_version: str, assessment_id: Optional[str], matched_rules: List[str]) -> str:
    key_src = f"{incident_id}|{calculation_version}|{assessment_id or ''}|{','.join(sorted(matched_rules))}"
    return hashlib.sha256(key_src.encode("utf-8")).hexdigest()


def evaluate_rules(incident_id: str, db: Session) -> Dict:
    # Load latest risk assessment
    ra = db.query(RiskAssessment).filter(RiskAssessment.incident_id == incident_id).order_by(RiskAssessment.created_at.desc()).first()
    if not ra:
        raise ValueError("no risk assessment for incident")

    score = float(ra.risk_score)
    calc_ver = ra.calculation_version

    # previous assessment within 2 hours
    prev = (
        db.query(RiskAssessment)
        .filter(RiskAssessment.incident_id == incident_id, RiskAssessment.created_at < ra.created_at)
        .order_by(RiskAssessment.created_at.desc())
        .first()
    )

    prev_score = float(prev.risk_score) if prev else None
    prev_age = (ra.created_at - prev.created_at) if prev else None

    matched = []
    trigger_values = {}

    # R1 ImmediateCritical
    if score >= 80.0:
        matched.append("ImmediateCritical")
        trigger_values["ImmediateCritical"] = {"score": score}

    # R3 FusionMultiConfirmed: check fused incident
    fir = db.query(FusedIncidentReport).filter(FusedIncidentReport.report_id == incident_id).first()
    if fir:
        fused = db.query(FusedIncident).filter(FusedIncident.id == fir.fused_incident_id).first()
        if fused:
            report_count = db.query(FusedIncidentReport).filter(FusedIncidentReport.fused_incident_id == fused.id).count()
            fusion_conf = float(getattr(fused, "confidence", 0.0))
            if report_count >= 3 and fusion_conf >= 0.9 and score >= 50.0:
                matched.append("FusionMultiConfirmed")
                trigger_values["FusionMultiConfirmed"] = {"report_count": report_count, "fusion_confidence": fusion_conf, "score": score}

    # R2 RisingSeverity
    if prev_score is not None and prev_age is not None:
        if prev_age <= timedelta(hours=2) and (score - prev_score) >= 20.0 and score >= 50.0:
            matched.append("RisingSeverity")
            trigger_values["RisingSeverity"] = {"previous_score": prev_score, "previous_at": prev.created_at.isoformat(), "score": score}

    # R4 AIHighSeveritySupport
    analysis = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == incident_id).first()
    if analysis and analysis.assessed_severity == "CRITICAL" and score >= 50.0:
        matched.append("AIHighSeveritySupport")
        trigger_values["AIHighSeveritySupport"] = {"assessed_severity": analysis.assessed_severity, "score": score}

    # determine highest priority matched rule
    triggered_rule = None
    for r in PRIORITY:
        if r in matched:
            triggered_rule = r
            break

    return {
        "assessment": ra,
        "matched": matched,
        "triggered_rule": triggered_rule,
        "trigger_values": trigger_values,
    }


def evaluate_and_create(incident_id: str, db: Session, created_by: Optional[str] = "system") -> EscalationEvent:
    eval_result = evaluate_rules(incident_id, db)
    ra = eval_result["assessment"]
    matched = eval_result["matched"]
    triggered_rule = eval_result["triggered_rule"]
    trigger_values = eval_result["trigger_values"]

    if not matched:
        # nothing to create
        return None

    # build escalation_key
    escalation_key = _make_escalation_key(incident_id, ra.calculation_version, ra.id, matched)

    # idempotency: check existing
    existing = db.query(EscalationEvent).filter(EscalationEvent.escalation_key == escalation_key).first()
    if existing:
        return existing

    # evidence: snapshot risk_factors and optional ai/fusion signals
    evidence = {"risk_factors": ra.risk_factors}
    # add analysis snapshot
    analysis = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == incident_id).first()
    if analysis:
        evidence["analysis"] = {"provider": analysis.provider, "assessed_severity": analysis.assessed_severity, "risk_indicators": analysis.risk_indicators}

    # add fused snapshot
    fir = db.query(FusedIncidentReport).filter(FusedIncidentReport.report_id == incident_id).first()
    if fir:
        fused = db.query(FusedIncident).filter(FusedIncident.id == fir.fused_incident_id).first()
        if fused:
            evidence["fusion"] = {"provider": fused.provider, "confidence": fused.confidence, "report_set_hash": fused.report_set_hash}

    ev = EscalationEvent(
        incident_id=incident_id,
        risk_assessment_id=ra.id,
        escalation_key=escalation_key,
        triggered_rule=triggered_rule,
        trigger_values=json.dumps(trigger_values),
        evidence=json.dumps(evidence),
        status="PENDING",
        created_by=created_by,
    )

    db.add(ev)
    db.commit()
    db.refresh(ev)
    return ev
