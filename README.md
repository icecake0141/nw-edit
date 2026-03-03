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
- Some modules under `backend/app` remain as shared implementation dependencies for v2.
- Credentials are handled in plaintext and stored in memory only.

## Install and Run (v2)

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (recommended for integration checks)

### Quick start

```bash
python3 -m pip install -r backend/requirements-dev.txt
./start_v2.sh
```

- Backend: `http://127.0.0.1:8010`
- Frontend: `http://127.0.0.1:3010`

### Validation

```bash
make check
make check-integration
```

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
