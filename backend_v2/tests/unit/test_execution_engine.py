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
"""Unit tests for canary-first execution engine."""

from backend_v2.app.application.execution_engine import ExecutionConfig, ExecutionEngine
from backend_v2.app.application.execution_control import ExecutionControl
from backend_v2.app.domain.models import DeviceExecutionResult, DeviceTarget, JobStatus
from backend_v2.app.infrastructure.in_memory_event_store import InMemoryEventStore


class StubWorker:
    """Deterministic worker with predefined outcomes by device key."""

    def __init__(self, plan: dict[str, list[str]]):
        self.plan = {k: list(v) for k, v in plan.items()}
        self.calls: list[str] = []

    def run(self, device: DeviceTarget, commands: list[str]) -> DeviceExecutionResult:
        del commands
        key = device.key
        self.calls.append(key)
        queue = self.plan.get(key, ["success"])
        status = queue.pop(0) if queue else "success"
        self.plan[key] = queue
        if status == "success":
            return DeviceExecutionResult(status="success", logs=[f"{key} ok"])
        return DeviceExecutionResult(status="failed", error=f"{key} failed")


def test_canary_failure_aborts_remaining_devices():
    canary = DeviceTarget(host="10.0.0.1", port=22)
    devices = [canary, DeviceTarget(host="10.0.0.2", port=22)]
    worker = StubWorker(plan={canary.key: ["failed"]})
    engine = ExecutionEngine(worker=worker)

    summary = engine.run_job(
        job_id="job-1",
        devices=devices,
        canary=canary,
        commands=["show version"],
        config=ExecutionConfig(),
    )

    assert summary.status == JobStatus.FAILED
    assert list(summary.device_results.keys()) == [canary.key]
    assert worker.calls == [canary.key]


def test_non_canary_retry_then_success():
    canary = DeviceTarget(host="10.0.1.1", port=22)
    other = DeviceTarget(host="10.0.1.2", port=22)
    worker = StubWorker(plan={other.key: ["failed", "success"]})
    engine = ExecutionEngine(worker=worker)

    summary = engine.run_job(
        job_id="job-2",
        devices=[canary, other],
        canary=canary,
        commands=["conf t"],
        config=ExecutionConfig(non_canary_retry_limit=1),
    )

    assert summary.status == JobStatus.COMPLETED
    assert summary.device_results[other.key].status == "success"
    assert summary.device_results[other.key].attempts == 2


def test_missing_canary_is_failed_job():
    canary = DeviceTarget(host="192.0.2.10", port=22)
    devices = [DeviceTarget(host="192.0.2.20", port=22)]
    worker = StubWorker(plan={})
    engine = ExecutionEngine(worker=worker)

    summary = engine.run_job(
        job_id="job-3",
        devices=devices,
        canary=canary,
        commands=["show run"],
        config=ExecutionConfig(),
    )

    assert summary.status == JobStatus.FAILED
    assert (
        summary.device_results[canary.key].error
        == "Canary is not part of target devices"
    )


def test_stop_on_error_stops_future_submissions():
    canary = DeviceTarget(host="203.0.113.1", port=22)
    d2 = DeviceTarget(host="203.0.113.2", port=22)
    d3 = DeviceTarget(host="203.0.113.3", port=22)
    worker = StubWorker(plan={d2.key: ["failed"], d3.key: ["success"]})
    engine = ExecutionEngine(worker=worker)

    summary = engine.run_job(
        job_id="job-4",
        devices=[canary, d2, d3],
        canary=canary,
        commands=["write memory"],
        config=ExecutionConfig(
            concurrency_limit=1,
            stop_on_error=True,
            non_canary_retry_limit=0,
        ),
    )

    assert summary.status == JobStatus.FAILED
    assert d3.key not in summary.device_results
    assert worker.calls == [canary.key, d2.key]


def test_engine_emits_completion_event():
    canary = DeviceTarget(host="198.51.100.1", port=22)
    worker = StubWorker(plan={})
    event_store = InMemoryEventStore()
    engine = ExecutionEngine(worker=worker, publisher=event_store)

    summary = engine.run_job(
        job_id="job-5",
        devices=[canary],
        canary=canary,
        commands=["show version"],
        config=ExecutionConfig(),
    )

    assert summary.status == JobStatus.COMPLETED
    events = event_store.list_events("job-5")
    assert events[-1].type == "job_complete"
    assert events[-1].status == "completed"


def test_engine_cancel_before_start():
    canary = DeviceTarget(host="203.0.113.50", port=22)
    worker = StubWorker(plan={})
    control = ExecutionControl()
    control.cancel_event.set()
    engine = ExecutionEngine(worker=worker)

    summary = engine.run_job(
        job_id="job-6",
        devices=[canary],
        canary=canary,
        commands=["show run"],
        config=ExecutionConfig(),
        control=control,
    )

    assert summary.status == JobStatus.CANCELLED
