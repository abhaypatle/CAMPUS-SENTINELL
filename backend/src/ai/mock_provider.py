from datetime import datetime, timezone
import json
from src.models.incident import IncidentReport, IncidentCategory, IncidentSeverity


class MockProvider:
    """Deterministic local provider for testing and development."""

    provider_id = "mock"

    def analyze(self, incident: IncidentReport) -> dict:
        # deterministic short summary and echo/assess fields
        summary = (incident.title or "") + " - " + (incident.description or "")
        summary = summary[:1000]

        # Deterministic keyword-based rules to derive assessed category/severity
        text = ((incident.title or "") + " " + (incident.description or "")).lower()

        # Category rules
        if any(k in text for k in ["fire", "smoke", "flame"]):
            assessed_category = IncidentCategory.FIRE.value
        elif any(k in text for k in ["injury", "injured", "medical", "unconscious"]):
            assessed_category = IncidentCategory.MEDICAL.value
        elif any(k in text for k in ["theft", "attack", "intruder", "security"]):
            assessed_category = IncidentCategory.SECURITY.value
        elif any(k in text for k in ["broken", "damage", "electrical", "water leak", "leak"]):
            assessed_category = IncidentCategory.INFRASTRUCTURE.value
        else:
            assessed_category = incident.category or IncidentCategory.OTHER.value

        # Severity rules
        critical_keywords = ["unconscious", "major fire", "active attack", "explosion", "life-threatening"]
        high_keywords = ["injury", "injured", "fire", "attack", "bleeding", "shooting", "stab"]

        if any(k in text for k in critical_keywords):
            assessed_severity = IncidentSeverity.CRITICAL.value
        elif any(k in text for k in high_keywords):
            assessed_severity = IncidentSeverity.HIGH.value
        else:
            # preserve reported severity when available, otherwise default to LOW
            assessed_severity = incident.severity or IncidentSeverity.LOW.value

        risk_indicators = {
            "length_description": len(incident.description or ""),
            "has_keywords": any(k in (incident.description or "").lower() for k in ["fire", "smoke", "injury", "attack"]),
        }

        recommended_action = "Investigate on site and assess risk." if risk_indicators["has_keywords"] else "Monitor and follow up."

        return {
            "summary": summary,
            "assessed_category": assessed_category,
            "assessed_severity": assessed_severity,
            "risk_indicators": risk_indicators,
            "recommended_action": recommended_action,
            "provider": self.provider_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }


class MockFusionProvider:
    """Deterministic fusion provider for testing."""

    provider_id = "mock-fusion"

    def analyze(self, reports: list) -> dict:
        # Deterministic evidence: aggregate keyword matches and location matches
        combined_texts = [((r.title or "") + " " + (r.description or "")).lower() for r in reports]
        all_text = " ".join(combined_texts)

        # simple keyword-based similarity score
        keywords = ["fire", "smoke", "injury", "attack", "theft", "broken", "electrical"]
        keyword_counts = {k: sum(1 for t in combined_texts if k in t) for k in keywords}

        # location agreement
        locations = [r.location_text for r in reports if r.location_text]
        location_match = len(set(locations)) == 1 and len(locations) > 0

        # simple confidence: (keyword hits proportion) + location bonus, normalized
        keyword_hits = sum(keyword_counts.values())
        base = min(1.0, keyword_hits / max(1, len(reports)))
        confidence = base + (0.2 if location_match else 0.0)
        confidence = max(0.0, min(1.0, confidence))

        evidence = {
            "keyword_counts": keyword_counts,
            "location_match": location_match,
            "report_count": len(reports),
        }

        reason = f"Matched {sum(1 for v in keyword_counts.values() if v>0)} keyword types; location_match={location_match}"

        return {
            "confidence": confidence,
            "reason": reason,
            "evidence": evidence,
            "provider": self.provider_id,
            "created_at": datetime.now(timezone.utc),
        }
