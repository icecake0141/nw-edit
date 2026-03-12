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

from backend_v2.app.api.schemas import (
    ActiveJobResponse,
    CreateJobRequest,
    DeviceImportResponse,
    DeviceProfileResponse,
    DeviceRunResponse,
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
from backend_v2.app.application.command_template import render_commands
from backend_v2.app.application.events import ExecutionEvent, utc_now
from backend_v2.app.application.execution_engine import (
    DeviceWorker,
    ExecutionConfig,
    ExecutionEngine,
)
from backend_v2.app.application.job_service import JobService
from backend_v2.app.domain.models import (
    DeviceTarget,
    ExecutionPreset,
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


def to_response(job: JobRecord) -> JobResponse:
    """Convert domain model to API response."""
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


def _resolve_run_targets(
    payload: RunJobRequest,
) -> tuple[list[DeviceTarget], DeviceTarget]:
    if payload.devices and payload.imported_device_keys is not None:
        raise HTTPException(
            status_code=400,
            detail="devices and imported_device_keys cannot be used together",
        )
    if payload.devices:
        devices = [DeviceTarget(host=d.host, port=d.port) for d in payload.devices]
    elif payload.imported_device_keys is not None:
        if not payload.imported_device_keys:
            raise HTTPException(
                status_code=400,
                detail="imported_device_keys cannot be empty",
            )
        imported_map = {d.key: d for d in device_store.list()}
        missing_keys = [
            key for key in payload.imported_device_keys if key not in imported_map
        ]
        if missing_keys:
            missing = ", ".join(missing_keys)
            raise HTTPException(
                status_code=400,
                detail=f"Unknown imported_device_keys: {missing}",
            )
        devices = [
            DeviceTarget(host=imported_map[key].host, port=imported_map[key].port)
            for key in payload.imported_device_keys
        ]
    else:
        devices = [DeviceTarget(host=d.host, port=d.port) for d in device_store.list()]
    if not devices:
        raise HTTPException(status_code=400, detail="No devices provided or imported")

    if payload.canary is None:
        raise HTTPException(
            status_code=400,
            detail="canary is required",
        )
    canary = DeviceTarget(host=payload.canary.host, port=payload.canary.port)
    if canary.key not in {device.key for device in devices}:
        raise HTTPException(
            status_code=400,
            detail="Canary device must be in the device list",
        )
    return devices, canary


def _to_run_response(summary: JobRunSummary) -> RunJobResponse:
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


def _prepare_run(job_id: str, payload: RunJobRequest) -> tuple[
    JobRecord,
    list[DeviceTarget],
    DeviceTarget,
    dict[str, list[str]],
    dict[str, list[str]],
    ExecutionConfig,
]:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")

    devices, canary = _resolve_run_targets(payload)
    verify_mode = (payload.verify_mode or "all").strip().lower()
    if verify_mode not in {"all", "canary", "none"}:
        raise HTTPException(
            status_code=400,
            detail="verify_mode must be one of: all, canary, none",
        )
    commands_by_device: dict[str, list[str]] = {}
    verify_commands_by_device: dict[str, list[str]] = {}
    for device in devices:
        profile = device_store.get_by_key(device.key)
        merged_vars = dict(job.global_vars)
        if profile is not None:
            merged_vars.update(profile.host_vars)
        rendered, missing = render_commands(payload.commands, merged_vars)
        if missing:
            missing_vars = ", ".join(sorted(missing))
            raise HTTPException(
                status_code=400,
                detail=(f"Missing command variables for {device.key}: {missing_vars}"),
            )
        commands_by_device[device.key] = rendered
        if verify_mode == "none":
            verify_commands_by_device[device.key] = []
            continue

        base_verify_commands = (
            list(payload.verify_commands)
            if payload.verify_commands is not None
            else (list(profile.verify_cmds) if profile is not None else [])
        )
        if verify_mode == "canary" and device.key != canary.key:
            verify_commands_by_device[device.key] = []
        else:
            verify_commands_by_device[device.key] = base_verify_commands

    config = ExecutionConfig(
        concurrency_limit=payload.concurrency_limit,
        stagger_delay=payload.stagger_delay,
        stop_on_error=payload.stop_on_error,
        non_canary_retry_limit=payload.non_canary_retry_limit,
        retry_backoff_seconds=payload.retry_backoff_seconds,
    )
    return job, devices, canary, commands_by_device, verify_commands_by_device, config


def _execute_run_prepared(
    job_id: str,
    devices: list[DeviceTarget],
    canary: DeviceTarget,
    commands_by_device: dict[str, list[str]],
    verify_commands_by_device: dict[str, list[str]],
    config: ExecutionConfig,
    commands: Optional[list[str]] = None,
    verify_commands: Optional[list[str]] = None,
) -> JobRunSummary:
    control = control_store.get_or_create(job_id)
    summary = engine.run_job(
        job_id=job_id,
        devices=devices,
        canary=canary,
        commands_by_device=commands_by_device,
        verify_commands_by_device=verify_commands_by_device,
        config=config,
        commands=commands,
        verify_commands=verify_commands,
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


def _to_preset_response(preset: ExecutionPreset) -> PresetResponse:
    return PresetResponse(
        preset_id=preset.preset_id,
        name=preset.name,
        os_model=preset.os_model,
        commands=preset.commands,
        verify_commands=preset.verify_commands,
        created_at=preset.created_at,
        updated_at=preset.updated_at,
    )


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
        devices=[
            DeviceProfileResponse(
                host=d.host,
                port=d.port,
                device_type=d.device_type,
                username=d.username,
                password=d.password,
                name=d.name,
                verify_cmds=d.verify_cmds,
                host_vars=d.host_vars,
                prod=d.prod,
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
                            DeviceProfileResponse(
                                host=d.host,
                                port=d.port,
                                device_type=d.device_type,
                                username=d.username,
                                password=d.password,
                                name=d.name,
                                verify_cmds=d.verify_cmds,
                                host_vars=d.host_vars,
                                prod=d.prod,
                                connection_ok=d.connection_ok,
                                error_message=d.error_message,
                            ).model_dump()
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
    return [
        DeviceProfileResponse(
            host=d.host,
            port=d.port,
            device_type=d.device_type,
            username=d.username,
            password=d.password,
            name=d.name,
            verify_cmds=d.verify_cmds,
            host_vars=d.host_vars,
            prod=d.prod,
            connection_ok=d.connection_ok,
            error_message=d.error_message,
        )
        for d in devices
    ]


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
        _to_preset_response(preset)
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
    return _to_preset_response(preset)


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
    return _to_preset_response(preset)


@app.post("/api/v2/jobs", response_model=JobResponse)
def create_job(payload: CreateJobRequest) -> JobResponse:
    """Create a queued job."""
    jobs = store.list()
    jobs.sort(key=lambda item: item.created_at, reverse=True)
    for existing in jobs:
        if existing.status in {JobStatus.QUEUED, JobStatus.RUNNING, JobStatus.PAUSED}:
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
    _, devices, canary, commands_by_device, verify_commands_by_device, config = (
        _prepare_run(
            job_id=job_id,
            payload=payload,
        )
    )

    try:
        service.apply_event(job_id=job_id, event_name="start")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    control = control_store.get_or_create(job_id)
    control.pause_event.clear()
    control.cancel_event.clear()

    summary = _execute_run_prepared(
        job_id=job_id,
        devices=devices,
        canary=canary,
        commands_by_device=commands_by_device,
        verify_commands_by_device=verify_commands_by_device,
        config=config,
        commands=payload.commands,
        verify_commands=list(payload.verify_commands or []),
    )
    return _to_run_response(summary)


@app.post("/api/v2/jobs/{job_id}/run/async", response_model=JobResponse)
def run_job_async(job_id: str, payload: RunJobRequest) -> JobResponse:
    """Run job in background thread."""
    _, devices, canary, commands_by_device, verify_commands_by_device, config = (
        _prepare_run(
            job_id=job_id,
            payload=payload,
        )
    )
    try:
        service.apply_event(job_id=job_id, event_name="start")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    control = control_store.get_or_create(job_id)
    control.pause_event.clear()
    control.cancel_event.clear()

    started = run_coordinator.start(
        job_id=job_id,
        target=lambda: _execute_run_prepared(
            job_id=job_id,
            devices=devices,
            canary=canary,
            commands_by_device=commands_by_device,
            verify_commands_by_device=verify_commands_by_device,
            config=config,
            commands=payload.commands,
            verify_commands=list(payload.verify_commands or []),
        ),
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
