from __future__ import annotations

import math
import random

from .config import BenchmarkConfig
from .models import FailureKind, Scenario


def _pick_failure(rng: random.Random, mix: dict[FailureKind, float]) -> FailureKind:
    value = rng.random()
    cumulative = 0.0
    for kind, weight in mix.items():
        cumulative += weight
        if value <= cumulative:
            return kind
    return next(reversed(mix))


def _polar_error(rng: random.Random, minimum: float, maximum: float) -> tuple[float, float]:
    magnitude = rng.uniform(minimum, maximum)
    angle = rng.uniform(-math.pi, math.pi)
    return magnitude * math.cos(angle), magnitude * math.sin(angle)


def generate_scenarios(config: BenchmarkConfig) -> list[Scenario]:
    scenarios: list[Scenario] = []
    for seed in config.seeds:
        for episode_index in range(config.episodes_per_seed):
            rng = random.Random((seed << 20) ^ (episode_index * 1_000_003) ^ 0x524F424F)
            failure = _pick_failure(rng, config.failure_mix)
            difficulty = rng.random()
            object_x = rng.uniform(0.60, 0.70)
            object_y = rng.uniform(-0.08, 0.08)
            sensor_noise = rng.uniform(0.003, 0.018)

            if failure is FailureKind.NONE:
                aim_x, aim_y = _polar_error(rng, 0.004, 0.035)
                pose_error = rng.uniform(0.01, 0.13)
                friction = rng.uniform(0.72, 1.05)
                disturbance = rng.uniform(0.01, 0.12)
            elif failure is FailureKind.EMPTY_GRASP:
                aim_x, aim_y = _polar_error(rng, 0.095, 0.18)
                pose_error = rng.uniform(0.03, 0.17)
                friction = rng.uniform(0.65, 0.95)
                disturbance = rng.uniform(0.03, 0.16)
            elif failure is FailureKind.POSE_OFFSET:
                aim_x, aim_y = _polar_error(rng, 0.025, 0.065)
                pose_error = rng.uniform(0.26, 0.58)
                friction = rng.uniform(0.62, 0.92)
                disturbance = rng.uniform(0.04, 0.18)
            else:
                aim_x, aim_y = _polar_error(rng, 0.006, 0.04)
                pose_error = rng.uniform(0.02, 0.16)
                friction = rng.uniform(0.16, 0.36)
                disturbance = rng.uniform(0.24, 0.58)

            scenarios.append(
                Scenario(
                    episode_id=f"s{seed}-e{episode_index:03d}",
                    seed=seed,
                    episode_index=episode_index,
                    injected_failure=failure,
                    object_x_m=object_x,
                    object_y_m=object_y,
                    aim_error_x_m=aim_x,
                    aim_error_y_m=aim_y,
                    pose_error_rad=pose_error,
                    friction=friction,
                    disturbance=disturbance,
                    sensor_noise=sensor_noise,
                    difficulty=difficulty,
                )
            )
    return scenarios

