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
# QUICKSTART v2

## 0. Install dependencies

`backend_v2` uses the shared backend dependency set.

```bash
python3 -m pip install -r backend/requirements-dev.txt
```

## 1. Start backend v2

```bash
uvicorn backend_v2.app.api.main:app --reload --port 8010
```

Modes:

```bash
export NW_EDIT_V2_WORKER_MODE=simulated   # or netmiko
export NW_EDIT_V2_VALIDATOR_MODE=simulated # or netmiko
export NW_EDIT_V2_SIMULATED_DELAY_MS=200   # optional (slow down simulated worker)
```

## 2. Start frontend v2

```bash
cd frontend_v2/public
python3 -m http.server 3010
```

Open `http://127.0.0.1:3010`.

## 3. Basic API flow

1. Import devices

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/devices/import \
  -H "Content-Type: text/plain" \
  --data-binary $'host,port,device_type,username,password,name,verify_cmds\n10.0.0.1,22,cisco_ios,admin,pass,edge-1,show run'
```

2. Create job

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_name":"demo","creator":"local"}'
```

3. Run async

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/run/async \
  -H "Content-Type: application/json" \
  -d '{"commands":["show version"]}'
```

4. Check status/result

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/active
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/events
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/result
```

5. Control async run

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/pause
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/resume
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/cancel
```

## 4. Local validation shortcuts

```bash
make check
make check-integration
```

## 5. Monitoring and troubleshooting

- Check active run:

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/active
```

- Check event stream buffer:

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/events
```

- Check latest run result:

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/result
```

If integration tests are skipped locally, ensure docker compose and mock SSH are available:

```bash
docker compose --profile test up -d mock-ssh
make check-integration
docker compose --profile test down
```

## 6. Known limitations and non-goals

- In-memory runtime only (no persistent DB/state).
- Credentials are handled in plaintext in process memory.
- v1 runtime paths (`start.sh`, `frontend`, `docs/QUICKSTART.md`) have been removed after hard cutover.
- Some modules under `backend/app` remain as internal dependencies for v2 netmiko execution/validation.
