from __future__ import annotations

import math
import platform
from typing import Any

from ..models import AttemptCommand, AttemptResult, FailureKind, Scenario
from .base import EvaluationBackend


class AnalyticBackend(EvaluationBackend):
    """A deterministic, dependency-free grasp surrogate used for paired CI tests.

    It is deliberately labelled as non-physics and never counts as ROCm evidence.
    """

    name = "analytic"

    def start_episode(self, scenario: Scenario) -> None:
        return None

    def attempt(
        self,
        scenario: Scenario,
        command: AttemptCommand,
        attempt_index: int,
    ) -> AttemptResult:
        aim_scale = max(0.0, 1.0 - command.aim_correction)
        pose_scale = max(0.0, 1.0 - command.pose_correction)
        aim_error = math.hypot(scenario.aim_error_x_m, scenario.aim_error_y_m) * aim_scale
        pose_error = scenario.pose_error_rad * pose_scale
        hold_margin = command.grip_force * scenario.friction - (0.24 + scenario.disturbance)

        if aim_error > 0.08:
            failure = FailureKind.EMPTY_GRASP
        elif pose_error > 0.22:
            failure = FailureKind.POSE_OFFSET
        elif hold_margin < 0.0:
            failure = FailureKind.SLIP
        else:
            failure = FailureKind.NONE

        success = failure is FailureKind.NONE
        signal = {
            FailureKind.NONE: 0.98,
            FailureKind.EMPTY_GRASP: min(0.99, 0.68 + aim_error * 1.7),
            FailureKind.POSE_OFFSET: min(0.99, 0.64 + pose_error * 0.55),
            FailureKind.SLIP: min(0.99, 0.72 + abs(hold_margin) * 0.28),
        }[failure]
        confidence = max(0.0, min(1.0, signal - scenario.sensor_noise * 2.2 - scenario.difficulty * 0.09))
        object_height = 0.16 if success else (0.045 if failure is FailureKind.SLIP else 0.02)
        latency = 382.0 + scenario.difficulty * 88.0 + attempt_index * 164.0
        states = _states_for_attempt(attempt_index, success, failure, latency)
        return AttemptResult(
            attempt_index=attempt_index,
            success=success,
            failure_kind=failure,
            confidence=round(confidence, 6),
            aim_error_m=round(aim_error, 6),
            pose_error_rad=round(pose_error, 6),
            hold_margin=round(hold_margin, 6),
            object_height_m=round(object_height, 6),
            simulated_latency_ms=round(latency, 3),
            states=states,
        )

    def evidence(self) -> dict[str, Any]:
        return {
            "backend": self.name,
            "engine": "deterministic analytic surrogate",
            "physics": False,
            "accelerator": "none",
            "rocm_verified": False,
            "platform": platform.platform(),
            "claim_boundary": "CI/reproducibility baseline only; not Radeon or physics evidence",
        }


def _states_for_attempt(
    attempt_index: int,
    success: bool,
    failure: FailureKind,
    latency_ms: float,
) -> list[dict[str, Any]]:
    offset = attempt_index * 170.0
    states = [
        {"state": "observe", "t_ms": round(offset, 3), "status": "ok"},
        {"state": "grasp", "t_ms": round(offset + latency_ms * 0.42, 3), "status": "ok"},
        {
            "state": "verify",
            "t_ms": round(offset + latency_ms * 0.76, 3),
            "status": "ok" if success else "failed",
        },
    ]
    if success:
        states.append({"state": "success", "t_ms": round(offset + latency_ms, 3), "status": "ok"})
    else:
        states.append(
            {
                "state": "diagnose",
                "t_ms": round(offset + latency_ms, 3),
                "status": "failed",
                "failure": failure.value,
            }
        )
    return states

