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
# Specification

Japanese version: [SPECIFICATION.ja.md](SPECIFICATION.ja.md)

## Scope

- Target: network device configuration updates via SSH.
- Architecture: single-process runtime, in-memory state.
- Deployment pattern: canary-first execution.

## Security model

- Device credentials are plaintext inputs (CSV/API) and held in memory only.
- No persistent database or secret vault integration in the current scope.
- Use only in trusted and isolated networks.

## Functional overview

- Device import and validation from CSV.
- Job creation and lifecycle (`queued/running/paused/completed/failed/cancelled`).
- Sync run (`/run`) and async run (`/run/async`).
- Async controls (`pause/resume/cancel/terminate`).
- WebSocket-based event stream for live status.
- Pre/apply/post outputs and diff per device.
- Execution preset save/reuse by OS model.

## CSV format

```csv
host,port,device_type,username,password,name,verify_cmds,host_vars,prod
192.168.1.1,22,cisco_ios,admin,password123,Router1,show running-config | section snmp,"{""hostname"":""router-1""}",true
```

### Columns

| Column | Required | Description | Default |
|--------|----------|-------------|---------|
| `host` | Yes | IP/FQDN | - |
| `port` | No | SSH port | `22` |
| `device_type` | Yes | Netmiko device type | - |
| `username` | Yes | SSH username | - |
| `password` | Yes | SSH password | - |
| `name` | No | Friendly name | - |
| `verify_cmds` | No | `;`-separated verification commands | - |
| `host_vars` | No | JSON object string for per-host template vars | - |
| `prod` | No | Production-host flag (`true` means production) | `false` |

## Command template variables

- Command placeholders use `{{var}}` syntax.
- Global variables are provided at job creation (`POST /api/v2/jobs` with `global_vars`).
- Host variables are provided per imported device via CSV `host_vars`.
- Merge precedence is `host_vars > global_vars`.
- If any placeholder is unresolved, run preflight fails with `HTTP 400` before device execution.

## v2 API surface (summary)

- Device import/list:
  - `POST /api/v2/devices/import`
  - `POST /api/v2/devices/import/progress` (NDJSON progress stream)
  - `GET /api/v2/devices`
- Job lifecycle/read:
  - `POST /api/v2/jobs`
  - `GET /api/v2/jobs`
  - `GET /api/v2/jobs/active`
  - `GET /api/v2/jobs/{job_id}`
  - `GET /api/v2/jobs/{job_id}/events`
  - `GET /api/v2/jobs/{job_id}/result`
- Execution:
  - `POST /api/v2/jobs/{job_id}/run`
  - `POST /api/v2/jobs/{job_id}/run/async`
  - `POST /api/v2/jobs/{job_id}/pause`
  - `POST /api/v2/jobs/{job_id}/resume`
  - `POST /api/v2/jobs/{job_id}/cancel`
  - `POST /api/v2/jobs/{job_id}/terminate` (alias of `cancel`)
  - `POST /api/v2/commands/exec` (read-only status command execution)
- Presets:
  - `GET /api/v2/presets`
  - `GET /api/v2/presets/os-models`
  - `POST /api/v2/presets`
  - `PUT /api/v2/presets/{preset_id}`
- WebSocket:
  - `/ws/v2/jobs/{job_id}`

## Run request extensions

- `verify_commands` (optional): if provided, used for all target devices.
- `canary` (required): explicit canary target (`host`, `port`).
- `imported_device_keys` (required): explicit imported-device targets (`host:port` list).
  - empty list is rejected with `HTTP 400`
  - unknown keys are rejected with `HTTP 400`
  - legacy ad-hoc `devices` is rejected with `HTTP 400`

## Runtime configuration

- `NW_EDIT_V2_WORKER_MODE=simulated|netmiko`
- `NW_EDIT_V2_VALIDATOR_MODE=simulated|netmiko`
- `NW_EDIT_V2_SIMULATED_DELAY_MS=<int>`

## Supported device types

The runtime uses Netmiko and supports common types such as:

- `cisco_ios`
- `cisco_xe`
- `cisco_nxos`
- `arista_eos`
- `juniper_junos`
- `linux` (Generic Linux)

For full coverage, see Netmiko documentation.

## Known limitations

- No persistence; restart clears in-memory state.
- No rollback implementation.
- Plaintext credential handling in process memory.
- Single-process scalability constraints.
- v1 runtime path is removed after hard cutover; only v2 startup/docs flow is supported.
