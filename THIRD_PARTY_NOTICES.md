# Third-party notices

RoboRecover original source code is Apache-2.0 licensed. No source from the user's internal projects is copied into this repository.

## Genesis

- Project: Genesis World
- Source: <https://github.com/Genesis-Embodied-AI/genesis-world>
- Pinned commit in the ROCm container: `a253ec5c043807cb0f785fd5e5adc865b248e34a`
- License: Apache License 2.0
- Usage: optional runtime dependency for the physical Franka/cube backend

The implementation calls public Genesis APIs and does not vendor Genesis source.

## Dashboard dependencies

The dashboard dependency graph and resolved versions are recorded in `dashboard/package-lock.json`. Key packages include React, Vite, TypeScript and Lucide React. Their upstream licenses remain applicable.

## ROCm container

`docker/Dockerfile.rocm` references an AMD ROCm/PyTorch base image. The base image and bundled components retain their respective upstream licenses. Review the image's license inventory before redistributing the built container; the Dockerfile itself does not relicense those components.

