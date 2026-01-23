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
"""Unit tests for job initialization and lifecycle edge cases."""

from backend.app.job_manager import JobManager
from backend.app.models import JobCreate, CanaryDevice, Device, DeviceParams


def test_job_captures_device_metadata_at_creation():
    """Test that job captures device metadata snapshot at creation time."""
    jm = JobManager()

    # Add devices with specific credentials
    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="oldpass",
            connection_ok=True,
            verify_cmds=["show version"],
        ),
        Device(
            host="192.168.1.2",
            port=22,
            device_type="cisco_nxos",
            username="admin",
            password="oldpass",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices)

    # Create job
    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test command",
        devices=[],  # Use all devices
    )
    job = jm.create_job(job_create)

    # Verify device_params were captured
    assert len(job.device_params) == 2
    assert "192.168.1.1:22" in job.device_params
    assert "192.168.1.2:22" in job.device_params

    # Check device 1 parameters
    dev1_params = job.device_params["192.168.1.1:22"]
    assert isinstance(dev1_params, DeviceParams)
    assert dev1_params.host == "192.168.1.1"
    assert dev1_params.port == 22
    assert dev1_params.device_type == "cisco_ios"
    assert dev1_params.username == "admin"
    assert dev1_params.password == "oldpass"
    assert dev1_params.verify_cmds == ["show version"]

    # Check device 2 parameters
    dev2_params = job.device_params["192.168.1.2:22"]
    assert dev2_params.device_type == "cisco_nxos"
    assert dev2_params.password == "oldpass"


def test_job_params_isolated_from_device_changes():
    """Test that job parameters are isolated from device list changes."""
    jm = JobManager()

    # Add initial devices
    initial_devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password1",
            connection_ok=True,
        ),
    ]
    jm.add_devices(initial_devices)

    # Create job
    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test",
        devices=[],
    )
    job = jm.create_job(job_create)

    # Store original params
    original_params = job.device_params["192.168.1.1:22"]
    assert original_params.password == "password1"

    # Now replace devices with different credentials
    new_devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_xe",
            username="newadmin",
            password="newpassword",
            connection_ok=True,
        ),
    ]
    jm.add_devices(new_devices)

    # Verify job's captured params are unchanged
    job_params = job.device_params["192.168.1.1:22"]
    assert job_params.password == "password1"  # Still old password
    assert job_params.device_type == "cisco_ios"  # Still old type
    assert job_params.username == "admin"  # Still old username

    # Verify JobManager has new devices
    current_devices = jm.get_devices()
    assert len(current_devices) == 1
    assert current_devices[0].password == "newpassword"


def test_job_with_custom_verify_commands():
    """Test that job-level verify commands override device defaults."""
    jm = JobManager()

    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
            connection_ok=True,
            verify_cmds=["device default cmd"],
        ),
    ]
    jm.add_devices(devices)

    # Create job with custom verify commands
    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test",
        devices=[],
        verify_cmds=["job specific cmd1", "job specific cmd2"],
    )
    job = jm.create_job(job_create)

    # Job should use job-level verify commands, not device defaults
    assert job.device_params["192.168.1.1:22"].verify_cmds == [
        "job specific cmd1",
        "job specific cmd2",
    ]


def test_job_without_custom_verify_commands_uses_device_defaults():
    """Test that jobs without verify_cmds use device defaults."""
    jm = JobManager()

    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
            connection_ok=True,
            verify_cmds=["device cmd1", "device cmd2"],
        ),
    ]
    jm.add_devices(devices)

    # Create job without custom verify commands
    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test",
        devices=[],
        verify_cmds=[],  # Empty
    )
    job = jm.create_job(job_create)

    # Should fall back to device defaults
    assert job.device_params["192.168.1.1:22"].verify_cmds == [
        "device cmd1",
        "device cmd2",
    ]


def test_multiple_jobs_with_different_device_states():
    """Test creating multiple jobs with changing device state."""
    jm = JobManager()

    # Add initial devices
    devices_v1 = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="v1pass",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.2",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="v1pass",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices_v1)

    # Create Job A
    job_a_create = JobCreate(
        job_name="Job A",
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="job a commands",
        devices=[],
    )
    job_a = jm.create_job(job_a_create)

    # Update devices
    devices_v2 = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_xe",
            username="newadmin",
            password="v2pass",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.3",
            port=2222,
            device_type="arista_eos",
            username="arista",
            password="v2pass",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices_v2)

    # Create Job B with new device state
    job_b_create = JobCreate(
        job_name="Job B",
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="job b commands",
        devices=[],
    )
    job_b = jm.create_job(job_b_create)

    # Job A should have v1 devices
    assert len(job_a.device_params) == 2
    assert "192.168.1.1:22" in job_a.device_params
    assert "192.168.1.2:22" in job_a.device_params
    assert job_a.device_params["192.168.1.1:22"].password == "v1pass"
    assert job_a.device_params["192.168.1.1:22"].device_type == "cisco_ios"

    # Job B should have v2 devices
    assert len(job_b.device_params) == 2
    assert "192.168.1.1:22" in job_b.device_params
    assert "192.168.1.3:2222" in job_b.device_params
    assert job_b.device_params["192.168.1.1:22"].password == "v2pass"
    assert job_b.device_params["192.168.1.1:22"].device_type == "cisco_xe"
    assert job_b.device_params["192.168.1.3:2222"].device_type == "arista_eos"


def test_job_with_specific_devices_subset():
    """Test that job correctly captures only specified devices."""
    jm = JobManager()

    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.2",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.3",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices)

    # Create job with only 2 of 3 devices
    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test",
        devices=[
            CanaryDevice(host="192.168.1.1", port=22),
            CanaryDevice(host="192.168.1.3", port=22),
        ],
    )
    job = jm.create_job(job_create)

    # Should have params for only 2 devices
    assert len(job.device_params) == 2
    assert "192.168.1.1:22" in job.device_params
    assert "192.168.1.3:22" in job.device_params
    assert "192.168.1.2:22" not in job.device_params


def test_job_params_immutable_after_creation():
    """Test that modifying device list doesn't affect existing job params."""
    jm = JobManager()

    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="pass",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices)

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test",
        devices=[],
    )
    job = jm.create_job(job_create)

    # Clear all devices
    jm.devices = []

    # Job params should still be intact
    assert "192.168.1.1:22" in job.device_params
    assert job.device_params["192.168.1.1:22"].password == "pass"
