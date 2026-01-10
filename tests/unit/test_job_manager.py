"""Unit tests for job manager."""

from backend.app.job_manager import JobManager
from backend.app.models import JobCreate, CanaryDevice, Device


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
