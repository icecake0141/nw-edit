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
"""Netmiko executor utilities for v2 runtime."""

from __future__ import annotations

import difflib
import threading
import time
from typing import Any

from netmiko import ConnectHandler
from netmiko.exceptions import (
    NetmikoAuthenticationException,
    NetmikoTimeoutException,
)

ERROR_PATTERNS = [
    "% Invalid input",
    "Invalid input detected",
    "Error:",
    "Ambiguous command",
    "Incomplete command",
]

MAX_LOG_SIZE = 1024 * 1024
MAX_DIFF_SIZE = 256 * 1024
CONNECTION_TIMEOUT = 10
COMMAND_TIMEOUT = 20
DEVICE_TIMEOUT = 180


def validate_device_connection(
    device_params: dict[str, Any],
) -> tuple[bool, str | None]:
    """Validate device connection with a lightweight prompt check."""
    try:
        connection = ConnectHandler(
            device_type=device_params["device_type"],
            host=device_params["host"],
            port=device_params.get("port", 22),
            username=device_params["username"],
            password=device_params["password"],
            timeout=CONNECTION_TIMEOUT,
        )
        connection.find_prompt()
        connection.disconnect()
        return True, None
    except NetmikoAuthenticationException as exc:
        return False, f"Authentication failed: {str(exc)}"
    except NetmikoTimeoutException as exc:
        return False, f"Connection timeout: {str(exc)}"
    except Exception as exc:  # pragma: no cover - defensive fallback
        return False, f"Connection error: {str(exc)}"


def _check_for_errors(output: str) -> str | None:
    for pattern in ERROR_PATTERNS:
        if pattern in output:
            return f"Command error detected: {pattern}"
    return None


def _trim_log(log: str, max_size: int = MAX_LOG_SIZE) -> tuple[str, bool]:
    if len(log) <= max_size:
        return log, False
    return log[:max_size], True


def _trim_diff(diff: str, max_size: int = MAX_DIFF_SIZE) -> tuple[str, bool, int]:
    original_size = len(diff)
    if original_size <= max_size:
        return diff, False, original_size
    return diff[:max_size], True, original_size


def _create_unified_diff(
    pre: str,
    post: str,
    from_label: str = "pre",
    to_label: str = "post",
) -> str:
    pre_lines = pre.splitlines(keepends=True)
    post_lines = post.splitlines(keepends=True)
    diff = difflib.unified_diff(
        pre_lines,
        post_lines,
        fromfile=from_label,
        tofile=to_label,
        lineterm="\n",
    )
    return "".join(diff)


def execute_device_commands(
    device_params: dict[str, Any],
    commands: list[str],
    verify_cmds: list[str],
    is_canary: bool = False,
    retry_on_connection_error: bool = True,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Execute config commands with pre/post verification and normalized outputs."""
    result: dict[str, Any] = {
        "status": "success",
        "error": None,
        "error_code": None,
        "pre_output": None,
        "apply_output": None,
        "post_output": None,
        "diff": None,
        "diff_truncated": False,
        "diff_original_size": 0,
        "logs": [],
        "log_trimmed": False,
    }

    logs: list[str] = []
    start_time = time.monotonic()

    def add_log(message: str) -> None:
        logs.append(message)

    def should_cancel() -> bool:
        return cancel_event.is_set() if cancel_event else False

    def handle_cancel() -> dict[str, Any]:
        result["status"] = "cancelled"
        result["error"] = "Job was cancelled by user request"
        result["error_code"] = "cancelled"
        add_log("Execution cancelled by user request")
        all_logs = "\n".join(logs)
        trimmed_logs, was_trimmed = _trim_log(all_logs)
        result["logs"] = trimmed_logs.split("\n") if trimmed_logs else logs
        result["log_trimmed"] = was_trimmed
        return result

    def handle_failure(
        error_code: str, error_message: str, log_message: str
    ) -> dict[str, Any]:
        result["status"] = "failed"
        result["error_code"] = error_code
        result["error"] = error_message
        add_log(log_message)
        all_logs = "\n".join(logs)
        trimmed_logs, was_trimmed = _trim_log(all_logs)
        result["logs"] = trimmed_logs.split("\n") if trimmed_logs else logs
        result["log_trimmed"] = was_trimmed
        return result

    def has_timed_out(stage: str) -> bool:
        elapsed = time.monotonic() - start_time
        if elapsed <= DEVICE_TIMEOUT:
            return False
        timeout_message = (
            f"Device total timeout ({DEVICE_TIMEOUT}s) exceeded during {stage}"
        )
        handle_failure(
            error_code="device_timeout",
            error_message=timeout_message,
            log_message=f"ERROR: {timeout_message}",
        )
        return True

    if should_cancel():
        return handle_cancel()
    if has_timed_out(stage="pre-connect checks"):
        return result

    connection: Any | None = None
    retry_count = 0
    max_retries = 0 if is_canary else 1

    while retry_count <= max_retries:
        try:
            if has_timed_out(stage="connection"):
                return result
            add_log(
                f"Connecting to {device_params['host']}:{device_params.get('port', 22)}..."
            )
            if should_cancel():
                return handle_cancel()
            connection = ConnectHandler(
                device_type=device_params["device_type"],
                host=device_params["host"],
                port=device_params.get("port", 22),
                username=device_params["username"],
                password=device_params["password"],
                timeout=CONNECTION_TIMEOUT,
            )
            add_log("Connected successfully")
            break
        except NetmikoTimeoutException as exc:
            if retry_count < max_retries and retry_on_connection_error:
                add_log(f"Connection failed: {str(exc)}. Retrying in 5s...")
                time.sleep(5)
                retry_count += 1
            else:
                return handle_failure(
                    error_code="connection_timeout",
                    error_message=f"Connection failed: {str(exc)}",
                    log_message=f"Connection failed: {str(exc)}",
                )
        except NetmikoAuthenticationException as exc:
            return handle_failure(
                error_code="authentication_failed",
                error_message=f"Connection failed: {str(exc)}",
                log_message=f"Connection failed: {str(exc)}",
            )
        except Exception as exc:
            if retry_count < max_retries and retry_on_connection_error:
                add_log(f"Connection failed: {str(exc)}. Retrying in 5s...")
                time.sleep(5)
                retry_count += 1
            else:
                return handle_failure(
                    error_code="connection_error",
                    error_message=f"Connection failed: {str(exc)}",
                    log_message=f"Connection failed: {str(exc)}",
                )

    try:
        if connection is None:
            raise RuntimeError("Connection was not established")

        if verify_cmds:
            add_log("Running pre-verification commands...")
            pre_outputs: list[str] = []
            for cmd in verify_cmds:
                if should_cancel():
                    connection.disconnect()
                    return handle_cancel()
                if has_timed_out(stage="pre-verification"):
                    connection.disconnect()
                    return result
                add_log(f"  > {cmd}")
                pre_outputs.append(
                    connection.send_command(cmd, read_timeout=COMMAND_TIMEOUT)
                )
            result["pre_output"] = "\n".join(pre_outputs)
            add_log("Pre-verification complete")

        add_log("Applying configuration commands...")
        for cmd in commands:
            if should_cancel():
                connection.disconnect()
                return handle_cancel()
            if has_timed_out(stage="configuration apply"):
                connection.disconnect()
                return result
            add_log(f"  > {cmd}")

        if has_timed_out(stage="configuration apply"):
            connection.disconnect()
            return result
        apply_output = connection.send_config_set(
            commands, read_timeout=COMMAND_TIMEOUT
        )
        result["apply_output"] = apply_output
        add_log("Configuration applied")

        error_message = _check_for_errors(apply_output)
        if error_message:
            connection.disconnect()
            return handle_failure(
                error_code="command_error",
                error_message=error_message,
                log_message=f"ERROR: {error_message}",
            )

        if verify_cmds:
            add_log("Running post-verification commands...")
            post_outputs: list[str] = []
            for cmd in verify_cmds:
                if should_cancel():
                    connection.disconnect()
                    return handle_cancel()
                if has_timed_out(stage="post-verification"):
                    connection.disconnect()
                    return result
                add_log(f"  > {cmd}")
                post_outputs.append(
                    connection.send_command(cmd, read_timeout=COMMAND_TIMEOUT)
                )
            result["post_output"] = "\n".join(post_outputs)
            add_log("Post-verification complete")

            if isinstance(result["pre_output"], str) and isinstance(
                result["post_output"], str
            ):
                diff = _create_unified_diff(result["pre_output"], result["post_output"])
                trimmed_diff, was_trimmed, original_size = _trim_diff(diff)
                result["diff"] = trimmed_diff
                result["diff_truncated"] = was_trimmed
                result["diff_original_size"] = original_size
                add_log("Diff created")

        connection.disconnect()
        add_log("Disconnected")

    except NetmikoTimeoutException as exc:
        if connection:
            try:
                connection.disconnect()
            except Exception:
                pass
        return handle_failure(
            error_code="command_timeout",
            error_message=f"Execution timeout: {str(exc)}",
            log_message=f"ERROR: {str(exc)}",
        )
    except Exception as exc:
        if connection:
            try:
                connection.disconnect()
            except Exception:
                pass
        return handle_failure(
            error_code="execution_error",
            error_message=f"Execution error: {str(exc)}",
            log_message=f"ERROR: {str(exc)}",
        )

    all_logs = "\n".join(logs)
    trimmed_logs, was_trimmed = _trim_log(all_logs)
    result["logs"] = trimmed_logs.split("\n") if trimmed_logs else logs
    result["log_trimmed"] = was_trimmed
    return result
