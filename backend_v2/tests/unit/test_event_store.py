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
"""Unit tests for in-memory event store."""

from backend_v2.app.application.events import ExecutionEvent
from backend_v2.app.infrastructure.in_memory_event_store import InMemoryEventStore


def test_event_store_appends_and_reads_with_cursor():
    store = InMemoryEventStore()
    e1 = ExecutionEvent(
        type="job_status", job_id="j1", timestamp="t1", status="running"
    )
    e2 = ExecutionEvent(
        type="job_complete", job_id="j1", timestamp="t2", status="completed"
    )

    store.publish(e1)
    store.publish(e2)

    assert store.event_count("j1") == 2
    assert [e.type for e in store.list_events("j1", 0)] == [
        "job_status",
        "job_complete",
    ]
    assert [e.type for e in store.list_events("j1", 1)] == ["job_complete"]
