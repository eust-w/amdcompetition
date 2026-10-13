<div align="center">
  <img src="docs/readme/hero.svg" alt="RoboRecover — workflow overview" width="100%">
  <h1>RoboRecover</h1>
  <p><strong>A reproducible benchmark for detecting and recovering from grasp failures.</strong></p>
  <p><a href="https://github.com/eust-w/amdcompetition/actions/workflows/ci.yml"><img alt="CI" src="https://img.shields.io/github/actions/workflow/status/eust-w/amdcompetition/ci.yml?branch=main&amp;style=flat-square&amp;label=CI"></a>
  <img alt="Python: 3.10–3.13" src="https://img.shields.io/badge/Python-3.10%E2%80%933.13-3776ab?style=flat-square">
  <img alt="Backends: Analytic / Genesis" src="https://img.shields.io/badge/Backends-Analytic%20%2F%20Genesis-db7353?style=flat-square">
  <img alt="Code license: Apache-2.0" src="https://img.shields.io/badge/Code%20license-Apache--2.0-d99536?style=flat-square"></p>
  <p>
    <a href="#overview">Overview</a> ·
    <a href="#quick-start">Quick start</a> ·
    <a href="#workflow">Workflow</a> ·
    <a href="#validation">Validation</a> ·
    <a href="#documentation">Documentation</a>
  </p>
  <p><a href="README.md">English</a> · <a href="README.zh-CN.md">简体中文</a></p>
</div>

---

<a id="overview"></a>
## Measure the recovery, not just the grasp

**RoboRecover** compares an unchanged baseline with an **observe → grasp → verify → diagnose → retry** controller on the same seeded scenarios. Every run produces episode records, aggregate metrics and content hashes for inspection and reproducibility checks.

| Paired experiments | Bounded recovery | Inspectable evidence |
| :--- | :--- | :--- |
| Baseline and recovery use identical scenarios | Empty grasps, slips and pose offsets; at most one retry by default | JSONL episodes, metric reports, manifests and a local evaluation console |

> [!IMPORTANT]
> The analytic backend is a deterministic calibration/CI path. It does not demonstrate physical grasping or ROCm execution. Hardware claims belong to the corresponding backend and its acceptance artifacts.

<a id="quick-start"></a>
## Quick start

Use **Python 3.10–3.13**. The optional dashboard uses Node.js; CI uses Node.js 22.

```bash
git clone https://github.com/eust-w/amdcompetition.git
cd amdcompetition
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[test]'

roborecover evaluate --backend analytic
```

### Open the evaluation console

```bash
npm --prefix dashboard ci
npm --prefix dashboard run build
roborecover serve --backend analytic
```

Open **<http://127.0.0.1:8787>**. The console reads run artifacts and launches evaluations through the local API; a displayed analytic run remains an analytic result.

<a id="workflow"></a>
## From a failed grasp to a comparable result

```text
Seeded scenario ──┬── baseline controller ───────────────┐
                  │                                      │
                  └── grasp → verify → diagnose → retry ─┤
                                                         ▼
                                        paired episodes + aggregate metrics
                                                         │
                                               hashes + reproducibility check
```

### Choose the evidence level

| Backend | Purpose | What it establishes |
| :--- | :--- | :--- |
| `analytic` | Fast calibration and CI | Recovery logic, metrics and artifact generation |
| `genesis-cpu` | Physical smoke experiments | Genesis Franka/cube execution on CPU |
| `genesis-rocm` | Radeon acceptance | Physical execution through `gs.amdgpu`, subject to strict runtime gates |

The ROCm gate checks Linux, HIP-enabled PyTorch, `/dev/kfd` and a single visible GPU in strict mode. A local unit test or dashboard screenshot is not a replacement for that gate.

<a id="validation"></a>
## Reproduce and compare two runs

```bash
python -m pytest
roborecover evaluate --backend analytic --output runs/repro-a
roborecover evaluate --backend analytic --output runs/repro-b

LEFT="runs/repro-a/$(cat runs/repro-a/LATEST)/report.json"
RIGHT="runs/repro-b/$(cat runs/repro-b/LATEST)/report.json"
roborecover verify-repro --left "$LEFT" --right "$RIGHT" --tolerance 0
```

The default analytic configuration contains **400 paired episodes**. Its numbers calibrate the benchmark; they must not be quoted as physical performance.

<details>
<summary><strong>Run the Radeon / ROCm acceptance path</strong></summary>

On a Linux Radeon host with Docker and the required devices:

```bash
docker build -f docker/Dockerfile.rocm -t roborecover:rocm .
docker run --rm \
  --device=/dev/kfd --device=/dev/dri --group-add=video \
  --ipc=host --security-opt seccomp=unconfined \
  -v "$PWD/runs:/workspace/runs" \
  roborecover:rocm check-rocm

docker run --rm \
  --device=/dev/kfd --device=/dev/dri --group-add=video \
  --ipc=host --security-opt seccomp=unconfined \
  -v "$PWD/runs:/workspace/runs" \
  --entrypoint bash roborecover:rocm scripts/acceptance_rocm.sh
```

Both physical reports must record `rocm_verified: true`, and the comparison must meet the configured tolerance. See [acceptance details](docs/rocm-acceptance.md).

</details>

### What a run leaves behind

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

`report.json` records the backend and claim boundary. `manifest.json` records artifact sizes and SHA-256 hashes. The reproducibility certificate is produced by the comparison step.

<a id="documentation"></a>
## Documentation

| Guide | Focus |
| :--- | :--- |
| [Architecture](docs/architecture.md) | Scenario, controller, runner and artifact boundaries |
| [Dashboard design](docs/dashboard-design.md) | Evaluation console |
| [Competition report](docs/competition-report.md) | Submission context and evidence |
| [ROCm acceptance](docs/rocm-acceptance.md) | Runtime and two-run gates |
| [Third-party notices](THIRD_PARTY_NOTICES.md) | Genesis and dependency provenance |

## License

Original code is [Apache-2.0](LICENSE). Genesis is an external dependency pinned by the ROCm container recipe. Container components retain their upstream licenses; see [third-party notices](THIRD_PARTY_NOTICES.md).
