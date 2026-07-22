from __future__ import annotations

import os
import platform
from importlib import metadata
from typing import Any

from ..models import AttemptCommand, AttemptResult, FailureKind, Scenario
from .base import EvaluationBackend


class ROCmValidationError(RuntimeError):
    pass


def probe_rocm(strict_single_gpu: bool = True) -> dict[str, Any]:
    try:
        import torch
    except ImportError as exc:
        raise ROCmValidationError("PyTorch is not installed") from exc

    hip_version = getattr(torch.version, "hip", None)
    device_count = torch.cuda.device_count() if torch.cuda.is_available() else 0
    devices = [torch.cuda.get_device_name(index) for index in range(device_count)]
    errors: list[str] = []
    if platform.system() != "Linux":
        errors.append("ROCm validation requires Linux")
    if not hip_version:
        errors.append("PyTorch was not built with HIP/ROCm")
    if not torch.cuda.is_available():
        errors.append("HIP device is not available through torch.cuda")
    if strict_single_gpu and device_count != 1:
        errors.append(f"strict single-GPU mode expected 1 visible device, found {device_count}")
    if not os.path.exists("/dev/kfd"):
        errors.append("/dev/kfd is not mounted")
    return {
        "platform": platform.platform(),
        "torch_version": torch.__version__,
        "hip_version": hip_version,
        "device_count": device_count,
        "devices": devices,
        "dev_kfd": os.path.exists("/dev/kfd"),
        "strict_single_gpu": strict_single_gpu,
        "passed": not errors,
        "errors": errors,
    }


class GenesisBackend(EvaluationBackend):
    """Physical Franka/cube grasp backend using Genesis.

    ``genesis-rocm`` refuses to start unless HIP and the single visible Radeon
    device gate pass. ``genesis-cpu`` is provided only for development smoke
    tests and is labelled accordingly in every artifact.
    """

    def __init__(self, mode: str, success_height_m: float, strict_single_gpu: bool = True) -> None:
        if mode not in {"genesis-cpu", "genesis-rocm"}:
            raise ValueError(f"unsupported Genesis mode: {mode}")
        self.name = mode
        self.success_height_m = success_height_m
        self.strict_single_gpu = strict_single_gpu
        self._rocm_probe: dict[str, Any] | None = None

        import genesis as gs
        import numpy as np

        self.gs = gs
        self.np = np
        if mode == "genesis-rocm":
            self._rocm_probe = probe_rocm(strict_single_gpu)
            if not self._rocm_probe["passed"]:
                raise ROCmValidationError("; ".join(self._rocm_probe["errors"]))
            gs.init(backend=gs.amdgpu, precision="32", logging_level="warning", seed=0)
        else:
            gs.init(backend=gs.cpu, precision="32", logging_level="warning", seed=0)

        self.scene = gs.Scene(
            sim_options=gs.options.SimOptions(dt=1.0 / 60.0, substeps=2),
            rigid_options=gs.options.RigidOptions(
                constraint_solver=gs.constraint_solver.Newton,
                enable_collision=True,
                enable_joint_limit=True,
                enable_self_collision=False,
            ),
            show_viewer=False,
        )
        self.scene.add_entity(gs.morphs.Plane())
        self.franka = self.scene.add_entity(
            gs.morphs.MJCF(file="xml/franka_emika_panda/panda.xml"),
            material=gs.materials.Rigid(coup_friction=1.0, friction=1.0),
        )
        self.cube = self.scene.add_entity(
            morph=gs.morphs.Box(size=(0.04, 0.04, 0.04), pos=(0.65, 0.0, 0.02)),
            material=gs.materials.Rigid(coup_friction=1.0, friction=1.0),
            surface=gs.surfaces.Rough(
                diffuse_texture=gs.textures.ColorTexture(color=(0.95, 0.28, 0.22)),
            ),
        )
        self.scene.build()
        self.motors_dof = np.arange(7)
        self.fingers_dof = np.arange(7, 9)
        self.end_effector = self.franka.get_link("hand")
        self.home_qpos = np.array(
            [-1.0124, 1.5559, 1.3662, -1.6878, -1.5799, 1.7757, 1.4602, 0.04, 0.04],
            dtype=np.float32,
        )
        self._active_scenario: Scenario | None = None

    def start_episode(self, scenario: Scenario) -> None:
        self._active_scenario = scenario
        self.franka.set_qpos(self.home_qpos, zero_velocity=True)
        self.cube.set_pos((scenario.object_x_m, scenario.object_y_m, 0.02), zero_velocity=True)
        self.cube.set_quat((1.0, 0.0, 0.0, 0.0), zero_velocity=True)
        for _ in range(3):
            self.scene.step()

    def attempt(
        self,
        scenario: Scenario,
        command: AttemptCommand,
        attempt_index: int,
    ) -> AttemptResult:
        if self._active_scenario != scenario:
            raise RuntimeError("start_episode must be called before attempt")

        cube_pos = self._vector(self.cube.get_pos())
        aim_scale = max(0.0, 1.0 - command.aim_correction)
        pose_scale = max(0.0, 1.0 - command.pose_correction)
        residual_x = scenario.aim_error_x_m * aim_scale
        residual_y = scenario.aim_error_y_m * aim_scale + 0.10 * scenario.pose_error_rad * pose_scale
        aim_error = (residual_x**2 + residual_y**2) ** 0.5
        pose_error = scenario.pose_error_rad * pose_scale
        target_x = float(cube_pos[0]) + residual_x
        target_y = float(cube_pos[1]) + residual_y

        qpos = self.franka.inverse_kinematics(
            link=self.end_effector,
            pos=(target_x, target_y, 0.13),
            quat=(0.0, 1.0, 0.0, 0.0),
        )
        self.franka.control_dofs_position(qpos[..., self.motors_dof], self.motors_dof)
        for _ in range(18):
            self.scene.step()

        grasp_force = -float(command.grip_force)
        for _ in range(12):
            self.franka.control_dofs_force(
                self.np.array([grasp_force, grasp_force], dtype=self.np.float32),
                self.fingers_dof,
            )
            self.scene.step()

        lift_qpos = self.franka.inverse_kinematics(
            link=self.end_effector,
            pos=(target_x, target_y, 0.30),
            quat=(0.0, 1.0, 0.0, 0.0),
        )
        self.franka.control_dofs_position(lift_qpos[..., self.motors_dof], self.motors_dof)
        for _ in range(42):
            self.franka.control_dofs_force(
                self.np.array([grasp_force, grasp_force], dtype=self.np.float32),
                self.fingers_dof,
            )
            self.scene.step()

        object_height = float(self._vector(self.cube.get_pos())[2])
        success = object_height >= self.success_height_m
        hold_margin = command.grip_force * scenario.friction - (0.24 + scenario.disturbance)
        if success:
            failure = FailureKind.NONE
        elif aim_error > 0.08:
            failure = FailureKind.EMPTY_GRASP
        elif pose_error > 0.22:
            failure = FailureKind.POSE_OFFSET
        else:
            failure = FailureKind.SLIP

        confidence = min(
            0.99,
            max(0.0, 0.91 - scenario.sensor_noise * 2.0 - scenario.difficulty * 0.08),
        )
        simulated_latency = 72 * (1000.0 / 60.0)
        states = _physical_states(attempt_index, success, failure, simulated_latency)
        return AttemptResult(
            attempt_index=attempt_index,
            success=success,
            failure_kind=failure,
            confidence=round(confidence, 6),
            aim_error_m=round(aim_error, 6),
            pose_error_rad=round(pose_error, 6),
            hold_margin=round(hold_margin, 6),
            object_height_m=round(object_height, 6),
            simulated_latency_ms=round(simulated_latency, 3),
            states=states,
        )

    def evidence(self) -> dict[str, Any]:
        version = metadata.version("genesis-world")
        if self.name == "genesis-rocm":
            probe = self._rocm_probe or {}
            return {
                "backend": self.name,
                "engine": f"Genesis {version}",
                "physics": True,
                "accelerator": "AMD Radeon via HIP",
                "rocm_verified": bool(probe.get("passed")),
                "hip_version": probe.get("hip_version"),
                "devices": probe.get("devices", []),
                "device_count": probe.get("device_count", 0),
                "strict_single_gpu": self.strict_single_gpu,
                "claim_boundary": "physical Franka/cube closed loop on gs.amdgpu",
            }
        return {
            "backend": self.name,
            "engine": f"Genesis {version}",
            "physics": True,
            "accelerator": "CPU",
            "rocm_verified": False,
            "platform": platform.platform(),
            "claim_boundary": "physical development smoke only; not Radeon evidence",
        }

    @staticmethod
    def _vector(value):
        if hasattr(value, "detach"):
            value = value.detach().cpu().numpy()
        if getattr(value, "ndim", 1) > 1:
            value = value[0]
        return value


def _physical_states(
    attempt_index: int,
    success: bool,
    failure: FailureKind,
    latency_ms: float,
) -> list[dict[str, Any]]:
    offset = attempt_index * 180.0
    states = [
        {"state": "observe", "t_ms": offset, "status": "ok"},
        {"state": "grasp", "t_ms": round(offset + latency_ms * 0.42, 3), "status": "ok"},
        {
            "state": "verify",
            "t_ms": round(offset + latency_ms * 0.82, 3),
            "status": "ok" if success else "failed",
        },
    ]
    states.append(
        {
            "state": "success" if success else "diagnose",
            "t_ms": round(offset + latency_ms, 3),
            "status": "ok" if success else "failed",
            **({} if success else {"failure": failure.value}),
        }
    )
    return states
