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
"""Unit tests for CSV parsing and device validation."""

from unittest.mock import Mock, patch
from backend.app.main import parse_csv_devices
from backend.app.ssh_executor import validate_device_connection


def test_parse_csv_valid():
    """Test parsing valid CSV."""
    csv_content = """host,port,device_type,username,password,name,verify_cmds
192.168.1.1,22,cisco_ios,admin,password123,Router1,show run | section snmp
10.0.0.1,2222,cisco_ios,admin,pass,Router2,"""

    devices, failed_rows = parse_csv_devices(csv_content)

    assert len(devices) == 2
    assert failed_rows == []
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

    devices, failed_rows = parse_csv_devices(csv_content)

    assert len(devices) == 1
    assert devices[0].port == 22  # default
    assert failed_rows == []


def test_parse_csv_blank_port_value():
    """Test CSV parsing with blank port value."""
    csv_content = """host,port,device_type,username,password
192.168.1.1,,cisco_ios,admin,password123"""

    devices, failed_rows = parse_csv_devices(csv_content)

    assert len(devices) == 1
    assert devices[0].port == 22
    assert failed_rows == []


def test_parse_csv_missing_required_fields():
    """Test CSV parsing with missing required fields."""
    csv_content = """host,device_type
192.168.1.1,cisco_ios"""

    devices, failed_rows = parse_csv_devices(csv_content)

    assert len(devices) == 0  # Should skip invalid rows
    assert len(failed_rows) == 1
    assert failed_rows[0].row_number == 2
    assert "Missing required fields" in failed_rows[0].error


def test_parse_csv_invalid_port_is_skipped():
    """Test CSV parsing skips row with invalid port and continues."""
    csv_content = """host,port,device_type,username,password
192.168.1.1,22,cisco_ios,admin,password123
192.168.1.2,abc,cisco_ios,admin,password123"""

    devices, failed_rows = parse_csv_devices(csv_content)

    assert len(devices) == 1
    assert devices[0].host == "192.168.1.1"
    assert len(failed_rows) == 1
    assert failed_rows[0].row_number == 3
    assert failed_rows[0].row["host"] == "192.168.1.2"
    assert failed_rows[0].error == "Invalid port value: abc"


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
