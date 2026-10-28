
from ..schemas import SeverityLevel

class SeverityService:
    """Assess complaint severity using explicit safety and impact indicators."""
    def assess(
        self,
        description: str,
        reported_hazard: bool = False,
        affected_people: int | None = None,
        service_disruption: bool = False,
    ) -> SeverityLevel:
        if not description.strip():
            return "undetermined"
        text = description.lower()
        critical_indicators = (
            "live electrical wire",
            "exposed live wire",
            "electrocution",
            "building collapse",
            "gas leak",
            "fire spreading",
        )
        high_indicators = (
            "major water leak",
            "severe flooding",
            "overflowing sewage",
            "road collapse",
            "power line down",
        )
        if any(term in text for term in critical_indicators):
            return "critical"
        if reported_hazard:
            return "high"
        if any(term in text for term in high_indicators):
            return "high"
        if affected_people is not None and affected_people < 0:
            return "undetermined"
        if affected_people is not None and affected_people >= 100:
            return "high"
        if service_disruption:
            return "medium"
        if affected_people is not None and affected_people > 0:
            return "medium"
        return "low"
