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
# テストとCI

英語版: [TESTING.md](TESTING.md)

## ローカルチェック（推奨）

リポジトリルートで実行:

```bash
./scripts/run_v2_checks.sh
```

このスクリプトは以下を実行します:

- `black --check`
- `flake8`
- `mypy --explicit-package-bases backend_v2/app`
- `pre-commit run --all-files`
- 単体テスト（`tests/unit` + `backend_v2/tests/unit`）
- 任意で統合テスト（`RUN_INTEGRATION=1`）

## Makeショートカット

```bash
make check
make check-integration
make typecheck
make precommit
```

## 単体テスト

```bash
python3 -m pytest tests/unit backend_v2/tests/unit -v --cov=backend/app --cov=backend_v2/app
```

## 統合テスト

```bash
docker compose --profile test up -d mock-ssh
python3 -m pytest tests/integration backend_v2/tests/integration -v -m integration
docker compose --profile test down
```

## CIワークフロー

メインCI: `.github/workflows/ci.yml`

ジョブ:

- `Lint`: black/flake8/mypy/py_compile
- `Test`: 単体テスト + カバレッジアーティファクト
- `Build Docker Image`: docker build + smoke run
- `Integration Tests`: docker ベース統合テスト

## トラブルシュート

- ローカルで統合テストが skip される場合は docker compose と mock SSH の起動状況を確認
- ドキュメントのみ変更時は `paths-ignore` により CI が起動しない場合があります
