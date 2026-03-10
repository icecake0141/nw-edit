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
- legacy な v1 backend 実装コード（`backend/app`）は削除済みです。
- 認証情報は平文のままプロセスメモリ上で扱います（永続化なし）。

## インストールと起動（v2）

### 前提条件

- Python 3.12+
- Docker / Docker Compose（統合検証時に推奨）

### クイックスタート

```bash
python3 -m pip install -r backend_v2/requirements-dev.txt
./start_v2.sh
```

- Backend: `http://127.0.0.1:8010`
- Frontend: `http://127.0.0.1:3010`

### 検証

```bash
make check
make check-integration
```

## コマンド変数（v2）

- 実行コマンドで `{{var}}` プレースホルダを利用可能。
- ジョブ単位の `global_vars` は `POST /api/v2/jobs` で指定。
- ホスト単位の `host_vars` は CSV 取込の `host_vars` 列（JSONオブジェクト文字列）で指定。
- 任意の CSV 列 `prod` で本番ホストを指定可能（`true` のとき本番、それ以外は `false` 扱い）。
- 解決優先順位は `host_vars > global_vars`。
- 未定義変数がある場合、デバイス実行前の preflight で `HTTP 400` を返す。
- フロントエンドの `Help` タブに、`global_vars` / `host_vars` と置換結果の実用例を掲載。

## 実行プリセット（v2）

- 実行画面（Create）で実行条件を `実行プリセット` として保存し、再利用できます。
- プリセットは `os_model`（`device_type`）単位で管理し、次を保持します。
  - `commands`
  - `verify_commands`
- 保存先はローカルJSONファイルです（`NW_EDIT_V2_PRESET_FILE`、既定: `backend_v2/data/run_presets.json`）。
- 実行画面のプリセット操作:
  - `Save New Preset`: 現在の `os_model` / `name` / `commands` / `verify_commands` で新規保存
  - `Update Selected Preset`: 選択中プリセットを現在のコマンド内容で更新
  - 同一 `name + os_model` で新規保存すると `HTTP 409`
  - Run成功時の自動保存は未対応
- 実行画面では次の順で利用します。
  - 対象OSモデルを選択
  - 実行プリセットを選択
  - 保存/更新時はプリセット名を入力
  - import済みデバイスから適用対象を選択（初期未選択）

## 実行前最終確認フロー（v2）

- Create画面に、実行前の最終確認ステップを追加しています。
- `実行前確認を使う` トグルはデフォルトONです（保持は画面内のみ。リロードで初期値に戻ります）。
- 実行ボタンは `Run` の1つで、常に `/api/v2/jobs/{job_id}/run/async` を実行します。
- トグルON時は、`Run` 押下時に先に確認パネルを表示し、以下を一覧表示します。
  - 対象ホスト
  - 実行コマンド
  - 確認用コマンド
  - 実行設定（有効な同時実行数を含む）
- `Canary success after` はラジオ選択です。
  - `Parallel`: 入力した `concurrency_limit` を使用
  - `Sequential (1 device at a time)`: `concurrency_limit=1` を強制し、入力欄は無効化されます
- バックエンドAPIの変更はなく、方式の差分はフロントエンドで `concurrency_limit` に反映します。

## ドキュメント

- ドキュメント一覧（英日）: [docs/INDEX.ja.md](docs/INDEX.ja.md)
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
