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
"""Integration tests using mock SSH server."""

import pytest
import subprocess
import sys
import time
from pathlib import Path
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import Device
from backend.app.ssh_executor import (
    execute_device_commands,
    run_status_command,
    validate_device_connection,
)


@pytest.mark.integration
def test_integration_connection_validation():
    """Test connection validation against mock SSH server."""
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin123",
    }

    success, error = validate_device_connection(device_params)

    # This will fail if mock SSH server is not running
    # In CI, this should be run with docker-compose
    if success:
        assert error is None
    else:
        # Server might not be running
        pytest.skip("Mock SSH server not available")


@pytest.mark.integration
def test_integration_execute_commands():
    """Test executing commands against mock SSH server."""
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin123",
    }

    # First check if server is available
    success, error = validate_device_connection(device_params)
    if not success:
        pytest.skip("Mock SSH server not available")

    commands = ["snmp-server community test RO", "snmp-server location TestLab"]

    verify_cmds = ["show running-config | section snmp"]

    result = execute_device_commands(
        device_params, commands, verify_cmds, is_canary=False
    )

    assert result["status"] == "success"
    assert result["error"] is None
    assert result["pre_output"] is not None
    assert result["apply_output"] is not None
    assert result["post_output"] is not None
    assert len(result["logs"]) > 0


@pytest.mark.integration
def test_integration_invalid_command():
    """Test executing invalid command against mock SSH server."""
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin123",
    }

    # First check if server is available
    success, error = validate_device_connection(device_params)
    if not success:
        pytest.skip("Mock SSH server not available")

    commands = ["invalid command that should fail"]

    result = execute_device_commands(device_params, commands, [], is_canary=False)

    # Mock server should return error for invalid commands
    assert result["status"] == "failed"
    assert "Command error detected" in result["error"]


@pytest.mark.integration
def test_integration_auth_failure():
    """Test authentication failure."""
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "wrongpassword",
    }

    success, error = validate_device_connection(device_params)

    if error and "not available" in error.lower():
        pytest.skip("Mock SSH server not available")

    assert success is False
    assert error is not None


@pytest.mark.integration
def test_integration_run_status_command():
    """Test read-only status command execution against mock SSH server."""
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin123",
    }

    success, _ = validate_device_connection(device_params)
    if not success:
        pytest.skip("Mock SSH server not available")

    output = run_status_command(device_params, "show ip interface brief")
    assert "Interface" in output


@pytest.mark.integration
def test_integration_status_command_api_end_to_end(monkeypatch):
    """Test status command endpoint end-to-end against mock SSH server."""
    client = TestClient(app)
    device_params = {
        "host": "localhost",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "admin123",
    }
    success, _ = validate_device_connection(device_params)
    mock_server_process = None
    if not success:
        server_script = (
            Path(__file__).resolve().parents[1] / "mock_ssh_server" / "server.py"
        )
        mock_server_process = subprocess.Popen(
            [sys.executable, str(server_script)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        for _ in range(20):
            success, _ = validate_device_connection(device_params)
            if success:
                break
            time.sleep(0.5)
        if not success:
            if mock_server_process:
                mock_server_process.terminate()
            pytest.skip("Unable to start mock SSH server")

    monkeypatch.setattr(
        "backend.app.main.job_manager.get_devices",
        lambda: [
            Device(
                host="localhost",
                port=2222,
                device_type="cisco_ios",
                username="admin",
                password="admin123",
                connection_ok=True,
            )
        ],
    )

    try:
        response = client.post(
            "/api/commands/exec",
            json={
                "host": "localhost",
                "port": 2222,
                "commands": "show ip interface brief",
            },
        )
        assert response.status_code == 200
        assert "Interface" in response.json()["output"]
    finally:
        if mock_server_process:
            mock_server_process.terminate()
            mock_server_process.wait(timeout=5)
