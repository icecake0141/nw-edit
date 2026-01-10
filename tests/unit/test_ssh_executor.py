"""Unit tests for SSH executor."""

from unittest.mock import Mock, patch
from backend.app.ssh_executor import (
    execute_device_commands,
    check_for_errors,
    create_unified_diff,
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
    from netmiko.exceptions import NetmikoTimeoutException

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
    from netmiko.exceptions import NetmikoTimeoutException

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
    assert mock_connect.call_count == 1  # Should not have retried
