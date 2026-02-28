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
"""Domain models for the v2 execution engine."""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class JobStatus(str, Enum):
    """Lifecycle states for a job."""

    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobEvent(str, Enum):
    """Events that trigger state transitions."""

    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    COMPLETE = "complete"
    FAIL = "fail"
    CANCEL = "cancel"


@dataclass(frozen=True)
class JobTransition:
    """Single transition entry."""

    current: JobStatus
    event: JobEvent
    next_status: JobStatus


@dataclass
class JobRecord:
    """Job aggregate stored in repository."""

    job_id: str
    job_name: str
    creator: str
    status: JobStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass(frozen=True)
class DeviceTarget:
    """Device connection target."""

    host: str
    port: int = 22

    @property
    def key(self) -> str:
        """Stable key for maps and logs."""
        return f"{self.host}:{self.port}"


@dataclass
class DeviceExecutionResult:
    """Result for one device execution."""

    status: str
    logs: list[str] = field(default_factory=list)
    error: Optional[str] = None
    attempts: int = 1
    pre_output: Optional[str] = None
    apply_output: Optional[str] = None
    post_output: Optional[str] = None
    diff: Optional[str] = None
    log_trimmed: bool = False


@dataclass
class JobRunSummary:
    """Execution summary for all devices."""

    job_id: str
    status: JobStatus
    device_results: dict[str, DeviceExecutionResult] = field(default_factory=dict)


@dataclass
class DeviceProfile:
    """Imported device profile."""

    host: str
    device_type: str
    username: str
    password: str
    port: int = 22
    name: Optional[str] = None
    verify_cmds: list[str] = field(default_factory=list)
    connection_ok: bool = False
    error_message: Optional[str] = None

    @property
    def key(self) -> str:
        return f"{self.host}:{self.port}"
