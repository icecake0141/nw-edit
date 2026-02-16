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
"""Tests for device import progress streaming."""

import json
from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_import_devices_with_progress_streams_events(monkeypatch):
    """Progress endpoint should emit start/progress/complete events in order."""

    def mock_validate(_device_params):
        return True, None

    monkeypatch.setattr("backend.app.main.validate_device_connection", mock_validate)

    csv_content = (
        "host,port,device_type,username,password,name\n"
        "192.168.1.1,22,cisco_ios,admin,pass,Router1\n"
        "192.168.1.2,22,cisco_ios,admin,pass,Router2"
    )

    response = client.post(
        "/api/devices/import/progress",
        data=csv_content,
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 200

    lines = [line for line in response.text.strip().splitlines() if line.strip()]
    events = [json.loads(line) for line in lines]

    assert events[0]["type"] == "start"
    assert events[0]["total"] == 2

    assert events[1]["type"] == "progress"
    assert events[1]["processed"] == 1
    assert events[1]["total"] == 2

    assert events[2]["type"] == "progress"
    assert events[2]["processed"] == 2
    assert events[2]["total"] == 2

    assert events[3]["type"] == "complete"
    assert events[3]["processed"] == 2
    assert events[3]["total"] == 2
    assert len(events[3]["devices"]) == 2
