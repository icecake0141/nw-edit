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
"""Device connection validator implementations."""

from __future__ import annotations

from backend_v2.app.application.device_import_service import DeviceConnectionValidator
from backend_v2.app.domain.models import DeviceProfile


class SimulatedConnectionValidator(DeviceConnectionValidator):
    """Always succeeds. Useful for local scaffold testing."""

    def validate(self, device: DeviceProfile) -> tuple[bool, str | None]:
        del device
        return True, None


class NetmikoConnectionValidator(DeviceConnectionValidator):
    """Uses existing Netmiko-based validator from v1 backend."""

    def validate(self, device: DeviceProfile) -> tuple[bool, str | None]:
        from backend.app.ssh_executor import validate_device_connection

        return validate_device_connection(
            {
                "host": device.host,
                "port": device.port,
                "device_type": device.device_type,
                "username": device.username,
                "password": device.password,
            }
        )
