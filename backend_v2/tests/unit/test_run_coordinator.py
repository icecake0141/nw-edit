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
"""Unit tests for background run coordinator."""

import time

from backend_v2.app.infrastructure.run_coordinator import RunCoordinator


def test_run_coordinator_rejects_duplicate_running_job():
    coordinator = RunCoordinator()

    def sleeper():
        time.sleep(0.2)

    first = coordinator.start("job-1", sleeper)
    second = coordinator.start("job-1", sleeper)

    assert first is True
    assert second is False
    assert coordinator.is_running("job-1") is True


def test_run_coordinator_allows_restart_after_thread_finishes():
    coordinator = RunCoordinator()

    def quick():
        time.sleep(0.05)

    assert coordinator.start("job-2", quick) is True
    time.sleep(0.1)
    assert coordinator.is_running("job-2") is False
    assert coordinator.start("job-2", quick) is True
