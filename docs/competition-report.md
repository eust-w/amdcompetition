# RoboRecover competition report

## Executive summary

RoboRecover evaluates whether a robot can recognize and recover from grasp failures instead of treating the first grasp command as terminal. It performs paired baseline and recovery trials on identical seeded scenarios, executes a bounded diagnostic retry, and produces content-addressed evidence.

## Problem

Manipulation policies often report nominal task success while obscuring empty grasps, pose misalignment and object slip. These failures are especially costly in unattended physical-AI workflows because a single failed primitive blocks every downstream step.

## Solution

The controller adds a small, auditable layer around the grasp policy:

1. Observe target and robot state.
2. Execute the original grasp unchanged.
3. Verify object lift.
4. Diagnose empty grasp, pose offset or slip.
5. Correct target pose or grip force.
6. Retry once and record the complete state transition.

The recovery mechanism is policy-agnostic and can wrap a classical controller, behavior-cloned policy or PPO policy.

## Current measured evidence

The current local calibration run contains 400 analytic paired episodes:

| Metric | Result |
| --- | ---: |
| Baseline success | 36.25% |
| Recovery success | 93.25% |
| Failure recovery rate | 89.41% |
| Failure detection rate | 100.00% |
| Mean retries per episode | 0.638 |
| Absolute success lift | 57.00 percentage points |

Two independent analytic runs produced the same SHA-256 result digest with zero metric delta. These numbers validate deterministic orchestration and metric generation only; they are **not physical-simulation or Radeon performance claims**.

## Radeon and ROCm use

The competition backend initializes Genesis with `gs.amdgpu` and refuses to run without HIP, `/dev/kfd`, and the configured single-visible-GPU requirement. Each episode physically resets and controls a Franka arm and cube, then verifies lift by measured cube height.

The current development machine is an Apple M4 Mac and cannot supply ROCm evidence. The repository includes a pinned ROCm container and fail-closed acceptance script for execution on Radeon Cloud or another authorized Radeon Linux host. The report must be updated with those two physical run artifacts before submission.

## Reproducibility

- Versioned JSON benchmark configuration.
- Independent RNG per `(seed, episode_index)`.
- Paired baseline and recovery scenarios.
- Canonical JSON serialization and SHA-256 result digest.
- Per-file manifest hashes.
- Independent-run comparison with explicit tolerance.
- Runtime backend, device, HIP, Python and Git provenance.

## Innovation and application value

The contribution is not a new monolithic grasp policy. It is a measurable recovery layer that turns an open-loop primitive into a closed loop and makes failure behavior inspectable. The same pattern is applicable to bin picking, laboratory automation, kitting and warehouse handling.

## Remaining submission gate

- Run the full `genesis-rocm` benchmark twice on an authorized single-Radeon host.
- Confirm physical recovery improvement and choose tolerances from observed variance.
- Add a real rendered frame/video to the artifact manifest.
- Record the final Git commit and container digest.
- Replace this section with the two ROCm run IDs and verified metrics.

