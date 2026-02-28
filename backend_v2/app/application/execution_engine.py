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
"""Device execution engine with canary-first orchestration."""

from __future__ import annotations

import time
from concurrent.futures import FIRST_COMPLETED, Future, ThreadPoolExecutor, wait
from dataclasses import dataclass
from typing import Protocol

from backend_v2.app.application.execution_control import ExecutionControl
from backend_v2.app.application.events import EventPublisher, ExecutionEvent, utc_now
from backend_v2.app.domain.models import (
    DeviceExecutionResult,
    DeviceTarget,
    JobRunSummary,
    JobStatus,
)


class DeviceWorker(Protocol):
    """Device worker abstraction (SSH adapter will implement this later)."""

    def run(self, device: DeviceTarget, commands: list[str]) -> DeviceExecutionResult:
        """Execute commands on one device and return result."""


@dataclass(frozen=True)
class ExecutionConfig:
    """Runtime behavior for the execution engine."""

    concurrency_limit: int = 5
    stagger_delay: float = 0.0
    stop_on_error: bool = True
    non_canary_retry_limit: int = 1
    retry_backoff_seconds: float = 0.0


class ExecutionEngine:
    """Canary-first orchestration with controlled parallel fan-out."""

    def __init__(self, worker: DeviceWorker, publisher: EventPublisher | None = None):
        self.worker = worker
        self.publisher = publisher

    def _emit(
        self,
        event_type: str,
        job_id: str,
        device: str | None = None,
        status: str | None = None,
        message: str | None = None,
    ) -> None:
        if self.publisher is None:
            return
        self.publisher.publish(
            ExecutionEvent(
                type=event_type,
                job_id=job_id,
                timestamp=utc_now(),
                device=device,
                status=status,
                message=message,
            )
        )

    def _run_with_retry(
        self,
        device: DeviceTarget,
        commands: list[str],
        retry_limit: int,
        backoff: float,
        control: ExecutionControl | None = None,
    ) -> DeviceExecutionResult:
        attempts = 0
        last_result: DeviceExecutionResult | None = None
        for attempt in range(retry_limit + 1):
            if control and control.cancel_event.is_set():
                return DeviceExecutionResult(
                    status="cancelled",
                    error="Execution cancelled",
                    attempts=attempt + 1,
                )
            attempts = attempt + 1
            result = self.worker.run(device=device, commands=commands)
            result.attempts = attempts
            last_result = result
            if result.status == "success":
                return result
            if attempt < retry_limit and backoff > 0:
                time.sleep(backoff)
        if last_result is None:
            return DeviceExecutionResult(
                status="failed",
                error="No execution result",
                attempts=attempts,
            )
        return last_result

    def run_job(
        self,
        job_id: str,
        devices: list[DeviceTarget],
        canary: DeviceTarget,
        commands: list[str],
        config: ExecutionConfig,
        control: ExecutionControl | None = None,
    ) -> JobRunSummary:
        """Run a job and return aggregated summary."""
        summary = JobRunSummary(job_id=job_id, status=JobStatus.RUNNING)
        self._emit(event_type="job_status", job_id=job_id, status="running")
        if control and control.cancel_event.is_set():
            summary.status = JobStatus.CANCELLED
            self._emit(event_type="job_complete", job_id=job_id, status="cancelled")
            return summary
        if not devices:
            summary.status = JobStatus.FAILED
            self._emit(event_type="job_complete", job_id=job_id, status="failed")
            return summary

        if canary.key not in {d.key for d in devices}:
            summary.status = JobStatus.FAILED
            summary.device_results[canary.key] = DeviceExecutionResult(
                status="failed",
                error="Canary is not part of target devices",
            )
            self._emit(
                event_type="device_status",
                job_id=job_id,
                device=canary.key,
                status="failed",
                message="Canary is not part of target devices",
            )
            self._emit(event_type="job_complete", job_id=job_id, status="failed")
            return summary

        # 1) Canary first, no retry.
        self._emit(
            event_type="device_status",
            job_id=job_id,
            device=canary.key,
            status="running",
            message="Starting canary",
        )
        canary_result = self._run_with_retry(
            device=canary,
            commands=commands,
            retry_limit=0,
            backoff=0.0,
            control=control,
        )
        summary.device_results[canary.key] = canary_result
        self._emit(
            event_type="device_status",
            job_id=job_id,
            device=canary.key,
            status=canary_result.status,
            message=canary_result.error,
        )
        if canary_result.status != "success":
            summary.status = (
                JobStatus.CANCELLED
                if canary_result.status == "cancelled"
                else JobStatus.FAILED
            )
            self._emit(
                event_type="job_complete", job_id=job_id, status=summary.status.value
            )
            return summary

        # 2) Execute remaining devices in parallel.
        remaining = [d for d in devices if d.key != canary.key]
        if not remaining:
            summary.status = JobStatus.COMPLETED
            self._emit(event_type="job_complete", job_id=job_id, status="completed")
            return summary

        concurrency = max(1, config.concurrency_limit)
        pending_devices = list(remaining)
        in_flight: dict[Future[DeviceExecutionResult], DeviceTarget] = {}
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            while pending_devices or in_flight:
                while (
                    control
                    and control.pause_event.is_set()
                    and not control.cancel_event.is_set()
                ):
                    time.sleep(0.2)
                if control and control.cancel_event.is_set():
                    summary.status = JobStatus.CANCELLED
                    self._emit(
                        event_type="job_complete", job_id=job_id, status="cancelled"
                    )
                    return summary
                while pending_devices and len(in_flight) < concurrency:
                    if config.stop_on_error and any(
                        r.status != "success" for r in summary.device_results.values()
                    ):
                        pending_devices = []
                        break
                    if control and control.cancel_event.is_set():
                        pending_devices = []
                        break
                    device = pending_devices.pop(0)
                    self._emit(
                        event_type="device_status",
                        job_id=job_id,
                        device=device.key,
                        status="running",
                    )
                    future = executor.submit(
                        self._run_with_retry,
                        device,
                        commands,
                        config.non_canary_retry_limit,
                        config.retry_backoff_seconds,
                        control,
                    )
                    in_flight[future] = device
                    if config.stagger_delay > 0:
                        time.sleep(config.stagger_delay)

                if not in_flight:
                    break

                done, _ = wait(in_flight.keys(), return_when=FIRST_COMPLETED)
                for future in done:
                    device = in_flight.pop(future)
                    result = future.result()
                    summary.device_results[device.key] = result
                    self._emit(
                        event_type="device_status",
                        job_id=job_id,
                        device=device.key,
                        status=result.status,
                        message=result.error,
                    )
                    if result.status == "cancelled":
                        summary.status = JobStatus.CANCELLED
                        self._emit(
                            event_type="job_complete", job_id=job_id, status="cancelled"
                        )
                        return summary

        if control and control.cancel_event.is_set():
            summary.status = JobStatus.CANCELLED
        else:
            has_failure = any(
                r.status != "success" for r in summary.device_results.values()
            )
            summary.status = JobStatus.FAILED if has_failure else JobStatus.COMPLETED
        self._emit(
            event_type="job_complete",
            job_id=job_id,
            status=summary.status.value,
        )
        return summary
