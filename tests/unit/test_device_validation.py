"""Unit tests for CSV parsing and device validation."""

from unittest.mock import Mock, patch
from backend.app.main import parse_csv_devices
from backend.app.ssh_executor import validate_device_connection


def test_parse_csv_valid():
    """Test parsing valid CSV."""
    csv_content = """host,port,device_type,username,password,name,verify_cmds
192.168.1.1,22,cisco_ios,admin,password123,Router1,show run | section snmp
10.0.0.1,2222,cisco_ios,admin,pass,Router2,"""

    devices = parse_csv_devices(csv_content)

    assert len(devices) == 2
    assert devices[0].host == "192.168.1.1"
    assert devices[0].port == 22
    assert devices[0].device_type == "cisco_ios"
    assert devices[0].username == "admin"
    assert devices[0].password == "password123"
    assert devices[0].name == "Router1"
    assert devices[0].verify_cmds == "show run | section snmp"

    assert devices[1].host == "10.0.0.1"
    assert devices[1].port == 2222


def test_parse_csv_missing_port():
    """Test CSV parsing with default port."""
    csv_content = """host,device_type,username,password
192.168.1.1,cisco_ios,admin,password123"""

    devices = parse_csv_devices(csv_content)

    assert len(devices) == 1
    assert devices[0].port == 22  # default


def test_parse_csv_missing_required_fields():
    """Test CSV parsing with missing required fields."""
    csv_content = """host,device_type
192.168.1.1,cisco_ios"""

    devices = parse_csv_devices(csv_content)

    assert len(devices) == 0  # Should skip invalid rows


@patch("backend.app.ssh_executor.ConnectHandler")
def test_validate_device_connection_success(mock_connect):
    """Test successful device connection validation."""
    mock_instance = Mock()
    mock_instance.find_prompt.return_value = "Router>"
    mock_connect.return_value = mock_instance

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    }

    success, error = validate_device_connection(device_params)

    assert success is True
    assert error is None
    mock_instance.disconnect.assert_called_once()


@patch("backend.app.ssh_executor.ConnectHandler")
def test_validate_device_connection_auth_failure(mock_connect):
    """Test device connection validation with authentication failure."""
    from netmiko.exceptions import NetmikoAuthenticationException

    mock_connect.side_effect = NetmikoAuthenticationException("Auth failed")

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "wrong",
    }

    success, error = validate_device_connection(device_params)

    assert success is False
    assert "Authentication failed" in error


@patch("backend.app.ssh_executor.ConnectHandler")
def test_validate_device_connection_timeout(mock_connect):
    """Test device connection validation with timeout."""
    from netmiko.exceptions import NetmikoTimeoutException

    mock_connect.side_effect = NetmikoTimeoutException("Timeout")

    device_params = {
        "host": "192.168.1.1",
        "port": 22,
        "device_type": "cisco_ios",
        "username": "admin",
        "password": "password",
    }

    success, error = validate_device_connection(device_params)

    assert success is False
    assert "Connection timeout" in error
