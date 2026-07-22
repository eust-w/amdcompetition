from __future__ import annotations

from time import perf_counter
from typing import Any

from .backends.base import EvaluationBackend
from .config import BenchmarkConfig
from .metrics import compute_metrics
from .policy import RecoveryController
from .scenarios import generate_scenarios


def run_benchmark(config: BenchmarkConfig, backend: EvaluationBackend) -> dict[str, Any]:
    controller = RecoveryController(config)
    episode_rows: list[dict[str, Any]] = []
    started = perf_counter()
    try:
        for scenario in generate_scenarios(config):
            baseline = controller.execute(backend, scenario, enable_recovery=False)
            recovery = controller.execute(backend, scenario, enable_recovery=True)
            episode_rows.append(
                {
                    "episode_id": scenario.episode_id,
                    "scenario": scenario.to_dict(),
                    "baseline": baseline.to_dict(),
                    "recovery": recovery.to_dict(),
                }
            )
    finally:
        backend.close()
    return {
        "metrics": compute_metrics(episode_rows),
        "episodes": episode_rows,
        "backend_evidence": backend.evidence(),
        "wall_time_seconds": round(perf_counter() - started, 6),
    }

