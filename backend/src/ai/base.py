from typing import Protocol
from src.models.incident import IncidentReport


class AIProvider(Protocol):
    def analyze(self, incident: IncidentReport) -> dict:
        """Analyze an IncidentReport and return a dict with keys:
        - summary (str)
        - assessed_category (str)
        - assessed_severity (str)
        - risk_indicators (dict | str)
        - recommended_action (str)
        - provider (str)
        - created_at (ISO timestamp) optional
        """
        ...


class FusionProvider(Protocol):
    def analyze(self, reports: list) -> dict:
        """Analyze a set of IncidentReport objects and return dict with keys:
        - confidence (float 0.0-1.0)
        - reason (str)
        - evidence (dict or str)
        - provider (str)
        - created_at optional
        """
        ...
