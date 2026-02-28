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
"""Thread-safe in-memory device store."""

from __future__ import annotations

from threading import Lock

from backend_v2.app.domain.models import DeviceProfile


class InMemoryDeviceStore:
    """Stores validated device profiles in memory."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._devices: list[DeviceProfile] = []

    def replace(self, devices: list[DeviceProfile]) -> None:
        with self._lock:
            self._devices = list(devices)

    def list(self) -> list[DeviceProfile]:
        with self._lock:
            return list(self._devices)

    def get_by_key(self, key: str) -> DeviceProfile | None:
        with self._lock:
            for device in self._devices:
                if device.key == key:
                    return device
        return None
