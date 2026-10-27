
import json
from pathlib import Path
from typing import Any


class PolicyRetriever:
    """
    Loads department mappings and SLA rules from a JSON file.

    This is a simple standalone implementation.
    Later, it can be adapted to the project's RAG/policy retrieval system.
    """

    def __init__(self, reference_path: str | Path | None = None):
        if reference_path is not None:
            self.reference_path = Path(reference_path)
        else:
            self.reference_path = (
                Path(__file__).parent
                / "routing_reference_data.example.json"
            )

        self._data: dict[str, Any] = {}

        if self.reference_path.exists():
            self._data = json.loads(
                self.reference_path.read_text(encoding="utf-8")
            )

    @property
    def is_demo_data(self) -> bool:
        """Indicate whether the loaded configuration is demo data."""
        return bool(self._data.get("demo_only", True))

    def department_rule(self, category: str) -> dict[str, Any] | None:
        """Return the department mapping for a category."""
        return self._data.get("departments", {}).get(category)

    def sla_rule(
        self,
        category: str,
        severity: str,
    ) -> dict[str, Any] | None:
        """Return the SLA rule for a category and severity."""
        return (
            self._data
            .get("sla_rules", {})
            .get(category, {})
            .get(severity)
        )
