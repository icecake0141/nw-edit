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
"""Unit tests for CSV import service."""

import time

from backend_v2.app.application.device_import_service import DeviceImportService
from backend_v2.app.infrastructure.device_connection_validators import (
    SimulatedConnectionValidator,
)
from backend_v2.app.infrastructure.in_memory_device_store import InMemoryDeviceStore
from backend_v2.app.domain.models import DeviceProfile


class SlowOrderAwareValidator:
    """Validator that delays by host and can fail selected hosts."""

    def __init__(
        self,
        delays: dict[str, float],
        fail_hosts: set[str] | None = None,
    ) -> None:
        self.delays = delays
        self.fail_hosts = fail_hosts or set()

    def validate(self, device: DeviceProfile) -> tuple[bool, str | None]:
        time.sleep(self.delays.get(device.host, 0.0))
        if device.host in self.fail_hosts:
            return False, "connection failed"
        return True, None


def test_import_csv_parses_and_stores_valid_devices():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password,name,verify_cmds,host_vars\n"
        '10.0.0.1,22,cisco_ios,admin,pass,edge-1,show run;show ip int br,"{""hostname"":""edge-1"",""site"":100}"\n'
    )

    assert len(result.devices) == 1
    device = result.devices[0]
    assert device.host == "10.0.0.1"
    assert device.verify_cmds == ["show run", "show ip int br"]
    assert device.host_vars == {"hostname": "edge-1", "site": "100"}
    assert device.connection_ok is True
    assert result.failed_rows == []


def test_import_csv_collects_failed_rows():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password,host_vars\n"
        ",22,cisco_ios,admin,pass\n"
        "10.0.0.2,abc,cisco_ios,admin,pass,\n"
    )

    assert len(result.devices) == 0
    assert len(result.failed_rows) == 2


def test_import_csv_parallel_validation_preserves_input_order():
    store = InMemoryDeviceStore()
    service = DeviceImportService(
        store=store,
        validator=SlowOrderAwareValidator(
            delays={"10.0.0.1": 0.20, "10.0.0.2": 0.05, "10.0.0.3": 0.01}
        ),
    )
    result = service.import_csv(
        "host,port,device_type,username,password\n"
        "10.0.0.1,22,cisco_ios,admin,pass\n"
        "10.0.0.2,22,cisco_ios,admin,pass\n"
        "10.0.0.3,22,cisco_ios,admin,pass\n"
    )

    assert [d.host for d in result.devices] == ["10.0.0.1", "10.0.0.2", "10.0.0.3"]
    assert [d.host for d in store.list()] == ["10.0.0.1", "10.0.0.2", "10.0.0.3"]


def test_import_csv_parallel_validation_is_faster_than_serial_baseline():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SlowOrderAwareValidator(
            delays={"10.0.1.1": 0.20, "10.0.1.2": 0.20, "10.0.1.3": 0.20}
        ),
    )

    started_at = time.perf_counter()
    result = service.import_csv(
        "host,port,device_type,username,password\n"
        "10.0.1.1,22,cisco_ios,admin,pass\n"
        "10.0.1.2,22,cisco_ios,admin,pass\n"
        "10.0.1.3,22,cisco_ios,admin,pass\n"
    )
    elapsed = time.perf_counter() - started_at

    assert len(result.devices) == 3
    assert elapsed < 0.45


def test_import_csv_does_not_store_failed_connection_devices():
    store = InMemoryDeviceStore()
    service = DeviceImportService(
        store=store,
        validator=SlowOrderAwareValidator(
            delays={"10.0.2.1": 0.01, "10.0.2.2": 0.01},
            fail_hosts={"10.0.2.2"},
        ),
    )
    result = service.import_csv(
        "host,port,device_type,username,password\n"
        "10.0.2.1,22,cisco_ios,admin,pass\n"
        "10.0.2.2,22,cisco_ios,admin,pass\n"
    )

    assert [d.host for d in result.devices] == ["10.0.2.1"]
    assert [d.host for d in store.list()] == ["10.0.2.1"]


def test_import_csv_rejects_invalid_host_vars_json():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password,host_vars\n"
        '10.0.0.3,22,cisco_ios,admin,pass,"{""hostname"":}"\n'
    )

    assert len(result.devices) == 0
    assert len(result.failed_rows) == 1
    assert "Invalid host_vars JSON" in result.failed_rows[0].error


def test_import_csv_rejects_non_object_host_vars():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password,host_vars\n"
        '10.0.0.4,22,cisco_ios,admin,pass,"[""a""]"\n'
    )

    assert len(result.devices) == 0
    assert len(result.failed_rows) == 1
    assert result.failed_rows[0].error == "host_vars must be a JSON object"


def test_import_csv_rejects_invalid_host_vars_keys():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password,host_vars\n"
        '10.0.0.5,22,cisco_ios,admin,pass,"{""bad-key"":""x""}"\n'
    )

    assert len(result.devices) == 0
    assert len(result.failed_rows) == 1
    assert "Invalid host_vars key(s): bad-key" == result.failed_rows[0].error
