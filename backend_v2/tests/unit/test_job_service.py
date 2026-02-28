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
"""Unit tests for v2 job service."""

import pytest

from backend_v2.app.application.job_service import JobService
from backend_v2.app.domain.models import JobStatus
from backend_v2.app.domain.state_machine import JobStateMachine
from backend_v2.app.infrastructure.in_memory_job_store import InMemoryJobStore


def build_service() -> JobService:
    return JobService(
        repository=InMemoryJobStore(),
        state_machine=JobStateMachine(),
    )


def test_create_job_defaults_to_queued():
    service = build_service()
    job = service.create_job(job_name="canary rollout", creator="alice")

    assert job.status == JobStatus.QUEUED
    assert job.created_at
    assert job.started_at is None
    assert job.completed_at is None


def test_apply_events_updates_timestamps():
    service = build_service()
    job = service.create_job(job_name="apply config", creator="bob")

    job = service.apply_event(job.job_id, "start")
    assert job.status == JobStatus.RUNNING
    assert job.started_at is not None
    assert job.completed_at is None

    job = service.apply_event(job.job_id, "complete")
    assert job.status == JobStatus.COMPLETED
    assert job.completed_at is not None


def test_apply_event_rejects_unknown_job():
    service = build_service()

    with pytest.raises(LookupError, match="Job not found"):
        service.apply_event("missing", "start")


def test_apply_event_rejects_invalid_transition():
    service = build_service()
    job = service.create_job(job_name="no-op", creator="carol")
    service.apply_event(job.job_id, "start")
    service.apply_event(job.job_id, "complete")

    with pytest.raises(ValueError, match="Invalid transition"):
        service.apply_event(job.job_id, "resume")
