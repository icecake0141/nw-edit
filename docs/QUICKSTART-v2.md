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
python3 -m pip install -r backend_v2/requirements-dev.txt
```

## 1. Export startup environment variables

`./start_v2.sh` requires the two runtime mode variables to be set explicitly before launch.

```bash
export NW_EDIT_V2_WORKER_MODE=netmiko
export NW_EDIT_V2_VALIDATOR_MODE=netmiko
```

Optional variables:

```bash
export NW_EDIT_V2_SIMULATED_DELAY_MS=200
export NW_EDIT_V2_PRESET_FILE=backend_v2/data/run_presets.json
export NW_EDIT_V2_CORS_ORIGINS=http://127.0.0.1:3010,http://localhost:3010
```

At startup, `./start_v2.sh` prints required and optional environment variables before launching the backend and frontend. Variable names containing `PASS`, `PASSWORD`, `SECRET`, `TOKEN`, `KEY`, `CREDENTIAL`, or `AUTH` are displayed as `***MASKED***`.

## 2. Start backend and frontend v2

```bash
./start_v2.sh
```

Open `http://127.0.0.1:3010`.

## 3. Start backend v2 manually (optional)

```bash
uvicorn backend_v2.app.api.main:app --reload --port 8010
```

Manual mode settings:

```bash
export NW_EDIT_V2_SIMULATED_DELAY_MS=200   # optional (slow down simulated worker)
```

## 4. Start frontend v2 manually (optional)

```bash
python3 -m backend_v2.app.frontend_server
```

Open `http://127.0.0.1:3010`.

Notes:
- The frontend binds to `127.0.0.1` by default.
- Directory listing is disabled; requests to unknown paths return `404`.

## 5. Basic API flow

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
  -d '{"commands":["show version"],"imported_device_keys":["10.0.0.1:22"],"canary":{"host":"10.0.0.1","port":22}}'
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

6. Create/list execution presets

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/presets \
  -H "Content-Type: application/json" \
  -d '{"name":"ios baseline","os_model":"cisco_ios","commands":["show version"],"verify_commands":["show ip interface brief"]}'

curl -s "http://127.0.0.1:8010/api/v2/presets?os_model=cisco_ios"
```

7. Create page preset workflow (manual save only)

- Enable `Preset Mode` on Create page.
- Select `Target OS Model`.
- Enter `Preset Name`, then click:
  - `Save New Preset` to create a new preset.
  - `Update Selected Preset` to overwrite selected preset.
- Duplicate `name + os_model` on `Save New Preset` returns `HTTP 409`.
- Presets are not auto-saved when a run succeeds.

## 6. Local validation shortcuts

```bash
make check
make check-integration
```

## 7. Monitoring and troubleshooting

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

## 8. Known limitations and non-goals

- In-memory runtime only (no persistent DB/state).
- Credentials are handled in plaintext in process memory.
- v1 runtime paths (`start.sh`, `frontend`, `docs/QUICKSTART.md`) have been removed after hard cutover.
