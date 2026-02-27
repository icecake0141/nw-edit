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
"""Tests for device import endpoint."""

from fastapi.testclient import TestClient

from backend.app.main import app

client = TestClient(app)


def test_import_devices_skips_invalid_port_rows(monkeypatch):
    """Import endpoint should continue processing valid rows."""

    def mock_validate(_device_params):
        return True, None

    monkeypatch.setattr("backend.app.main.validate_device_connection", mock_validate)

    csv_content = (
        "host,port,device_type,username,password\n"
        "192.168.1.1,22,cisco_ios,admin,pass\n"
        "192.168.1.2,abc,cisco_ios,admin,pass\n"
        "192.168.1.3,22,cisco_ios,admin,pass"
    )

    response = client.post(
        "/api/devices/import",
        data=csv_content,
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 200
    payload = response.json()

    assert len(payload["devices"]) == 2
    assert len(payload["failed_rows"]) == 1
    assert payload["failed_rows"][0]["row_number"] == 3
    assert payload["failed_rows"][0]["error"] == "Invalid port value: abc"
