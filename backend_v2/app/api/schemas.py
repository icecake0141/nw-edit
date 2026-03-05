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
"""API schemas for v2 backend."""

from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class CreateJobRequest(BaseModel):
    """Payload to create a job."""

    job_name: str = Field(min_length=1, max_length=200)
    creator: str = Field(min_length=1, max_length=100)
    global_vars: Dict[str, str] = Field(default_factory=dict)


class JobResponse(BaseModel):
    """Job response payload."""

    job_id: str
    job_name: str
    creator: str
    status: str
    created_at: str
    global_vars: Dict[str, str] = Field(default_factory=dict)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class DeviceTargetPayload(BaseModel):
    """Device target for job execution payload."""

    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)


class RunJobRequest(BaseModel):
    """Payload to run a job in scaffold mode."""

    devices: Optional[List[DeviceTargetPayload]] = None
    canary: Optional[DeviceTargetPayload] = None
    commands: List[str] = Field(min_length=1)
    verify_commands: Optional[List[str]] = None
    verify_mode: str = Field(default="all")
    imported_device_keys: Optional[List[str]] = None
    concurrency_limit: int = Field(default=5, ge=1, le=100)
    stagger_delay: float = Field(default=0.0, ge=0.0, le=60.0)
    stop_on_error: bool = True
    non_canary_retry_limit: int = Field(default=1, ge=0, le=3)
    retry_backoff_seconds: float = Field(default=0.0, ge=0.0, le=60.0)


class DeviceRunResponse(BaseModel):
    """Device execution output."""

    status: str
    attempts: int
    error: Optional[str] = None
    error_code: Optional[str] = None
    logs: List[str]
    pre_output: str = ""
    apply_output: str = ""
    post_output: str = ""
    diff: str = ""
    diff_truncated: bool = False
    diff_original_size: int = 0
    log_trimmed: bool = False


class RunJobResponse(BaseModel):
    """Aggregated run response."""

    job_id: str
    status: str
    commands: List[str] = Field(default_factory=list)
    verify_commands: List[str] = Field(default_factory=list)
    target_device_keys: List[str] = Field(default_factory=list)
    device_results: Dict[str, DeviceRunResponse]


class PresetCreateRequest(BaseModel):
    """Payload to create an execution preset."""

    name: str = Field(min_length=1, max_length=200)
    os_model: str = Field(min_length=1, max_length=100)
    commands: List[str] = Field(min_length=1)
    verify_commands: List[str] = Field(default_factory=list)


class PresetUpdateRequest(BaseModel):
    """Payload to update an execution preset."""

    name: str = Field(min_length=1, max_length=200)
    os_model: str = Field(min_length=1, max_length=100)
    commands: List[str] = Field(min_length=1)
    verify_commands: List[str] = Field(default_factory=list)


class PresetResponse(BaseModel):
    """Execution preset response payload."""

    preset_id: str
    name: str
    os_model: str
    commands: List[str]
    verify_commands: List[str]
    created_at: str
    updated_at: str


class DeviceProfileResponse(BaseModel):
    """Imported device representation."""

    host: str
    port: int
    device_type: str
    username: str
    password: str
    name: Optional[str] = None
    verify_cmds: List[str]
    host_vars: Dict[str, str] = Field(default_factory=dict)
    connection_ok: bool
    error_message: Optional[str] = None


class FailedRowResponse(BaseModel):
    """Failed CSV row details."""

    row_number: int
    row: Dict[str, str]
    error: str


class DeviceImportResponse(BaseModel):
    """Import response payload."""

    devices: List[DeviceProfileResponse]
    failed_rows: List[FailedRowResponse]


class StatusCommandRequest(BaseModel):
    """Payload for read-only status command execution."""

    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=22, ge=1, le=65535)
    commands: str = Field(min_length=1)


class StatusCommandResponse(BaseModel):
    """Status command execution response."""

    output: str


class ExecutionEventResponse(BaseModel):
    """Execution event payload."""

    type: str
    job_id: str
    timestamp: str
    device: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None


class ActiveJobResponse(BaseModel):
    """Active job response."""

    active: bool
    job: Optional[JobResponse] = None


class RuntimeModesResponse(BaseModel):
    """Runtime mode response."""

    worker_mode: str
    validator_mode: str
