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
import json
import os
from queue import Queue
from threading import Thread
from typing import Iterator, Optional

from fastapi import Body, FastAPI, HTTPException
from fastapi import WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend_v2.app.api.mappers import (
    to_device_profile_response,
    to_job_response,
    to_preset_response,
    to_run_response,
)
from backend_v2.app.api.run_execution import (
    apply_control_action,
    execute_prepared_run,
    publish_job_status,
    request_cancel,
    request_pause,
    request_resume,
    reset_run_control,
)
from backend_v2.app.api.run_preparation import prepare_run
from backend_v2.app.api.schemas import (
    AppResetCountsResponse,
    AppResetResponse,
    ActiveJobResponse,
    CreateJobRequest,
    DeviceImportResponse,
    DeviceProfileResponse,
    ExecutionEventResponse,
    RuntimeModesResponse,
    StatusCommandRequest,
    StatusCommandResponse,
    JobResponse,
    PresetCreateRequest,
    PresetResponse,
    PresetUpdateRequest,
    RunJobRequest,
    RunJobResponse,
    FailedRowResponse,
)
from backend_v2.app.application.device_import_service import (
    DeviceConnectionValidator,
    DeviceImportService,
)
from backend_v2.app.application.execution_engine import (
    DeviceWorker,
    ExecutionEngine,
)
from backend_v2.app.application.job_service import JobService
from backend_v2.app.domain.models import is_active_job
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
from backend_v2.app.infrastructure.file_preset_store import (
    FilePresetStore,
    PresetConflictError,
)
from backend_v2.app.infrastructure.netmiko_device_worker import NetmikoDeviceWorker
from backend_v2.app.infrastructure.netmiko_executor import (
    parse_status_commands,
    run_status_commands,
)
from backend_v2.app.infrastructure.run_coordinator import RunCoordinator
from backend_v2.app.infrastructure.simulated_device_worker import SimulatedDeviceWorker

app = FastAPI(
    title="Network Device Configuration Manager v2 (Scaffold)",
    version="0.1.0",
)

# Allow the local v2 frontend on 127.0.0.1:3010 to call API on 8010.
# Comma-separated override is available for deployment-specific origins.
cors_origins = [
    origin.strip()
    for origin in os.getenv(
        "NW_EDIT_V2_CORS_ORIGINS",
        "http://127.0.0.1:3010",
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

store = InMemoryJobStore()
device_store = InMemoryDeviceStore()
event_store = InMemoryEventStore()
run_store = InMemoryRunStore()
control_store = InMemoryControlStore()
preset_store = FilePresetStore(
    path=os.getenv(
        "NW_EDIT_V2_PRESET_FILE",
        "backend_v2/data/run_presets.json",
    ).strip(),
)
run_coordinator = RunCoordinator()
service = JobService(repository=store, state_machine=JobStateMachine())


def resolve_worker_mode() -> str:
    return os.getenv("NW_EDIT_V2_WORKER_MODE", "netmiko").strip().lower()


def resolve_validator_mode() -> str:
    return os.getenv("NW_EDIT_V2_VALIDATOR_MODE", "netmiko").strip().lower()


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


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health endpoint."""
    return {"status": "ok"}


@app.get("/api/v2/runtime/modes", response_model=RuntimeModesResponse)
def get_runtime_modes() -> RuntimeModesResponse:
    """Expose runtime worker/validator mode for UI."""
    return RuntimeModesResponse(
        worker_mode=resolve_worker_mode(),
        validator_mode=resolve_validator_mode(),
    )


@app.post("/api/v2/devices/import", response_model=DeviceImportResponse)
def import_devices(
    csv_content: str = Body(..., media_type="text/plain")
) -> DeviceImportResponse:
    """Import and validate devices from CSV text."""
    result = device_import_service.import_csv(csv_content=csv_content)
    if result.failed_rows:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "CSV import failed due to invalid rows",
                "failed_rows": [
                    {
                        "row_number": row.row_number,
                        "row": row.row,
                        "error": row.error,
                    }
                    for row in result.failed_rows
                ],
            },
        )
    return DeviceImportResponse(
        devices=[to_device_profile_response(d) for d in result.devices],
        failed_rows=[
            FailedRowResponse(
                row_number=row.row_number,
                row=row.row,
                error=row.error,
            )
            for row in result.failed_rows
        ],
    )


@app.post("/api/v2/devices/import/progress")
def import_devices_with_progress(
    csv_content: str = Body(..., media_type="text/plain")
) -> StreamingResponse:
    """Import devices and stream validation progress as NDJSON."""

    done = object()
    events: Queue[object] = Queue()

    def publish(event: dict[str, object]) -> None:
        events.put(event)

    def worker() -> None:
        try:
            result = device_import_service.import_csv(
                csv_content=csv_content, progress_callback=publish
            )
            if result.failed_rows:
                events.put(
                    {
                        "type": "error",
                        "detail": {
                            "message": "CSV import failed due to invalid rows",
                            "failed_rows": [
                                {
                                    "row_number": row.row_number,
                                    "row": row.row,
                                    "error": row.error,
                                }
                                for row in result.failed_rows
                            ],
                        },
                    }
                )
            else:
                events.put(
                    {
                        "type": "complete",
                        "processed": len(result.devices),
                        "total": len(result.devices),
                        "devices": [
                            to_device_profile_response(d).model_dump()
                            for d in result.devices
                        ],
                    }
                )
        except Exception as exc:
            events.put({"type": "error", "detail": str(exc)})
        finally:
            events.put(done)

    Thread(target=worker, daemon=True).start()

    def stream() -> Iterator[str]:
        while True:
            event = events.get()
            if event is done:
                break
            yield json.dumps(event, ensure_ascii=False) + "\n"

    return StreamingResponse(stream(), media_type="application/x-ndjson")


@app.get("/api/v2/devices", response_model=list[DeviceProfileResponse])
def list_devices() -> list[DeviceProfileResponse]:
    """List currently imported valid devices."""
    devices = device_store.list()
    return [to_device_profile_response(d) for d in devices]


@app.post("/api/v2/app/reset", response_model=AppResetResponse)
def reset_app_state() -> AppResetResponse:
    """Clear volatile in-memory application state."""
    jobs = store.list()
    active_jobs = [job for job in jobs if is_active_job(job)]
    if active_jobs:
        raise HTTPException(
            status_code=409,
            detail="Cannot reset app state while a job is queued, running, or paused",
        )

    cleared = AppResetCountsResponse(
        devices=device_store.clear(),
        jobs=store.clear(),
        events=event_store.clear(),
        run_results=run_store.clear(),
        controls=control_store.clear(),
    )
    return AppResetResponse(reset=True, cleared=cleared)


@app.post("/api/v2/commands/exec", response_model=StatusCommandResponse)
def execute_status_command(payload: StatusCommandRequest) -> StatusCommandResponse:
    """Execute read-only status commands on an imported device."""
    key = f"{payload.host}:{payload.port}"
    profile = device_store.get_by_key(key)
    if profile is None:
        raise HTTPException(status_code=404, detail="Device not found")

    try:
        if resolve_worker_mode() == "netmiko":
            output = run_status_commands(
                {
                    "host": profile.host,
                    "port": profile.port,
                    "device_type": profile.device_type,
                    "username": profile.username,
                    "password": profile.password,
                },
                payload.commands,
            )
        else:
            commands = parse_status_commands(payload.commands)
            output = "\n\n".join([f"$ {cmd}\n(simulated output)" for cmd in commands])
        return StatusCommandResponse(output=output)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@app.get("/api/v2/presets", response_model=list[PresetResponse])
def list_presets(os_model: Optional[str] = None) -> list[PresetResponse]:
    """List execution presets with optional os_model filter."""
    return [
        to_preset_response(preset)
        for preset in preset_store.list_presets(os_model=os_model)
    ]


@app.get("/api/v2/presets/os-models", response_model=list[str])
def list_preset_os_models() -> list[str]:
    """List os models that have at least one preset."""
    return preset_store.list_os_models()


@app.post("/api/v2/presets", response_model=PresetResponse)
def create_preset(payload: PresetCreateRequest) -> PresetResponse:
    """Create execution preset."""
    try:
        preset = preset_store.create(
            name=payload.name,
            os_model=payload.os_model,
            commands=list(payload.commands),
            verify_commands=list(payload.verify_commands),
        )
    except PresetConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return to_preset_response(preset)


@app.put("/api/v2/presets/{preset_id}", response_model=PresetResponse)
def update_preset(preset_id: str, payload: PresetUpdateRequest) -> PresetResponse:
    """Update execution preset."""
    try:
        preset = preset_store.update(
            preset_id=preset_id,
            name=payload.name,
            os_model=payload.os_model,
            commands=list(payload.commands),
            verify_commands=list(payload.verify_commands),
        )
    except PresetConflictError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    if preset is None:
        raise HTTPException(status_code=404, detail="Preset not found")
    return to_preset_response(preset)


@app.post("/api/v2/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    """Create a queued job."""
    jobs = store.list()
    jobs.sort(key=lambda item: item.created_at, reverse=True)
    for existing in jobs:
        if is_active_job(existing):
            label = existing.job_name or existing.job_id
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Job '{label}' is already {existing.status.value}. "
                    "Wait for it to finish or cancel it before starting another job."
                ),
            )
    job = service.create_job(
        job_name=payload.job_name,
        creator=payload.creator,
        global_vars=payload.global_vars,
    )
    return to_job_response(job)


@app.get("/api/v2/jobs", response_model=list[JobResponse])
def list_jobs() -> list[JobResponse]:
    """List created jobs in reverse chronological order."""
    jobs = store.list()
    jobs.sort(key=lambda item: item.created_at, reverse=True)
    return [to_job_response(job) for job in jobs]


@app.get("/api/v2/jobs/active", response_model=ActiveJobResponse)
def active_job() -> ActiveJobResponse:
    """Return latest active job if present."""
    jobs = store.list()
    jobs.sort(key=lambda item: item.created_at, reverse=True)
    for job in jobs:
        if is_active_job(job):
            return ActiveJobResponse(active=True, job=to_job_response(job))
    return ActiveJobResponse(active=False, job=None)


@app.get("/api/v2/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: str) -> JobResponse:
    """Fetch job details."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return to_job_response(job)


@app.get("/api/v2/jobs/{job_id}/events", response_model=list[ExecutionEventResponse])
def list_job_events(job_id: str) -> list[ExecutionEventResponse]:
    """List buffered execution events for a job."""
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
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
    return to_job_response(job)


@app.post("/api/v2/jobs/{job_id}/run", response_model=RunJobResponse)
def run_job(job_id: str, payload: RunJobRequest) -> RunJobResponse:
    """Run job with simulated worker and return summary."""
    prepared = prepare_run(
        job_id=job_id,
        payload=payload,
        job_store=store,
        device_store=device_store,
    )

    reset_run_control(
        job_id=job_id,
        service=service,
        control_store=control_store,
    )

    summary = execute_prepared_run(
        job_id=job_id,
        prepared=prepared,
        engine=engine,
        control_store=control_store,
        run_store=run_store,
        service=service,
        commands=payload.commands,
        verify_commands=list(payload.verify_commands or []),
    )
    return to_run_response(summary)


@app.post("/api/v2/jobs/{job_id}/run/async", response_model=JobResponse)
def run_job_async(job_id: str, payload: RunJobRequest) -> JobResponse:
    """Run job in background thread."""
    prepared = prepare_run(
        job_id=job_id,
        payload=payload,
        job_store=store,
        device_store=device_store,
    )
    reset_run_control(
        job_id=job_id,
        service=service,
        control_store=control_store,
    )

    started = run_coordinator.start(
        job_id=job_id,
        target=lambda: execute_prepared_run(
            job_id=job_id,
            prepared=prepared,
            engine=engine,
            control_store=control_store,
            run_store=run_store,
            service=service,
            commands=payload.commands,
            verify_commands=list(payload.verify_commands or []),
        ),
    )
    if not started:
        raise HTTPException(status_code=409, detail="Job run already in progress")
    publish_job_status(
        event_store=event_store,
        job_id=job_id,
        status="running",
        message="Async run started",
    )
    fresh = store.get(job_id)
    if fresh is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return to_job_response(fresh)


@app.post("/api/v2/jobs/{job_id}/pause", response_model=JobResponse)
def pause_job(job_id: str) -> JobResponse:
    """Pause async run scheduling."""
    job = apply_control_action(
        job_id=job_id,
        job_store=store,
        control_store=control_store,
        service=service,
        event_store=event_store,
        event_name="pause",
        status="paused",
        message="Pause requested",
        mutate_control=request_pause,
    )
    return to_job_response(job)


@app.post("/api/v2/jobs/{job_id}/resume", response_model=JobResponse)
def resume_job(job_id: str) -> JobResponse:
    """Resume paused async run."""
    job = apply_control_action(
        job_id=job_id,
        job_store=store,
        control_store=control_store,
        service=service,
        event_store=event_store,
        event_name="resume",
        status="running",
        message="Resume requested",
        mutate_control=request_resume,
    )
    return to_job_response(job)


@app.post("/api/v2/jobs/{job_id}/cancel", response_model=JobResponse)
def cancel_job(job_id: str) -> JobResponse:
    """Cancel async run."""
    job = apply_control_action(
        job_id=job_id,
        job_store=store,
        control_store=control_store,
        service=service,
        event_store=event_store,
        event_name="cancel",
        status="cancelled",
        message="Cancel requested",
        mutate_control=request_cancel,
    )
    return to_job_response(job)


@app.post("/api/v2/jobs/{job_id}/terminate", response_model=JobResponse)
def terminate_job(job_id: str) -> JobResponse:
    """Backward-compatible alias of cancel endpoint."""
    return cancel_job(job_id)


@app.get("/api/v2/jobs/{job_id}/result", response_model=RunJobResponse)
def get_job_result(job_id: str) -> RunJobResponse:
    """Return latest run result for a job."""
    summary = run_store.get(job_id)
    if summary is None:
        raise HTTPException(status_code=404, detail="Run result not found")
    return to_run_response(summary)


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
