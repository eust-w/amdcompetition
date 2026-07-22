from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import AttemptCommand, AttemptResult, Scenario


class EvaluationBackend(ABC):
    name: str

    @abstractmethod
    def start_episode(self, scenario: Scenario) -> None:
        """Reset the backend to the scenario's initial state."""

    @abstractmethod
    def attempt(
        self,
        scenario: Scenario,
        command: AttemptCommand,
        attempt_index: int,
    ) -> AttemptResult:
        """Execute one grasp attempt."""

    @abstractmethod
    def evidence(self) -> dict[str, Any]:
        """Return machine-readable backend provenance."""

    def close(self) -> None:
        return None

