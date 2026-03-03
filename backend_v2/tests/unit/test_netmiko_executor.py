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


def test_validate_device_connection_timeout(monkeypatch):
    def raise_timeout(**kwargs):
        del kwargs
        raise executor.NetmikoTimeoutException("timed out")

    monkeypatch.setattr(executor, "ConnectHandler", raise_timeout)
    ok, error = executor.validate_device_connection(_device_params())
    assert ok is False
    assert error is not None
    assert "Connection timeout" in error


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


def test_execute_device_commands_connection_timeout_failure(monkeypatch):
    def raise_timeout(**kwargs):
        del kwargs
        raise executor.NetmikoTimeoutException("connect timeout")

    monkeypatch.setattr(executor, "ConnectHandler", raise_timeout)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=[],
        is_canary=True,
    )
    assert result["status"] == "failed"
    assert result["error_code"] == "connection_timeout"


def test_execute_device_commands_connection_error_retries_once(monkeypatch):
    attempts = {"count": 0}

    def raise_runtime(**kwargs):
        del kwargs
        attempts["count"] += 1
        raise RuntimeError("connection broken")

    monkeypatch.setattr(executor, "ConnectHandler", raise_runtime)
    monkeypatch.setattr(executor.time, "sleep", lambda *_: None)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=[],
        is_canary=False,
        retry_on_connection_error=True,
    )
    assert attempts["count"] == 2
    assert result["status"] == "failed"
    assert result["error_code"] == "connection_error"


def test_execute_device_commands_command_timeout(monkeypatch):
    fake = _FakeConnection()

    def send_config_set_timeout(commands: list[str], read_timeout: int) -> str:
        del commands, read_timeout
        raise executor.NetmikoTimeoutException("command timeout")

    fake.send_config_set = send_config_set_timeout  # type: ignore[method-assign]
    monkeypatch.setattr(executor, "ConnectHandler", lambda **kwargs: fake)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=[],
        is_canary=True,
    )
    assert result["status"] == "failed"
    assert result["error_code"] == "command_timeout"
    assert fake.disconnected is True


def test_execute_device_commands_execution_error(monkeypatch):
    fake = _FakeConnection()

    def send_config_set_runtime_error(commands: list[str], read_timeout: int) -> str:
        del commands, read_timeout
        raise RuntimeError("boom")

    fake.send_config_set = send_config_set_runtime_error  # type: ignore[method-assign]
    monkeypatch.setattr(executor, "ConnectHandler", lambda **kwargs: fake)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=[],
        is_canary=True,
    )
    assert result["status"] == "failed"
    assert result["error_code"] == "execution_error"
    assert fake.disconnected is True


def test_execute_device_commands_cancelled_during_pre_verification(monkeypatch):
    cancel_event = threading.Event()
    fake = _FakeConnection()

    original_send_command = fake.send_command

    def send_command_and_cancel(command: str, read_timeout: int) -> str:
        output = original_send_command(command, read_timeout)
        cancel_event.set()
        return output

    fake.send_command = send_command_and_cancel  # type: ignore[method-assign]
    monkeypatch.setattr(executor, "ConnectHandler", lambda **kwargs: fake)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=["show run", "show ip int br"],
        is_canary=True,
        cancel_event=cancel_event,
    )
    assert result["status"] == "cancelled"
    assert result["error_code"] == "cancelled"
    assert fake.disconnected is True


def test_execute_device_commands_device_timeout_before_connect(monkeypatch):
    monkeypatch.setattr(executor, "DEVICE_TIMEOUT", -1)

    def should_not_connect(**kwargs):
        del kwargs
        raise AssertionError("ConnectHandler should not be called on early timeout")

    monkeypatch.setattr(executor, "ConnectHandler", should_not_connect)
    result = executor.execute_device_commands(
        device_params=_device_params(),
        commands=["show version"],
        verify_cmds=[],
    )
    assert result["status"] == "failed"
    assert result["error_code"] == "device_timeout"
