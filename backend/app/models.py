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
"""Pydantic models for the network device configuration application."""

from typing import Optional, List, Dict
from pydantic import BaseModel, Field
from enum import Enum


class DeviceType(str, Enum):
    """Supported device types."""

    CISCO_IOS = "cisco_ios"
    CISCO_XE = "cisco_xe"
    CISCO_NXOS = "cisco_nxos"
    CISCO_ASA = "cisco_asa"
    ARISTA_EOS = "arista_eos"
    JUNIPER_JUNOS = "juniper_junos"


class DeviceInput(BaseModel):
    """Device input from CSV."""

    host: str
    port: int = 22
    device_type: str
    username: str
    password: str
    name: Optional[str] = None
    verify_cmds: Optional[str] = None  # semicolon-separated


class Device(BaseModel):
    """Device model after validation."""

    host: str
    port: int = 22
    device_type: str
    username: str
    password: str
    name: Optional[str] = None
    verify_cmds: List[str] = Field(default_factory=list)
    connection_ok: bool = False
    error_message: Optional[str] = None


class DeviceImportResponse(BaseModel):
    """Response from device import."""

    devices: List[Device]


class CanaryDevice(BaseModel):
    """Canary device identifier."""

    host: str
    port: int = 22


class VerifyMode(str, Enum):
    """Verification mode."""

    NONE = "none"
    CANARY = "canary"
    ALL = "all"


class JobCreate(BaseModel):
    """Job creation request."""

    job_name: Optional[str] = None
    creator: Optional[str] = None
    devices: List[CanaryDevice] = Field(default_factory=list)  # empty = all
    canary: CanaryDevice
    commands: str  # multiline commands
    verify_only: VerifyMode = VerifyMode.CANARY
    verify_cmds: List[str] = Field(default_factory=list)
    concurrency_limit: int = 5
    stagger_delay: float = 1.0
    stop_on_error: bool = True


class DeviceStatus(str, Enum):
    """Device execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobStatus(str, Enum):
    """Job execution status."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeviceResult(BaseModel):
    """Result for a single device."""

    host: str
    port: int
    status: DeviceStatus = DeviceStatus.QUEUED
    error: Optional[str] = None
    pre_output: Optional[str] = None
    apply_output: Optional[str] = None
    post_output: Optional[str] = None
    diff: Optional[str] = None
    logs: List[str] = Field(default_factory=list)
    log_trimmed: bool = False
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class DeviceParams(BaseModel):
    """Device connection parameters snapshot for job execution."""

    host: str
    port: int
    device_type: str
    username: str
    password: str
    verify_cmds: List[str] = Field(default_factory=list)


class Job(BaseModel):
    """Job model."""

    job_id: str
    job_name: Optional[str] = None
    creator: Optional[str] = None
    status: JobStatus = JobStatus.QUEUED
    canary: CanaryDevice
    commands: str
    verify_only: VerifyMode = VerifyMode.CANARY
    verify_cmds: List[str] = Field(default_factory=list)
    concurrency_limit: int = 5
    stagger_delay: float = 1.0
    stop_on_error: bool = True
    device_results: Dict[str, DeviceResult] = Field(default_factory=dict)
    device_params: Dict[str, DeviceParams] = Field(default_factory=dict)
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


class JobResponse(BaseModel):
    """Response from job creation."""

    job_id: str
    status: JobStatus


class StatusCommandRequest(BaseModel):
    """Request to execute read-only status commands on a managed device."""

    host: str
    port: int = 22
    commands: str


class StatusCommandResponse(BaseModel):
    """Response for status command execution."""

    output: str


class WSMessage(BaseModel):
    """WebSocket message base."""

    type: str
    job_id: str


class WSLogMessage(WSMessage):
    """WebSocket log message."""

    type: str = "log"
    device: str
    phase: str  # pre, apply, post
    data: str


class WSDeviceStatusMessage(WSMessage):
    """WebSocket device status message."""

    type: str = "device_status"
    device: str
    status: DeviceStatus
    error: Optional[str] = None


class WSJobCompleteMessage(WSMessage):
    """WebSocket job complete message."""

    type: str = "job_complete"
    status: JobStatus


class WSJobStatusMessage(WSMessage):
    """WebSocket job status message."""

    type: str = "job_status"
    status: JobStatus
