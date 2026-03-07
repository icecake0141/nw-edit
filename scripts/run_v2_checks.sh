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

PYTHON_BIN="${PYTHON:-python3.12}"

compose_cmd=""
if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  compose_cmd="docker compose"
elif command -v docker-compose >/dev/null 2>&1; then
  compose_cmd="docker-compose"
fi

missing=()
for cmd in "${PYTHON_BIN}"; do
  if ! command -v "${cmd}" >/dev/null 2>&1; then
    missing+=("${cmd}")
  fi
done

if [[ ${#missing[@]} -gt 0 ]]; then
  echo "[v2-checks] missing required commands: ${missing[*]}"
  echo "[v2-checks] set PYTHON=python3.12 or install Python 3.12 and dev dependencies"
  echo "[v2-checks] example: ${PYTHON_BIN} -m pip install -r backend_v2/requirements-dev.txt"
  exit 2
fi

echo "[v2-checks] python: $(${PYTHON_BIN} --version)"

echo "[v2-checks] black"
"${PYTHON_BIN}" -m black --check backend_v2/app backend_v2/tests

echo "[v2-checks] flake8"
"${PYTHON_BIN}" -m flake8 backend_v2/app backend_v2/tests --max-line-length=120 --extend-ignore=E203,W503

echo "[v2-checks] mypy (backend_v2)"
"${PYTHON_BIN}" -m mypy --explicit-package-bases backend_v2/app

echo "[v2-checks] pre-commit"
PRE_COMMIT_HOME="${PRE_COMMIT_HOME:-.pre-commit-cache}" "${PYTHON_BIN}" -m pre_commit run --all-files

echo "[v2-checks] py_compile"
PYTHONPYCACHEPREFIX=.pycache "${PYTHON_BIN}" -m py_compile \
  backend_v2/app/api/main.py \
  backend_v2/app/application/execution_engine.py

echo "[v2-checks] pytest"
PYTHONPATH=. "${PYTHON_BIN}" -m pytest backend_v2/tests/unit -v --cov=backend_v2/app --cov-report=term

if [[ "${RUN_INTEGRATION:-0}" == "1" ]]; then
  if [[ "${AUTO_START_MOCK_SSH:-1}" == "1" ]]; then
    if [[ -n "${compose_cmd}" ]]; then
      echo "[v2-checks] starting mock SSH server"
      ${compose_cmd} --profile test up -d mock-ssh >/dev/null
      trap "${compose_cmd} --profile test down >/dev/null || true" EXIT
      echo "[v2-checks] waiting for mock SSH on localhost:2222"
      "${PYTHON_BIN}" - <<'PY'
import socket
import time

deadline = time.time() + 20
while time.time() < deadline:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(2.0)
    try:
        sock.connect(("127.0.0.1", 2222))
        banner = sock.recv(64)
        sock.close()
        if banner.startswith(b"SSH-"):
            print("[v2-checks] mock SSH banner is ready")
            break
    except OSError:
        sock.close()
        time.sleep(0.5)
else:
    print("[v2-checks] warning: mock SSH banner did not become ready within 20s")
PY
    else
      echo "[v2-checks] warning: docker compose not found; running integration tests without auto-start"
    fi
  fi

  echo "[v2-checks] integration"
  PYTHONPATH=. "${PYTHON_BIN}" -m pytest backend_v2/tests/integration -v -m integration
fi
