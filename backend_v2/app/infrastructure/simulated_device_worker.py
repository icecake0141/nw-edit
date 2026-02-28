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
"""Simulation worker for API-level scaffolding."""

from __future__ import annotations

import os
import time

from backend_v2.app.application.execution_engine import DeviceWorker
from backend_v2.app.domain.models import DeviceExecutionResult, DeviceTarget


class SimulatedDeviceWorker(DeviceWorker):
    """Returns successful execution for every device."""

    def run(self, device: DeviceTarget, commands: list[str]) -> DeviceExecutionResult:
        delay_ms = int(os.getenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "0").strip() or "0")
        if delay_ms > 0:
            time.sleep(delay_ms / 1000.0)
        command_count = len(commands)
        return DeviceExecutionResult(
            status="success",
            logs=[f"simulated apply on {device.key}: {command_count} commands"],
        )
