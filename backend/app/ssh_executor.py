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
"""SSH executor using Netmiko for network device operations."""

import time
import difflib
from typing import List, Tuple, Optional, Any, Dict
import threading
from netmiko import ConnectHandler  # type: ignore[import-untyped]
from netmiko.exceptions import (  # type: ignore[import-untyped]
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

# Error patterns to detect command failures
ERROR_PATTERNS = [
    "% Invalid input",
    "Invalid input detected",
    "Error:",
    "Ambiguous command",
    "Incomplete command",
]

# Limits
MAX_LOG_SIZE = 1024 * 1024  # 1 MiB
CONNECTION_TIMEOUT = 10
COMMAND_TIMEOUT = 20
DEVICE_TIMEOUT = 180


def validate_device_connection(device_params: dict) -> Tuple[bool, Optional[str]]:
    """
    Validate device connection with lightweight test.

    Args:
        device_params: Dictionary with host, port, device_type, username, password

    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        connection = ConnectHandler(
            device_type=device_params["device_type"],
            host=device_params["host"],
            port=device_params.get("port", 22),
            username=device_params["username"],
            password=device_params["password"],
            timeout=CONNECTION_TIMEOUT,
        )
        # Get prompt to verify connection works
        connection.find_prompt()
        connection.disconnect()
        return True, None
    except NetmikoAuthenticationException as e:
        return False, f"Authentication failed: {str(e)}"
    except NetmikoTimeoutException as e:
        return False, f"Connection timeout: {str(e)}"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def check_for_errors(output: str) -> Optional[str]:
    """
    Check if output contains error patterns.

    Args:
        output: Command output to check

    Returns:
        Error message if found, None otherwise
    """
    for pattern in ERROR_PATTERNS:
        if pattern in output:
            return f"Command error detected: {pattern}"
    return None


def trim_log(log: str, max_size: int = MAX_LOG_SIZE) -> Tuple[str, bool]:
    """
    Trim log to max size, keeping the head (earliest content).

    Args:
        log: Log string to trim
        max_size: Maximum size in bytes

    Returns:
        Tuple of (trimmed_log, was_trimmed)
    """
    if len(log) <= max_size:
        return log, False

    # Keep the head
    trimmed = log[:max_size]
    return trimmed, True


def create_unified_diff(
    pre: str, post: str, from_label: str = "pre", to_label: str = "post"
) -> str:
    """
    Create unified diff between pre and post outputs.

    Args:
        pre: Pre-change output
        post: Post-change output
        from_label: Label for pre version
        to_label: Label for post version

    Returns:
        Unified diff string
    """
    pre_lines = pre.splitlines(keepends=True)
    post_lines = post.splitlines(keepends=True)

    diff = difflib.unified_diff(
        pre_lines, post_lines, fromfile=from_label, tofile=to_label, lineterm="\n"
    )

    return "".join(diff)


def execute_device_commands(
    device_params: dict,
    commands: List[str],
    verify_cmds: List[str],
    is_canary: bool = False,
    retry_on_connection_error: bool = True,
    cancel_event: Optional[threading.Event] = None,
) -> dict:
    """
    Execute commands on a device with pre/post verification.

    Args:
        device_params: Device connection parameters
        commands: Commands to apply (config mode)
        verify_cmds: Verification commands (exec mode)
        is_canary: Whether this is the canary device (no retries)
        retry_on_connection_error: Whether to retry on connection errors

    Returns:
        Dictionary with status, outputs, diff, logs, and error info
    """
    result: Dict[str, Any] = {
        "status": "success",
        "error": None,
        "pre_output": None,
        "apply_output": None,
        "post_output": None,
        "diff": None,
        "logs": [],
        "log_trimmed": False,
    }

    logs = []

    def add_log(msg: str):
        logs.append(msg)

    def should_cancel() -> bool:
        return cancel_event.is_set() if cancel_event else False

    def handle_cancel() -> dict:
        result["status"] = "cancelled"
        result["error"] = "Job was cancelled by user request"
        add_log("Execution cancelled by user request")
        all_logs = "\n".join(logs)
        trimmed_logs, was_trimmed = trim_log(all_logs)
        result["logs"] = trimmed_logs.split("\n") if trimmed_logs else logs
        result["log_trimmed"] = was_trimmed
        return result

    if should_cancel():
        return handle_cancel()

    # Attempt connection with retry logic
    connection: Optional[Any] = None
    retry_count = 0
    max_retries = 0 if is_canary else 1

    while retry_count <= max_retries:
        try:
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
        except (
            NetmikoTimeoutException,
            NetmikoAuthenticationException,
            Exception,
        ) as e:
            if retry_count < max_retries and retry_on_connection_error:
                add_log(f"Connection failed: {str(e)}. Retrying in 5s...")
                time.sleep(5)
                retry_count += 1
            else:
                result["status"] = "failed"
                result["error"] = f"Connection failed: {str(e)}"
                add_log(f"Connection failed: {str(e)}")
                result["logs"] = logs
                return result

    try:
        # Pre-verification
        if connection is None:
            raise RuntimeError("Connection was not established")

        if verify_cmds:
            add_log("Running pre-verification commands...")
            pre_outputs = []
            for cmd in verify_cmds:
                if should_cancel():
                    if connection:
                        connection.disconnect()
                    return handle_cancel()
                add_log(f"  > {cmd}")
                output = connection.send_command(cmd, read_timeout=COMMAND_TIMEOUT)
                pre_outputs.append(output)
            result["pre_output"] = "\n".join(pre_outputs)
            add_log("Pre-verification complete")

        # Apply configuration commands
        add_log("Applying configuration commands...")
        for cmd in commands:
            if should_cancel():
                if connection:
                    connection.disconnect()
                return handle_cancel()
            add_log(f"  > {cmd}")

        apply_output = connection.send_config_set(
            commands, read_timeout=COMMAND_TIMEOUT
        )
        result["apply_output"] = apply_output
        add_log("Configuration applied")

        # Check for command errors
        error_msg = check_for_errors(apply_output)
        if error_msg:
            result["status"] = "failed"
            result["error"] = error_msg
            add_log(f"ERROR: {error_msg}")
            result["logs"] = logs
            connection.disconnect()
            return result

        # Post-verification
        if verify_cmds:
            add_log("Running post-verification commands...")
            post_outputs = []
            for cmd in verify_cmds:
                if should_cancel():
                    if connection:
                        connection.disconnect()
                    return handle_cancel()
                add_log(f"  > {cmd}")
                output = connection.send_command(cmd, read_timeout=COMMAND_TIMEOUT)
                post_outputs.append(output)
            result["post_output"] = "\n".join(post_outputs)
            add_log("Post-verification complete")

            # Create diff
            if isinstance(result["pre_output"], str) and isinstance(
                result["post_output"], str
            ):
                diff = create_unified_diff(result["pre_output"], result["post_output"])
                result["diff"] = diff
                add_log("Diff created")

        connection.disconnect()
        add_log("Disconnected")

    except Exception as e:
        result["status"] = "failed"
        result["error"] = f"Execution error: {str(e)}"
        add_log(f"ERROR: {str(e)}")
        if connection:
            try:
                connection.disconnect()
            except Exception:
                pass

    # Trim logs if needed
    all_logs = "\n".join(logs)
    trimmed_logs, was_trimmed = trim_log(all_logs)
    result["logs"] = trimmed_logs.split("\n") if trimmed_logs else logs
    result["log_trimmed"] = was_trimmed

    return result
