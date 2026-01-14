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
"""Job manager for orchestrating device configuration tasks."""

import asyncio
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, cast
from concurrent.futures import ThreadPoolExecutor, Future
import threading

from .models import (
    Job,
    JobCreate,
    JobStatus,
    DeviceStatus,
    DeviceResult,
    CanaryDevice,
    Device,
)
from .ssh_executor import execute_device_commands


class JobControl:
    """Control flags for running jobs."""

    def __init__(self):
        self.pause_event = threading.Event()
        self.cancel_event = threading.Event()


class JobManager:
    """Manages jobs and device execution in memory."""

    def __init__(self):
        self.jobs: Dict[str, Job] = {}
        self.devices: List[Device] = []
        self.lock = threading.Lock()
        self.ws_callbacks: Dict[str, List] = {}  # job_id -> list of callback functions
        self.job_controls: Dict[str, JobControl] = {}
        self.job_threads: Dict[str, threading.Thread] = {}

    def add_devices(self, devices: List[Device]):
        """Add validated devices to in-memory storage."""
        with self.lock:
            # Only add devices that passed connection test
            valid_devices = [d for d in devices if d.connection_ok]
            self.devices = valid_devices

    def get_devices(self) -> List[Device]:
        """Get all devices."""
        with self.lock:
            return self.devices.copy()

    def create_job(self, job_create: JobCreate) -> Job:
        """Create a new job."""
        job_id = str(uuid.uuid4())

        # Determine which devices to use
        if job_create.devices:
            # Use specified devices
            device_list = job_create.devices
        else:
            # Use all current devices
            device_list = [CanaryDevice(host=d.host, port=d.port) for d in self.devices]

        # Create device results
        device_results = {}
        for dev in device_list:
            key = f"{dev.host}:{dev.port}"
            device_results[key] = DeviceResult(
                host=dev.host, port=dev.port, status=DeviceStatus.QUEUED
            )

        job = Job(
            job_id=job_id,
            job_name=job_create.job_name,
            creator=job_create.creator,
            status=JobStatus.QUEUED,
            canary=job_create.canary,
            commands=job_create.commands,
            verify_only=job_create.verify_only,
            verify_cmds=job_create.verify_cmds,
            concurrency_limit=job_create.concurrency_limit,
            stagger_delay=job_create.stagger_delay,
            stop_on_error=job_create.stop_on_error,
            device_results=device_results,
            created_at=datetime.utcnow().isoformat(),
        )

        with self.lock:
            self.jobs[job_id] = job
            self.job_controls[job_id] = JobControl()

        return job

    def get_job(self, job_id: str) -> Optional[Job]:
        """Get job by ID."""
        with self.lock:
            return self.jobs.get(job_id)

    def register_ws_callback(self, job_id: str, callback):
        """Register a WebSocket callback for job updates."""
        with self.lock:
            if job_id not in self.ws_callbacks:
                self.ws_callbacks[job_id] = []
            self.ws_callbacks[job_id].append(callback)

    def unregister_ws_callback(self, job_id: str, callback):
        """Unregister a WebSocket callback."""
        with self.lock:
            if job_id in self.ws_callbacks:
                try:
                    self.ws_callbacks[job_id].remove(callback)
                except ValueError:
                    pass

    async def send_ws_message(self, job_id: str, message: dict):
        """Send message to all WebSocket clients for this job."""
        with self.lock:
            callbacks = self.ws_callbacks.get(job_id, []).copy()

        for callback in callbacks:
            try:
                await callback(message)
            except Exception:
                pass

    def pause_job(self, job_id: str) -> bool:
        """Pause a running job."""
        with self.lock:
            job = self.jobs.get(job_id)
            control = self.job_controls.get(job_id)

            if not job or not control:
                return False
            if job.status != JobStatus.RUNNING:
                return False
            job.status = JobStatus.PAUSED
            control.pause_event.set()

        asyncio.run(
            self.send_ws_message(
                job_id, {"type": "job_status", "job_id": job_id, "status": "paused"}
            )
        )
        return True

    def resume_job(self, job_id: str) -> bool:
        """Resume a paused job."""
        with self.lock:
            job = self.jobs.get(job_id)
            control = self.job_controls.get(job_id)

            if not job or not control:
                return False
            if job.status != JobStatus.PAUSED:
                return False
            job.status = JobStatus.RUNNING
            control.pause_event.clear()

        asyncio.run(
            self.send_ws_message(
                job_id, {"type": "job_status", "job_id": job_id, "status": "running"}
            )
        )
        return True

    def terminate_job(self, job_id: str) -> bool:
        """Terminate a running or queued job."""
        with self.lock:
            job = self.jobs.get(job_id)
            control = self.job_controls.get(job_id)

            if not job or not control:
                return False
            if job.status in {
                JobStatus.COMPLETED,
                JobStatus.FAILED,
                JobStatus.CANCELLED,
            }:
                return False
            control.cancel_event.set()
            control.pause_event.clear()
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow().isoformat()
            for dr in job.device_results.values():
                if dr.status == DeviceStatus.QUEUED:
                    dr.status = DeviceStatus.CANCELLED

        asyncio.run(
            self.send_ws_message(
                job_id,
                {"type": "job_status", "job_id": job_id, "status": "cancelled"},
            )
        )
        return True

    def _wait_if_paused(self, job_id: str, control: JobControl) -> bool:
        """Block while a job is paused. Returns False if cancellation is requested."""
        while control.pause_event.is_set():
            if control.cancel_event.is_set():
                return False
            time.sleep(0.2)
        return not control.cancel_event.is_set()

    def execute_job(self, job_id: str):
        """Execute a job in a background thread."""
        job = self.get_job(job_id)
        if not job:
            return

        # Start execution in thread
        thread = threading.Thread(target=self._run_job, args=(job_id,))
        thread.daemon = True
        thread.start()
        with self.lock:
            self.job_threads[job_id] = thread

    def _run_job(self, job_id: str):
        """Run job execution (blocking, runs in thread)."""
        job = self.get_job(job_id)
        if not job:
            return
        control = self.job_controls.get(job_id)
        if not control:
            return

        if control.cancel_event.is_set():
            with self.lock:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow().isoformat()
            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {
                        "type": "job_complete",
                        "job_id": job_id,
                        "status": "cancelled",
                    },
                )
            )
            return

        # Update job status
        with self.lock:
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow().isoformat()

        # Send job started message
        asyncio.run(
            self.send_ws_message(
                job_id, {"type": "job_status", "job_id": job_id, "status": "running"}
            )
        )

        # Parse commands
        commands = [cmd.strip() for cmd in job.commands.split("\n") if cmd.strip()]

        # Get device parameters
        device_params_map: Dict[str, Dict[str, Any]] = {}
        for device in self.devices:
            key = f"{device.host}:{device.port}"
            verify_cmds = (
                list(job.verify_cmds) if job.verify_cmds else list(device.verify_cmds)
            )
            device_params_map[key] = {
                "host": device.host,
                "port": device.port,
                "device_type": device.device_type,
                "username": device.username,
                "password": device.password,
                "verify_cmds": verify_cmds,
            }

        # Execute canary first
        canary_key = f"{job.canary.host}:{job.canary.port}"
        if canary_key not in job.device_results:
            # Canary not in device list - fail immediately
            with self.lock:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow().isoformat()
            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {"type": "job_complete", "job_id": job_id, "status": "failed"},
                )
            )
            return

        # Get canary device params
        if canary_key not in device_params_map:
            with self.lock:
                job.status = JobStatus.FAILED
                job.completed_at = datetime.utcnow().isoformat()
            return

        canary_params = device_params_map[canary_key]

        # Update canary status
        with self.lock:
            job.device_results[canary_key].status = DeviceStatus.RUNNING
            job.device_results[canary_key].started_at = datetime.utcnow().isoformat()

        asyncio.run(
            self.send_ws_message(
                job_id,
                {
                    "type": "device_status",
                    "job_id": job_id,
                    "device": canary_key,
                    "status": "running",
                    "error": None,
                },
            )
        )

        # Send canary log
        asyncio.run(
            self.send_ws_message(
                job_id,
                {
                    "type": "log",
                    "job_id": job_id,
                    "device": canary_key,
                    "phase": "pre",
                    "data": "Starting canary device execution...",
                },
            )
        )

        if not self._wait_if_paused(job_id, control):
            with self.lock:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow().isoformat()
            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {"type": "job_complete", "job_id": job_id, "status": "cancelled"},
                )
            )
            return

        # Execute canary (no retry)
        canary_verify_cmds = cast(List[str], canary_params["verify_cmds"])
        canary_result = execute_device_commands(
            device_params=canary_params,
            commands=commands,
            verify_cmds=canary_verify_cmds,
            is_canary=True,
            retry_on_connection_error=False,
            cancel_event=control.cancel_event,
        )

        # Update canary result
        with self.lock:
            dr = job.device_results[canary_key]
            if canary_result["status"] == "success":
                dr.status = DeviceStatus.SUCCESS
            elif canary_result["status"] == "cancelled":
                dr.status = DeviceStatus.CANCELLED
            else:
                dr.status = DeviceStatus.FAILED
            dr.error = canary_result["error"]
            dr.pre_output = canary_result["pre_output"]
            dr.apply_output = canary_result["apply_output"]
            dr.post_output = canary_result["post_output"]
            dr.diff = canary_result["diff"]
            dr.logs = canary_result["logs"]
            dr.log_trimmed = canary_result["log_trimmed"]
            dr.completed_at = datetime.utcnow().isoformat()

        # Send canary logs
        for log_line in canary_result["logs"]:
            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {
                        "type": "log",
                        "job_id": job_id,
                        "device": canary_key,
                        "phase": "apply",
                        "data": log_line,
                    },
                )
            )

        # Send canary status
        asyncio.run(
            self.send_ws_message(
                job_id,
                {
                    "type": "device_status",
                    "job_id": job_id,
                    "device": canary_key,
                    "status": dr.status.value,
                    "error": dr.error,
                },
            )
        )

        # Check canary result
        if canary_result["status"] != "success":
            # Canary failed - abort job
            with self.lock:
                job.status = (
                    JobStatus.CANCELLED
                    if canary_result["status"] == "cancelled"
                    else JobStatus.FAILED
                )
                job.completed_at = datetime.utcnow().isoformat()

            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {
                        "type": "job_complete",
                        "job_id": job_id,
                        "status": job.status.value,
                    },
                )
            )
            return

        # Canary succeeded - process remaining devices
        remaining_devices = [
            (key, params)
            for key, params in device_params_map.items()
            if key != canary_key and key in job.device_results
        ]

        if not remaining_devices:
            # Only canary device - job complete
            with self.lock:
                job.status = JobStatus.COMPLETED
                job.completed_at = datetime.utcnow().isoformat()

            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {"type": "job_complete", "job_id": job_id, "status": "completed"},
                )
            )
            return

        # Execute remaining devices with concurrency
        stop_flag = threading.Event()

        def execute_device_wrapper(device_key: str, device_params: dict):
            """Wrapper for device execution."""
            if stop_flag.is_set() or control.cancel_event.is_set():
                # Job stopped, mark as cancelled
                with self.lock:
                    job.device_results[device_key].status = DeviceStatus.CANCELLED
                return
            if not self._wait_if_paused(job_id, control):
                with self.lock:
                    job.device_results[device_key].status = DeviceStatus.CANCELLED
                return

            # Update device status
            with self.lock:
                job.device_results[device_key].status = DeviceStatus.RUNNING
                job.device_results[device_key].started_at = (
                    datetime.utcnow().isoformat()
                )

            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {
                        "type": "device_status",
                        "job_id": job_id,
                        "device": device_key,
                        "status": "running",
                        "error": None,
                    },
                )
            )

            # Execute device
            verify_cmds = cast(List[str], device_params["verify_cmds"])
            result = execute_device_commands(
                device_params=device_params,
                commands=commands,
                verify_cmds=verify_cmds,
                is_canary=False,
                retry_on_connection_error=True,
                cancel_event=control.cancel_event,
            )

            # Update device result
            with self.lock:
                dr = job.device_results[device_key]
                if result["status"] == "success":
                    dr.status = DeviceStatus.SUCCESS
                elif result["status"] == "cancelled":
                    dr.status = DeviceStatus.CANCELLED
                else:
                    dr.status = DeviceStatus.FAILED
                dr.error = result["error"]
                dr.pre_output = result["pre_output"]
                dr.apply_output = result["apply_output"]
                dr.post_output = result["post_output"]
                dr.diff = result["diff"]
                dr.logs = result["logs"]
                dr.log_trimmed = result["log_trimmed"]
                dr.completed_at = datetime.utcnow().isoformat()

            # Send device logs
            for log_line in result["logs"]:
                asyncio.run(
                    self.send_ws_message(
                        job_id,
                        {
                            "type": "log",
                            "job_id": job_id,
                            "device": device_key,
                            "phase": "apply",
                            "data": log_line,
                        },
                    )
                )

            # Send device status
            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {
                        "type": "device_status",
                        "job_id": job_id,
                        "device": device_key,
                        "status": dr.status.value,
                        "error": dr.error,
                    },
                )
            )

            # Check if should stop on error
            if result["status"] != "success" and job.stop_on_error:
                stop_flag.set()

        # Submit tasks with staggering
        executor = ThreadPoolExecutor(max_workers=job.concurrency_limit)
        futures: List[Future] = []

        for device_key, device_params in remaining_devices:
            if stop_flag.is_set() or control.cancel_event.is_set():
                # Mark remaining as cancelled
                with self.lock:
                    job.device_results[device_key].status = DeviceStatus.CANCELLED
                continue
            if not self._wait_if_paused(job_id, control):
                with self.lock:
                    job.device_results[device_key].status = DeviceStatus.CANCELLED
                continue

            future = executor.submit(execute_device_wrapper, device_key, device_params)
            futures.append(future)
            time.sleep(job.stagger_delay)

        # Wait for all tasks to complete
        for future in futures:
            try:
                future.result()
            except Exception:
                pass

        executor.shutdown(wait=True)

        # Determine final job status
        if control.cancel_event.is_set():
            with self.lock:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow().isoformat()
            asyncio.run(
                self.send_ws_message(
                    job_id,
                    {
                        "type": "job_complete",
                        "job_id": job_id,
                        "status": "cancelled",
                    },
                )
            )
            return

        all_success = all(
            dr.status == DeviceStatus.SUCCESS for dr in job.device_results.values()
        )
        any_failed = any(
            dr.status == DeviceStatus.FAILED for dr in job.device_results.values()
        )

        with self.lock:
            if all_success:
                job.status = JobStatus.COMPLETED
            elif any_failed:
                job.status = JobStatus.FAILED
            else:
                job.status = JobStatus.CANCELLED
            job.completed_at = datetime.utcnow().isoformat()

        asyncio.run(
            self.send_ws_message(
                job_id,
                {"type": "job_complete", "job_id": job_id, "status": job.status.value},
            )
        )


# Global job manager instance
job_manager = JobManager()
