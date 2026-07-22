# Radeon / ROCm acceptance

## Passing definition

A competition run is accepted only when all of the following are true:

1. The host is Linux and exposes `/dev/kfd`.
2. PyTorch reports a non-empty `torch.version.hip`.
3. `torch.cuda.is_available()` is true under the ROCm compatibility API.
4. Exactly one device is visible in strict competition mode.
5. Genesis initializes explicitly with `gs.amdgpu`.
6. The physical Franka/cube baseline and recovery branches finish.
7. Two independent runs use the same config/backend and remain within the metric tolerance.
8. Both reports carry `rocm_verified: true` and include HIP/device metadata.

The local macOS machine cannot satisfy items 1–4. A local analytic or Genesis CPU result is therefore never upgraded to a Radeon claim.

## Commands

```bash
roborecover check-rocm
roborecover evaluate --backend genesis-rocm --config configs/benchmark.json --output runs/rocm-a
roborecover evaluate --backend genesis-rocm --config configs/benchmark.json --output runs/rocm-b

LEFT="runs/rocm-a/$(cat runs/rocm-a/LATEST)/report.json"
RIGHT="runs/rocm-b/$(cat runs/rocm-b/LATEST)/report.json"
roborecover verify-repro \
  --left "$LEFT" \
  --right "$RIGHT" \
  --certificate runs/reproducibility.json \
  --tolerance 0.02
```

The `0.02` tolerance applies to aggregate rates because parallel floating-point physics may not be bit-identical. The raw episodes and result digests remain available for inspection.

## Required evidence to retain

- `check-rocm` JSON output.
- Both run directories and `reproducibility.json`.
- Container image identifier/digest.
- Git commit used for the run.
- Optional real simulation frame or video, hashed in the run manifest.

