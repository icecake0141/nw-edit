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
# 仕様

英語版: [SPECIFICATION.md](SPECIFICATION.md)

## スコープ

- 対象: SSH経由のネットワークデバイス設定更新
- 構成: シングルプロセス、インメモリ状態管理
- 展開方式: カナリア先行実行

## セキュリティモデル

- デバイス認証情報は CSV/API で平文入力され、メモリ上のみ保持
- 永続DBやシークレット管理との統合は現スコープ外
- 信頼できる隔離ネットワークでの利用を前提

## 機能概要

- CSVによるデバイス取り込みと接続検証
- ジョブライフサイクル管理（`queued/running/paused/completed/failed/cancelled`）
- 同期実行（`/run`）と非同期実行（`/run/async`）
- 非同期制御（`pause/resume/cancel`）
- WebSocketによるリアルタイムイベント配信
- デバイス単位の `pre/apply/post/diff` 結果
- OSモデル別の実行プリセット保存・再利用

## CSV形式

```csv
host,port,device_type,username,password,name,verify_cmds,host_vars
192.168.1.1,22,cisco_ios,admin,password123,Router1,show running-config | section snmp,"{""hostname"":""router-1""}"
```

### カラム

| カラム | 必須 | 説明 | 既定値 |
|--------|------|------|--------|
| `host` | はい | IP/FQDN | - |
| `port` | いいえ | SSHポート | `22` |
| `device_type` | はい | Netmikoデバイスタイプ | - |
| `username` | はい | SSHユーザー名 | - |
| `password` | はい | SSHパスワード | - |
| `name` | いいえ | 表示名 | - |
| `verify_cmds` | いいえ | `;` 区切りの検証コマンド | - |
| `host_vars` | いいえ | ホスト毎テンプレート変数(JSONオブジェクト文字列) | - |

## コマンドテンプレート変数

- コマンドのプレースホルダ記法は `{{var}}`。
- グローバル変数はジョブ作成時（`POST /api/v2/jobs` の `global_vars`）に指定。
- ホスト毎変数は CSV の `host_vars` 列で指定。
- マージ優先順位は `host_vars > global_vars`。
- 未解決プレースホルダが1つでもある場合、デバイス実行前に preflight で `HTTP 400` を返す。

## v2 API一覧（要約）

- デバイス:
  - `POST /api/v2/devices/import`
  - `GET /api/v2/devices`
- ジョブ:
  - `POST /api/v2/jobs`
  - `GET /api/v2/jobs`
  - `GET /api/v2/jobs/active`
  - `GET /api/v2/jobs/{job_id}`
  - `GET /api/v2/jobs/{job_id}/events`
  - `GET /api/v2/jobs/{job_id}/result`
- 実行:
  - `POST /api/v2/jobs/{job_id}/run`
  - `POST /api/v2/jobs/{job_id}/run/async`
  - `POST /api/v2/jobs/{job_id}/pause`
  - `POST /api/v2/jobs/{job_id}/resume`
  - `POST /api/v2/jobs/{job_id}/cancel`
- プリセット:
  - `GET /api/v2/presets`
  - `GET /api/v2/presets/os-models`
  - `POST /api/v2/presets`
  - `PUT /api/v2/presets/{preset_id}`
- WebSocket:
  - `/ws/v2/jobs/{job_id}`

## 実行リクエスト拡張

- `verify_commands`（任意）: 指定時は全対象デバイスへ共通適用。
- `imported_device_keys`（任意）: import済みデバイスの実行対象を `host:port` で明示。
  - ad-hoc の `devices` と同時指定不可
  - 空配列は `HTTP 400`

## 実行時設定

- `NW_EDIT_V2_WORKER_MODE=simulated|netmiko`
- `NW_EDIT_V2_VALIDATOR_MODE=simulated|netmiko`
- `NW_EDIT_V2_SIMULATED_DELAY_MS=<int>`

## 対応デバイスタイプ

Netmikoベースで、代表的には以下をサポート:

- `cisco_ios`
- `cisco_xe`
- `cisco_nxos`
- `arista_eos`
- `juniper_junos`
- `linux`（Generic Linux）

詳細は Netmiko ドキュメントを参照。

## 既知制約

- 永続化なし（再起動でインメモリ状態は消去）
- ロールバック未実装
- 認証情報はプロセスメモリ上で平文扱い
- シングルプロセス由来のスケール制約
- hard cutover 後、v1 ランタイム導線は削除済みで v2 のみサポート
