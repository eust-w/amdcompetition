#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

.venv/bin/python -m pytest
npm --prefix dashboard ci
npm --prefix dashboard run build

.venv/bin/roborecover evaluate --backend analytic --output runs/repro-a
.venv/bin/roborecover evaluate --backend analytic --output runs/repro-b

left="runs/repro-a/$(tr -d '\n' < runs/repro-a/LATEST)/report.json"
right="runs/repro-b/$(tr -d '\n' < runs/repro-b/LATEST)/report.json"
.venv/bin/roborecover verify-repro \
  --left "$left" \
  --right "$right" \
  --certificate runs/reproducibility.json \
  --tolerance 0

