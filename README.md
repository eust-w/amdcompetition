# RoboRecover

RoboRecover is a paired, reproducible benchmark for detecting and recovering from robotic grasp failures. It compares an unchanged baseline with an observe–grasp–verify–diagnose–retry controller on identical seeded scenarios and emits evidence suitable for competition review.

The repository deliberately separates three claims:

| Backend | Purpose | What it proves |
| --- | --- | --- |
| `analytic` | dependency-free CI and metric calibration | deterministic orchestration, recovery logic, metrics and artifacts; **not physics or ROCm** |
| `genesis-cpu` | local physical smoke test | Genesis Franka/cube control loop; **not Radeon** |
| `genesis-rocm` | competition acceptance | Genesis physics running through `gs.amdgpu` after HIP and single-GPU gates pass |

No result is labelled ROCm-verified unless the runtime exposes Linux, a HIP-enabled PyTorch build, `/dev/kfd`, and exactly one visible device when strict mode is enabled.

## What is implemented

- Deterministic failure injection for empty grasps, slips and pose offsets.
- Paired baseline/recovery trials using the exact same scenario.
- Failure detection and a bounded recovery state machine with at most one retry by default.
- A physical Genesis Franka/cube backend and a dependency-free analytic test backend.
- Per-episode JSONL, aggregate metrics, content hashes, config/result digests and a Markdown summary.
- Independent-run reproducibility comparison and a machine-readable certificate.
- A React evaluation console backed only by current run artifacts.
- A strict ROCm preflight and a pinned Radeon container recipe.

## Quick start

Python 3.10–3.13 and Node.js are required for the full local experience.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[test]'
npm --prefix dashboard ci

.venv/bin/pytest
.venv/bin/roborecover evaluate --backend analytic
npm --prefix dashboard run build
.venv/bin/roborecover serve --backend analytic
```

Open <http://127.0.0.1:8787>. The button in the header launches a real local evaluation through the same-origin API; it does not fabricate UI-only results.

## Reproduce the metric result

```bash
.venv/bin/roborecover evaluate --backend analytic --output runs/repro-a
.venv/bin/roborecover evaluate --backend analytic --output runs/repro-b

LEFT="runs/repro-a/$(cat runs/repro-a/LATEST)/report.json"
RIGHT="runs/repro-b/$(cat runs/repro-b/LATEST)/report.json"
.venv/bin/roborecover verify-repro --left "$LEFT" --right "$RIGHT" --tolerance 0
```

The default analytic benchmark contains 400 paired episodes. Its result is a calibration/CI result and must not be presented as physical performance.

## Radeon / ROCm acceptance

Build on a Linux Radeon host with Docker access to `/dev/kfd` and `/dev/dri`:

```bash
docker build -f docker/Dockerfile.rocm -t roborecover:rocm .
docker run --rm \
  --device=/dev/kfd \
  --device=/dev/dri \
  --group-add=video \
  --ipc=host \
  --security-opt seccomp=unconfined \
  -v "$PWD/runs:/workspace/runs" \
  roborecover:rocm check-rocm
```

Then execute the full two-run gate:

```bash
docker run --rm \
  --device=/dev/kfd --device=/dev/dri --group-add=video \
  --ipc=host --security-opt seccomp=unconfined \
  -v "$PWD/runs:/workspace/runs" \
  --entrypoint bash roborecover:rocm scripts/acceptance_rocm.sh
```

The acceptance script fails closed: it must produce two `genesis-rocm` reports, both must say `rocm_verified: true`, and their metric deltas must stay within the configured tolerance. See [ROCm acceptance](docs/rocm-acceptance.md).

## Evidence layout

Each run is content-addressed:

```text
runs/
├── LATEST
├── reproducibility.json
└── run-<backend>-<config>-<result>/
    ├── config.json
    ├── episodes.jsonl
    ├── manifest.json
    ├── report.json
    └── summary.md
```

`report.json` carries the explicit backend claim boundary. `manifest.json` records SHA-256 and byte size for each submitted artifact.

## Design and scope

- [Architecture](docs/architecture.md)
- [Dashboard visual specification](docs/dashboard-design.md)
- [Competition report](docs/competition-report.md)
- [ROCm acceptance](docs/rocm-acceptance.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)

## License

Original RoboRecover code is licensed under Apache License 2.0. Genesis is not copied into this repository; the ROCm container installs an exact Apache-2.0-licensed upstream commit. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

