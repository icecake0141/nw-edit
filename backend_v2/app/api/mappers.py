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
"""Mapping helpers from domain models to API response schemas."""

from __future__ import annotations

from backend_v2.app.api.schemas import (
    DeviceProfileResponse,
    DeviceRunResponse,
    JobResponse,
    PresetResponse,
    RunJobResponse,
)
from backend_v2.app.domain.models import (
    DeviceProfile,
    ExecutionPreset,
    JobRecord,
    JobRunSummary,
)


def to_job_response(job: JobRecord) -> JobResponse:
    """Convert a job domain model to an API response."""
    return JobResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        creator=job.creator,
        status=job.status.value,
        created_at=job.created_at,
        global_vars=job.global_vars,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def to_run_response(summary: JobRunSummary) -> RunJobResponse:
    """Convert an execution summary to an API response."""
    return RunJobResponse(
        job_id=summary.job_id,
        status=summary.status.value,
        commands=summary.commands,
        verify_commands=summary.verify_commands,
        target_device_keys=summary.target_device_keys,
        device_results={
            key: DeviceRunResponse(
                status=result.status,
                attempts=result.attempts,
                error=result.error,
                error_code=result.error_code,
                logs=result.logs,
                pre_output=result.pre_output or "",
                apply_output=result.apply_output or "",
                post_output=result.post_output or "",
                diff=result.diff or "",
                diff_truncated=result.diff_truncated,
                diff_original_size=result.diff_original_size,
                log_trimmed=result.log_trimmed,
            )
            for key, result in summary.device_results.items()
        },
    )


def to_preset_response(preset: ExecutionPreset) -> PresetResponse:
    """Convert an execution preset domain model to an API response."""
    return PresetResponse(
        preset_id=preset.preset_id,
        name=preset.name,
        os_model=preset.os_model,
        commands=preset.commands,
        verify_commands=preset.verify_commands,
        created_at=preset.created_at,
        updated_at=preset.updated_at,
    )


def to_device_profile_response(device: DeviceProfile) -> DeviceProfileResponse:
    """Convert an imported device profile to an API response."""
    return DeviceProfileResponse(
        host=device.host,
        port=device.port,
        device_type=device.device_type,
        username=device.username,
        password=device.password,
        name=device.name,
        verify_cmds=device.verify_cmds,
        host_vars=device.host_vars,
        prod=device.prod,
        connection_ok=device.connection_ok,
        error_message=device.error_message,
    )
