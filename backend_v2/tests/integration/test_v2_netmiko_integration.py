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
"""Integration tests for backend_v2 in netmiko mode."""

import importlib
import subprocess
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from backend_v2.app.infrastructure.netmiko_executor import validate_device_connection


def _ensure_mock_server():
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin123",
    }
    success, _ = validate_device_connection(device_params)
    if success:
        return None

    server_script = (
        Path(__file__).resolve().parents[3] / "tests" / "mock_ssh_server" / "server.py"
    )
    process = subprocess.Popen(
        [sys.executable, str(server_script)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(20):
        success, _ = validate_device_connection(device_params)
        if success:
            return process
        time.sleep(0.5)

    process.terminate()
    process.wait(timeout=5)
    return None


def _wait_for_status(
    client: TestClient,
    job_id: str,
    expected_statuses: set[str],
    timeout_seconds: float = 8.0,
) -> str | None:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = client.get(f"/api/v2/jobs/{job_id}")
        if response.status_code == 200:
            status = response.json().get("status")
            if status in expected_statuses:
                return status
        time.sleep(0.1)
    return None


@pytest.mark.integration
def test_v2_netmiko_import_and_run(monkeypatch):
    """Import device and run commands in netmiko mode."""
    process = _ensure_mock_server()
    if process is None:
        # Could be already running, re-check once.
        ready, _ = validate_device_connection(
            {
                "host": "localhost",
                "port": 2222,
                "device_type": "cisco_ios",
                "username": "admin",
                "password": "admin123",
            }
        )
        if not ready:
            pytest.skip("Mock SSH server not available")

    monkeypatch.setenv("NW_EDIT_V2_WORKER_MODE", "netmiko")
    monkeypatch.setenv("NW_EDIT_V2_VALIDATOR_MODE", "netmiko")
    import backend_v2.app.api.main as api_main

    importlib.reload(api_main)
    client = TestClient(api_main.app)

    try:
        import_response = client.post(
            "/api/v2/devices/import",
            content=(
                "host,port,device_type,username,password,name,verify_cmds\n"
                "localhost,2222,cisco_ios,admin,admin123,mock,show running-config | section snmp\n"
            ),
            headers={"Content-Type": "text/plain"},
        )
        assert import_response.status_code == 200
        assert len(import_response.json()["devices"]) == 1

        create_response = client.post(
            "/api/v2/jobs",
            json={"job_name": "netmiko-v2", "creator": "integration"},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        run_response = client.post(
            f"/api/v2/jobs/{job_id}/run",
            json={"commands": ["snmp-server location IntegrationLab"]},
        )
        assert run_response.status_code == 200
        payload = run_response.json()
        assert payload["status"] in {"completed", "failed"}
        result = payload["device_results"]["localhost:2222"]
        assert "pre_output" in result
        assert "post_output" in result
    finally:
        if process:
            process.terminate()
            process.wait(timeout=5)


@pytest.mark.integration
def test_v2_netmiko_async_pause_resume_cancel(monkeypatch):
    """Exercise async pause/resume/cancel lifecycle in netmiko mode."""
    process = _ensure_mock_server()
    if process is None:
        ready, _ = validate_device_connection(
            {
                "host": "localhost",
                "port": 2222,
                "device_type": "cisco_ios",
                "username": "admin",
                "password": "admin123",
            }
        )
        if not ready:
            pytest.skip("Mock SSH server not available")

    monkeypatch.setenv("NW_EDIT_V2_WORKER_MODE", "netmiko")
    monkeypatch.setenv("NW_EDIT_V2_VALIDATOR_MODE", "netmiko")
    import backend_v2.app.infrastructure.netmiko_executor as netmiko_executor
    import backend_v2.app.api.main as api_main

    original_execute = netmiko_executor.execute_device_commands

    def delayed_execute_device_commands(*args, **kwargs):
        time.sleep(2.0)
        return original_execute(*args, **kwargs)

    monkeypatch.setattr(
        netmiko_executor, "execute_device_commands", delayed_execute_device_commands
    )
    importlib.reload(api_main)
    client = TestClient(api_main.app)

    try:
        import_response = client.post(
            "/api/v2/devices/import",
            content=(
                "host,port,device_type,username,password,name,verify_cmds\n"
                "localhost,2222,cisco_ios,admin,admin123,mock-a,show running-config | section snmp\n"
                "127.0.0.1,2222,cisco_ios,admin,admin123,mock-b,show running-config | section snmp\n"
            ),
            headers={"Content-Type": "text/plain"},
        )
        assert import_response.status_code == 200
        assert len(import_response.json()["devices"]) == 2

        create_response = client.post(
            "/api/v2/jobs",
            json={"job_name": "netmiko-v2-async-control", "creator": "integration"},
        )
        assert create_response.status_code == 200
        job_id = create_response.json()["job_id"]

        start_response = client.post(
            f"/api/v2/jobs/{job_id}/run/async",
            json={
                "commands": ["snmp-server contact Integration Team"],
                "concurrency_limit": 1,
                "stagger_delay": 0.0,
            },
        )
        assert start_response.status_code == 200
        assert (
            _wait_for_status(client, job_id, {"running", "paused", "cancelled"})
            is not None
        )

        pause_response = client.post(f"/api/v2/jobs/{job_id}/pause")
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "paused"

        resume_response = client.post(f"/api/v2/jobs/{job_id}/resume")
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "running"

        cancel_response = client.post(f"/api/v2/jobs/{job_id}/cancel")
        assert cancel_response.status_code == 200
        assert cancel_response.json()["status"] == "cancelled"

        final_status = _wait_for_status(client, job_id, {"cancelled"}, 10.0)
        assert final_status == "cancelled"

        events_response = client.get(f"/api/v2/jobs/{job_id}/events")
        assert events_response.status_code == 200
        statuses = {item.get("status") for item in events_response.json()}
        assert {"paused", "running", "cancelled"}.issubset(statuses)
    finally:
        if process:
            process.terminate()
            process.wait(timeout=5)
