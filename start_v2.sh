#!/usr/bin/env bash
#
# Copyright 2026 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This file was created or modified with the assistance of an AI (Large Language Model).
# Review required for correctness, security, and licensing.

set -euo pipefail

REQUIRED_ENVS=(
  "NW_EDIT_V2_WORKER_MODE"
  "NW_EDIT_V2_VALIDATOR_MODE"
)

OPTIONAL_ENVS=(
  "NW_EDIT_V2_SIMULATED_DELAY_MS"
  "NW_EDIT_V2_PRESET_FILE"
  "NW_EDIT_V2_CORS_ORIGINS"
)

mask_value() {
  local name="$1"
  local value="$2"

  case "${name}" in
    *PASS*|*PASSWORD*|*SECRET*|*TOKEN*|*KEY*|*CREDENTIAL*|*AUTH*)
      echo "***MASKED***"
      ;;
    *)
      echo "${value}"
      ;;
  esac
}

print_env_value() {
  local name="$1"

  if [[ "${!name+x}" == "x" && -n "${!name}" ]]; then
    printf '  - %s=%s\n' "${name}" "$(mask_value "${name}" "${!name}")"
  else
    printf '  - %s=<unset>\n' "${name}"
  fi
}

validate_required_envs() {
  local missing=()
  local name

  for name in "${REQUIRED_ENVS[@]}"; do
    if [[ "${!name+x}" != "x" || -z "${!name}" ]]; then
      missing+=("${name}")
    fi
  done

  if ((${#missing[@]} > 0)); then
    echo "[v2] missing required environment variables:" >&2
    printf '  - %s\n' "${missing[@]}" >&2
    echo "[v2] export the required variables before running ./start_v2.sh" >&2
    exit 1
  fi
}

print_env_group() {
  local title="$1"
  shift
  local name

  echo "[v2] ${title}:"
  for name in "$@"; do
    print_env_value "${name}"
  done
}

validate_required_envs

MODE_WORKER="${NW_EDIT_V2_WORKER_MODE}"
MODE_VALIDATOR="${NW_EDIT_V2_VALIDATOR_MODE}"
MODE_SIM_DELAY_MS="${NW_EDIT_V2_SIMULATED_DELAY_MS:-0}"
FRONTEND_HOST="${NW_EDIT_V2_FRONTEND_HOST:-127.0.0.1}"
FRONTEND_PORT="${NW_EDIT_V2_FRONTEND_PORT:-3010}"

echo "[v2] worker mode: ${MODE_WORKER}"
echo "[v2] validator mode: ${MODE_VALIDATOR}"
echo "[v2] simulated delay ms: ${MODE_SIM_DELAY_MS}"
print_env_group "required envs" "${REQUIRED_ENVS[@]}"
print_env_group "optional envs" "${OPTIONAL_ENVS[@]}"
echo "[v2] backend: http://127.0.0.1:8010"
echo "[v2] frontend: http://${FRONTEND_HOST}:${FRONTEND_PORT}"

cleanup() {
  kill "${BACKEND_PID:-0}" "${FRONTEND_PID:-0}" 2>/dev/null || true
}
trap cleanup EXIT

NW_EDIT_V2_WORKER_MODE="${MODE_WORKER}" \
NW_EDIT_V2_VALIDATOR_MODE="${MODE_VALIDATOR}" \
NW_EDIT_V2_SIMULATED_DELAY_MS="${MODE_SIM_DELAY_MS}" \
uvicorn backend_v2.app.api.main:app --port 8010 --host 127.0.0.1 &
BACKEND_PID=$!

NW_EDIT_V2_FRONTEND_HOST="${FRONTEND_HOST}" \
NW_EDIT_V2_FRONTEND_PORT="${FRONTEND_PORT}" \
python3 -m backend_v2.app.frontend_server &
FRONTEND_PID=$!

wait
