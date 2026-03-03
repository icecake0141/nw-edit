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
"""Unit tests for command template rendering."""

from backend_v2.app.application.command_template import render_command, render_commands


def test_render_command_uses_global_var():
    rendered, missing = render_command(
        "snmp-server location {{timezone}}",
        {"timezone": "Asia/Tokyo"},
    )
    assert rendered == "snmp-server location Asia/Tokyo"
    assert missing == set()


def test_render_command_collects_missing_var():
    rendered, missing = render_command("hostname {{hostname}}", {})
    assert rendered == "hostname {{hostname}}"
    assert missing == {"hostname"}


def test_render_commands_handles_duplicates_and_multiple_tokens():
    rendered, missing = render_commands(
        [
            "banner {{site}} {{site}}",
            "clock timezone {{timezone}}",
        ],
        {"site": "tokyo"},
    )
    assert rendered == [
        "banner tokyo tokyo",
        "clock timezone {{timezone}}",
    ]
    assert missing == {"timezone"}
