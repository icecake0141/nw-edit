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
"""Unit tests for job manager."""

from backend.app.job_manager import JobManager
from backend.app.models import JobCreate, CanaryDevice, Device, JobStatus, DeviceStatus


def test_job_manager_add_devices():
    """Test adding devices to job manager."""
    jm = JobManager()

    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.2",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password",
            connection_ok=False,  # Should not be added
            error_message="Connection failed",
        ),
    ]

    jm.add_devices(devices)

    stored_devices = jm.get_devices()
    assert len(stored_devices) == 1  # Only the connected device
    assert stored_devices[0].host == "192.168.1.1"


def test_job_manager_create_job():
    """Test creating a job."""
    jm = JobManager()

    # Add some devices first
    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.2",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices)

    job_create = JobCreate(
        job_name="Test Job",
        creator="Admin",
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="snmp-server community public RO",
        verify_cmds=["show run | section snmp"],
        devices=[],  # Empty means use all
    )

    job = jm.create_job(job_create)

    assert job.job_id is not None
    assert job.job_name == "Test Job"
    assert job.creator == "Admin"
    assert len(job.device_results) == 2
    assert "192.168.1.1:22" in job.device_results
    assert "192.168.1.2:22" in job.device_results


def test_job_manager_create_job_with_specific_devices():
    """Test creating a job with specific devices."""
    jm = JobManager()

    devices = [
        Device(
            host="192.168.1.1",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password",
            connection_ok=True,
        ),
        Device(
            host="192.168.1.2",
            port=22,
            device_type="cisco_ios",
            username="admin",
            password="password",
            connection_ok=True,
        ),
    ]
    jm.add_devices(devices)

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22),
        commands="test",
        devices=[CanaryDevice(host="192.168.1.1", port=22)],  # Only one device
    )

    job = jm.create_job(job_create)

    assert len(job.device_results) == 1
    assert "192.168.1.1:22" in job.device_results


def test_job_manager_get_job():
    """Test retrieving a job."""
    jm = JobManager()

    jm.add_devices(
        [
            Device(
                host="192.168.1.1",
                port=22,
                device_type="cisco_ios",
                username="admin",
                password="password",
                connection_ok=True,
            )
        ]
    )

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22), commands="test", devices=[]
    )

    job = jm.create_job(job_create)
    job_id = job.job_id

    retrieved = jm.get_job(job_id)

    assert retrieved is not None
    assert retrieved.job_id == job_id

    # Test non-existent job
    assert jm.get_job("nonexistent") is None


def test_job_manager_pause_resume():
    """Test pausing and resuming a job."""
    jm = JobManager()

    jm.add_devices(
        [
            Device(
                host="192.168.1.1",
                port=22,
                device_type="cisco_ios",
                username="admin",
                password="password",
                connection_ok=True,
            )
        ]
    )

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22), commands="test", devices=[]
    )

    job = jm.create_job(job_create)
    with jm.lock:
        job.status = JobStatus.RUNNING

    assert jm.pause_job(job.job_id) is True
    assert job.status == JobStatus.PAUSED
    assert jm.resume_job(job.job_id) is True
    assert job.status == JobStatus.RUNNING


def test_job_manager_terminate_job_marks_cancelled():
    """Test terminating a job marks queued devices as cancelled."""
    jm = JobManager()

    jm.add_devices(
        [
            Device(
                host="192.168.1.1",
                port=22,
                device_type="cisco_ios",
                username="admin",
                password="password",
                connection_ok=True,
            )
        ]
    )

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22), commands="test", devices=[]
    )

    job = jm.create_job(job_create)
    with jm.lock:
        job.status = JobStatus.RUNNING

    assert jm.terminate_job(job.job_id) is True
    assert job.status == JobStatus.CANCELLED
    for result in job.device_results.values():
        assert result.status == DeviceStatus.CANCELLED


def test_job_manager_active_job_detection():
    """Test active job detection."""
    jm = JobManager()

    jm.add_devices(
        [
            Device(
                host="192.168.1.1",
                port=22,
                device_type="cisco_ios",
                username="admin",
                password="password",
                connection_ok=True,
            )
        ]
    )

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22), commands="test", devices=[]
    )

    job = jm.create_job(job_create)
    with jm.lock:
        job.status = JobStatus.RUNNING

    active_job = jm.get_active_job()
    assert active_job is not None
    assert active_job.job_id == job.job_id


def test_job_manager_history_limit_trims_oldest():
    """Test history limit trimming oldest completed jobs."""
    jm = JobManager(history_limit=2)

    jm.add_devices(
        [
            Device(
                host="192.168.1.1",
                port=22,
                device_type="cisco_ios",
                username="admin",
                password="password",
                connection_ok=True,
            )
        ]
    )

    job_create = JobCreate(
        canary=CanaryDevice(host="192.168.1.1", port=22), commands="test", devices=[]
    )

    job_one = jm.create_job(job_create)
    with jm.lock:
        job_one.status = JobStatus.COMPLETED

    job_two = jm.create_job(job_create)
    with jm.lock:
        job_two.status = JobStatus.COMPLETED

    job_three = jm.create_job(job_create)
    with jm.lock:
        job_three.status = JobStatus.COMPLETED

    history_ids = [job.job_id for job in jm.list_jobs()]
    assert history_ids == [job_three.job_id, job_two.job_id]
