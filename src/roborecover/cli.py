from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .artifacts import write_run
from .backends.genesis_backend import ROCmValidationError, probe_rocm
from .config import load_config
from .runner import run_benchmark
from .server import create_backend, serve_dashboard


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _add_common_backend(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--backend",
        choices=("analytic", "genesis-cpu", "genesis-rocm"),
        default="analytic",
        help="analytic is CI-only; genesis-rocm is the competition acceptance backend",
    )


def build_parser() -> argparse.ArgumentParser:
    root = _project_root()
    parser = argparse.ArgumentParser(prog="roborecover")
    subparsers = parser.add_subparsers(dest="command", required=True)

    evaluate = subparsers.add_parser("evaluate", help="run paired baseline/recovery evaluation")
    evaluate.add_argument("--config", type=Path, default=root / "configs" / "benchmark.json")
    evaluate.add_argument("--output", type=Path, default=root / "runs")
    _add_common_backend(evaluate)

    probe = subparsers.add_parser("check-rocm", help="validate HIP and the visible Radeon GPU")
    probe.add_argument("--allow-multiple-gpus", action="store_true")

    verify = subparsers.add_parser("verify-repro", help="compare two independent report files")
    verify.add_argument("--left", type=Path, required=True)
    verify.add_argument("--right", type=Path, required=True)
    verify.add_argument("--certificate", type=Path, default=root / "runs" / "reproducibility.json")
    verify.add_argument("--tolerance", type=float, default=0.0)

    serve = subparsers.add_parser("serve", help="serve the built dashboard and local evaluation API")
    serve.add_argument("--host", default="127.0.0.1")
    serve.add_argument("--port", type=int, default=8787)
    serve.add_argument("--config", type=Path, default=root / "configs" / "benchmark.json")
    serve.add_argument("--runs", type=Path, default=root / "runs")
    _add_common_backend(serve)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    root = _project_root()
    try:
        if args.command == "check-rocm":
            result = probe_rocm(strict_single_gpu=not args.allow_multiple_gpus)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["passed"] else 2
        if args.command == "verify-repro":
            result = _verify_reproducibility(args.left, args.right, args.tolerance)
            args.certificate.parent.mkdir(parents=True, exist_ok=True)
            args.certificate.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result["passed"] else 3
        if args.command == "evaluate":
            config = load_config(args.config)
            backend = create_backend(args.backend, config.success_height_m, config.strict_single_gpu)
            result = run_benchmark(config, backend)
            run_dir, report = write_run(root, args.output, config, result)
            print(
                json.dumps(
                    {
                        "run_dir": str(run_dir),
                        "run_id": report["run_id"],
                        "result_digest": report["result_digest"],
                        "metrics": report["metrics"],
                        "backend_evidence": report["backend_evidence"],
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return 0
        if args.command == "serve":
            serve_dashboard(root, args.host, args.port, args.config, args.runs, args.backend)
            return 0
    except (ROCmValidationError, FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 1


def _verify_reproducibility(left_path: Path, right_path: Path, tolerance: float) -> dict:
    if tolerance < 0:
        raise ValueError("tolerance must be non-negative")
    left = json.loads(left_path.read_text(encoding="utf-8"))
    right = json.loads(right_path.read_text(encoding="utf-8"))
    metric_keys = (
        "baseline_success_rate",
        "recovery_success_rate",
        "failure_recovery_rate",
        "failure_detection_rate",
        "mean_retries",
        "absolute_success_lift",
    )
    deltas = {
        key: round(abs(float(left["metrics"][key]) - float(right["metrics"][key])), 12)
        for key in metric_keys
    }
    same_config = left["config_digest"] == right["config_digest"]
    digest_match = left["result_digest"] == right["result_digest"]
    backend_match = left["backend_evidence"]["backend"] == right["backend_evidence"]["backend"]
    passed = same_config and backend_match and all(delta <= tolerance for delta in deltas.values())
    return {
        "schema_version": "1.0",
        "passed": passed,
        "tolerance": tolerance,
        "same_config": same_config,
        "same_backend": backend_match,
        "result_digest_match": digest_match,
        "left_run_id": left["run_id"],
        "right_run_id": right["run_id"],
        "left_result_digest": left["result_digest"],
        "right_result_digest": right["result_digest"],
        "metric_deltas": deltas,
        "backend": left["backend_evidence"]["backend"],
        "rocm_verified_both": bool(
            left["backend_evidence"].get("rocm_verified")
            and right["backend_evidence"].get("rocm_verified")
        ),
    }


if __name__ == "__main__":
    raise SystemExit(main())
