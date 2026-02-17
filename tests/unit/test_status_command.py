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
"""Unit tests for status command execution."""

from unittest.mock import Mock, patch
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.models import Device
from backend.app.ssh_executor import run_status_command


@patch("backend.app.ssh_executor.ConnectHandler")
def test_run_status_command_success(mock_connect):
    """Status command runner should execute exec-mode commands."""
    mock_conn = Mock()
    mock_conn.send_command.side_effect = ["interface output", "snmp output"]
    mock_connect.return_value = mock_conn

    output = run_status_command(
        {
            "host": "192.168.1.1",
            "port": 22,
            "device_type": "cisco_ios",
            "username": "admin",
            "password": "password",
        },
        "show ip interface brief\nshow running-config | section snmp",
    )

    assert "$ show ip interface brief" in output
    assert "interface output" in output
    assert "$ show running-config | section snmp" in output
    assert "snmp output" in output
    mock_conn.disconnect.assert_called_once()


def test_run_status_command_blocks_disruptive_commands():
    """Status command runner should reject likely disruptive commands."""
    try:
        run_status_command(
            {
                "host": "192.168.1.1",
                "port": 22,
                "device_type": "cisco_ios",
                "username": "admin",
                "password": "password",
            },
            "configure terminal",
        )
        raise AssertionError("Expected ValueError for disruptive command")
    except ValueError as error:
        assert "Potentially disruptive commands" in str(error)


def test_status_command_api_success(monkeypatch):
    """Status command API should execute commands on managed device."""
    client = TestClient(app)

    monkeypatch.setattr(
        "backend.app.main.job_manager.get_devices",
        lambda: [
            Device(
                host="192.168.1.1",
                port=22,
                device_type="cisco_ios",
                username="admin",
                password="password",
                connection_ok=True,
            )
        ],
    )
    monkeypatch.setattr(
        "backend.app.main.run_status_command",
        lambda _device_params, _commands: "$ show ip interface brief\ninterface output",
    )

    response = client.post(
        "/api/commands/exec",
        json={
            "host": "192.168.1.1",
            "port": 22,
            "commands": "show ip interface brief",
        },
    )

    assert response.status_code == 200
    assert "interface output" in response.json()["output"]


def test_status_command_api_device_not_found(monkeypatch):
    """Status command API should return 404 when target device is not managed."""
    client = TestClient(app)
    monkeypatch.setattr("backend.app.main.job_manager.get_devices", lambda: [])

    response = client.post(
        "/api/commands/exec",
        json={
            "host": "192.168.1.100",
            "port": 22,
            "commands": "show version",
        },
    )

    assert response.status_code == 404
