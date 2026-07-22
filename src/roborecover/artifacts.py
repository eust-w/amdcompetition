from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import BenchmarkConfig


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git_revision(root: Path) -> str:
    result = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "UNCOMMITTED"


def write_run(
    project_root: Path,
    output_root: Path,
    config: BenchmarkConfig,
    result: dict[str, Any],
) -> tuple[Path, dict[str, Any]]:
    config_data = config.to_dict()
    config_digest = sha256_bytes(canonical_json(config_data).encode("utf-8"))
    episodes_payload = "".join(canonical_json(row) + "\n" for row in result["episodes"])
    result_digest = sha256_bytes(episodes_payload.encode("utf-8"))
    run_id = f"run-{result['backend_evidence']['backend']}-{config_digest[:8]}-{result_digest[:8]}"
    run_dir = output_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    config_path = run_dir / "config.json"
    episodes_path = run_dir / "episodes.jsonl"
    report_path = run_dir / "report.json"
    summary_path = run_dir / "summary.md"
    config_path.write_text(json.dumps(config_data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    episodes_path.write_text(episodes_payload, encoding="utf-8")

    report = {
        "schema_version": "1.0",
        "run_id": run_id,
        "benchmark": config.name,
        "config_digest": f"sha256:{config_digest}",
        "result_digest": f"sha256:{result_digest}",
        "git_commit": git_revision(project_root),
        "runtime": {
            "python": sys.version.split()[0],
            "platform": platform.platform(),
            "wall_time_seconds": result["wall_time_seconds"],
        },
        "backend_evidence": result["backend_evidence"],
        "metrics": result["metrics"],
        "example_recovery": next(
            (
                row
                for row in result["episodes"]
                if not row["baseline"]["success"] and row["recovery"]["success"]
            ),
            result["episodes"][0] if result["episodes"] else None,
        ),
    }
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    summary_path.write_text(_markdown_summary(report), encoding="utf-8")

    manifest = {
        "schema_version": "1.0",
        "run_id": run_id,
        "files": {
            path.name: {"sha256": sha256_file(path), "bytes": path.stat().st_size}
            for path in (config_path, episodes_path, report_path, summary_path)
        },
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "LATEST").write_text(run_id + "\n", encoding="utf-8")
    return run_dir, report


def _markdown_summary(report: dict[str, Any]) -> str:
    metrics = report["metrics"]
    evidence = report["backend_evidence"]
    return f"""# RoboRecover evaluation {report['run_id']}

## Result

- Episodes: {metrics['episodes']}
- Baseline success: {metrics['baseline_success_rate']:.2%}
- Recovery success: {metrics['recovery_success_rate']:.2%}
- Failure recovery rate: {metrics['failure_recovery_rate']:.2%}
- Mean retries: {metrics['mean_retries']:.3f}

## Backend evidence

- Backend: {evidence['backend']}
- Engine: {evidence['engine']}
- ROCm verified: {evidence['rocm_verified']}
- Claim boundary: {evidence.get('claim_boundary', 'none')}

## Reproducibility

- Config digest: `{report['config_digest']}`
- Result digest: `{report['result_digest']}`
- Git commit: `{report['git_commit']}`
"""

