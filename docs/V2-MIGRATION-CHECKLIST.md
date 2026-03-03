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

- [x] Device import and validation (`POST /api/v2/devices/import`, `GET /api/v2/devices`)
- [x] Job lifecycle APIs (`create/list/get/events`)
- [x] Execution modes (`run`, `run/async`) and active-job snapshot
- [x] Execution controls (`pause/resume/cancel`) in netmiko mode
- [x] Result API includes consistent `pre_output` / `apply_output` / `post_output` / `diff` fields
- [x] WebSocket monitor flow for live execution tracking
- [x] Frontend supports import, create, monitor, history/detail without relying on v1 UI

## 3. Reliability and quality gates (must pass)

Run from repository root:

```bash
./scripts/run_v2_checks.sh
```

Required outcome:

- [x] `black --check` passes
- [x] `flake8` passes
- [x] `mypy --explicit-package-bases backend_v2/app` passes
- [x] `pre-commit run --all-files` passes
- [x] `pytest tests/unit backend_v2/tests/unit -v` passes
- [x] `pytest tests/integration backend_v2/tests/integration -v -m integration` passes
- [x] CI workflow is green on the migration PR branch

## 4. Operational readiness gates

- [x] `start_v2.sh` is the recommended local startup path in README and docs
- [x] Environment variables for v2 modes are documented with safe defaults
- [x] Monitoring/troubleshooting steps for v2 are documented
- [x] Known limitations and non-goals are documented

## 5. Documentation and release gates

- [x] Migration notes document behavior differences vs v1
- [x] Backward-compatibility impact is clearly stated
- [x] Rollout plan includes staged adoption and rollback policy
- [x] PR checklist and release checklist are updated for v2-first delivery

## 6. v1 deprecation gates

Choose one and record it in the migration PR:

1. Soft deprecation: keep v1 code, but mark as deprecated and remove from default flow.
2. Hard cutover: remove v1 runtime paths after v2 production acceptance.

Checklist:

- [x] README default examples use v2 endpoints and startup scripts
- [x] CI default gates include v2 checks as blocking
- [x] v1 status is documented (deprecated or removed)

## 7. Sign-off template

Migration completion sign-off:

- Scope owner: `icecake0141`
- Reviewer(s): `Maintainer review via merged PRs #79 and #81`
- Date: `2026-03-03`
- Decision: `GO`
- Risks accepted:
  - v1 code paths remain in repository during soft-deprecation window
  - Legacy docs remain available for fallback use
- Follow-up issues:
  - Hard cutover (optional): remove v1 runtime paths in a dedicated cleanup PR

Evidence:

- CI green on `main` for commit `40cc9fe` (workflow run `22624179626`)
- Integration job succeeded in CI with docker-backed mock SSH

## 8. Suggested implementation order

1. Netmiko integration and timeout/error normalization
2. Result schema consistency and diff size policy
3. Frontend v2 page split and typed API client
4. Migration notes + release checklist finalization
5. v2 default path switch in README/start scripts/CI messaging
6. v1 soft deprecation or hard removal
