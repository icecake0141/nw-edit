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
"""In-memory execution control store."""

from __future__ import annotations

from threading import Lock

from backend_v2.app.application.execution_control import ExecutionControl


class InMemoryControlStore:
    """Stores execution control objects by job_id."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._controls: dict[str, ExecutionControl] = {}

    def get_or_create(self, job_id: str) -> ExecutionControl:
        with self._lock:
            if job_id not in self._controls:
                self._controls[job_id] = ExecutionControl()
            return self._controls[job_id]

    def get(self, job_id: str) -> ExecutionControl | None:
        with self._lock:
            return self._controls.get(job_id)
