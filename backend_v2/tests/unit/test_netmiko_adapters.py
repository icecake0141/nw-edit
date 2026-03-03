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
"""Unit tests for v2 netmiko adapter classes."""

from __future__ import annotations

import backend_v2.app.infrastructure.netmiko_executor as netmiko_executor

from backend_v2.app.domain.models import DeviceProfile, DeviceTarget
from backend_v2.app.infrastructure.device_connection_validators import (
    NetmikoConnectionValidator,
    SimulatedConnectionValidator,
)
from backend_v2.app.infrastructure.netmiko_device_worker import NetmikoDeviceWorker


def _profile() -> DeviceProfile:
    return DeviceProfile(
        host="10.0.0.1",
        port=2222,
        device_type="cisco_ios",
        username="admin",
        password="secret",
        verify_cmds=["show running-config | section snmp"],
    )


def test_simulated_connection_validator_always_succeeds():
    validator = SimulatedConnectionValidator()
    ok, error = validator.validate(_profile())
    assert ok is True
    assert error is None


def test_netmiko_connection_validator_delegates_with_expected_params(monkeypatch):
    captured: dict[str, object] = {}

    def fake_validate_device_connection(device_params):
        captured.update(device_params)
        return True, None

    monkeypatch.setattr(
        netmiko_executor, "validate_device_connection", fake_validate_device_connection
    )

    validator = NetmikoConnectionValidator()
    ok, error = validator.validate(_profile())

    assert ok is True
    assert error is None
    assert captured == {
        "host": "10.0.0.1",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "secret",
    }


def test_netmiko_worker_returns_failed_when_profile_not_found():
    worker = NetmikoDeviceWorker(profile_resolver=lambda key: None)
    result = worker.run(DeviceTarget(host="10.9.9.9", port=22), ["show version"])
    assert result.status == "failed"
    assert "Device profile not found" in str(result.error)


def test_netmiko_worker_maps_executor_payload(monkeypatch):
    captured: dict[str, object] = {}

    def fake_execute_device_commands(**kwargs):
        captured.update(kwargs)
        return {
            "status": "success",
            "logs": ["connected", "done"],
            "error": None,
            "error_code": None,
            "pre_output": "before",
            "apply_output": "applied",
            "post_output": "after",
            "diff": "--- pre\n+++ post\n",
            "diff_truncated": True,
            "diff_original_size": 12345,
            "log_trimmed": True,
        }

    monkeypatch.setattr(
        netmiko_executor, "execute_device_commands", fake_execute_device_commands
    )

    profile = _profile()
    worker = NetmikoDeviceWorker(profile_resolver=lambda key: profile)
    result = worker.run(
        DeviceTarget(host=profile.host, port=profile.port),
        ["snmp-server location HQ"],
    )

    assert result.status == "success"
    assert result.logs == ["connected", "done"]
    assert result.pre_output == "before"
    assert result.apply_output == "applied"
    assert result.post_output == "after"
    assert result.diff_truncated is True
    assert result.diff_original_size == 12345
    assert result.log_trimmed is True
    assert captured["device_params"] == {
        "host": "10.0.0.1",
        "port": 2222,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "secret",
        "verify_cmds": ["show running-config | section snmp"],
    }
    assert captured["commands"] == ["snmp-server location HQ"]
    assert captured["verify_cmds"] == ["show running-config | section snmp"]
    assert captured["is_canary"] is True
    assert captured["retry_on_connection_error"] is False
