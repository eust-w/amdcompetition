from __future__ import annotations

from collections import defaultdict
from typing import Any


def _ratio(numerator: int, denominator: int) -> float:
    return round(numerator / denominator, 6) if denominator else 0.0


def compute_metrics(episodes: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(episodes)
    baseline_successes = sum(bool(item["baseline"]["success"]) for item in episodes)
    recovery_successes = sum(bool(item["recovery"]["success"]) for item in episodes)
    baseline_failures = total - baseline_successes
    recovered = sum(
        (not item["baseline"]["success"]) and item["recovery"]["success"] for item in episodes
    )
    detected = sum(
        (not item["baseline"]["success"]) and item["recovery"]["detected_failure"] for item in episodes
    )
    retry_total = sum(int(item["recovery"]["retries"]) for item in episodes)

    taxonomy: dict[str, dict[str, float | int]] = defaultdict(
        lambda: {"injected": 0, "baseline_failed": 0, "detected": 0, "recovered": 0, "latency_sum_ms": 0.0}
    )
    per_seed: dict[int, dict[str, int]] = defaultdict(
        lambda: {"episodes": 0, "baseline_successes": 0, "recovery_successes": 0}
    )
    for item in episodes:
        kind = item["scenario"]["injected_failure"]
        row = taxonomy[kind]
        row["injected"] += 1
        failed = not item["baseline"]["success"]
        row["baseline_failed"] += int(failed)
        row["detected"] += int(failed and item["recovery"]["detected_failure"])
        row["recovered"] += int(failed and item["recovery"]["success"])
        if failed:
            row["latency_sum_ms"] += sum(
                attempt["simulated_latency_ms"] for attempt in item["recovery"]["attempts"][1:]
            )

        seed_row = per_seed[int(item["scenario"]["seed"])]
        seed_row["episodes"] += 1
        seed_row["baseline_successes"] += int(item["baseline"]["success"])
        seed_row["recovery_successes"] += int(item["recovery"]["success"])

    taxonomy_rows = []
    for kind, row in sorted(taxonomy.items()):
        failures = int(row["baseline_failed"])
        recovered_for_kind = int(row["recovered"])
        taxonomy_rows.append(
            {
                "failure_type": kind,
                "injected": int(row["injected"]),
                "baseline_failed": failures,
                "detected": int(row["detected"]),
                "recovered": recovered_for_kind,
                "recovery_rate": _ratio(recovered_for_kind, failures),
                "mean_recovery_latency_ms": round(float(row["latency_sum_ms"]) / failures, 3) if failures else 0.0,
            }
        )

    per_seed_rows = []
    for seed, row in sorted(per_seed.items()):
        count = row["episodes"]
        per_seed_rows.append(
            {
                "seed": seed,
                "episodes": count,
                "baseline_success_rate": _ratio(row["baseline_successes"], count),
                "recovery_success_rate": _ratio(row["recovery_successes"], count),
            }
        )

    return {
        "episodes": total,
        "baseline_successes": baseline_successes,
        "baseline_success_rate": _ratio(baseline_successes, total),
        "recovery_successes": recovery_successes,
        "recovery_success_rate": _ratio(recovery_successes, total),
        "baseline_failures": baseline_failures,
        "recovered_failures": recovered,
        "failure_recovery_rate": _ratio(recovered, baseline_failures),
        "failure_detection_rate": _ratio(detected, baseline_failures),
        "mean_retries": round(retry_total / total, 6) if total else 0.0,
        "absolute_success_lift": round(_ratio(recovery_successes, total) - _ratio(baseline_successes, total), 6),
        "failure_taxonomy": taxonomy_rows,
        "per_seed": per_seed_rows,
    }

