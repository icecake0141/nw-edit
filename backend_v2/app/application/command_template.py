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
"""Command templating helpers for run-time variable substitution."""

from __future__ import annotations

import re

_TOKEN_PATTERN = re.compile(r"{{\s*([A-Za-z_][A-Za-z0-9_]*)\s*}}")


def render_command(template: str, vars: dict[str, str]) -> tuple[str, set[str]]:
    """Render one command template and collect missing variable names."""
    missing: set[str] = set()

    def replacer(match: re.Match[str]) -> str:
        key = match.group(1)
        if key in vars:
            return vars[key]
        missing.add(key)
        return match.group(0)

    return _TOKEN_PATTERN.sub(replacer, template), missing


def render_commands(
    commands: list[str], vars: dict[str, str]
) -> tuple[list[str], set[str]]:
    """Render command templates and aggregate all missing variable names."""
    rendered: list[str] = []
    missing: set[str] = set()
    for command in commands:
        value, missing_vars = render_command(command, vars)
        rendered.append(value)
        missing.update(missing_vars)
    return rendered, missing
