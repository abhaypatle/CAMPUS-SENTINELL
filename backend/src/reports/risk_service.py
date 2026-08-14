import json
from typing import Tuple, List
from sqlalchemy.orm import Session
from src.models.incident import IncidentReport
from src.models.incident_analysis import IncidentAnalysis
from src.models.fusion import FusedIncident, FusedIncidentReport
from src.models.risk_assessment import RiskAssessment


def _clamp_score(s: float) -> float:
    if s < 0.0:
        return 0.0
    if s > 100.0:
        return 100.0
    return round(s, 1)


def compute_risk_score(incident_id: str, db: Session, calculation_version: str = "v1") -> Tuple[float, str, List[dict]]:
    # Load incident
    incident = db.query(IncidentReport).filter(IncidentReport.id == incident_id).first()
    if not incident:
        raise ValueError("incident not found")

    # Base severity map
    severity_map = {"LOW": 10.0, "MEDIUM": 30.0, "HIGH": 60.0, "CRITICAL": 85.0}
    category_modifier = {
        "FIRE": 12.0,
        "MEDICAL": 8.0,
        "SECURITY": 10.0,
        "INFRASTRUCTURE": 4.0,
        "SAFETY": 6.0,
        "OTHER": 0.0,
    }

    ai_severity_map = {"LOW": 2.0, "MEDIUM": 8.0, "HIGH": 18.0, "CRITICAL": 30.0}

    factors = []

    base = severity_map.get(incident.severity, 0.0)
    factors.append({"key": "base_severity", "value": incident.severity, "contribution": base, "explanation": f"IncidentReport.severity={incident.severity}", "source": "authoritative"})

    cat_mod = category_modifier.get(incident.category, 0.0)
    factors.append({"key": "category_modifier", "value": incident.category, "contribution": cat_mod, "explanation": f"category={incident.category}", "source": "authoritative"})

    # AI analysis optional
    ai_sev_contrib = 0.0
    ai_ind_contrib = 0.0
    analysis = db.query(IncidentAnalysis).filter(IncidentAnalysis.incident_id == incident_id).first()
    if analysis:
        asev = ai_severity_map.get(analysis.assessed_severity, 0.0)
        ai_sev_contrib = asev
        factors.append({"key": "ai_assessed_severity", "value": analysis.assessed_severity, "contribution": asev, "explanation": f"AI assessed {analysis.assessed_severity}", "source": f"analysis:{analysis.provider}"})

        # risk_indicators treated as dict if JSON string
        try:
            ri = analysis.risk_indicators
            if isinstance(ri, str):
                ri = json.loads(ri)
        except Exception:
            ri = {}

        # count high indicators (heuristic): if boolean True or numeric > threshold
        high_count = 0
        if isinstance(ri, dict):
            for k, v in ri.items():
                if isinstance(v, bool) and v:
                    high_count += 1
                elif isinstance(v, (int, float)) and v > 0:
                    high_count += 1

        ai_ind_contrib = min(15.0, high_count * 3.0)
        if ai_ind_contrib:
            factors.append({"key": "ai_risk_indicators", "value": ri, "contribution": ai_ind_contrib, "explanation": f"{high_count} high indicators", "source": f"analysis:{analysis.provider}"})

    # Fusion optional
    fusion_mult = 1.0
    multi_bonus = 0.0
    loc_bonus = 0.0
    # find fused incident where this report is included
    fir = db.query(FusedIncidentReport).filter(FusedIncidentReport.report_id == incident_id).first()
    if fir:
        fused = db.query(FusedIncident).filter(FusedIncident.id == fir.fused_incident_id).first()
        if fused:
            fusion_conf = float(getattr(fused, "confidence", 0.0))
            fusion_mult = 1.0 + (fusion_conf * 0.5)
            # count reports in fused incident
            report_count = db.query(FusedIncidentReport).filter(FusedIncidentReport.fused_incident_id == fused.id).count()
            multi_bonus = min(20.0, max(0.0, (report_count - 1) * 5.0))
            # basic location match detection: check evidence field for location_match key if present
            try:
                ev = json.loads(fused.evidence) if fused.evidence else {}
                if isinstance(ev, dict) and ev.get("location_match"):
                    loc_bonus = 5.0
            except Exception:
                loc_bonus = 0.0

            factors.append({"key": "fusion_confidence", "value": fusion_conf, "contribution": 0.0, "explanation": "applied as multiplier", "source": f"fusion:{fused.provider}"})
            if multi_bonus:
                factors.append({"key": "multi_report_bonus", "value": report_count, "contribution": multi_bonus, "explanation": f"{report_count} reports in fusion", "source": "fusion"})
            if loc_bonus:
                factors.append({"key": "location_match_bonus", "value": True, "contribution": loc_bonus, "explanation": "location match across fused reports", "source": "fusion"})

    # sum raw contributions
    raw = base + cat_mod + ai_sev_contrib + ai_ind_contrib + multi_bonus + loc_bonus

    # apply multiplier
    score = raw * fusion_mult
    score = _clamp_score(score)

    # compute risk level thresholds
    if score >= 80.0:
        level = "CRITICAL"
    elif score >= 50.0:
        level = "HIGH"
    elif score >= 25.0:
        level = "MEDIUM"
    else:
        level = "LOW"

    # update factors list to include final contributions (for multiplier-type factor, compute contribution)
    # compute fusion multiplier contribution as (score - pre_mult_score)
    pre_mult_score = raw
    fusion_contribution = round(score - pre_mult_score, 2) if fusion_mult != 1.0 else 0.0
    # find fusion_confidence factor and update contribution
    for f in factors:
        if f["key"] == "fusion_confidence":
            f["contribution"] = fusion_contribution

    return score, level, factors


def create_risk_assessment(incident_id: str, db: Session, created_by: str | None = None, calculation_version: str = "v1") -> RiskAssessment:
    # compute
    score, level, factors = compute_risk_score(incident_id, db, calculation_version)

    ra = RiskAssessment(incident_id=incident_id, risk_score=score, risk_level=level, risk_factors=json.dumps(factors), calculation_version=calculation_version)
    db.add(ra)
    db.commit()
    db.refresh(ra)
    return ra
