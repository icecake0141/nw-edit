"""Main FastAPI application."""

import csv
import io
from typing import List
from fastapi import FastAPI, HTTPException, WebSocket, Body
from fastapi.middleware.cors import CORSMiddleware

from .models import (
    Device,
    DeviceInput,
    DeviceImportResponse,
    JobCreate,
    JobResponse,
    Job,
)
from .job_manager import job_manager
from .ssh_executor import validate_device_connection
from .ws import websocket_endpoint

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
        validated_devices = []

        for device_input in device_inputs:
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
                    cmd.strip()
                    for cmd in device_input.verify_cmds.split(";")
                    if cmd.strip()
                ]

            device = Device(
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

            validated_devices.append(device)

        # Add validated devices to job manager
        job_manager.add_devices(validated_devices)

        return DeviceImportResponse(devices=validated_devices)

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/devices", response_model=List[Device])
async def get_devices():
    """Get all imported devices."""
    return job_manager.get_devices()


@app.post("/api/jobs", response_model=JobResponse)
async def create_job(job_create: JobCreate):
    """
    Create a new configuration job.

    Validates canary device is in device list and commands are non-empty.
    """
    # Validate commands
    if not job_create.commands or not job_create.commands.strip():
        raise HTTPException(status_code=400, detail="Commands cannot be empty")

    # Get devices
    devices = job_manager.get_devices()

    # If no devices specified, use all
    if not job_create.devices:
        job_create.devices = [{"host": d.host, "port": d.port} for d in devices]

    # Validate canary is in device list
    canary_key = f"{job_create.canary.host}:{job_create.canary.port}"
    device_keys = [f"{d['host']}:{d['port']}" for d in job_create.devices]

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
