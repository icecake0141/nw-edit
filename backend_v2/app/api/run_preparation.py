# Copyright 2026 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This file was created or modified with the assistance of an AI (Large Language Model).
# Review required for correctness, security, and licensing.
"""Helpers for validating and preparing job run requests."""

from __future__ import annotations

from dataclasses import dataclass

from fastapi import HTTPException

from backend_v2.app.api.schemas import RunJobRequest
from backend_v2.app.application.command_template import render_commands
from backend_v2.app.application.execution_engine import ExecutionConfig
from backend_v2.app.domain.models import DeviceTarget, JobRecord
from backend_v2.app.infrastructure.in_memory_device_store import InMemoryDeviceStore
from backend_v2.app.infrastructure.in_memory_job_store import InMemoryJobStore


@dataclass(frozen=True)
class PreparedRun:
    """Validated run request with rendered per-device commands."""

    job: JobRecord
    devices: list[DeviceTarget]
    canary: DeviceTarget
    commands_by_device: dict[str, list[str]]
    verify_commands_by_device: dict[str, list[str]]
    config: ExecutionConfig


def resolve_run_targets(
    payload: RunJobRequest,
    device_store: InMemoryDeviceStore,
) -> tuple[list[DeviceTarget], DeviceTarget]:
    """Resolve imported device keys and canary payload to execution targets."""
    extra_fields = payload.model_extra or {}
    if "devices" in extra_fields:
        raise HTTPException(
            status_code=400,
            detail="devices is no longer supported; use imported_device_keys",
        )
    if payload.imported_device_keys is None:
        raise HTTPException(
            status_code=400,
            detail="imported_device_keys is required",
        )
    if not payload.imported_device_keys:
        raise HTTPException(
            status_code=400,
            detail="imported_device_keys cannot be empty",
        )
    imported_map = {device.key: device for device in device_store.list()}
    missing_keys = [
        key for key in payload.imported_device_keys if key not in imported_map
    ]
    if missing_keys:
        missing = ", ".join(missing_keys)
        raise HTTPException(
            status_code=400,
            detail=f"Unknown imported_device_keys: {missing}",
        )
    devices = [
        DeviceTarget(host=imported_map[key].host, port=imported_map[key].port)
        for key in payload.imported_device_keys
    ]

    if payload.canary is None:
        raise HTTPException(
            status_code=400,
            detail="canary is required",
        )
    canary = DeviceTarget(host=payload.canary.host, port=payload.canary.port)
    if canary.key not in {device.key for device in devices}:
        raise HTTPException(
            status_code=400,
            detail="Canary device must be in the device list",
        )
    return devices, canary


def prepare_run(
    job_id: str,
    payload: RunJobRequest,
    job_store: InMemoryJobStore,
    device_store: InMemoryDeviceStore,
) -> PreparedRun:
    """Validate a run request and render commands for each target device."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    devices, canary = resolve_run_targets(payload, device_store=device_store)
    command_scope = (payload.command_scope or "all").strip().lower()
    if command_scope not in {"all", "canary"}:
        raise HTTPException(
            status_code=400,
            detail="command_scope must be one of: all, canary",
        )
    if command_scope == "canary":
        devices = [device for device in devices if device.key == canary.key]

    verify_mode = (payload.verify_mode or "all").strip().lower()
    if verify_mode not in {"all", "canary", "none"}:
        raise HTTPException(
            status_code=400,
            detail="verify_mode must be one of: all, canary, none",
        )
    commands_by_device: dict[str, list[str]] = {}
    verify_commands_by_device: dict[str, list[str]] = {}
    for device in devices:
        profile = device_store.get_by_key(device.key)
        merged_vars = dict(job.global_vars)
        if profile is not None:
            merged_vars.update(profile.host_vars)
        rendered, missing = render_commands(payload.commands, merged_vars)
        if missing:
            missing_vars = ", ".join(sorted(missing))
            raise HTTPException(
                status_code=400,
                detail=(f"Missing command variables for {device.key}: {missing_vars}"),
            )
        commands_by_device[device.key] = rendered
        if verify_mode == "none":
            verify_commands_by_device[device.key] = []
            continue

        base_verify_commands = (
            list(payload.verify_commands)
            if payload.verify_commands is not None
            else (list(profile.verify_cmds) if profile is not None else [])
        )
        if verify_mode == "canary" and device.key != canary.key:
            verify_commands_by_device[device.key] = []
        else:
            verify_commands_by_device[device.key] = base_verify_commands

    config = ExecutionConfig(
        concurrency_limit=payload.concurrency_limit,
        stagger_delay=payload.stagger_delay,
        stop_on_error=payload.stop_on_error,
        non_canary_retry_limit=payload.non_canary_retry_limit,
        retry_backoff_seconds=payload.retry_backoff_seconds,
    )
    return PreparedRun(
        job=job,
        devices=devices,
        canary=canary,
        commands_by_device=commands_by_device,
        verify_commands_by_device=verify_commands_by_device,
        config=config,
    )
