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
"""In-memory run summary store."""

from __future__ import annotations

from threading import Lock

from backend_v2.app.domain.models import JobRunSummary


class InMemoryRunStore:
    """Stores latest run summary by job_id."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._latest_by_job: dict[str, JobRunSummary] = {}

    def save(self, summary: JobRunSummary) -> None:
        with self._lock:
            self._latest_by_job[summary.job_id] = summary

    def get(self, job_id: str) -> JobRunSummary | None:
        with self._lock:
            return self._latest_by_job.get(job_id)
