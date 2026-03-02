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
"""Unit tests for SSH executor."""

from unittest.mock import Mock, patch
from netmiko.exceptions import NetmikoTimeoutException  # type: ignore[import-untyped]
from backend.app.ssh_executor import (
    execute_device_commands,
    check_for_errors,
    create_unified_diff,
    trim_diff,
    trim_log,
)


def test_check_for_errors():
    """Test error pattern detection."""
    # Should detect errors
    assert check_for_errors("% Invalid input detected at '^' marker") is not None
    assert check_for_errors("Error: Command not found") is not None
    assert check_for_errors("Ambiguous command: 'conf'") is not None
    assert check_for_errors("Incomplete command") is not None

    # Should not detect errors
    assert check_for_errors("Configuration mode entered") is None
    assert check_for_errors("interface GigabitEthernet0/1") is None


def test_trim_log():
    """Test log trimming."""
    # Small log should not be trimmed
    small_log = "Line 1\nLine 2\nLine 3"
    result, trimmed = trim_log(small_log)
    assert trimmed is False
    assert result == small_log

    # Large log should be trimmed
    large_log = "A" * (1024 * 1024 + 100)
    result, trimmed = trim_log(large_log)
    assert trimmed is True
    assert len(result) == 1024 * 1024
    assert result == large_log[: 1024 * 1024]


def test_create_unified_diff():
    """Test unified diff creation."""
    pre = "line 1\nline 2\nline 3\n"
    post = "line 1\nline 2 modified\nline 3\n"

    diff = create_unified_diff(pre, post)

    assert "---" in diff
    assert "+++" in diff
    assert "-line 2" in diff
    assert "+line 2 modified" in diff


def test_trim_diff():
    """Test diff trimming metadata."""
    small_diff = "x" * 20
    trimmed_diff, was_trimmed, original_size = trim_diff(small_diff, max_size=100)
    assert trimmed_diff == small_diff
    assert was_trimmed is False
    assert original_size == 20

    large_diff = "y" * 120
    trimmed_diff, was_trimmed, original_size = trim_diff(large_diff, max_size=50)
    assert was_trimmed is True
    assert original_size == 120
    assert len(trimmed_diff) == 50


@patch("backend.app.ssh_executor.ConnectHandler")
def test_execute_device_commands_success(mock_connect):
    """Test successful command execution."""
    mock_conn = Mock()
    mock_conn.send_command.return_value = "SNMP config output"
    mock_conn.send_config_set.return_value = "Config applied successfully"
    mock_connect.return_value = mock_conn

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    }

    commands = ["snmp-server community public RO"]
    verify_cmds = ["show running-config | section snmp"]

    result = execute_device_commands(
        device_params, commands, verify_cmds, is_canary=False
    )

    assert result["status"] == "success"
    assert result["error"] is None
    assert result["pre_output"] == "SNMP config output"
    assert result["apply_output"] == "Config applied successfully"
    assert result["post_output"] == "SNMP config output"
    assert result["diff"] is not None
    assert result["diff_truncated"] is False
    assert result["diff_original_size"] >= len(result["diff"])
    assert len(result["logs"]) > 0

    mock_conn.disconnect.assert_called()


@patch("backend.app.ssh_executor.ConnectHandler")
def test_execute_device_commands_with_error(mock_connect):
    """Test command execution with error in output."""
    mock_conn = Mock()
    mock_conn.send_command.return_value = "SNMP config"
    mock_conn.send_config_set.return_value = "% Invalid input detected"
    mock_connect.return_value = mock_conn

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    }

    commands = ["invalid command"]
    verify_cmds = ["show running-config"]

    result = execute_device_commands(
        device_params, commands, verify_cmds, is_canary=False
    )

    assert result["status"] == "failed"
    assert "Command error detected" in result["error"]


@patch("backend.app.ssh_executor.ConnectHandler")
def test_execute_device_commands_connection_retry(mock_connect):
    """Test connection retry logic for non-canary device."""
    # Fail first, succeed second
    mock_conn = Mock()
    mock_conn.send_command.return_value = "output"
    mock_conn.send_config_set.return_value = "success"

    call_count = [0]

    def connect_side_effect(*args, **kwargs):
        call_count[0] += 1
        if call_count[0] == 1:
            raise NetmikoTimeoutException("Timeout")
        return mock_conn

    mock_connect.side_effect = connect_side_effect

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    }

    commands = ["test"]
    verify_cmds = []

    result = execute_device_commands(
        device_params,
        commands,
        verify_cmds,
        is_canary=False,  # Non-canary should retry
        retry_on_connection_error=True,
    )

    assert result["status"] == "success"
    assert call_count[0] == 2  # Should have retried


@patch("backend.app.ssh_executor.ConnectHandler")
def test_execute_device_commands_canary_no_retry(mock_connect):
    """Test canary device does not retry on connection failure."""
    mock_connect.side_effect = NetmikoTimeoutException("Timeout")

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    }

    commands = ["test"]
    verify_cmds = []

    result = execute_device_commands(
        device_params,
        commands,
        verify_cmds,
        is_canary=True,  # Canary should not retry
        retry_on_connection_error=False,
    )

    assert result["status"] == "failed"
    assert "Connection failed" in result["error"]
    assert result["error_code"] == "connection_timeout"
    assert mock_connect.call_count == 1  # Should not have retried


@patch("backend.app.ssh_executor.ConnectHandler")
def test_execute_device_commands_command_timeout_error_code(mock_connect):
    """Test command timeout classification."""
    mock_conn = Mock()
    mock_conn.send_command.return_value = "SNMP config"
    mock_conn.send_config_set.side_effect = NetmikoTimeoutException("read timeout")
    mock_connect.return_value = mock_conn

    result = execute_device_commands(
        device_params={
            "host": "192.168.1.1",
            "port": 22,
            "device_type": "cisco_ios",
            "username": "admin",
            "password": "password",
        },
        commands=["snmp-server community public RO"],
        verify_cmds=["show running-config | section snmp"],
    )

    assert result["status"] == "failed"
    assert result["error_code"] == "command_timeout"


@patch("backend.app.ssh_executor.ConnectHandler")
@patch("backend.app.ssh_executor.time.monotonic")
def test_execute_device_commands_total_timeout_error_code(mock_monotonic, mock_connect):
    """Test total device timeout classification before command execution."""
    mock_conn = Mock()
    mock_connect.return_value = mock_conn
    mock_monotonic.side_effect = [0.0, 181.0]

    result = execute_device_commands(
        device_params={
            "host": "192.168.1.1",
            "port": 22,
            "device_type": "cisco_ios",
            "username": "admin",
            "password": "password",
        },
        commands=["show version"],
        verify_cmds=[],
    )

    assert result["status"] == "failed"
    assert result["error_code"] == "device_timeout"
    assert "Device total timeout" in result["error"]
    assert mock_connect.call_count == 0


@patch("backend.app.ssh_executor.ConnectHandler")
def test_execute_device_commands_diff_truncation_metadata(mock_connect):
    """Test diff truncation metadata when diff exceeds configured size."""
    from backend.app import ssh_executor

    mock_conn = Mock()
    mock_conn.send_command.side_effect = [
        "line-1\nline-2",
        "line-1\nline-2\nline-3\nline-4\nline-5",
    ]
    mock_conn.send_config_set.return_value = "ok"
    mock_connect.return_value = mock_conn

    original_defaults = ssh_executor.trim_diff.__defaults__
    ssh_executor.trim_diff.__defaults__ = (10,)
    try:
        result = execute_device_commands(
            device_params={
                "host": "192.168.1.1",
                "port": 22,
                "device_type": "cisco_ios",
                "username": "admin",
                "password": "password",
            },
            commands=["snmp-server community public RO"],
            verify_cmds=["show running-config | section snmp"],
        )
    finally:
        ssh_executor.trim_diff.__defaults__ = original_defaults

    assert result["status"] == "success"
    assert result["diff_truncated"] is True
    assert result["diff_original_size"] > len(result["diff"])
    assert len(result["diff"]) == 10
