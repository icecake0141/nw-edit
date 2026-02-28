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
"""Application layer use-cases for job lifecycle."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Protocol
from uuid import uuid4

from backend_v2.app.domain.models import JobEvent, JobRecord, JobStatus
from backend_v2.app.domain.state_machine import JobStateMachine


class JobRepository(Protocol):
    """Repository contract for job persistence."""

    def save(self, job: JobRecord) -> None:
        """Store or update a job."""

    def get(self, job_id: str) -> JobRecord | None:
        """Fetch a job by ID."""


def utc_now() -> str:
    """UTC timestamp in ISO format."""
    return datetime.now(timezone.utc).isoformat()


class JobService:
    """Use-case orchestration for job create and status transitions."""

    _event_map = {
        "start": JobEvent.START,
        "pause": JobEvent.PAUSE,
        "resume": JobEvent.RESUME,
        "complete": JobEvent.COMPLETE,
        "fail": JobEvent.FAIL,
        "cancel": JobEvent.CANCEL,
    }

    def __init__(self, repository: JobRepository, state_machine: JobStateMachine):
        self.repository = repository
        self.state_machine = state_machine

    def create_job(self, job_name: str, creator: str) -> JobRecord:
        """Create a queued job."""
        job = JobRecord(
            job_id=str(uuid4()),
            job_name=job_name,
            creator=creator,
            status=JobStatus.QUEUED,
            created_at=utc_now(),
        )
        self.repository.save(job)
        return job

    def apply_event(self, job_id: str, event_name: str) -> JobRecord:
        """Apply transition event to an existing job."""
        if event_name not in self._event_map:
            raise ValueError(f"Unknown event: {event_name}")

        job = self.repository.get(job_id)
        if job is None:
            raise LookupError(f"Job not found: {job_id}")

        event = self._event_map[event_name]
        transition = self.state_machine.transition(job.status, event)
        job.status = transition.next_status

        now = utc_now()
        if event == JobEvent.START and job.started_at is None:
            job.started_at = now
        if job.status in {JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED}:
            job.completed_at = now

        self.repository.save(job)
        return job
