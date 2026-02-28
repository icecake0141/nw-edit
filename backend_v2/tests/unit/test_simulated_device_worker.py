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
"""Tests for simulated device worker."""

import time

from backend_v2.app.domain.models import DeviceTarget
from backend_v2.app.infrastructure.simulated_device_worker import SimulatedDeviceWorker


def test_simulated_worker_obeys_optional_delay(monkeypatch):
    monkeypatch.setenv("NW_EDIT_V2_SIMULATED_DELAY_MS", "50")
    worker = SimulatedDeviceWorker()
    start = time.perf_counter()
    result = worker.run(DeviceTarget(host="10.0.0.10", port=22), ["show version"])
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert result.status == "success"
    assert elapsed_ms >= 40
