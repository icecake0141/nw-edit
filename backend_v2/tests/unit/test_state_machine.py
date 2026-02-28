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
"""Unit tests for job state transitions."""

import pytest

from backend_v2.app.domain.models import JobEvent, JobStatus
from backend_v2.app.domain.state_machine import JobStateMachine


def test_valid_transitions():
    sm = JobStateMachine()

    assert (
        sm.transition(JobStatus.QUEUED, JobEvent.START).next_status == JobStatus.RUNNING
    )
    assert (
        sm.transition(JobStatus.RUNNING, JobEvent.PAUSE).next_status == JobStatus.PAUSED
    )
    assert (
        sm.transition(JobStatus.PAUSED, JobEvent.RESUME).next_status
        == JobStatus.RUNNING
    )
    assert (
        sm.transition(JobStatus.RUNNING, JobEvent.COMPLETE).next_status
        == JobStatus.COMPLETED
    )


@pytest.mark.parametrize(
    ("status", "event"),
    [
        (JobStatus.COMPLETED, JobEvent.START),
        (JobStatus.FAILED, JobEvent.RESUME),
        (JobStatus.CANCELLED, JobEvent.COMPLETE),
        (JobStatus.QUEUED, JobEvent.RESUME),
    ],
)
def test_invalid_transitions_raise(status, event):
    sm = JobStateMachine()

    with pytest.raises(ValueError, match="Invalid transition"):
        sm.transition(status, event)
