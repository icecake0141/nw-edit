<!--
Copyright 2026 icecake0141
SPDX-License-Identifier: Apache-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Please review for correctness and security.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0
-->
# Reimplementation Plan (v2 Scaffold)

## Current Status

The `backend_v2` scaffold now includes:
- Domain state machine for job lifecycle
- Application service for create/transition use-cases
- Canary-first execution engine with retry/backoff and stop-on-error
- Pause/resume/cancel execution control for async runs
- In-memory repositories for jobs, devices, execution events, and run results
- FastAPI endpoints for create/list/get/event/run/run-async/control/result
- WebSocket endpoint for job event streaming
- Minimal `frontend_v2` runner with import/history/async control
- API-level tests for async pause/resume/cancel control flow

## Next Milestones

1. Real SSH worker
- Expand Netmiko-mode integration coverage with mock SSH.
- Add per-device total timeout and explicit timeout error categories.
- Normalize command/connection errors into structured status codes.

2. Device import + validation
- Add progress events for large CSV imports.
- Add optional partial-import mode (keep invalid rows for manual retry).
- Add mask/redaction policy for sensitive columns in responses.

3. Verification and diff
- Ensure Netmiko worker fills `pre_output/apply_output/post_output/diff` consistently.
- Add configurable diff size caps and truncation metadata.
- Add API option to skip diff generation for performance.

4. Frontend v2
- Replace plain JS fetch calls with generated typed API client.
- Split into explicit pages (Import, Job Create, Monitor, History, Detail).
- Render per-device diffs and control actions with stronger UX states.

5. Hardening and release gates
- Add mypy and pre-commit checks for `backend_v2`.
- Expand docker-backed integration coverage for async pause/resume/cancel flow.
- Finalize migration notes and release checklist for v2 adoption.
