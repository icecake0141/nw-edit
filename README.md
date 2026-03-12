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
# Network Device Configuration Manager
[![CI](https://github.com/icecake0141/nw-edit/actions/workflows/ci.yml/badge.svg)](https://github.com/icecake0141/nw-edit/actions/workflows/ci.yml)
[![Dependabot Updates](https://github.com/icecake0141/nw-edit/actions/workflows/dependabot/dependabot-updates/badge.svg)](https://github.com/icecake0141/nw-edit/actions/workflows/dependabot/dependabot-updates)

A minimal web application for applying multi-line configuration commands to multiple network devices over SSH.

## Overview

- v2 path (`backend_v2` + `frontend_v2`) is the default.
- v1 runtime path (`start.sh`, `frontend`) has been removed after hard cutover.
- Legacy v1 backend implementation code (`backend/app`) has been removed.
- Credentials are handled in plaintext and stored in memory only.

## Install and Run (v2)

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (recommended for integration checks)

### Quick start

```bash
python3 -m pip install -r backend_v2/requirements-dev.txt
./start_v2.sh
```

- Backend: `http://127.0.0.1:8010`
- Frontend: `http://127.0.0.1:3010`
- Frontend is served by the repo-managed hardened static server, not `python -m http.server`.
- Directory listing is disabled by design; unknown paths return `404`.

### Validation

```bash
make check
make check-integration
```

## Command variables (v2)

- Use `{{var}}` placeholders in run commands.
- Define job-level `global_vars` at `POST /api/v2/jobs`.
- Define per-host `host_vars` in CSV import (`host_vars` column as JSON object string).
- Optional CSV column `prod` flags production hosts (`true` means production, others are treated as `false`).
- Resolution order is `host_vars > global_vars`.
- Missing variables fail preflight with `HTTP 400` before any device command runs.
- The frontend `Help` tab includes practical variable examples (`global_vars` / `host_vars` / substitution results).

## Execution presets (v2)

- Save and reuse execution conditions as `実行プリセット` (execution presets) from the Create page.
- Presets are scoped by `os_model` (`device_type`) and contain:
  - `commands`
  - `verify_commands`
- Presets are stored in local JSON file (`NW_EDIT_V2_PRESET_FILE`, default: `backend_v2/data/run_presets.json`).
- Create page preset actions:
  - `Save New Preset`: create a new preset from current `os_model`, `name`, `commands`, and `verify_commands`
  - `Update Selected Preset`: update currently selected preset with current command inputs
  - duplicate `name + os_model` on save returns `HTTP 409`
  - auto-save on run success is not supported
- Create page flow:
  - choose OS model
  - choose preset
  - enter preset name when saving/updating
  - choose imported target devices (initially unselected)

## Pre-run review flow (v2)

- Create page now supports a final review step before execution.
- `実行前確認を使う` toggle is enabled by default (UI-state only; resets on page reload).
- The execution action is a single `Run` button and always uses `/api/v2/jobs/{job_id}/run/async`.
- If review is enabled, `Run` opens a review panel first and lists:
  - target hosts
  - run commands
  - verify commands
  - effective run settings
- `Canary success after` controls post-canary fanout:
  - `Parallel` uses input `concurrency_limit`
  - `Sequential (1 device at a time)` forces `concurrency_limit=1` and disables the input
- No backend API changes were added; strategy is mapped only to `concurrency_limit`.

## Documentation

- Full index (EN/JA): [docs/INDEX.md](docs/INDEX.md)
- v2 quickstart: [docs/QUICKSTART-v2.md](docs/QUICKSTART-v2.md)
- v2 quickstart (JA): [docs/QUICKSTART-v2.ja.md](docs/QUICKSTART-v2.ja.md)
- v1->v2 migration notes: [docs/MIGRATION-v1-to-v2.md](docs/MIGRATION-v1-to-v2.md)
- v1->v2 migration notes (JA): [docs/MIGRATION-v1-to-v2.ja.md](docs/MIGRATION-v1-to-v2.ja.md)
- migration completion gate: [docs/V2-MIGRATION-CHECKLIST.md](docs/V2-MIGRATION-CHECKLIST.md)
- migration completion gate (JA): [docs/V2-MIGRATION-CHECKLIST.ja.md](docs/V2-MIGRATION-CHECKLIST.ja.md)
- specification: [docs/SPECIFICATION.md](docs/SPECIFICATION.md)
- specification (JA): [docs/SPECIFICATION.ja.md](docs/SPECIFICATION.ja.md)
- testing and CI: [docs/TESTING.md](docs/TESTING.md)
- testing and CI (JA): [docs/TESTING.ja.md](docs/TESTING.ja.md)
- contribution guide: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- contribution guide (JA): [docs/CONTRIBUTING.ja.md](docs/CONTRIBUTING.ja.md)
- Japanese README: [README.ja.md](README.ja.md)

## License

See [LICENSE](LICENSE).
