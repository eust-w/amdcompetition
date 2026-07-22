#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

python -m roborecover check-rocm
python -m roborecover evaluate \
  --backend genesis-rocm \
  --config configs/benchmark.json \
  --output runs/rocm-a
python -m roborecover evaluate \
  --backend genesis-rocm \
  --config configs/benchmark.json \
  --output runs/rocm-b

left="runs/rocm-a/$(tr -d '\n' < runs/rocm-a/LATEST)/report.json"
right="runs/rocm-b/$(tr -d '\n' < runs/rocm-b/LATEST)/report.json"

python -m roborecover verify-repro \
  --left "$left" \
  --right "$right" \
  --certificate runs/reproducibility.json \
  --tolerance 0.02

python - "$left" "$right" <<'PY'
import json
import sys

for path in sys.argv[1:]:
    report = json.load(open(path, encoding="utf-8"))
    evidence = report["backend_evidence"]
    if evidence["backend"] != "genesis-rocm" or evidence["rocm_verified"] is not True:
        raise SystemExit(f"ROCm evidence gate failed for {path}")
print("ROCm physical closed-loop acceptance passed for both runs")
PY

