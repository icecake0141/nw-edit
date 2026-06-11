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
"""Helpers for running jobs and applying execution control actions."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import HTTPException

from backend_v2.app.api.run_preparation import PreparedRun
from backend_v2.app.application.events import ExecutionEvent, utc_now
from backend_v2.app.application.execution_control import ExecutionControl
from backend_v2.app.application.execution_engine import ExecutionEngine
from backend_v2.app.application.job_service import JobService
from backend_v2.app.domain.models import JobRecord, JobRunSummary
from backend_v2.app.infrastructure.in_memory_control_store import InMemoryControlStore
from backend_v2.app.infrastructure.in_memory_event_store import InMemoryEventStore
from backend_v2.app.infrastructure.in_memory_job_store import InMemoryJobStore
from backend_v2.app.infrastructure.in_memory_run_store import InMemoryRunStore

SUMMARY_EVENT_BY_STATUS = {
    "completed": "complete",
    "cancelled": "cancel",
    "failed": "fail",
}


def reset_run_control(
    job_id: str,
    service: JobService,
    control_store: InMemoryControlStore,
) -> ExecutionControl:
    """Transition a job to running and clear stale pause/cancel flags."""
    try:
        service.apply_event(job_id=job_id, event_name="start")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    control = control_store.get_or_create(job_id)
    control.pause_event.clear()
    control.cancel_event.clear()
    return control


def execute_prepared_run(
    job_id: str,
    prepared: PreparedRun,
    engine: ExecutionEngine,
    control_store: InMemoryControlStore,
    run_store: InMemoryRunStore,
    service: JobService,
    commands: list[str] | None = None,
    verify_commands: list[str] | None = None,
) -> JobRunSummary:
    """Execute a prepared run, persist its summary, and update job state."""
    control = control_store.get_or_create(job_id)
    summary = engine.run_job(
        job_id=job_id,
        devices=prepared.devices,
        canary=prepared.canary,
        commands_by_device=prepared.commands_by_device,
        verify_commands_by_device=prepared.verify_commands_by_device,
        config=prepared.config,
        commands=commands,
        verify_commands=verify_commands,
        control=control,
    )
    run_store.save(summary)
    event_name = SUMMARY_EVENT_BY_STATUS.get(summary.status.value)
    if event_name is not None:
        try:
            service.apply_event(job_id=job_id, event_name=event_name)
        except ValueError:
            pass
    return summary


def publish_job_status(
    event_store: InMemoryEventStore,
    job_id: str,
    status: str,
    message: str,
) -> None:
    """Publish a job_status event."""
    event_store.publish(
        ExecutionEvent(
            type="job_status",
            job_id=job_id,
            timestamp=utc_now(),
            status=status,
            message=message,
        )
    )


def request_pause(control: ExecutionControl) -> None:
    """Set the pause flag for a running job."""
    control.pause_event.set()


def request_resume(control: ExecutionControl) -> None:
    """Clear the pause flag for a paused job."""
    control.pause_event.clear()


def request_cancel(control: ExecutionControl) -> None:
    """Set cancel and clear pause so a paused job can observe cancellation."""
    control.cancel_event.set()
    control.pause_event.clear()


def apply_control_action(
    job_id: str,
    job_store: InMemoryJobStore,
    control_store: InMemoryControlStore,
    service: JobService,
    event_store: InMemoryEventStore,
    event_name: str,
    status: str,
    message: str,
    mutate_control: Callable[[ExecutionControl], None],
) -> JobRecord:
    """Apply pause/resume/cancel control flags and lifecycle transition."""
    job = job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    control = control_store.get(job_id)
    if control is None:
        raise HTTPException(status_code=409, detail="No run control available")

    mutate_control(control)
    try:
        job = service.apply_event(job_id=job_id, event_name=event_name)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    publish_job_status(
        event_store=event_store,
        job_id=job_id,
        status=status,
        message=message,
    )
    return job
