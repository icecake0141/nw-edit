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
"""Unit tests for websocket connection manager."""

import asyncio

import pytest

from backend.app.ws import ConnectionManager


class _FakeWebSocket:
    def __init__(self):
        self.accepted = False

    async def accept(self):
        self.accepted = True


class _SlowConnection:
    def __init__(self):
        self.messages = []

    async def send_json(self, message: dict):
        await asyncio.sleep(0.05)
        self.messages.append(message)


class _FastConnection:
    def __init__(self):
        self.messages = []

    async def send_json(self, message: dict):
        self.messages.append(message)


class _FailingConnection:
    async def send_json(self, message: dict):
        raise RuntimeError("send failed")


@pytest.mark.asyncio
async def test_send_message_times_out_slow_connection(monkeypatch):
    manager = ConnectionManager()
    job_id = "job-1"
    slow = _SlowConnection()
    fast = _FastConnection()
    manager.active_connections[job_id] = {slow, fast}

    monkeypatch.setattr("backend.app.ws.WS_SEND_TIMEOUT_SECONDS", 0.01)

    await manager.send_message(job_id, {"type": "test"})

    assert fast.messages == [{"type": "test"}]
    assert slow not in manager.active_connections[job_id]


@pytest.mark.asyncio
async def test_send_message_removes_failing_connection():
    manager = ConnectionManager()
    job_id = "job-2"
    failing = _FailingConnection()
    fast = _FastConnection()
    manager.active_connections[job_id] = {failing, fast}

    await manager.send_message(job_id, {"type": "test"})

    assert fast.messages == [{"type": "test"}]
    assert failing not in manager.active_connections[job_id]


@pytest.mark.asyncio
async def test_connect_registers_single_callback_per_job(monkeypatch):
    manager = ConnectionManager()
    callbacks = []

    def _register(job_id: str, callback):
        callbacks.append((job_id, callback))

    monkeypatch.setattr("backend.app.ws.job_manager.register_ws_callback", _register)

    ws1 = _FakeWebSocket()
    ws2 = _FakeWebSocket()

    await manager.connect("job-3", ws1)
    await manager.connect("job-3", ws2)

    assert ws1.accepted is True
    assert ws2.accepted is True
    assert len(callbacks) == 1
    assert callbacks[0][0] == "job-3"


@pytest.mark.asyncio
async def test_disconnect_unregisters_callback_when_last_connection_closed(monkeypatch):
    manager = ConnectionManager()
    registered = []
    unregistered = []

    def _register(job_id: str, callback):
        registered.append((job_id, callback))

    def _unregister(job_id: str, callback):
        unregistered.append((job_id, callback))

    monkeypatch.setattr("backend.app.ws.job_manager.register_ws_callback", _register)
    monkeypatch.setattr(
        "backend.app.ws.job_manager.unregister_ws_callback", _unregister
    )

    ws1 = _FakeWebSocket()
    ws2 = _FakeWebSocket()

    await manager.connect("job-4", ws1)
    await manager.connect("job-4", ws2)
    await manager.disconnect("job-4", ws1)

    assert len(unregistered) == 0

    await manager.disconnect("job-4", ws2)

    assert len(registered) == 1
    assert len(unregistered) == 1
    assert unregistered[0][0] == "job-4"
    assert unregistered[0][1] is registered[0][1]
