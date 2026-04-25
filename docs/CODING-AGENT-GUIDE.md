<!--
Copyright 2026 icecake0141
SPDX-License-Identifier: Apache-2.0

This file was created or modified with the assistance of an AI (Large Language Model).
Please review for correctness and security.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
-->
# Coding Agent Guide

Use this guide as the first stop when changing nw-edit. It maps common change goals to the shortest useful path through the current v2 codebase.

## Current System

- The default runtime is v2: `backend_v2` plus `frontend_v2`.
- `backend_v2/app/api/main.py` wires the FastAPI app, CORS, in-memory stores, runtime worker/validator modes, routes, and background execution.
- `frontend_v2/public/index.html`, `frontend_v2/public/api-client.js`, and `frontend_v2/public/app.js` implement the browser UI without a frontend build step.
- Job, device, event, and run state are in memory. Execution presets are stored in a local JSON file through `FilePresetStore`.
- Device credentials from CSV are kept in memory and are not persisted by the backend device store.
- Older implementation-summary docs may mention removed v1 paths. Prefer `README.md`, `docs/INDEX.md`, this guide, and current v2 source files when orienting.

## Change Paths

### Device Import and Validation

Start with:

- `backend_v2/app/api/main.py`: `/api/v2/devices/import`, `/api/v2/devices/import/progress`, `/api/v2/devices`
- `backend_v2/app/application/device_import_service.py`: CSV parsing, header normalization, `host_vars`, `prod`, validation fan-out
- `backend_v2/app/infrastructure/device_connection_validators.py`: simulated and Netmiko validation behavior
- `backend_v2/app/infrastructure/in_memory_device_store.py`: accepted-device storage

Update tests in:

- `backend_v2/tests/unit/test_device_import_service.py`
- `backend_v2/tests/unit/test_api_main.py`
- `backend_v2/tests/unit/test_netmiko_adapters.py` when validator behavior changes
- `backend_v2/tests/integration/test_v2_netmiko_integration.py` for real SSH-facing behavior

### Job Creation and Lifecycle

Start with:

- `backend_v2/app/api/main.py`: `/api/v2/jobs`, active-job checks, pause/resume/cancel routes
- `backend_v2/app/api/schemas.py`: request and response contracts
- `backend_v2/app/application/job_service.py`: job creation and lifecycle events
- `backend_v2/app/domain/models.py`: `JobRecord`, `JobStatus`, run summary models
- `backend_v2/app/domain/state_machine.py`: allowed status transitions
- `backend_v2/app/infrastructure/in_memory_job_store.py`, `in_memory_control_store.py`, `in_memory_run_store.py`

Update tests in:

- `backend_v2/tests/unit/test_job_service.py`
- `backend_v2/tests/unit/test_state_machine.py`
- `backend_v2/tests/unit/test_control_store.py`
- `backend_v2/tests/unit/test_api_main.py`

### Command Variables and Preflight

Start with:

- `backend_v2/app/application/command_template.py`: `{{var}}` parsing and rendering
- `backend_v2/app/api/main.py`: `_prepare_run`, merge order for `global_vars` and per-device `host_vars`
- `backend_v2/app/api/schemas.py`: `CreateJobRequest`, `RunJobRequest`
- `frontend_v2/public/app.js`: global variable collection, review panel, run payload assembly

Update tests in:

- `backend_v2/tests/unit/test_command_template.py`
- `backend_v2/tests/unit/test_api_main.py`
- Frontend behavior should be manually checked in the browser for payload or review-flow changes.

### Execution Orchestration

Start with:

- `backend_v2/app/api/main.py`: `_prepare_run`, `_execute_run_prepared`, sync and async run routes
- `backend_v2/app/application/execution_engine.py`: canary-first execution, concurrency, retry, pause, cancel, stop-on-error
- `backend_v2/app/application/execution_control.py`: pause and cancel primitives
- `backend_v2/app/application/events.py`: execution event shape and timestamping
- `backend_v2/app/infrastructure/run_coordinator.py`: one active run per job
- `backend_v2/app/infrastructure/netmiko_device_worker.py` and `simulated_device_worker.py`: per-device execution adapters

Update tests in:

- `backend_v2/tests/unit/test_execution_engine.py`
- `backend_v2/tests/unit/test_run_coordinator.py`
- `backend_v2/tests/unit/test_simulated_device_worker.py`
- `backend_v2/tests/unit/test_netmiko_executor.py`
- `backend_v2/tests/unit/test_api_main.py`
- `backend_v2/tests/integration/test_v2_netmiko_integration.py` when Netmiko behavior changes

### Presets

Start with:

- `backend_v2/app/api/main.py`: `/api/v2/presets` routes
- `backend_v2/app/api/schemas.py`: preset request and response models
- `backend_v2/app/domain/models.py`: `ExecutionPreset`
- `backend_v2/app/infrastructure/file_preset_store.py`: JSON persistence, conflict handling, OS-model filtering
- `frontend_v2/public/app.js`: preset mode, selection, save, update, and run-form integration

Update tests in:

- `backend_v2/tests/unit/test_file_preset_store.py`
- `backend_v2/tests/unit/test_api_main.py`

### Status Commands

Start with:

- `backend_v2/app/api/main.py`: `/api/v2/commands/exec`
- `backend_v2/app/api/schemas.py`: `StatusCommandRequest`, `StatusCommandResponse`
- `backend_v2/app/infrastructure/netmiko_executor.py`: status command parsing and Netmiko execution
- `frontend_v2/public/api-client.js` and `frontend_v2/public/app.js`: client call and UI output

Update tests in:

- `backend_v2/tests/unit/test_netmiko_executor.py`
- `backend_v2/tests/unit/test_api_main.py`

### WebSocket, Events, and Monitoring UI

Start with:

- `backend_v2/app/api/main.py`: `/ws/jobs/{job_id}`, `/api/v2/jobs/{job_id}/events`, `/api/v2/jobs/{job_id}/result`
- `backend_v2/app/application/events.py`: event model and publisher contract
- `backend_v2/app/infrastructure/in_memory_event_store.py`: event storage
- `frontend_v2/public/app.js`: monitor state, socket handling, device cards, logs, result refresh

Update tests in:

- `backend_v2/tests/unit/test_event_store.py`
- `backend_v2/tests/unit/test_api_main.py`
- Manual browser checks for UI rendering and WebSocket behavior

### Frontend Workflows

Start with:

- `frontend_v2/public/index.html`: DOM structure, tabs, forms, controls
- `frontend_v2/public/app.js`: UI state, event handlers, rendering, run review, warnings
- `frontend_v2/public/api-client.js`: API contracts consumed by the UI
- `backend_v2/app/frontend_server.py`: hardened static serving behavior

Update tests in:

- `backend_v2/tests/unit/test_frontend_server.py` for static server changes
- Backend API tests if frontend changes require API contract changes
- Manual browser checks for layout, text fit, and main workflows

## API and Data Contract Rules

- Change `backend_v2/app/api/schemas.py` before changing route behavior that affects request or response JSON.
- Keep frontend JSDoc typedefs in `frontend_v2/public/api-client.js` aligned with backend schemas.
- Keep `DeviceTarget.key` format as `host:port` unless every caller and stored map is migrated.
- Preserve the command variable precedence `host_vars > global_vars`.
- Preserve imported-device execution through `imported_device_keys`; the old inline `devices` run payload is rejected.

## Validation Commands

- `make check`: default local validation for backend unit tests and configured checks.
- `make check-integration`: run when SSH/Netmiko, device validation, command execution, or Docker integration behavior changes.
- `make typecheck`: run when changing Python application code or public Python contracts.
- `make precommit`: run before PRs or when touching formatting-sensitive files.

For docs-only changes, inspect the changed Markdown and links. Runtime validation is not required unless executable code or documented commands changed.

## Documentation and Policy Checklist

- New and modified source files must keep the Apache-2.0 license header and LLM attribution required by `docs/LLM-GENERATED-CODE.en.md`.
- Confirm the repository root `LICENSE` file remains present.
- Update `README.md` for user-facing setup or behavior changes.
- Update `docs/SPECIFICATION.md` for contract, workflow, or behavior changes.
- Update `docs/TESTING.md` when validation commands or test expectations change.
- Update `docs/QUICKSTART-v2.md` when startup, environment variables, or the primary user flow changes.
- Add changelog or migration notes only when the project release process requires them for the change.
