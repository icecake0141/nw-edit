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
"""Thread-safe in-memory event store and publisher."""

from threading import Lock

from backend_v2.app.application.events import EventPublisher, ExecutionEvent


class InMemoryEventStore(EventPublisher):
    """Stores execution events for polling and websocket streaming."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._events_by_job: dict[str, list[ExecutionEvent]] = {}

    def publish(self, event: ExecutionEvent) -> None:
        with self._lock:
            self._events_by_job.setdefault(event.job_id, []).append(event)

    def list_events(self, job_id: str, start_index: int = 0) -> list[ExecutionEvent]:
        with self._lock:
            events = self._events_by_job.get(job_id, [])
            return list(events[start_index:])

    def event_count(self, job_id: str) -> int:
        with self._lock:
            return len(self._events_by_job.get(job_id, []))
