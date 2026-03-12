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
# QUICKSTART v2（日本語）

## 1. 起動用の環境変数を export

`./start_v2.sh` は、起動前に 2 つのランタイムモード変数を明示設定する必要があります。

```bash
export NW_EDIT_V2_WORKER_MODE=netmiko
export NW_EDIT_V2_VALIDATOR_MODE=netmiko
```

任意の変数:

```bash
export NW_EDIT_V2_SIMULATED_DELAY_MS=200
export NW_EDIT_V2_PRESET_FILE=backend_v2/data/run_presets.json
export NW_EDIT_V2_CORS_ORIGINS=http://127.0.0.1:3010,http://localhost:3010
```

`./start_v2.sh` は backend/frontend の起動前に required/optional の環境変数一覧を表示します。変数名に `PASS`、`PASSWORD`、`SECRET`、`TOKEN`、`KEY`、`CREDENTIAL`、`AUTH` を含む場合、値は `***MASKED***` で表示されます。

## 2. backend と frontend v2 を起動

```bash
./start_v2.sh
```

`http://127.0.0.1:3010` を開いてください。

## 3. backend v2 を個別起動（任意）

```bash
uvicorn backend_v2.app.api.main:app --reload --port 8010
```

個別起動時の設定:

```bash
export NW_EDIT_V2_SIMULATED_DELAY_MS=200   # 任意（simulated worker の遅延）
```

## 4. frontend v2 を個別起動（任意）

```bash
python3 -m backend_v2.app.frontend_server
```

`http://127.0.0.1:3010` を開いてください。

補足:
- Frontend はデフォルトで `127.0.0.1` にのみ bind します。
- Directory Listing は無効で、存在しないパスは `404` を返します。

## 5. 基本的な API フロー

1. デバイスをインポート

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/devices/import \
  -H "Content-Type: text/plain" \
  --data-binary $'host,port,device_type,username,password,name,verify_cmds\n10.0.0.1,22,cisco_ios,admin,pass,edge-1,show run'
```

2. ジョブを作成

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs \
  -H "Content-Type: application/json" \
  -d '{"job_name":"demo","creator":"local"}'
```

3. 非同期実行を開始

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/run/async \
  -H "Content-Type: application/json" \
  -d '{"commands":["show version"],"imported_device_keys":["10.0.0.1:22"],"canary":{"host":"10.0.0.1","port":22}}'
```

4. ステータス/結果を確認

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/active
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/events
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/result
```

5. 非同期実行を制御

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/pause
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/resume
curl -s -X POST http://127.0.0.1:8010/api/v2/jobs/<job_id>/cancel
```

6. 実行プリセットの作成/一覧

```bash
curl -s -X POST http://127.0.0.1:8010/api/v2/presets \
  -H "Content-Type: application/json" \
  -d '{"name":"ios baseline","os_model":"cisco_ios","commands":["show version"],"verify_commands":["show ip interface brief"]}'

curl -s "http://127.0.0.1:8010/api/v2/presets?os_model=cisco_ios"
```

7. Create画面のプリセット運用（手動保存のみ）

- Create画面で `Preset Mode` を有効化。
- `Target OS Model` を選択。
- `Preset Name` を入力し、次を利用:
  - `Save New Preset`: 新規保存
  - `Update Selected Preset`: 選択中プリセットを上書き更新
- `Save New Preset` で同一 `name + os_model` が存在する場合は `HTTP 409`。
- Run成功時の自動保存は行われません。

## 6. ローカル検証ショートカット

```bash
make check
make check-integration
```

## 7. 監視とトラブルシュート

- 実行中ジョブの確認:

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/active
```

- イベント履歴の確認:

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/events
```

- 実行結果の確認:

```bash
curl -s http://127.0.0.1:8010/api/v2/jobs/<job_id>/result
```

ローカルで統合テストが skip される場合は、docker compose と mock SSH を有効化してください:

```bash
docker compose --profile test up -d mock-ssh
make check-integration
docker compose --profile test down
```

## 8. 既知制約と非目標

- 実行時データはインメモリのみ（永続DBなし）。
- 認証情報はプロセスメモリ上で平文扱い。
- hard cutover により v1 ランタイム導線（`start.sh`、`frontend`、`docs/QUICKSTART.md`）は削除済み。
