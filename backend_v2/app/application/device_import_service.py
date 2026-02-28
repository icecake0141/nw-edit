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
"""CSV device import use-case for v2 backend."""

from __future__ import annotations

import csv
import io
from dataclasses import dataclass, field
from typing import Protocol

from backend_v2.app.domain.models import DeviceProfile
from backend_v2.app.infrastructure.in_memory_device_store import InMemoryDeviceStore


class DeviceConnectionValidator(Protocol):
    """Connection validator contract."""

    def validate(self, device: DeviceProfile) -> tuple[bool, str | None]:
        """Return connection status and optional error."""


@dataclass
class FailedRow:
    """Failed CSV row details."""

    row_number: int
    row: dict[str, str]
    error: str


@dataclass
class DeviceImportResult:
    """Import result details."""

    devices: list[DeviceProfile] = field(default_factory=list)
    failed_rows: list[FailedRow] = field(default_factory=list)


class DeviceImportService:
    """Parses and validates device CSV data."""

    def __init__(
        self, store: InMemoryDeviceStore, validator: DeviceConnectionValidator
    ):
        self.store = store
        self.validator = validator

    def import_csv(self, csv_content: str) -> DeviceImportResult:
        reader = csv.DictReader(io.StringIO(csv_content))
        failures: list[FailedRow] = []
        parsed_devices: list[DeviceProfile] = []

        for row_number, row in enumerate(reader, start=2):
            normalized = {
                (key or ""): ((value or "").strip() if isinstance(value, str) else "")
                for key, value in row.items()
            }
            required = ("host", "device_type", "username", "password")
            missing = [field for field in required if not normalized.get(field)]
            if missing:
                failures.append(
                    FailedRow(
                        row_number=row_number,
                        row=normalized,
                        error=f"Missing required fields: {', '.join(missing)}",
                    )
                )
                continue

            port_raw = normalized.get("port", "")
            try:
                port = int(port_raw or "22")
            except ValueError:
                failures.append(
                    FailedRow(
                        row_number=row_number,
                        row=normalized,
                        error=f"Invalid port value: {port_raw}",
                    )
                )
                continue

            verify_cmds = [
                cmd.strip()
                for cmd in (normalized.get("verify_cmds") or "").split(";")
                if cmd.strip()
            ]
            parsed_devices.append(
                DeviceProfile(
                    host=normalized["host"],
                    port=port,
                    device_type=normalized["device_type"],
                    username=normalized["username"],
                    password=normalized["password"],
                    name=normalized.get("name") or None,
                    verify_cmds=verify_cmds,
                )
            )

        valid_devices: list[DeviceProfile] = []
        for device in parsed_devices:
            ok, error = self.validator.validate(device)
            device.connection_ok = ok
            device.error_message = error
            if ok:
                valid_devices.append(device)

        self.store.replace(valid_devices)
        return DeviceImportResult(devices=valid_devices, failed_rows=failures)
