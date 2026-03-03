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
"""Unit tests for v2 netmiko executor helpers."""

from __future__ import annotations

import threading

import backend_v2.app.infrastructure.netmiko_executor as executor


class _FakeConnection:
    def __init__(self, pre_output: str = "before", post_output: str = "after"):
        self._pre_output = pre_output
        self._post_output = post_output
        self._send_count = 0
        self.disconnected = False

    def find_prompt(self) -> str:
        return "router#"

    def send_command(self, command: str, read_timeout: int) -> str:
        del command, read_timeout
        self._send_count += 1
        if self._send_count == 1:
            return self._pre_output
        return self._post_output

    def send_config_set(self, commands: list[str], read_timeout: int) -> str:
        del read_timeout
        return "\n".join(commands)

    def disconnect(self) -> None:
        self.disconnected = True


def _device_params() -> dict[str, object]:
    return {
        "host": "10.0.0.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "secret",
    }


def test_validate_device_connection_success(monkeypatch):
    fake = _FakeConnection()
    monkeypatch.setattr(executor, "ConnectHandler", lambda **kwargs: fake)
    ok, error = executor.validate_device_connection(_device_params())
    assert ok is True
    assert error is None
    assert fake.disconnected is True


def test_validate_device_connection_auth_failure(monkeypatch):
    def raise_auth(**kwargs):
        del kwargs
        raise executor.NetmikoAuthenticationException("bad credentials")

    monkeypatch.setattr(executor, "ConnectHandler", raise_auth)
    ok, error = executor.validate_device_connection(_device_params())
    assert ok is False
    assert error is not None
    assert "Authentication failed" in error


def test_execute_device_commands_success_with_diff(monkeypatch):
    fake = _FakeConnection(pre_output="snmp old", post_output="snmp new")
    monkeypatch.setattr(executor, "ConnectHandler", lambda **kwargs: fake)

    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["snmp-server contact Ops Team"],
        verify_cmds=["show running-config | section snmp"],
        is_canary=True,
    )

    assert result["status"] == "success"
    assert result["pre_output"] == "snmp old"
    assert result["post_output"] == "snmp new"
    assert isinstance(result["diff"], str)
    assert result["diff_truncated"] is False
    assert result["diff_original_size"] >= 0
    assert fake.disconnected is True


def test_execute_device_commands_detects_command_error(monkeypatch):
    fake = _FakeConnection()

    def send_config_set_error(commands: list[str], read_timeout: int) -> str:
        del commands, read_timeout
        return "% Invalid input detected at '^' marker."

    fake.send_config_set = send_config_set_error  # type: ignore[method-assign]
    monkeypatch.setattr(executor, "ConnectHandler", lambda **kwargs: fake)

    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["bad command"],
        verify_cmds=[],
        is_canary=True,
    )

    assert result["status"] == "failed"
    assert result["error_code"] == "command_error"
    assert "Command error detected" in str(result["error"])


def test_execute_device_commands_cancelled_before_connect(monkeypatch):
    cancel_event = threading.Event()
    cancel_event.set()

    def should_not_connect(**kwargs):
        del kwargs
        raise AssertionError("ConnectHandler should not be called when cancelled")

    monkeypatch.setattr(executor, "ConnectHandler", should_not_connect)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=[],
        cancel_event=cancel_event,
    )
    assert result["status"] == "cancelled"
    assert result["error_code"] == "cancelled"
