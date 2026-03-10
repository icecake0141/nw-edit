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
"""API-level tests for v2 scaffold."""

import json
import os
import time

from fastapi.testclient import TestClient
import pytest

import backend_v2.app.api.main as api_main

from backend_v2.app.api.main import app
from backend_v2.app.domain.models import DeviceExecutionResult, JobRunSummary, JobStatus


class FailHostValidator:
    """Validator that fails for a specific host."""

    def validate(self, device):
        if device.host == "does-not-exist.local":
            return False, "connection failed"
        return True, None


def import_devices_for_run(client: TestClient, rows: list[str]) -> None:
    payload = (
        "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
        + "\n".join(rows)
    )
    imported = client.post(
        "/api/v2/devices/import",
        content=payload,
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200


@pytest.fixture(autouse=True)
def reset_in_memory_runtime_state():
    """Ensure each test starts with a clean in-memory runtime state."""
    original_worker_mode = os.environ.get("NW_EDIT_V2_WORKER_MODE")
    original_validator_mode = os.environ.get("NW_EDIT_V2_VALIDATOR_MODE")
    os.environ["NW_EDIT_V2_WORKER_MODE"] = "simulated"
    os.environ["NW_EDIT_V2_VALIDATOR_MODE"] = "simulated"

    deadline = time.monotonic() + 2.0
    while True:
        with api_main.run_coordinator._lock:
            alive = [
                thread
                for thread in api_main.run_coordinator._threads.values()
                if thread.is_alive()
            ]
        if not alive or time.monotonic() >= deadline:
            break
        time.sleep(0.05)
    with api_main.run_coordinator._lock:
        api_main.run_coordinator._threads = {
            job_id: thread
            for job_id, thread in api_main.run_coordinator._threads.items()
            if thread.is_alive()
        }
    with api_main.store._lock:
        api_main.store._jobs.clear()
    with api_main.device_store._lock:
        api_main.device_store._devices.clear()
    with api_main.event_store._lock:
        api_main.event_store._events_by_job.clear()
    with api_main.run_store._lock:
        api_main.run_store._latest_by_job.clear()
    with api_main.control_store._lock:
        api_main.control_store._controls.clear()
    api_main.engine.worker = api_main.SimulatedDeviceWorker()
    api_main.device_import_service.validator = api_main.SimulatedConnectionValidator()
    yield
    if original_worker_mode is None:
        os.environ.pop("NW_EDIT_V2_WORKER_MODE", None)
    else:
        os.environ["NW_EDIT_V2_WORKER_MODE"] = original_worker_mode
    if original_validator_mode is None:
        os.environ.pop("NW_EDIT_V2_VALIDATOR_MODE", None)
    else:
        os.environ["NW_EDIT_V2_VALIDATOR_MODE"] = original_validator_mode


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_runtime_modes_endpoint_defaults_worker_to_netmiko(monkeypatch):
    monkeypatch.delenv("NW_EDIT_V2_WORKER_MODE", raising=False)
    monkeypatch.delenv("NW_EDIT_V2_VALIDATOR_MODE", raising=False)
    client = TestClient(app)

    response = client.get("/api/v2/runtime/modes")

    assert response.status_code == 200
    assert response.json() == {
        "worker_mode": "netmiko",
        "validator_mode": "netmiko",
    }


def test_cors_allows_local_frontend_origin():
    client = TestClient(app)
    preflight = client.options(
        "/api/v2/devices/import",
        headers={
            "Origin": "http://127.0.0.1:3010",
            "Access-Control-Request-Method": "POST",
        },
    )
    assert preflight.status_code == 200
    assert preflight.headers["access-control-allow-origin"] == "http://127.0.0.1:3010"


def test_create_job_persists_global_vars():
    client = TestClient(app)
    response = client.post(
        "/api/v2/jobs",
        json={
            "job_name": "with globals",
            "creator": "tester",
            "global_vars": {"timezone": "Asia/Tokyo"},
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["global_vars"] == {"timezone": "Asia/Tokyo"}

    job = client.get(f"/api/v2/jobs/{payload['job_id']}")
    assert job.status_code == 200
    assert job.json()["global_vars"] == {"timezone": "Asia/Tokyo"}


def test_job_run_with_simulated_worker():
    client = TestClient(app)
    import_devices_for_run(
        client,
        [
            "10.1.0.1,22,cisco_ios,admin,pass,edge-a,show run,",
            "10.1.0.2,22,cisco_ios,admin,pass,edge-b,show run,",
        ],
    )
    create_response = client.post(
        "/api/v2/jobs",
        json={"job_name": "test rollout", "creator": "tester"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "imported_device_keys": ["10.1.0.1:22", "10.1.0.2:22"],
            "canary": {"host": "10.1.0.1", "port": 22},
            "commands": ["show version", "show ip int br"],
            "concurrency_limit": 2,
            "stagger_delay": 0.0,
            "stop_on_error": True,
            "non_canary_retry_limit": 1,
            "retry_backoff_seconds": 0.0,
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["status"] == "completed"
    assert payload["device_results"]["10.1.0.1:22"]["status"] == "success"
    assert payload["device_results"]["10.1.0.2:22"]["status"] == "success"
    assert "pre_output" in payload["device_results"]["10.1.0.1:22"]
    assert "diff" in payload["device_results"]["10.1.0.1:22"]
    assert "diff_truncated" in payload["device_results"]["10.1.0.1:22"]
    assert "diff_original_size" in payload["device_results"]["10.1.0.1:22"]

    events_response = client.get(f"/api/v2/jobs/{job_id}/events")
    assert events_response.status_code == 200
    events = events_response.json()
    assert len(events) > 0
    assert events[-1]["type"] == "job_complete"

    result_response = client.get(f"/api/v2/jobs/{job_id}/result")
    assert result_response.status_code == 200
    assert result_response.json()["status"] == "completed"


def test_device_import_and_run_with_imported_devices():
    client = TestClient(app)
    import_response = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            '10.2.0.1,22,cisco_ios,admin,pass,edge-a,show run,"{""hostname"":""edge-a""}"\n'
            '10.2.0.2,22,cisco_ios,admin,pass,edge-b,,"{""hostname"":""edge-b""}"\n'
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert import_response.status_code == 200
    assert len(import_response.json()["devices"]) == 2

    create_response = client.post(
        "/api/v2/jobs",
        json={"job_name": "imported run", "creator": "tester"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "commands": ["show version"],
            "imported_device_keys": ["10.2.0.1:22", "10.2.0.2:22"],
            "canary": {"host": "10.2.0.1", "port": 22},
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["status"] == "completed"
    assert "10.2.0.1:22" in payload["device_results"]


def test_import_devices_includes_prod_attribute_in_response():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars,prod\n"
            "10.2.9.1,22,cisco_ios,admin,pass,edge-prod,show run,,true\n"
            "10.2.9.2,22,cisco_ios,admin,pass,edge-nonprod,show run,,invalid\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200
    payload = imported.json()
    assert len(payload["devices"]) == 2
    assert payload["devices"][0]["prod"] is True
    assert payload["devices"][1]["prod"] is False


def test_list_devices_includes_prod_attribute():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars,prod\n"
            "10.2.10.1,22,cisco_ios,admin,pass,edge-prod,show run,,TRUE\n"
            "10.2.10.2,22,cisco_ios,admin,pass,edge-nonprod,show run,,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200

    listed = client.get("/api/v2/devices")
    assert listed.status_code == 200
    payload = listed.json()
    prod_flags = {f"{item['host']}:{item['port']}": item["prod"] for item in payload}
    assert prod_flags["10.2.10.1:22"] is True
    assert prod_flags["10.2.10.2:22"] is False


def test_run_fails_preflight_when_command_variable_is_missing():
    client = TestClient(app)
    import_devices_for_run(
        client,
        ["10.8.0.1,22,cisco_ios,admin,pass,edge-a,show run,"],
    )
    create_response = client.post(
        "/api/v2/jobs",
        json={"job_name": "missing vars", "creator": "tester"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "imported_device_keys": ["10.8.0.1:22"],
            "canary": {"host": "10.8.0.1", "port": 22},
            "commands": ["hostname {{hostname}}"],
        },
    )
    assert run_response.status_code == 400
    assert "Missing command variables" in run_response.json()["detail"]


def test_run_prefers_host_vars_over_global_vars():
    client = TestClient(app)
    import_response = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            '10.7.0.1,22,cisco_ios,admin,pass,edge-a,,"{""hostname"":""host-a""}"\n'
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert import_response.status_code == 200

    create_response = client.post(
        "/api/v2/jobs",
        json={
            "job_name": "host override",
            "creator": "tester",
            "global_vars": {"hostname": "global-name"},
        },
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "commands": ["hostname {{hostname}}"],
            "imported_device_keys": ["10.7.0.1:22"],
            "canary": {"host": "10.7.0.1", "port": 22},
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["status"] == "completed"


def test_run_rejects_when_canary_is_not_in_target_devices():
    client = TestClient(app)
    import_devices_for_run(
        client,
        ["10.3.0.1,22,cisco_ios,admin,pass,edge-a,show run,"],
    )
    create_response = client.post(
        "/api/v2/jobs",
        json={"job_name": "mismatch canary", "creator": "tester"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "imported_device_keys": ["10.3.0.1:22"],
            "canary": {"host": "10.3.0.99", "port": 22},
            "commands": ["show version"],
        },
    )
    assert run_response.status_code == 400
    assert run_response.json()["detail"] == "Canary device must be in the device list"


def test_list_jobs_endpoint():
    client = TestClient(app)
    import_devices_for_run(
        client,
        ["10.10.0.1,22,cisco_ios,admin,pass,edge-a,show run,"],
    )
    first = client.post("/api/v2/jobs", json={"job_name": "first", "creator": "a"})
    assert first.status_code == 200
    first_id = first.json()["job_id"]

    run_first = client.post(
        f"/api/v2/jobs/{first_id}/run",
        json={
            "imported_device_keys": ["10.10.0.1:22"],
            "canary": {"host": "10.10.0.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert run_first.status_code == 200

    second = client.post("/api/v2/jobs", json={"job_name": "second", "creator": "b"})
    assert second.status_code == 200

    response = client.get("/api/v2/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) >= 2
    assert all("job_id" in item and "status" in item for item in jobs)


def test_create_job_returns_409_when_active_job_exists():
    client = TestClient(app)
    first = client.post("/api/v2/jobs", json={"job_name": "first", "creator": "ops"})
    assert first.status_code == 200

    second = client.post("/api/v2/jobs", json={"job_name": "second", "creator": "ops"})
    assert second.status_code == 409
    assert "already queued" in second.json()["detail"]


def test_create_job_allowed_after_active_job_is_terminal():
    client = TestClient(app)
    import_devices_for_run(
        client,
        ["10.10.0.9,22,cisco_ios,admin,pass,edge-a,show run,"],
    )
    first = client.post("/api/v2/jobs", json={"job_name": "first", "creator": "ops"})
    assert first.status_code == 200
    first_id = first.json()["job_id"]

    run_first = client.post(
        f"/api/v2/jobs/{first_id}/run",
        json={
            "imported_device_keys": ["10.10.0.9:22"],
            "canary": {"host": "10.10.0.9", "port": 22},
            "commands": ["show version"],
        },
    )
    assert run_first.status_code == 200
    assert run_first.json()["status"] in {"completed", "failed", "cancelled"}

    second = client.post("/api/v2/jobs", json={"job_name": "second", "creator": "ops"})
    assert second.status_code == 200


def test_active_job_endpoint():
    client = TestClient(app)
    create = client.post(
        "/api/v2/jobs", json={"job_name": "active-check", "creator": "ops"}
    )
    assert create.status_code == 200

    active = client.get("/api/v2/jobs/active")
    assert active.status_code == 200
    payload = active.json()
    assert payload["active"] is True
    assert payload["job"]["job_name"] == "active-check"


def test_run_job_async_endpoint():
    client = TestClient(app)
    import_devices_for_run(
        client,
        ["10.9.0.1,22,cisco_ios,admin,pass,edge-a,show run,"],
    )
    create = client.post(
        "/api/v2/jobs", json={"job_name": "async-run", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": ["10.9.0.1:22"],
            "canary": {"host": "10.9.0.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert start.status_code == 200
    assert start.json()["status"] in {"running", "completed", "failed"}


def test_pause_resume_cancel_routes_exist():
    client = TestClient(app)
    import_devices_for_run(
        client,
        [
            "10.9.1.1,22,cisco_ios,admin,pass,edge-a,show run,",
            "10.9.1.2,22,cisco_ios,admin,pass,edge-b,show run,",
        ],
    )
    create = client.post("/api/v2/jobs", json={"job_name": "ctl-run", "creator": "ops"})
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": ["10.9.1.1:22", "10.9.1.2:22"],
            "canary": {"host": "10.9.1.1", "port": 22},
            "commands": ["show version"],
            "concurrency_limit": 1,
            "stagger_delay": 0.2,
        },
    )

    pause = client.post(f"/api/v2/jobs/{job_id}/pause")
    resume = client.post(f"/api/v2/jobs/{job_id}/resume")
    cancel = client.post(f"/api/v2/jobs/{job_id}/cancel")
    terminate = client.post(f"/api/v2/jobs/{job_id}/terminate")
    assert pause.status_code in {200, 400, 409}
    assert resume.status_code in {200, 400, 409}
    assert cancel.status_code in {200, 400, 409}
    assert terminate.status_code in {200, 400, 409}


def test_async_pause_resume_cancel_flow(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "700")
    import_devices_for_run(
        client,
        [
            "10.9.2.1,22,cisco_ios,admin,pass,edge-a,show run,",
            "10.9.2.2,22,cisco_ios,admin,pass,edge-b,show run,",
            "10.9.2.3,22,cisco_ios,admin,pass,edge-c,show run,",
            "10.9.2.4,22,cisco_ios,admin,pass,edge-d,show run,",
        ],
    )

    create = client.post(
        "/api/v2/jobs", json={"job_name": "async-control-flow", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": [
                "10.9.2.1:22",
                "10.9.2.2:22",
                "10.9.2.3:22",
                "10.9.2.4:22",
            ],
            "canary": {"host": "10.9.2.1", "port": 22},
            "commands": ["show version"],
            "concurrency_limit": 1,
            "stagger_delay": 0.0,
        },
    )
    assert start.status_code == 200

    # Wait until job enters running state.
    for _ in range(20):
        current = client.get(f"/api/v2/jobs/{job_id}")
        assert current.status_code == 200
        if current.json()["status"] == "running":
            break
        time.sleep(0.1)

    pause = client.post(f"/api/v2/jobs/{job_id}/pause")
    assert pause.status_code == 200
    assert pause.json()["status"] == "paused"

    control = api_main.control_store.get(job_id)
    assert control is not None
    assert control.pause_event.is_set() is True

    resume = client.post(f"/api/v2/jobs/{job_id}/resume")
    assert resume.status_code == 200
    assert resume.json()["status"] == "running"
    assert control.pause_event.is_set() is False

    cancel = client.post(f"/api/v2/jobs/{job_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["status"] == "cancelled"
    assert control.cancel_event.is_set() is True


def test_terminate_alias_cancels_async_run(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "700")
    import_devices_for_run(
        client,
        [
            "10.9.2.10,22,cisco_ios,admin,pass,edge-a,show run,",
            "10.9.2.11,22,cisco_ios,admin,pass,edge-b,show run,",
        ],
    )

    create = client.post(
        "/api/v2/jobs", json={"job_name": "async-terminate-flow", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": ["10.9.2.10:22", "10.9.2.11:22"],
            "canary": {"host": "10.9.2.10", "port": 22},
            "commands": ["show version"],
            "concurrency_limit": 1,
            "stagger_delay": 0.0,
        },
    )
    assert start.status_code == 200

    for _ in range(20):
        current = client.get(f"/api/v2/jobs/{job_id}")
        assert current.status_code == 200
        if current.json()["status"] == "running":
            break
        time.sleep(0.1)

    terminate = client.post(f"/api/v2/jobs/{job_id}/terminate")
    assert terminate.status_code == 200
    assert terminate.json()["status"] == "cancelled"


def test_sync_run_rejected_while_same_job_is_running_async(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "700")
    import_devices_for_run(
        client,
        [
            "10.9.3.1,22,cisco_ios,admin,pass,edge-a,show run,",
            "10.9.3.2,22,cisco_ios,admin,pass,edge-b,show run,",
        ],
    )

    create = client.post(
        "/api/v2/jobs", json={"job_name": "race-sync", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start_async = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": ["10.9.3.1:22", "10.9.3.2:22"],
            "canary": {"host": "10.9.3.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert start_async.status_code == 200

    sync = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "imported_device_keys": ["10.9.3.1:22"],
            "canary": {"host": "10.9.3.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert sync.status_code == 409
    assert "Invalid transition" in sync.json()["detail"]


def test_duplicate_async_run_does_not_clear_pause_control(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "700")
    import_devices_for_run(
        client,
        [
            "10.9.4.1,22,cisco_ios,admin,pass,edge-a,show run,",
            "10.9.4.2,22,cisco_ios,admin,pass,edge-b,show run,",
            "10.9.4.3,22,cisco_ios,admin,pass,edge-c,show run,",
        ],
    )

    create = client.post(
        "/api/v2/jobs", json={"job_name": "race-async", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start_async = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": [
                "10.9.4.1:22",
                "10.9.4.2:22",
                "10.9.4.3:22",
            ],
            "canary": {"host": "10.9.4.1", "port": 22},
            "commands": ["show version"],
            "concurrency_limit": 1,
        },
    )
    assert start_async.status_code == 200

    time.sleep(0.15)
    pause = client.post(f"/api/v2/jobs/{job_id}/pause")
    assert pause.status_code == 200

    control = api_main.control_store.get(job_id)
    assert control is not None
    assert control.pause_event.is_set() is True

    duplicate_async = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "imported_device_keys": ["10.9.4.1:22"],
            "canary": {"host": "10.9.4.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert duplicate_async.status_code == 409
    assert control.pause_event.is_set() is True


def test_presets_crud_and_duplicate_conflict():
    client = TestClient(app)
    name = f"ios-base-{time.time_ns()}"

    create = client.post(
        "/api/v2/presets",
        json={
            "name": name,
            "os_model": "cisco_ios",
            "commands": ["show version"],
            "verify_commands": ["show run | sec snmp"],
        },
    )
    assert create.status_code == 200
    created = create.json()
    assert created["name"] == name
    assert created["os_model"] == "cisco_ios"

    listed = client.get("/api/v2/presets?os_model=cisco_ios")
    assert listed.status_code == 200
    assert any(item["preset_id"] == created["preset_id"] for item in listed.json())

    duplicate = client.post(
        "/api/v2/presets",
        json={
            "name": name,
            "os_model": "cisco_ios",
            "commands": ["show clock"],
            "verify_commands": [],
        },
    )
    assert duplicate.status_code == 409

    updated = client.put(
        f"/api/v2/presets/{created['preset_id']}",
        json={
            "name": name,
            "os_model": "cisco_ios",
            "commands": ["show clock"],
            "verify_commands": ["show interfaces"],
        },
    )
    assert updated.status_code == 200
    assert updated.json()["commands"] == ["show clock"]
    assert updated.json()["verify_commands"] == ["show interfaces"]

    models = client.get("/api/v2/presets/os-models")
    assert models.status_code == 200
    assert "cisco_ios" in models.json()


def test_run_with_imported_device_keys_limits_targets():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.5.0.1,22,cisco_ios,admin,pass,edge-a,show run,\n"
            "10.5.0.2,22,cisco_ios,admin,pass,edge-b,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200

    create = client.post(
        "/api/v2/jobs",
        json={"job_name": "imported-keys", "creator": "tester"},
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "commands": ["show version"],
            "imported_device_keys": ["10.5.0.2:22"],
            "canary": {"host": "10.5.0.2", "port": 22},
        },
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["target_device_keys"] == ["10.5.0.2:22"]
    assert list(payload["device_results"].keys()) == ["10.5.0.2:22"]


def test_run_rejects_empty_imported_device_keys():
    client = TestClient(app)
    create = client.post(
        "/api/v2/jobs",
        json={"job_name": "empty-imported-keys", "creator": "tester"},
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "commands": ["show version"],
            "imported_device_keys": [],
        },
    )
    assert run.status_code == 400
    assert "imported_device_keys cannot be empty" in run.json()["detail"]


def test_run_uses_verify_commands_override_in_response():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.6.0.1,22,cisco_ios,admin,pass,edge-a,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200

    create = client.post(
        "/api/v2/jobs",
        json={"job_name": "verify-override", "creator": "tester"},
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "commands": ["show version"],
            "imported_device_keys": ["10.6.0.1:22"],
            "verify_commands": ["show ip interface brief"],
            "canary": {"host": "10.6.0.1", "port": 22},
        },
    )
    assert run.status_code == 200
    payload = run.json()
    assert payload["commands"] == ["show version"]
    assert payload["verify_commands"] == ["show ip interface brief"]


def test_import_devices_returns_400_when_connection_validation_fails(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(
        api_main.device_import_service, "validator", FailHostValidator()
    )

    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "does-not-exist.local,22,cisco_ios,admin,pass,edge-a,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 400
    detail = imported.json()["detail"]
    assert detail["message"] == "CSV import failed due to invalid rows"
    assert len(detail["failed_rows"]) == 1
    assert detail["failed_rows"][0]["row_number"] == 2


def test_import_devices_accepts_extra_column_values_for_v0_1_0_compatibility():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name\n"
            "10.6.0.2,22,cisco_ios,admin,pass,edge-a,unexpected\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200
    payload = imported.json()
    assert len(payload["devices"]) == 1
    assert payload["devices"][0]["host"] == "10.6.0.2"


def test_import_devices_skips_blank_lines_for_v0_1_0_compatibility():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "\n"
            "10.6.0.3,22,cisco_ios,admin,pass,edge-a,show run,\n"
            "\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200
    payload = imported.json()
    assert len(payload["devices"]) == 1
    assert payload["devices"][0]["host"] == "10.6.0.3"


def test_import_devices_accepts_header_casing_and_whitespace_variants():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            " Host ,Port,Device_Type,Username,Password,Name,Verify_Cmds,Host_Vars\n"
            "10.6.0.4,22,cisco_ios,admin,pass,edge-a,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200
    payload = imported.json()
    assert len(payload["devices"]) == 1
    assert payload["devices"][0]["host"] == "10.6.0.4"


def test_status_command_exec_returns_output_for_imported_device():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.11.0.1,22,cisco_ios,admin,pass,edge,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200

    response = client.post(
        "/api/v2/commands/exec",
        json={
            "host": "10.11.0.1",
            "port": 22,
            "commands": "show version\nshow ip interface brief",
        },
    )
    assert response.status_code == 200
    output = response.json()["output"]
    assert "$ show version" in output
    assert "$ show ip interface brief" in output


def test_status_command_exec_returns_404_for_unknown_device():
    client = TestClient(app)
    response = client.post(
        "/api/v2/commands/exec",
        json={"host": "10.11.9.9", "port": 22, "commands": "show version"},
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Device not found"


def test_status_command_exec_rejects_disruptive_commands():
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.11.0.2,22,cisco_ios,admin,pass,edge,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200

    response = client.post(
        "/api/v2/commands/exec",
        json={"host": "10.11.0.2", "port": 22, "commands": "reload"},
    )
    assert response.status_code == 400
    assert "Potentially disruptive commands" in response.json()["detail"]


def test_import_devices_progress_stream_success():
    client = TestClient(app)
    response = client.post(
        "/api/v2/devices/import/progress",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.14.0.1,22,cisco_ios,admin,pass,edge-a,show run,\n"
            "10.14.0.2,22,cisco_ios,admin,pass,edge-b,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    assert events[0]["type"] == "start"
    assert events[-1]["type"] == "complete"
    assert events[-1]["total"] == 2
    assert len(events[-1]["devices"]) == 2


def test_import_devices_progress_stream_emits_error_for_invalid_rows():
    client = TestClient(app)
    response = client.post(
        "/api/v2/devices/import/progress",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.14.1.1,22,cisco_ios,admin,pass,edge-a,show run,\n"
            "10.14.1.2,abc,cisco_ios,admin,pass,edge-b,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 200
    events = [json.loads(line) for line in response.text.splitlines() if line.strip()]
    assert events[0]["type"] == "start"
    assert events[-1]["type"] == "error"
    assert events[-1]["detail"]["message"] == "CSV import failed due to invalid rows"
    assert len(events[-1]["detail"]["failed_rows"]) >= 1


def test_run_verify_mode_none_disables_verify_commands(monkeypatch):
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.12.0.1,22,cisco_ios,admin,pass,edge-a,show run,\n"
            "10.12.0.2,22,cisco_ios,admin,pass,edge-b,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200
    created = client.post(
        "/api/v2/jobs", json={"job_name": "verify-none", "creator": "t"}
    )
    assert created.status_code == 200
    job_id = created.json()["job_id"]
    captured: dict[str, object] = {}

    def fake_run_job(**kwargs):
        captured.update(kwargs)
        return JobRunSummary(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            device_results={
                "10.12.0.1:22": DeviceExecutionResult(status="success"),
                "10.12.0.2:22": DeviceExecutionResult(status="success"),
            },
        )

    monkeypatch.setattr(api_main.engine, "run_job", fake_run_job)
    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "commands": ["show version"],
            "imported_device_keys": ["10.12.0.1:22", "10.12.0.2:22"],
            "verify_commands": ["show run"],
            "verify_mode": "none",
            "canary": {"host": "10.12.0.1", "port": 22},
        },
    )
    assert run.status_code == 200
    verify_by_device = captured["verify_commands_by_device"]
    assert verify_by_device["10.12.0.1:22"] == []
    assert verify_by_device["10.12.0.2:22"] == []


def test_run_rejects_missing_canary():
    client = TestClient(app)
    import_devices_for_run(
        client,
        ["10.16.0.1,22,cisco_ios,admin,pass,edge-a,show run,"],
    )
    create = client.post(
        "/api/v2/jobs", json={"job_name": "missing-canary", "creator": "tester"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "imported_device_keys": ["10.16.0.1:22"],
            "commands": ["show version"],
        },
    )
    assert run.status_code == 400
    assert run.json()["detail"] == "canary is required"


def test_run_rejects_legacy_devices_field():
    client = TestClient(app)
    create = client.post(
        "/api/v2/jobs", json={"job_name": "legacy-devices", "creator": "tester"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "devices": [{"host": "10.99.0.1", "port": 22}],
            "canary": {"host": "10.99.0.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert run.status_code == 400
    assert (
        run.json()["detail"]
        == "devices is no longer supported; use imported_device_keys"
    )


def test_run_verify_mode_canary_targets_only_canary(monkeypatch):
    client = TestClient(app)
    imported = client.post(
        "/api/v2/devices/import",
        content=(
            "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
            "10.13.0.1,22,cisco_ios,admin,pass,edge-a,show run,\n"
            "10.13.0.2,22,cisco_ios,admin,pass,edge-b,show run,\n"
        ),
        headers={"Content-Type": "text/plain"},
    )
    assert imported.status_code == 200
    created = client.post(
        "/api/v2/jobs", json={"job_name": "verify-canary", "creator": "t"}
    )
    assert created.status_code == 200
    job_id = created.json()["job_id"]
    captured: dict[str, object] = {}

    def fake_run_job(**kwargs):
        captured.update(kwargs)
        return JobRunSummary(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            device_results={
                "10.13.0.1:22": DeviceExecutionResult(status="success"),
                "10.13.0.2:22": DeviceExecutionResult(status="success"),
            },
        )

    monkeypatch.setattr(api_main.engine, "run_job", fake_run_job)
    run = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "imported_device_keys": ["10.13.0.1:22", "10.13.0.2:22"],
            "canary": {"host": "10.13.0.2", "port": 22},
            "commands": ["show version"],
            "verify_commands": ["show run"],
            "verify_mode": "canary",
        },
    )
    assert run.status_code == 200
    verify_by_device = captured["verify_commands_by_device"]
    assert verify_by_device["10.13.0.1:22"] == []
    assert verify_by_device["10.13.0.2:22"] == ["show run"]
