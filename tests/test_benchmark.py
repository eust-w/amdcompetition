from pathlib import Path

from roborecover.artifacts import canonical_json
from roborecover.backends.analytic import AnalyticBackend
from roborecover.config import load_config
from roborecover.runner import run_benchmark


ROOT = Path(__file__).resolve().parents[1]


def _run():
    return run_benchmark(load_config(ROOT / "configs" / "benchmark.json"), AnalyticBackend())


def test_recovery_improves_paired_success_rate() -> None:
    result = _run()
    metrics = result["metrics"]
    assert metrics["recovery_success_rate"] > metrics["baseline_success_rate"]
    assert metrics["failure_recovery_rate"] >= 0.70
    assert metrics["failure_detection_rate"] >= 0.90
    assert metrics["mean_retries"] <= 1.0


def test_analytic_episode_results_are_bit_reproducible() -> None:
    first = _run()
    second = _run()
    assert canonical_json(first["episodes"]) == canonical_json(second["episodes"])
    assert first["metrics"] == second["metrics"]


def test_baseline_and_recovery_are_paired_on_identical_scenarios() -> None:
    result = _run()
    assert len(result["episodes"]) == 400
    for row in result["episodes"]:
        assert row["baseline"]["attempts"][0] == row["recovery"]["attempts"][0]

