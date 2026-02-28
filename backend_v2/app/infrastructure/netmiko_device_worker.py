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
"""Netmiko-based device worker adapter for v2 execution engine."""

from __future__ import annotations

from typing import Callable

from backend_v2.app.application.execution_engine import DeviceWorker
from backend_v2.app.domain.models import (
    DeviceExecutionResult,
    DeviceProfile,
    DeviceTarget,
)


class NetmikoDeviceWorker(DeviceWorker):
    """Executes commands using the existing v1 ssh executor."""

    def __init__(self, profile_resolver: Callable[[str], DeviceProfile | None]):
        self.profile_resolver = profile_resolver

    def run(self, device: DeviceTarget, commands: list[str]) -> DeviceExecutionResult:
        profile = self.profile_resolver(device.key)
        if profile is None:
            return DeviceExecutionResult(
                status="failed",
                error=f"Device profile not found for {device.key}",
            )

        from backend.app.ssh_executor import execute_device_commands

        output = execute_device_commands(
            device_params={
                "host": profile.host,
                "port": profile.port,
                "device_type": profile.device_type,
                "username": profile.username,
                "password": profile.password,
                "verify_cmds": list(profile.verify_cmds),
            },
            commands=commands,
            verify_cmds=list(profile.verify_cmds),
            is_canary=True,
            retry_on_connection_error=False,
        )
        return DeviceExecutionResult(
            status=output.get("status", "failed"),
            logs=list(output.get("logs", [])),
            error=output.get("error"),
            pre_output=output.get("pre_output"),
            apply_output=output.get("apply_output"),
            post_output=output.get("post_output"),
            diff=output.get("diff"),
            log_trimmed=bool(output.get("log_trimmed", False)),
        )
