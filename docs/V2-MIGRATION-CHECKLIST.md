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
# v2 Migration Completion Checklist

This document defines when migration from v1 (`backend` + `frontend`) to v2 (`backend_v2` + `frontend_v2`) can be considered complete.

## 1. Scope and decision

Migration is complete only when all of the following are true:

1. v2 provides all required user-facing capabilities currently used in v1 operations.
2. v2 quality gates (lint, typecheck, unit/integration tests, pre-commit) pass in CI.
3. Runbook and migration notes are published and reviewed.
4. Default startup and documentation paths point to v2.
5. v1 is explicitly marked as deprecated (or removed in a final cleanup PR).

## 2. Capability parity gates (must pass)

- [ ] Device import and validation (`POST /api/v2/devices/import`, `GET /api/v2/devices`)
- [ ] Job lifecycle APIs (`create/list/get/events`)
- [ ] Execution modes (`run`, `run/async`) and active-job snapshot
- [ ] Execution controls (`pause/resume/cancel`) in netmiko mode
- [ ] Result API includes consistent `pre_output` / `apply_output` / `post_output` / `diff` fields
- [ ] WebSocket monitor flow for live execution tracking
- [ ] Frontend supports import, create, monitor, history/detail without relying on v1 UI

## 3. Reliability and quality gates (must pass)

Run from repository root:

```bash
./scripts/run_v2_checks.sh
```

Required outcome:

- [ ] `black --check` passes
- [ ] `flake8` passes
- [ ] `mypy --explicit-package-bases backend_v2/app` passes
- [ ] `pre-commit run --all-files` passes
- [ ] `pytest tests/unit backend_v2/tests/unit -v` passes
- [ ] `pytest tests/integration backend_v2/tests/integration -v -m integration` passes
- [ ] CI workflow is green on the migration PR branch

## 4. Operational readiness gates

- [ ] `start_v2.sh` is the recommended local startup path in README and docs
- [ ] Environment variables for v2 modes are documented with safe defaults
- [ ] Monitoring/troubleshooting steps for v2 are documented
- [ ] Known limitations and non-goals are documented

## 5. Documentation and release gates

- [ ] Migration notes document behavior differences vs v1
- [ ] Backward-compatibility impact is clearly stated
- [ ] Rollout plan includes staged adoption and rollback policy
- [ ] PR checklist and release checklist are updated for v2-first delivery

## 6. v1 deprecation gates

Choose one and record it in the migration PR:

1. Soft deprecation: keep v1 code, but mark as deprecated and remove from default flow.
2. Hard cutover: remove v1 runtime paths after v2 production acceptance.

Checklist:

- [ ] README default examples use v2 endpoints and startup scripts
- [ ] CI default gates include v2 checks as blocking
- [ ] v1 status is documented (deprecated or removed)

## 7. Sign-off template

Use this section in the migration completion PR:

- Scope owner:
- Reviewer(s):
- Date:
- Decision: `GO` / `NO-GO`
- Risks accepted:
- Follow-up issues:

## 8. Suggested implementation order

1. Netmiko integration and timeout/error normalization
2. Result schema consistency and diff size policy
3. Frontend v2 page split and typed API client
4. Migration notes + release checklist finalization
5. v2 default path switch in README/start scripts/CI messaging
6. v1 soft deprecation or hard removal
