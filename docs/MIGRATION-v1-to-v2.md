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
# Migration Notes: v1 to v2

This guide summarizes behavior differences and rollout guidance when migrating from v1 (`backend` + `frontend`) to v2 (`backend_v2` + `frontend_v2`).

## Current recommendation

- Default path: v2 (`./start_v2.sh`)
- v1 (`./start.sh`, `docs/QUICKSTART.md`) is legacy and should only be used for temporary fallback or comparison.

## API differences

- v1 API base: `/api/*`
- v2 API base: `/api/v2/*`
- v2 adds explicit async control endpoints:
  - `POST /api/v2/jobs/{job_id}/run/async`
  - `POST /api/v2/jobs/{job_id}/pause`
  - `POST /api/v2/jobs/{job_id}/resume`
  - `POST /api/v2/jobs/{job_id}/cancel`

## Response schema differences

- v2 run result now includes additional metadata per device:
  - `error_code`
  - `diff_truncated`
  - `diff_original_size`
- v2 normalizes `pre_output`, `apply_output`, `post_output`, and `diff` to always be strings.

## Runtime and behavior notes

- v2 supports explicit worker/validator mode toggles:
  - `NW_EDIT_V2_WORKER_MODE=simulated|netmiko`
  - `NW_EDIT_V2_VALIDATOR_MODE=simulated|netmiko`
  - `NW_EDIT_V2_SIMULATED_DELAY_MS=<int>`
- Netmiko integration tests may be skipped locally when mock SSH is unavailable.

## Rollout plan

1. Use v2 in local and staging with `make check` and `make check-integration`.
2. Validate pause/resume/cancel operational flow in netmiko mode.
3. Update internal runbooks and dashboards to consume v2 endpoints and metadata.
4. Mark v1 endpoints and startup flow as deprecated in team docs.
5. Remove v1 runtime paths only after sign-off in `docs/V2-MIGRATION-CHECKLIST.md`.

## Rollback policy

- During migration window, rollback means temporarily switching startup/docs references back to v1.
- After hard cutover and v1 removal, rollback requires reverting release commits that removed v1 code paths.

## Release checklist pointer

Use [docs/V2-MIGRATION-CHECKLIST.md](docs/V2-MIGRATION-CHECKLIST.md) as the release gate for `GO/NO-GO` decisions.
