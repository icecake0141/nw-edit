"""Integration tests using mock SSH server."""

import pytest
from backend.app.ssh_executor import execute_device_commands, validate_device_connection


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
