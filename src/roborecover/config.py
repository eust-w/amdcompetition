from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import FailureKind


@dataclass(frozen=True)
class BenchmarkConfig:
    schema_version: str
    name: str
    seeds: tuple[int, ...]
    episodes_per_seed: int
    failure_mix: dict[FailureKind, float]
    detector_threshold: float
    max_retries: int
    success_height_m: float
    strict_single_gpu: bool

    @property
    def episode_count(self) -> int:
        return len(self.seeds) * self.episodes_per_seed

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "name": self.name,
            "seeds": list(self.seeds),
            "episodes_per_seed": self.episodes_per_seed,
            "failure_mix": {key.value: value for key, value in self.failure_mix.items()},
            "detector_threshold": self.detector_threshold,
            "max_retries": self.max_retries,
            "success_height_m": self.success_height_m,
            "strict_single_gpu": self.strict_single_gpu,
        }


def load_config(path: str | Path) -> BenchmarkConfig:
    source = Path(path)
    data = json.loads(source.read_text(encoding="utf-8"))
    failure_mix = {FailureKind(key): float(value) for key, value in data["failure_mix"].items()}
    total_weight = sum(failure_mix.values())
    if abs(total_weight - 1.0) > 1e-9:
        raise ValueError(f"failure_mix must sum to 1.0, got {total_weight}")
    seeds = tuple(int(seed) for seed in data["seeds"])
    if not seeds or len(seeds) != len(set(seeds)):
        raise ValueError("seeds must be a non-empty list of unique integers")
    episodes_per_seed = int(data["episodes_per_seed"])
    if episodes_per_seed < 1:
        raise ValueError("episodes_per_seed must be positive")
    max_retries = int(data["max_retries"])
    if max_retries not in (0, 1, 2):
        raise ValueError("max_retries must be between 0 and 2")
    threshold = float(data["detector_threshold"])
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("detector_threshold must be in [0, 1]")
    return BenchmarkConfig(
        schema_version=str(data["schema_version"]),
        name=str(data["name"]),
        seeds=seeds,
        episodes_per_seed=episodes_per_seed,
        failure_mix=failure_mix,
        detector_threshold=threshold,
        max_retries=max_retries,
        success_height_m=float(data["success_height_m"]),
        strict_single_gpu=bool(data.get("strict_single_gpu", True)),
    )

