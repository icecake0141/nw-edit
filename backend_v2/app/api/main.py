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
"""FastAPI entrypoint for backend_v2 scaffold."""

import asyncio
import os

from fastapi import Body, FastAPI, HTTPException
from fastapi import WebSocket, WebSocketDisconnect

from backend_v2.app.api.schemas import (
    ActiveJobResponse,
    CreateJobRequest,
    DeviceImportResponse,
    DeviceProfileResponse,
    DeviceRunResponse,
    ExecutionEventResponse,
    JobResponse,
    RunJobRequest,
    RunJobResponse,
    FailedRowResponse,
)
from backend_v2.app.application.device_import_service import (
    DeviceConnectionValidator,
    DeviceImportService,
)
from backend_v2.app.application.events import ExecutionEvent, utc_now
from backend_v2.app.application.execution_engine import (
    DeviceWorker,
    ExecutionConfig,
    ExecutionEngine,
)
from backend_v2.app.application.job_service import JobService
from backend_v2.app.domain.models import (
    DeviceTarget,
    JobRecord,
    JobRunSummary,
    JobStatus,
)
from backend_v2.app.domain.state_machine import JobStateMachine
from backend_v2.app.infrastructure.device_connection_validators import (
    NetmikoConnectionValidator,
    SimulatedConnectionValidator,
)
from backend_v2.app.infrastructure.in_memory_device_store import InMemoryDeviceStore
from backend_v2.app.infrastructure.in_memory_event_store import InMemoryEventStore
from backend_v2.app.infrastructure.in_memory_job_store import InMemoryJobStore
from backend_v2.app.infrastructure.in_memory_run_store import InMemoryRunStore
from backend_v2.app.infrastructure.in_memory_control_store import InMemoryControlStore
from backend_v2.app.infrastructure.netmiko_device_worker import NetmikoDeviceWorker
from backend_v2.app.infrastructure.run_coordinator import RunCoordinator
from backend_v2.app.infrastructure.simulated_device_worker import SimulatedDeviceWorker

app = FastAPI(
    title="Network Device Configuration Manager v2 (Scaffold)",
    version="0.1.0",
)

store = InMemoryJobStore()
device_store = InMemoryDeviceStore()
event_store = InMemoryEventStore()
run_store = InMemoryRunStore()
control_store = InMemoryControlStore()
run_coordinator = RunCoordinator()
service = JobService(repository=store, state_machine=JobStateMachine())


def resolve_worker_mode() -> str:
    return os.getenv("NW_EDIT_V2_WORKER_MODE", "simulated").strip().lower()


def resolve_validator_mode() -> str:
    return os.getenv("NW_EDIT_V2_VALIDATOR_MODE", "simulated").strip().lower()


if resolve_worker_mode() == "netmiko":
    worker: DeviceWorker = NetmikoDeviceWorker(profile_resolver=device_store.get_by_key)
else:
    worker = SimulatedDeviceWorker()
engine = ExecutionEngine(worker=worker, publisher=event_store)

if resolve_validator_mode() == "netmiko":
    validator: DeviceConnectionValidator = NetmikoConnectionValidator()
else:
    validator = SimulatedConnectionValidator()
device_import_service = DeviceImportService(store=device_store, validator=validator)


def to_response(job: JobRecord) -> JobResponse:
    """Convert domain model to API response."""
    return JobResponse(
        job_id=job.job_id,
        job_name=job.job_name,
        creator=job.creator,
        status=job.status.value,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
    )


def _resolve_run_targets(
    payload: RunJobRequest,
) -> tuple[list[DeviceTarget], DeviceTarget]:
    if payload.devices:
        devices = [DeviceTarget(host=d.host, port=d.port) for d in payload.devices]
    else:
        devices = [DeviceTarget(host=d.host, port=d.port) for d in device_store.list()]
    if not devices:
        raise HTTPException(status_code=400, detail="No devices provided or imported")

    if payload.canary:
        canary = DeviceTarget(host=payload.canary.host, port=payload.canary.port)
    else:
        canary = devices[0]
    return devices, canary


def _to_run_response(summary: JobRunSummary) -> RunJobResponse:
    return RunJobResponse(
        job_id=summary.job_id,
        status=summary.status.value,
        device_results={
            key: DeviceRunResponse(
                status=result.status,
                attempts=result.attempts,
                error=result.error,
                logs=result.logs,
                pre_output=result.pre_output,
                apply_output=result.apply_output,
                post_output=result.post_output,
                diff=result.diff,
                log_trimmed=result.log_trimmed,
            )
            for key, result in summary.device_results.items()
        },
    )


def _execute_run(job_id: str, payload: RunJobRequest) -> JobRunSummary:
    control = control_store.get_or_create(job_id)
    devices, canary = _resolve_run_targets(payload)
    config = ExecutionConfig(
        concurrency_limit=payload.concurrency_limit,
        stagger_delay=payload.stagger_delay,
        stop_on_error=payload.stop_on_error,
        non_canary_retry_limit=payload.non_canary_retry_limit,
        retry_backoff_seconds=payload.retry_backoff_seconds,
    )
    summary = engine.run_job(
        job_id=job_id,
        devices=devices,
        canary=canary,
        commands=payload.commands,
        config=config,
        control=control,
    )
    run_store.save(summary)
    if summary.status.value == "completed":
        try:
            service.apply_event(job_id=job_id, event_name="complete")
        except ValueError:
            pass
    elif summary.status.value == "cancelled":
        try:
            service.apply_event(job_id=job_id, event_name="cancel")
        except ValueError:
            pass
    elif summary.status.value == "failed":
        try:
            service.apply_event(job_id=job_id, event_name="fail")
        except ValueError:
            pass
    return summary


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint."""
    return {"status": "ok"}


@app.post("/api/v2/devices/import", response_model=DeviceImportResponse)
def import_devices(
    csv_content: str = Body(..., media_type="text/plain")
) -> DeviceImportResponse:
    """Import and validate devices from CSV text."""
    result = device_import_service.import_csv(csv_content=csv_content)
    return DeviceImportResponse(
        devices=[
            DeviceProfileResponse(
                host=d.host,
                port=d.port,
                device_type=d.device_type,
                username=d.username,
                password=d.password,
                name=d.name,
                verify_cmds=d.verify_cmds,
                connection_ok=d.connection_ok,
                error_message=d.error_message,
            )
            for d in result.devices
        ],
        failed_rows=[
            FailedRowResponse(
                row_number=row.row_number,
                row=row.row,
                error=row.error,
            )
            for row in result.failed_rows
        ],
    )


@app.get("/api/v2/devices", response_model=list[DeviceProfileResponse])
def list_devices() -> list[DeviceProfileResponse]:
    """List currently imported valid devices."""
    devices = device_store.list()
    return [
        DeviceProfileResponse(
            host=d.host,
            port=d.port,
            device_type=d.device_type,
            username=d.username,
            password=d.password,
            name=d.name,
            verify_cmds=d.verify_cmds,
            connection_ok=d.connection_ok,
            error_message=d.error_message,
        )
        for d in devices
    ]


@app.post("/api/v2/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    """Create a queued job."""
    job = service.create_job(job_name=payload.job_name, creator=payload.creator)
    return to_response(job)


@app.get("/api/v2/jobs", response_model=list[JobResponse])
def list_jobs() -> list[JobResponse]:
    """List created jobs in reverse chronological order."""
    jobs = store.list()
    jobs.sort(key=lambda item: item.created_at, reverse=True)
    return [to_response(job) for job in jobs]


@app.get("/api/v2/jobs/active", response_model=ActiveJobResponse)
def active_job() -> ActiveJobResponse:
    """Return latest active job if present."""
    jobs = store.list()
    jobs.sort(key=lambda item: item.created_at, reverse=True)
    for job in jobs:
        if job.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED}:
            return ActiveJobResponse(active=True, job=to_response(job))
    return ActiveJobResponse(active=False, job=None)


@app.get("/api/v2/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    """Fetch job details."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return to_response(job)


@app.get("/api/v2/jobs/{job_id}/events", response_model=list[ExecutionEventResponse])
def list_job_events(job_id: str) -> list[ExecutionEventResponse]:
    """List buffered execution events for a job."""
    events = event_store.list_events(job_id=job_id)
    return [
        ExecutionEventResponse(
            type=e.type,
            job_id=e.job_id,
            timestamp=e.timestamp,
            device=e.device,
            status=e.status,
            message=e.message,
        )
        for e in events
    ]


@app.post("/api/v2/jobs/{job_id}/events/{event_name}", response_model=JobResponse)
def apply_event(job_id: str, event_name: str) -> JobResponse:
    """Apply lifecycle event to an existing job."""
    try:
        job = service.apply_event(job_id=job_id, event_name=event_name)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return to_response(job)


@app.post("/api/v2/jobs/{job_id}/run", response_model=RunJobResponse)
def run_job(job_id: str, payload: RunJobRequest) -> RunJobResponse:
    """Run job with simulated worker and return summary."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    try:
        service.apply_event(job_id=job_id, event_name="start")
    except ValueError:
        pass
    control = control_store.get_or_create(job_id)
    control.pause_event.clear()
    control.cancel_event.clear()

    summary = _execute_run(job_id=job_id, payload=payload)
    return _to_run_response(summary)


@app.post("/api/v2/jobs/{job_id}/run/async", response_model=JobResponse)
def run_job_async(job_id: str, payload: RunJobRequest) -> JobResponse:
    """Run job in background thread."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    try:
        service.apply_event(job_id=job_id, event_name="start")
    except ValueError:
        pass
    control = control_store.get_or_create(job_id)
    control.pause_event.clear()
    control.cancel_event.clear()

    started = run_coordinator.start(
        job_id=job_id, target=lambda: _execute_run(job_id, payload)
    )
    if not started:
        raise HTTPException(status_code=409, detail="Job run already in progress")
    event_store.publish(
        ExecutionEvent(
            type="job_status",
            job_id=job_id,
            timestamp=utc_now(),
            status="running",
            message="Async run started",
        )
    )
    fresh = store.get(job_id)
    if fresh is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return to_response(fresh)


@app.post("/api/v2/jobs/{job_id}/pause", response_model=JobResponse)
def pause_job(job_id: str) -> JobResponse:
    """Pause async run scheduling."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    control = control_store.get(job_id)
    if control is None:
        raise HTTPException(status_code=409, detail="No run control available")
    control.pause_event.set()
    try:
        job = service.apply_event(job_id=job_id, event_name="pause")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    event_store.publish(
        ExecutionEvent(
            type="job_status",
            job_id=job_id,
            timestamp=utc_now(),
            status="paused",
            message="Pause requested",
        )
    )
    return to_response(job)


@app.post("/api/v2/jobs/{job_id}/resume", response_model=JobResponse)
def resume_job(job_id: str) -> JobResponse:
    """Resume paused async run."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    control = control_store.get(job_id)
    if control is None:
        raise HTTPException(status_code=409, detail="No run control available")
    control.pause_event.clear()
    try:
        job = service.apply_event(job_id=job_id, event_name="resume")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    event_store.publish(
        ExecutionEvent(
            type="job_status",
            job_id=job_id,
            timestamp=utc_now(),
            status="running",
            message="Resume requested",
        )
    )
    return to_response(job)


@app.post("/api/v2/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str) -> JobResponse:
    """Cancel async run."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    control = control_store.get(job_id)
    if control is None:
        raise HTTPException(status_code=409, detail="No run control available")
    control.cancel_event.set()
    control.pause_event.clear()
    try:
        job = service.apply_event(job_id=job_id, event_name="cancel")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    event_store.publish(
        ExecutionEvent(
            type="job_status",
            job_id=job_id,
            timestamp=utc_now(),
            status="cancelled",
            message="Cancel requested",
        )
    )
    return to_response(job)


@app.get("/api/v2/jobs/{job_id}/result", response_model=RunJobResponse)
def get_job_result(job_id: str) -> RunJobResponse:
    """Return latest run result for a job."""
    summary = run_store.get(job_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Run result not found")
    return _to_run_response(summary)


@app.websocket("/ws/v2/jobs/{job_id}")
async def ws_job_events(websocket: WebSocket, job_id: str) -> None:
    """Stream in-memory execution events for a job."""
    await websocket.accept()
    cursor = 0
    try:
        while True:
            events = event_store.list_events(job_id=job_id, start_index=cursor)
            for event in events:
                await websocket.send_json(
                    {
                        "type": event.type,
                        "job_id": event.job_id,
                        "timestamp": event.timestamp,
                        "device": event.device,
                        "status": event.status,
                        "message": event.message,
                    }
                )
                cursor += 1
                if event.type == "job_complete":
                    await websocket.close()
                    return
            await asyncio.sleep(0.2)
    except WebSocketDisconnect:
        return
