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

MODE_WORKER="${NW_EDIT_V2_WORKER_MODE:-simulated}"
MODE_VALIDATOR="${NW_EDIT_V2_VALIDATOR_MODE:-simulated}"
MODE_SIM_DELAY_MS="${NW_EDIT_V2_SIMULATED_DELAY_MS:-0}"

echo "[v2] worker mode: ${MODE_WORKER}"
echo "[v2] validator mode: ${MODE_VALIDATOR}"
echo "[v2] simulated delay ms: ${MODE_SIM_DELAY_MS}"
echo "[v2] backend: http://127.0.0.1:8010"
echo "[v2] frontend: http://127.0.0.1:3010"

cleanup() {
  kill "${BACKEND_PID:-0}" "${FRONTEND_PID:-0}" 2>/dev/null || true
}
trap cleanup EXIT

NW_EDIT_V2_WORKER_MODE="${MODE_WORKER}" \
NW_EDIT_V2_VALIDATOR_MODE="${MODE_VALIDATOR}" \
NW_EDIT_V2_SIMULATED_DELAY_MS="${MODE_SIM_DELAY_MS}" \
uvicorn backend_v2.app.api.main:app --port 8010 --host 127.0.0.1 &
BACKEND_PID=$!

(cd frontend_v2/public && python3 -m http.server 3010 --bind 127.0.0.1) &
FRONTEND_PID=$!

wait
