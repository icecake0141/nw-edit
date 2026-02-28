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
# backend_v2 (Reimplementation Scaffold)

This folder is the starting point for a clean-room reimplementation.

See also:
- [v2 quickstart](/Users/daisukek/Codex/nw-edit/docs/QUICKSTART-v2.md)

Current scope:
- Domain model for job lifecycle
- Explicit finite state machine for job status transitions
- Application use-cases for create/start/pause/resume/complete/fail/cancel
- Thread-safe in-memory repository
- Minimal FastAPI API (`/health`, `/api/v2/jobs`, event transitions)
- Simulated run endpoint (`POST /api/v2/jobs/{job_id}/run`)
- WebSocket event stream (`/ws/v2/jobs/{job_id}`)
- CSV device import (`POST /api/v2/devices/import`)
- In-memory device list (`GET /api/v2/devices`)
- Job list endpoint (`GET /api/v2/jobs`)
- Job event history (`GET /api/v2/jobs/{job_id}/events`)
- Latest run result (`GET /api/v2/jobs/{job_id}/result`)
- Background run start (`POST /api/v2/jobs/{job_id}/run/async`)
- Active job snapshot (`GET /api/v2/jobs/active`)
- Pause active run (`POST /api/v2/jobs/{job_id}/pause`)
- Resume paused run (`POST /api/v2/jobs/{job_id}/resume`)
- Cancel active run (`POST /api/v2/jobs/{job_id}/cancel`)
- Unit tests for state transitions and service behavior

Run tests:

```bash
python3 -m pytest backend_v2/tests/unit -v
```

Run integration tests (with mock SSH):

```bash
docker-compose --profile test up -d mock-ssh
python3 -m pytest backend_v2/tests/integration -v -m integration
docker-compose --profile test down
```

Run full local checks (v1 + v2):

```bash
./scripts/run_v2_checks.sh
```

Shortcuts:

```bash
make check
make check-integration
make typecheck
make precommit
```

Run API locally:

```bash
uvicorn backend_v2.app.api.main:app --reload --port 8010
```

Or run both backend/frontend:

```bash
./start_v2.sh
```

Modes:
- `NW_EDIT_V2_WORKER_MODE=simulated|netmiko` (default: `simulated`)
- `NW_EDIT_V2_VALIDATOR_MODE=simulated|netmiko` (default: `simulated`)
- `NW_EDIT_V2_SIMULATED_DELAY_MS=<int>` (optional, for async-control testing)

Run minimal frontend locally:

```bash
cd frontend_v2/public
python3 -m http.server 3010
```

Sample flow:

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_name":"demo","creator":"local"}'

curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/run \
  -H "Content-Type: application/json" \
  -d '{
    "devices":[{"host":"10.0.0.1","port":22},{"host":"10.0.0.2","port":22}],
    "canary":{"host":"10.0.0.1","port":22},
    "commands":["show version"]
  }'

curl -s http://127.0.0.1:8010/api/v2/jobs
```

Next steps:
1. Replace simulated worker with Netmiko worker in integration tests.
2. Add pre/post verify diff fields to API responses for UI rendering.
3. Add frontend v2 pages beyond the current scaffold runner.
