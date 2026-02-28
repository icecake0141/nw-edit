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


class JobResponse(BaseModel):
    """Job response payload."""

    job_id: str
    job_name: str
    creator: str
    status: str
    created_at: str
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
    logs: List[str]
    pre_output: Optional[str] = None
    apply_output: Optional[str] = None
    post_output: Optional[str] = None
    diff: Optional[str] = None
    log_trimmed: bool = False


class RunJobResponse(BaseModel):
    """Aggregated run response."""

    job_id: str
    status: str
    device_results: Dict[str, DeviceRunResponse]


class DeviceProfileResponse(BaseModel):
    """Imported device representation."""

    host: str
    port: int
    device_type: str
    username: str
    password: str
    name: Optional[str] = None
    verify_cmds: List[str]
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
