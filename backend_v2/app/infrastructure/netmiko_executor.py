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
import re
import threading
import time
from collections.abc import Callable
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
    "Unknown action",
]

MAX_LOG_SIZE = 1024 * 1024
MAX_DIFF_SIZE = 256 * 1024
CONNECTION_TIMEOUT = 10
COMMAND_TIMEOUT = 20
DEVICE_TIMEOUT = 180
DANGEROUS_STATUS_COMMAND_PATTERNS = [
    r"^\s*conf(?:ig(?:ure)?)?(?:\s+(?:t|term(?:inal)?|replace))?\b",
    r"^\s*reload\b",
    r"^\s*write\b",
    r"^\s*copy\s+running-config\s+startup-config\b",
    r"^\s*erase\b",
    r"^\s*delete\b",
    r"^\s*format\b",
    r"^\s*shutdown\b",
]


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


def _initial_execution_result() -> dict[str, Any]:
    return {
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


def _finalize_logs(result: dict[str, Any], logs: list[str]) -> None:
    all_logs = "\n".join(logs)
    trimmed_logs, was_trimmed = _trim_log(all_logs)
    result["logs"] = trimmed_logs.split("\n") if trimmed_logs else logs
    result["log_trimmed"] = was_trimmed


def _mark_cancelled(result: dict[str, Any], logs: list[str]) -> dict[str, Any]:
    result["status"] = "cancelled"
    result["error"] = "Job was cancelled by user request"
    result["error_code"] = "cancelled"
    logs.append("Execution cancelled by user request")
    _finalize_logs(result, logs)
    return result


def _mark_failed(
    result: dict[str, Any],
    logs: list[str],
    error_code: str,
    error_message: str,
    log_message: str,
) -> dict[str, Any]:
    result["status"] = "failed"
    result["error_code"] = error_code
    result["error"] = error_message
    logs.append(log_message)
    _finalize_logs(result, logs)
    return result


def _disconnect(connection: Any | None) -> None:
    if connection:
        try:
            connection.disconnect()
        except Exception:
            pass


def _run_verification_commands(
    connection: Any,
    verify_cmds: list[str],
    logs: list[str],
    should_cancel: Callable[[], bool],
    has_timed_out: Callable[[str], bool],
    stage: str,
    result: dict[str, Any],
) -> tuple[str, str | None]:
    outputs: list[str] = []
    for cmd in verify_cmds:
        if should_cancel():
            connection.disconnect()
            return "\n".join(outputs), "cancelled"
        if has_timed_out(stage):
            connection.disconnect()
            return "\n".join(outputs), "timed_out"
        logs.append(f"  > {cmd}")
        output = str(connection.send_command(cmd, read_timeout=COMMAND_TIMEOUT))
        outputs.append(output)
        error_message = _check_for_errors(output)
        if error_message:
            connection.disconnect()
            _mark_failed(
                result=result,
                logs=logs,
                error_code="command_error",
                error_message=error_message,
                log_message=f"ERROR: {error_message}",
            )
            return "\n".join(outputs), "failed"
    return "\n".join(outputs), None


def _connect_with_retry(
    device_params: dict[str, Any],
    max_retries: int,
    retry_on_connection_error: bool,
    logs: list[str],
    should_cancel: Callable[[], bool],
    has_timed_out: Callable[[str], bool],
    result: dict[str, Any],
) -> tuple[Any | None, str | None]:
    retry_count = 0
    while retry_count <= max_retries:
        try:
            if has_timed_out("connection"):
                return None, "timed_out"
            logs.append(
                f"Connecting to {device_params['host']}:{device_params.get('port', 22)}..."
            )
            if should_cancel():
                return None, "cancelled"
            connection = ConnectHandler(
                device_type=device_params["device_type"],
                host=device_params["host"],
                port=device_params.get("port", 22),
                username=device_params["username"],
                password=device_params["password"],
                timeout=CONNECTION_TIMEOUT,
            )
            logs.append("Connected successfully")
            return connection, None
        except NetmikoTimeoutException as exc:
            if retry_count < max_retries and retry_on_connection_error:
                logs.append(f"Connection failed: {str(exc)}. Retrying in 5s...")
                time.sleep(5)
                retry_count += 1
            else:
                _mark_failed(
                    result=result,
                    logs=logs,
                    error_code="connection_timeout",
                    error_message=f"Connection failed: {str(exc)}",
                    log_message=f"Connection failed: {str(exc)}",
                )
                return None, "failed"
        except NetmikoAuthenticationException as exc:
            _mark_failed(
                result=result,
                logs=logs,
                error_code="authentication_failed",
                error_message=f"Connection failed: {str(exc)}",
                log_message=f"Connection failed: {str(exc)}",
            )
            return None, "failed"
        except Exception as exc:
            if retry_count < max_retries and retry_on_connection_error:
                logs.append(f"Connection failed: {str(exc)}. Retrying in 5s...")
                time.sleep(5)
                retry_count += 1
            else:
                _mark_failed(
                    result=result,
                    logs=logs,
                    error_code="connection_error",
                    error_message=f"Connection failed: {str(exc)}",
                    log_message=f"Connection failed: {str(exc)}",
                )
                return None, "failed"
    return None, "failed"


def _apply_configuration_commands(
    connection: Any,
    commands: list[str],
    logs: list[str],
    should_cancel: Callable[[], bool],
    has_timed_out: Callable[[str], bool],
    result: dict[str, Any],
) -> str | None:
    logs.append("Applying configuration commands...")
    for cmd in commands:
        if should_cancel():
            connection.disconnect()
            return "cancelled"
        if has_timed_out("configuration apply"):
            connection.disconnect()
            return "timed_out"
        logs.append(f"  > {cmd}")

    if has_timed_out("configuration apply"):
        connection.disconnect()
        return "timed_out"
    apply_output = str(
        connection.send_config_set(commands, read_timeout=COMMAND_TIMEOUT)
    )
    result["apply_output"] = apply_output
    logs.append("Configuration applied")

    error_message = _check_for_errors(apply_output)
    if error_message:
        connection.disconnect()
        _mark_failed(
            result=result,
            logs=logs,
            error_code="command_error",
            error_message=error_message,
            log_message=f"ERROR: {error_message}",
        )
        return "failed"
    return None


def _store_verification_diff(result: dict[str, Any], logs: list[str]) -> None:
    if isinstance(result["pre_output"], str) and isinstance(result["post_output"], str):
        diff = _create_unified_diff(result["pre_output"], result["post_output"])
        trimmed_diff, was_trimmed, original_size = _trim_diff(diff)
        result["diff"] = trimmed_diff
        result["diff_truncated"] = was_trimmed
        result["diff_original_size"] = original_size
        logs.append("Diff created")


def parse_status_commands(commands: str) -> list[str]:
    """Parse newline-separated status commands and block disruptive ones."""
    command_list = [cmd.strip() for cmd in commands.splitlines() if cmd.strip()]
    if not command_list:
        raise ValueError("Commands cannot be empty")

    blocked = [
        cmd
        for cmd in command_list
        if any(
            re.search(pattern, cmd, re.IGNORECASE)
            for pattern in DANGEROUS_STATUS_COMMAND_PATTERNS
        )
    ]
    if blocked:
        raise ValueError(
            f"Potentially disruptive commands are not allowed: {', '.join(blocked)}"
        )
    return command_list


def run_status_commands(device_params: dict[str, Any], commands: str) -> str:
    """Execute read-only status commands in exec mode."""
    command_list = parse_status_commands(commands)
    connection: Any | None = None
    try:
        connection = ConnectHandler(
            device_type=device_params["device_type"],
            host=device_params["host"],
            port=device_params.get("port", 22),
            username=device_params["username"],
            password=device_params["password"],
            timeout=CONNECTION_TIMEOUT,
        )
        outputs = []
        for cmd in command_list:
            output = str(connection.send_command(cmd, read_timeout=COMMAND_TIMEOUT))
            error_message = _check_for_errors(output)
            if error_message:
                raise RuntimeError(error_message)
            outputs.append(f"$ {cmd}\n{output}")
        return "\n\n".join(outputs)
    except NetmikoAuthenticationException as exc:
        raise RuntimeError(f"Authentication failed: {str(exc)}") from exc
    except NetmikoTimeoutException as exc:
        raise RuntimeError(f"Command execution timeout: {str(exc)}") from exc
    except RuntimeError:
        raise
    except Exception as exc:
        raise RuntimeError(f"SSH execution error: {str(exc)}") from exc
    finally:
        if connection:
            try:
                connection.disconnect()
            except Exception:
                pass


def execute_device_commands(
    device_params: dict[str, Any],
    commands: list[str],
    verify_cmds: list[str],
    is_canary: bool = False,
    retry_on_connection_error: bool = True,
    cancel_event: threading.Event | None = None,
) -> dict[str, Any]:
    """Execute config commands with pre/post verification and normalized outputs."""
    result = _initial_execution_result()
    logs: list[str] = []
    start_time = time.monotonic()

    def add_log(message: str) -> None:
        logs.append(message)

    def should_cancel() -> bool:
        return cancel_event.is_set() if cancel_event else False

    def handle_cancel() -> dict[str, Any]:
        return _mark_cancelled(result, logs)

    def handle_failure(
        error_code: str, error_message: str, log_message: str
    ) -> dict[str, Any]:
        return _mark_failed(
            result=result,
            logs=logs,
            error_code=error_code,
            error_message=error_message,
            log_message=log_message,
        )

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

    max_retries = 0 if is_canary else 1
    connection, connection_status = _connect_with_retry(
        device_params=device_params,
        max_retries=max_retries,
        retry_on_connection_error=retry_on_connection_error,
        logs=logs,
        should_cancel=should_cancel,
        has_timed_out=has_timed_out,
        result=result,
    )
    if connection_status == "cancelled":
        return handle_cancel()
    if connection_status in {"timed_out", "failed"}:
        return result

    try:
        if connection is None:
            raise RuntimeError("Connection was not established")

        if verify_cmds:
            add_log("Running pre-verification commands...")
            pre_output, pre_status = _run_verification_commands(
                connection=connection,
                verify_cmds=verify_cmds,
                logs=logs,
                should_cancel=should_cancel,
                has_timed_out=has_timed_out,
                stage="pre-verification",
                result=result,
            )
            if pre_status == "cancelled":
                return handle_cancel()
            if pre_status in {"timed_out", "failed"}:
                return result
            result["pre_output"] = pre_output
            add_log("Pre-verification complete")

        apply_status = _apply_configuration_commands(
            connection=connection,
            commands=commands,
            logs=logs,
            should_cancel=should_cancel,
            has_timed_out=has_timed_out,
            result=result,
        )
        if apply_status == "cancelled":
            return handle_cancel()
        if apply_status in {"timed_out", "failed"}:
            return result

        if verify_cmds:
            add_log("Running post-verification commands...")
            post_output, post_status = _run_verification_commands(
                connection=connection,
                verify_cmds=verify_cmds,
                logs=logs,
                should_cancel=should_cancel,
                has_timed_out=has_timed_out,
                stage="post-verification",
                result=result,
            )
            if post_status == "cancelled":
                return handle_cancel()
            if post_status in {"timed_out", "failed"}:
                return result
            result["post_output"] = post_output
            add_log("Post-verification complete")

            _store_verification_diff(result, logs)

        connection.disconnect()
        add_log("Disconnected")

    except NetmikoTimeoutException as exc:
        _disconnect(connection)
        return handle_failure(
            error_code="command_timeout",
            error_message=f"Execution timeout: {str(exc)}",
            log_message=f"ERROR: {str(exc)}",
        )
    except Exception as exc:
        _disconnect(connection)
        return handle_failure(
            error_code="execution_error",
            error_message=f"Execution error: {str(exc)}",
            log_message=f"ERROR: {str(exc)}",
        )

    _finalize_logs(result, logs)
    return result
