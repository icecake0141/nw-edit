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
"""Finite state machine for job lifecycle control."""

from .models import JobEvent, JobStatus, JobTransition


class JobStateMachine:
    """Validates and executes job status transitions."""

    _transitions = {
        (JobStatus.QUEUED, JobEvent.START): JobStatus.RUNNING,
        (JobStatus.QUEUED, JobEvent.CANCEL): JobStatus.CANCELLED,
        (JobStatus.RUNNING, JobEvent.PAUSE): JobStatus.PAUSED,
        (JobStatus.RUNNING, JobEvent.COMPLETE): JobStatus.COMPLETED,
        (JobStatus.RUNNING, JobEvent.FAIL): JobStatus.FAILED,
        (JobStatus.RUNNING, JobEvent.CANCEL): JobStatus.CANCELLED,
        (JobStatus.PAUSED, JobEvent.RESUME): JobStatus.RUNNING,
        (JobStatus.PAUSED, JobEvent.CANCEL): JobStatus.CANCELLED,
    }

    def can_transition(self, status: JobStatus, event: JobEvent) -> bool:
        """Return True if transition is valid for the current status."""
        return (status, event) in self._transitions

    def transition(self, status: JobStatus, event: JobEvent) -> JobTransition:
        """Apply a transition or raise ValueError for invalid transitions."""
        key = (status, event)
        if key not in self._transitions:
            raise ValueError(
                f"Invalid transition: status={status.value}, event={event.value}"
            )
        return JobTransition(
            current=status, event=event, next_status=self._transitions[key]
        )
