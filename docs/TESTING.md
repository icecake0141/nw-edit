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
# Testing and CI

## Local checks (recommended)

Run from repository root:

```bash
./scripts/run_v2_checks.sh
```

This runs:

- `black --check`
- `flake8`
- `mypy --explicit-package-bases backend_v2/app`
- `pre-commit run --all-files`
- unit tests (`tests/unit` + `backend_v2/tests/unit`)
- optional integration tests (`RUN_INTEGRATION=1`)

## Make shortcuts

```bash
make check
make check-integration
make typecheck
make precommit
```

## Unit tests

```bash
python3 -m pytest tests/unit backend_v2/tests/unit -v --cov=backend/app --cov=backend_v2/app
```

## Integration tests

```bash
docker compose --profile test up -d mock-ssh
python3 -m pytest tests/integration backend_v2/tests/integration -v -m integration
docker compose --profile test down
```

## CI workflow

Main CI workflow: `.github/workflows/ci.yml`

Jobs:

- `Lint`: black/flake8/mypy/py_compile
- `Test`: unit tests + coverage artifact
- `Build Docker Image`: docker build + smoke run
- `Integration Tests`: docker-backed integration suite

## Troubleshooting

- If integration tests skip locally, verify docker compose and mock SSH availability.
- If only docs changed, CI may be skipped due to `paths-ignore` configuration.
