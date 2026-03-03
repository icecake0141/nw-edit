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
# ネットワークデバイス設定管理ツール

複数のネットワークデバイスに対して、SSH経由で複数行の設定コマンドを適用するための最小構成Webアプリケーションです。

## 概要

- v2 系（`backend_v2` + `frontend_v2`）をデフォルト運用とします。
- hard cutover 後、v1 ランタイム導線（`start.sh`、`frontend`）は削除済みです。
- `backend/app` 配下の一部モジュールは v2 の共通実装依存として継続利用します。
- 認証情報は平文のままプロセスメモリ上で扱います（永続化なし）。

## インストールと起動（v2）

### 前提条件

- Python 3.12+
- Docker / Docker Compose（統合検証時に推奨）

### クイックスタート

```bash
python3 -m pip install -r backend/requirements-dev.txt
./start_v2.sh
```

- Backend: `http://127.0.0.1:8010`
- Frontend: `http://127.0.0.1:3010`

### 検証

```bash
make check
make check-integration
```

## ドキュメント

- v2 クイックスタート: [docs/QUICKSTART-v2.ja.md](docs/QUICKSTART-v2.ja.md)
- v2 quickstart（英語）: [docs/QUICKSTART-v2.md](docs/QUICKSTART-v2.md)
- v1->v2 移行ノート: [docs/MIGRATION-v1-to-v2.ja.md](docs/MIGRATION-v1-to-v2.ja.md)
- v1->v2 migration notes（英語）: [docs/MIGRATION-v1-to-v2.md](docs/MIGRATION-v1-to-v2.md)
- 移行完了判定: [docs/V2-MIGRATION-CHECKLIST.ja.md](docs/V2-MIGRATION-CHECKLIST.ja.md)
- migration checklist（英語）: [docs/V2-MIGRATION-CHECKLIST.md](docs/V2-MIGRATION-CHECKLIST.md)
- 仕様: [docs/SPECIFICATION.ja.md](docs/SPECIFICATION.ja.md)
- specification（英語）: [docs/SPECIFICATION.md](docs/SPECIFICATION.md)
- テスト/CI: [docs/TESTING.ja.md](docs/TESTING.ja.md)
- testing/CI（英語）: [docs/TESTING.md](docs/TESTING.md)
- 貢献ガイド: [docs/CONTRIBUTING.ja.md](docs/CONTRIBUTING.ja.md)
- contribution guide（英語）: [docs/CONTRIBUTING.md](docs/CONTRIBUTING.md)
- English README: [README.md](README.md)

## ライセンス

[LICENSE](LICENSE) を参照してください。
