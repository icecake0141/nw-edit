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

from backend_v2.app.application.device_import_service import DeviceImportService
from backend_v2.app.infrastructure.device_connection_validators import (
    SimulatedConnectionValidator,
)
from backend_v2.app.infrastructure.in_memory_device_store import InMemoryDeviceStore


def test_import_csv_parses_and_stores_valid_devices():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password,name,verify_cmds\n"
        "10.0.0.1,22,cisco_ios,admin,pass,edge-1,show run;show ip int br\n"
    )

    assert len(result.devices) == 1
    device = result.devices[0]
    assert device.host == "10.0.0.1"
    assert device.verify_cmds == ["show run", "show ip int br"]
    assert device.connection_ok is True
    assert result.failed_rows == []


def test_import_csv_collects_failed_rows():
    service = DeviceImportService(
        store=InMemoryDeviceStore(),
        validator=SimulatedConnectionValidator(),
    )
    result = service.import_csv(
        "host,port,device_type,username,password\n"
        ",22,cisco_ios,admin,pass\n"
        "10.0.0.2,abc,cisco_ios,admin,pass\n"
    )

    assert len(result.devices) == 0
    assert len(result.failed_rows) == 2
