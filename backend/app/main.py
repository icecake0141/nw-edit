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
"""Main FastAPI application."""

import csv
import io
import json
import logging
from datetime import datetime
from typing import List
from fastapi import FastAPI, HTTPException, WebSocket, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from .models import (
    Device,
    DeviceInput,
    DeviceImportResponse,
    JobCreate,
    JobResponse,
    Job,
    JobStatus,
    CanaryDevice,
    StatusCommandRequest,
    StatusCommandResponse,
    JobHistoryEntry,
    ActiveJobResponse,
)
from .job_manager import job_manager
from .ssh_executor import validate_device_connection, run_status_command
from .ws import websocket_endpoint

logger = logging.getLogger(__name__)


def build_job_history_entry(job: Job) -> JobHistoryEntry:
    """Build a history entry summary from a job."""
    duration_seconds = None
    if job.started_at:
        end_time = job.completed_at or datetime.utcnow().isoformat()
        duration_seconds = (
            datetime.fromisoformat(end_time) - datetime.fromisoformat(job.started_at)
        ).total_seconds()

    exit_code = None
    if job.status == JobStatus.COMPLETED:
        exit_code = 0
    elif job.status == JobStatus.FAILED:
        exit_code = 1
    elif job.status == JobStatus.CANCELLED:
        exit_code = 130

    return JobHistoryEntry(
        job_id=job.job_id,
        job_name=job.job_name,
        creator=job.creator,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        duration_seconds=duration_seconds,
        exit_code=exit_code,
    )


# Create FastAPI app
app = FastAPI(
    title="Network Device Configuration Manager",
    description="Multi-device SSH configuration management tool",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For MVP, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def parse_csv_devices(csv_content: str) -> List[DeviceInput]:
    """
    Parse CSV content into DeviceInput objects.

    Expected columns: host, port (optional), device_type, username, password, name (optional), verify_cmds (optional)
    """
    devices = []
    reader = csv.DictReader(io.StringIO(csv_content))

    for row in reader:
        # Validate required fields
        if (
            not row.get("host")
            or not row.get("device_type")
            or not row.get("username")
            or not row.get("password")
        ):
            continue

        device = DeviceInput(
            host=row["host"].strip(),
            port=int(row.get("port", "").strip() or "22"),
            device_type=row["device_type"].strip(),
            username=row["username"].strip(),
            password=row["password"].strip(),
            name=row.get("name", "").strip() or None,
            verify_cmds=row.get("verify_cmds", "").strip() or None,
        )
        devices.append(device)

    return devices


def validate_single_device_for_import(device_input: DeviceInput) -> Device:
    """Validate a single imported device with connection test."""
    device_params = {
        "host": device_input.host,
        "port": device_input.port,
        "device_type": device_input.device_type,
        "username": device_input.username,
        "password": device_input.password,
    }

    # Test connection
    success, error_message = validate_device_connection(device_params)

    # Parse verify_cmds
    verify_cmds = []
    if device_input.verify_cmds:
        verify_cmds = [
            cmd.strip() for cmd in device_input.verify_cmds.split(";") if cmd.strip()
        ]

    return Device(
        host=device_input.host,
        port=device_input.port,
        device_type=device_input.device_type,
        username=device_input.username,
        password=device_input.password,
        name=device_input.name,
        verify_cmds=verify_cmds,
        connection_ok=success,
        error_message=error_message,
    )


@app.post("/api/devices/import", response_model=DeviceImportResponse)
async def import_devices(csv_content: str = Body(..., media_type="text/plain")):
    """
    Import devices from CSV content.

    Validates devices with lightweight connection test.
    Only returns devices that pass connection test.
    """
    try:
        # Parse CSV
        device_inputs = parse_csv_devices(csv_content)

        if not device_inputs:
            raise HTTPException(status_code=400, detail="No valid devices found in CSV")

        # Validate each device with connection test
        validated_devices = [
            validate_single_device_for_import(device_input)
            for device_input in device_inputs
        ]

        # Add validated devices to job manager
        job_manager.add_devices(validated_devices)

        return DeviceImportResponse(devices=validated_devices)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/devices/import/progress")
async def import_devices_with_progress(
    csv_content: str = Body(..., media_type="text/plain")
):
    """Import devices from CSV and stream validation progress as NDJSON."""

    def generate_progress_stream():
        try:
            device_inputs = parse_csv_devices(csv_content)
            if not device_inputs:
                yield json.dumps(
                    {"type": "error", "detail": "No valid devices found in CSV"}
                ) + "\n"
                return

            total = len(device_inputs)
            yield json.dumps({"type": "start", "total": total}) + "\n"
            validated_devices: List[Device] = []
            for index, device_input in enumerate(device_inputs, start=1):
                validated_device = validate_single_device_for_import(device_input)
                validated_devices.append(validated_device)
                yield json.dumps(
                    {
                        "type": "progress",
                        "processed": index,
                        "total": total,
                        "host": validated_device.host,
                        "port": validated_device.port,
                        "connection_ok": validated_device.connection_ok,
                    }
                ) + "\n"

            job_manager.add_devices(validated_devices)
            yield json.dumps(
                {
                    "type": "complete",
                    "processed": total,
                    "total": total,
                    "devices": [device.model_dump() for device in validated_devices],
                }
            ) + "\n"
        except Exception as e:
            yield json.dumps({"type": "error", "detail": str(e)}) + "\n"

    return StreamingResponse(
        generate_progress_stream(), media_type="application/x-ndjson"
    )


@app.get("/api/devices", response_model=List[Device])
async def get_devices():
    """Get all imported devices."""
    return job_manager.get_devices()


@app.post("/api/commands/exec", response_model=StatusCommandResponse)
async def execute_status_command(request: StatusCommandRequest):
    """Execute read-only status commands on a managed device."""
    target_device = next(
        (
            d
            for d in job_manager.get_devices()
            if d.host == request.host and d.port == request.port
        ),
        None,
    )
    if not target_device:
        raise HTTPException(status_code=404, detail="Device not found")

    command_count = len(
        [
            command.strip()
            for command in request.commands.splitlines()
            if command.strip()
        ]
    )
    logger.info(
        "Status command request for %s:%s with %s command(s)",
        request.host,
        request.port,
        command_count,
    )

    try:
        output = run_status_command(
            {
                "host": target_device.host,
                "port": target_device.port,
                "device_type": target_device.device_type,
                "username": target_device.username,
                "password": target_device.password,
            },
            request.commands,
        )
        return StatusCommandResponse(output=output)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@app.get("/api/jobs", response_model=List[JobHistoryEntry])
async def list_jobs():
    """List job history entries for the current session."""
    return [build_job_history_entry(job) for job in job_manager.list_jobs()]


@app.get("/api/jobs/active", response_model=ActiveJobResponse)
async def get_active_job():
    """Get the active job lock state."""
    active_job = job_manager.get_active_job()
    if not active_job:
        return ActiveJobResponse(active=False)
    return ActiveJobResponse(active=True, job=build_job_history_entry(active_job))


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(job_create: JobCreate):
    """
    Create a new configuration job.

    Validates canary device is in device list and commands are non-empty.
    """
    # Validate commands
    if not job_create.commands or not job_create.commands.strip():
        raise HTTPException(status_code=400, detail="Commands cannot be empty")

    active_job = job_manager.get_active_job()
    if active_job:
        active_label = active_job.job_name or active_job.job_id
        raise HTTPException(
            status_code=409,
            detail=(
                f"Job '{active_label}' is already {active_job.status.value}. "
                "Wait for it to finish or cancel it before starting another job."
            ),
        )

    # Get devices
    devices = job_manager.get_devices()

    # If no devices specified, use all
    if not job_create.devices:
        job_create.devices = [CanaryDevice(host=d.host, port=d.port) for d in devices]

    # Validate canary is in device list
    canary_key = f"{job_create.canary.host}:{job_create.canary.port}"
    device_keys = [f"{d.host}:{d.port}" for d in job_create.devices]

    if canary_key not in device_keys:
        raise HTTPException(
            status_code=400, detail="Canary device must be in the device list"
        )

    # Create job
    job = job_manager.create_job(job_create)

    # Start job execution in background
    job_manager.execute_job(job.job_id)

    return JobResponse(job_id=job.job_id, status=job.status)


@app.get("/api/jobs/{job_id}", response_model=Job)
async def get_job(job_id: str):
    """Get job details."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@app.post("/api/jobs/{job_id}/pause", response_model=JobResponse)
async def pause_job(job_id: str):
    """Pause a running job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job_manager.pause_job(job_id):
        raise HTTPException(status_code=409, detail="Job is not running")
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, status=job.status)


@app.post("/api/jobs/{job_id}/resume", response_model=JobResponse)
async def resume_job(job_id: str):
    """Resume a paused job."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job_manager.resume_job(job_id):
        raise HTTPException(status_code=409, detail="Job is not paused")
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, status=job.status)


@app.post("/api/jobs/{job_id}/terminate", response_model=JobResponse)
async def terminate_job(job_id: str):
    """Terminate a running job and clean up remaining tasks."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if not job_manager.terminate_job(job_id):
        raise HTTPException(status_code=409, detail="Job already completed")
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return JobResponse(job_id=job_id, status=job.status)


@app.websocket("/ws/jobs/{job_id}")
async def websocket_job(websocket: WebSocket, job_id: str):
    """WebSocket endpoint for real-time job updates."""
    # Verify job exists
    job = job_manager.get_job(job_id)
    if not job:
        await websocket.close(code=4004)
        return

    await websocket_endpoint(websocket, job_id)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Network Device Configuration Manager API"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
