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

import time

from fastapi.testclient import TestClient

import backend_v2.app.api.main as api_main

from backend_v2.app.api.main import app


def test_health_endpoint():
    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_job_run_with_simulated_worker():
    client = TestClient(app)
    create_response = client.post(
        "/api/v2/jobs",
        json={"job_name": "test rollout", "creator": "tester"},
    )
    assert create_response.status_code == 200
    job_id = create_response.json()["job_id"]

    run_response = client.post(
        f"/api/v2/jobs/{job_id}/run",
        json={
            "devices": [
                {"host": "10.1.0.1", "port": 22},
                {"host": "10.1.0.2", "port": 22},
            ],
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
            "host,port,device_type,username,password,name,verify_cmds\n"
            "10.2.0.1,22,cisco_ios,admin,pass,edge-a,show run\n"
            "10.2.0.2,22,cisco_ios,admin,pass,edge-b,\n"
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
        },
    )
    assert run_response.status_code == 200
    payload = run_response.json()
    assert payload["status"] == "completed"
    assert "10.2.0.1:22" in payload["device_results"]


def test_list_jobs_endpoint():
    client = TestClient(app)
    client.post("/api/v2/jobs", json={"job_name": "first", "creator": "a"})
    client.post("/api/v2/jobs", json={"job_name": "second", "creator": "b"})

    response = client.get("/api/v2/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) >= 2
    assert all("job_id" in item and "status" in item for item in jobs)


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
    create = client.post(
        "/api/v2/jobs", json={"job_name": "async-run", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "devices": [{"host": "10.9.0.1", "port": 22}],
            "canary": {"host": "10.9.0.1", "port": 22},
            "commands": ["show version"],
        },
    )
    assert start.status_code == 200
    assert start.json()["status"] in {"running", "completed", "failed"}


def test_pause_resume_cancel_routes_exist():
    client = TestClient(app)
    create = client.post("/api/v2/jobs", json={"job_name": "ctl-run", "creator": "ops"})
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "devices": [
                {"host": "10.9.1.1", "port": 22},
                {"host": "10.9.1.2", "port": 22},
            ],
            "canary": {"host": "10.9.1.1", "port": 22},
            "commands": ["show version"],
            "concurrency_limit": 1,
            "stagger_delay": 0.2,
        },
    )

    pause = client.post(f"/api/v2/jobs/{job_id}/pause")
    resume = client.post(f"/api/v2/jobs/{job_id}/resume")
    cancel = client.post(f"/api/v2/jobs/{job_id}/cancel")
    assert pause.status_code in {200, 400, 409}
    assert resume.status_code in {200, 400, 409}
    assert cancel.status_code in {200, 400, 409}


def test_async_pause_resume_cancel_flow(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "700")

    create = client.post(
        "/api/v2/jobs", json={"job_name": "async-control-flow", "creator": "ops"}
    )
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    start = client.post(
        f"/api/v2/jobs/{job_id}/run/async",
        json={
            "devices": [
                {"host": "10.9.2.1", "port": 22},
                {"host": "10.9.2.2", "port": 22},
                {"host": "10.9.2.3", "port": 22},
                {"host": "10.9.2.4", "port": 22},
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
