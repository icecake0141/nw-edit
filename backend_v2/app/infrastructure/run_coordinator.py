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
"""Background run coordinator."""

from threading import Lock, Thread
from typing import Callable, Any


class RunCoordinator:
    """Runs one background thread per job."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._threads: dict[str, Thread] = {}

    def _cleanup_dead_locked(self) -> None:
        dead = [
            job_id for job_id, thread in self._threads.items() if not thread.is_alive()
        ]
        for job_id in dead:
            self._threads.pop(job_id, None)

    def is_running(self, job_id: str) -> bool:
        with self._lock:
            self._cleanup_dead_locked()
            thread = self._threads.get(job_id)
            return bool(thread and thread.is_alive())

    def start(self, job_id: str, target: Callable[[], Any]) -> bool:
        """Start background run if not already running."""
        with self._lock:
            self._cleanup_dead_locked()
            thread = self._threads.get(job_id)
            if thread and thread.is_alive():
                return False
            new_thread = Thread(target=target, daemon=True)
            self._threads[job_id] = new_thread
            new_thread.start()
            return True
