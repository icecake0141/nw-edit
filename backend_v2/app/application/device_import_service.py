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
from concurrent.futures import ThreadPoolExecutor
import json
import re
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

    IMPORT_VALIDATION_WORKERS = 3
    _DEVICE_TYPE_ALIASES = {
        "generic linux": "linux",
        "generic_linux": "linux",
        "generic-linux": "linux",
    }

    def __init__(
        self, store: InMemoryDeviceStore, validator: DeviceConnectionValidator
    ):
        self.store = store
        self.validator = validator
        self._var_name_pattern = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

    def _normalize_device_type(self, device_type: str) -> str:
        canonical = device_type.strip()
        alias = self._DEVICE_TYPE_ALIASES.get(canonical.lower())
        if alias:
            return alias
        return canonical

    def import_csv(self, csv_content: str) -> DeviceImportResult:
        reader = csv.DictReader(io.StringIO(csv_content))
        failures: list[FailedRow] = []
        parsed_entries: list[tuple[int, dict[str, str], DeviceProfile]] = []
        required_headers = ("host", "device_type", "username", "password")

        raw_headers = reader.fieldnames or []
        headers = [header.strip() for header in raw_headers if header is not None]
        missing_headers = [name for name in required_headers if name not in headers]
        if missing_headers:
            return DeviceImportResult(
                devices=[],
                failed_rows=[
                    FailedRow(
                        row_number=1,
                        row={},
                        error=(
                            "CSV header is invalid or missing required columns: "
                            + ", ".join(missing_headers)
                        ),
                    )
                ],
            )

        row_number = 1
        while True:
            row_number += 1
            try:
                row = next(reader)
            except StopIteration:
                break
            except csv.Error as exc:
                failures.append(
                    FailedRow(
                        row_number=row_number,
                        row={},
                        error=f"CSV syntax error: {str(exc)}",
                    )
                )
                break
            extra_values = row.get(None)
            if extra_values:
                failures.append(
                    FailedRow(
                        row_number=row_number,
                        row={},
                        error=(
                            "CSV syntax error: unexpected extra column values: "
                            + ", ".join(value for value in extra_values if value)
                        ),
                    )
                )
                continue
            normalized = {
                (key or ""): ((value or "").strip() if isinstance(value, str) else "")
                for key, value in row.items()
            }
            missing = [field for field in required_headers if not normalized.get(field)]
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
            host_vars_raw = normalized.get("host_vars") or ""
            host_vars: dict[str, str] = {}
            if host_vars_raw:
                try:
                    loaded = json.loads(host_vars_raw)
                except json.JSONDecodeError as exc:
                    failures.append(
                        FailedRow(
                            row_number=row_number,
                            row=normalized,
                            error=f"Invalid host_vars JSON: {exc.msg}",
                        )
                    )
                    continue
                if not isinstance(loaded, dict):
                    failures.append(
                        FailedRow(
                            row_number=row_number,
                            row=normalized,
                            error="host_vars must be a JSON object",
                        )
                    )
                    continue
                invalid_keys = [
                    key
                    for key in loaded.keys()
                    if not isinstance(key, str) or not self._var_name_pattern.match(key)
                ]
                if invalid_keys:
                    failures.append(
                        FailedRow(
                            row_number=row_number,
                            row=normalized,
                            error=(
                                "Invalid host_vars key(s): "
                                + ", ".join(str(key) for key in invalid_keys)
                            ),
                        )
                    )
                    continue
                host_vars = {str(key): str(value) for key, value in loaded.items()}
            parsed_entries.append(
                (
                    row_number,
                    dict(normalized),
                    DeviceProfile(
                        host=normalized["host"],
                        port=port,
                        device_type=self._normalize_device_type(
                            normalized["device_type"]
                        ),
                        username=normalized["username"],
                        password=normalized["password"],
                        name=normalized.get("name") or None,
                        verify_cmds=verify_cmds,
                        host_vars=host_vars,
                    ),
                )
            )

        validation_results: dict[
            int, tuple[int, dict[str, str], DeviceProfile, bool, str | None]
        ] = {}
        indexed_devices = list(enumerate(parsed_entries))
        with ThreadPoolExecutor(max_workers=self.IMPORT_VALIDATION_WORKERS) as executor:
            future_map = {
                executor.submit(self.validator.validate, entry[2]): (index, entry)
                for index, entry in indexed_devices
            }
            for future, (index, entry) in future_map.items():
                ok, error = future.result()
                row_number, row, device = entry
                validation_results[index] = (row_number, row, device, ok, error)

        valid_devices: list[DeviceProfile] = []
        for index in sorted(validation_results):
            row_number, row, device, ok, error = validation_results[index]
            device.connection_ok = ok
            device.error_message = error
            if ok:
                valid_devices.append(device)
            else:
                failures.append(
                    FailedRow(
                        row_number=row_number,
                        row=row,
                        error=error or "Connection validation failed",
                    )
                )

        if failures:
            return DeviceImportResult(devices=[], failed_rows=failures)

        self.store.replace(valid_devices)
        return DeviceImportResult(devices=valid_devices, failed_rows=[])
