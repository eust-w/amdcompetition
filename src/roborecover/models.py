from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class FailureKind(str, Enum):
    NONE = "none"
    EMPTY_GRASP = "empty_grasp"
    SLIP = "slip"
    POSE_OFFSET = "pose_offset"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class Scenario:
    episode_id: str
    seed: int
    episode_index: int
    injected_failure: FailureKind
    object_x_m: float
    object_y_m: float
    aim_error_x_m: float
    aim_error_y_m: float
    pose_error_rad: float
    friction: float
    disturbance: float
    sensor_noise: float
    difficulty: float

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["injected_failure"] = self.injected_failure.value
        return data


@dataclass(frozen=True)
class AttemptCommand:
    aim_correction: float
    pose_correction: float
    grip_force: float


@dataclass
class AttemptResult:
    attempt_index: int
    success: bool
    failure_kind: FailureKind
    confidence: float
    aim_error_m: float
    pose_error_rad: float
    hold_margin: float
    object_height_m: float
    simulated_latency_ms: float
    states: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["failure_kind"] = self.failure_kind.value
        return data


@dataclass
class PolicyResult:
    success: bool
    retries: int
    detected_failure: bool
    diagnosed_as: FailureKind
    attempts: list[AttemptResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "retries": self.retries,
            "detected_failure": self.detected_failure,
            "diagnosed_as": self.diagnosed_as.value,
            "attempts": [attempt.to_dict() for attempt in self.attempts],
        }

