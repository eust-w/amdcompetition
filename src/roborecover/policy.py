from __future__ import annotations

from dataclasses import dataclass

from .backends.base import EvaluationBackend
from .config import BenchmarkConfig
from .models import AttemptCommand, FailureKind, PolicyResult, Scenario


@dataclass(frozen=True)
class FailureDiagnosis:
    detected: bool
    kind: FailureKind
    confidence: float


class RecoveryController:
    """Deterministic observe-grasp-verify-diagnose-retry controller."""

    def __init__(self, config: BenchmarkConfig) -> None:
        self.config = config

    @staticmethod
    def baseline_command() -> AttemptCommand:
        return AttemptCommand(aim_correction=0.0, pose_correction=0.0, grip_force=1.0)

    def diagnose(self, result) -> FailureDiagnosis:
        detected = (not result.success) and result.confidence >= self.config.detector_threshold
        return FailureDiagnosis(
            detected=detected,
            kind=result.failure_kind if detected else FailureKind.UNKNOWN,
            confidence=result.confidence,
        )

    @staticmethod
    def recovery_command(kind: FailureKind, scenario: Scenario) -> AttemptCommand:
        correction = max(0.68, 0.94 - scenario.difficulty * 0.22)
        if kind is FailureKind.EMPTY_GRASP:
            return AttemptCommand(correction, 0.45, 1.25)
        if kind is FailureKind.POSE_OFFSET:
            return AttemptCommand(0.72, correction, 1.35)
        if kind is FailureKind.SLIP:
            return AttemptCommand(0.76, 0.74, 2.8)
        return AttemptCommand(0.55, 0.55, 1.45)

    def execute(
        self,
        backend: EvaluationBackend,
        scenario: Scenario,
        enable_recovery: bool,
    ) -> PolicyResult:
        backend.start_episode(scenario)
        first = backend.attempt(scenario, self.baseline_command(), attempt_index=0)
        attempts = [first]
        if first.success or not enable_recovery or self.config.max_retries == 0:
            return PolicyResult(
                success=first.success,
                retries=0,
                detected_failure=False,
                diagnosed_as=FailureKind.NONE if first.success else FailureKind.UNKNOWN,
                attempts=attempts,
            )

        diagnosis = self.diagnose(first)
        if not diagnosis.detected:
            return PolicyResult(False, 0, False, FailureKind.UNKNOWN, attempts)

        for retry_index in range(1, self.config.max_retries + 1):
            command = self.recovery_command(diagnosis.kind, scenario)
            retry = backend.attempt(scenario, command, attempt_index=retry_index)
            retry.states.insert(0, {"state": "retry", "t_ms": retry_index * 170.0, "status": "ok"})
            attempts.append(retry)
            if retry.success:
                break
            diagnosis = self.diagnose(retry)
            if not diagnosis.detected:
                break

        return PolicyResult(
            success=attempts[-1].success,
            retries=len(attempts) - 1,
            detected_failure=True,
            diagnosed_as=diagnosis.kind,
            attempts=attempts,
        )

