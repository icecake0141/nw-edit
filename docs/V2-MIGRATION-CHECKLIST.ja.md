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
# v2 移行完了チェックリスト

英語版: [V2-MIGRATION-CHECKLIST.md](V2-MIGRATION-CHECKLIST.md)

この文書は v1（`backend` + `frontend`）から v2（`backend_v2` + `frontend_v2`）への移行完了判定基準を定義します。

## 1. 判定条件

以下をすべて満たす場合に完了:

1. v2 が現行運用で必要なユーザー機能を提供
2. v2 の品質ゲート（lint/type/test/pre-commit）が CI で成功
3. Runbook と移行ノートが公開・レビュー済み
4. 起動導線とドキュメントのデフォルトが v2
5. v1 が deprecated 明記済み（または最終PRで削除済み）

## 2. 機能パリティ

- [x] デバイス取込と検証
- [x] ジョブライフサイクルAPI
- [x] 同期/非同期実行 + active snapshot
- [x] netmikoモードで pause/resume/cancel
- [x] `pre/apply/post/diff` の一貫レスポンス
- [x] WebSocket でのリアルタイム監視
- [x] v1 UI 非依存で Import/Create/Monitor/History/Detail が利用可能

## 3. 品質ゲート

- [x] `black --check`
- [x] `flake8`
- [x] `mypy --explicit-package-bases backend_v2/app`
- [x] `pre-commit run --all-files`
- [x] `PYTHONPATH=. pytest backend_v2/tests/unit -v`
- [x] `PYTHONPATH=. pytest backend_v2/tests/integration -v -m integration`
- [x] 移行PRで CI green

## 4. 運用準備

- [x] README/docs の推奨起動が `start_v2.sh`
- [x] v2 環境変数が既定値付きで文書化
- [x] 監視/トラブルシュート手順が文書化
- [x] 既知制約・非目標が文書化

## 5. ドキュメント/リリース

- [x] v1との差分を移行ノートに記載
- [x] 後方互換影響を明記
- [x] 段階ロールアウト/ロールバック方針を明記
- [x] v2-first 前提で PR/リリースチェックを更新

## 6. v1 扱い

- [x] README 既定例が v2
- [x] CI 既定ゲートに v2 チェックを含む
- [x] v1 ステータス（deprecated/removed）を文書化
- [x] v1 ランタイム導線（`start.sh`、`frontend`、`docs/QUICKSTART.md`）を削除

## 7. サインオフ記録

- Scope owner: `icecake0141`
- Reviewer(s): `PR #79, #81 でのメンテナレビュー`
- Date: `2026-03-03`（soft deprecation）, `2026-03-03`（hard cutover）
- Decision: `GO`
- Accepted risks:
  - ローカルで統合テストを完全実行するには docker-backed mock SSH が必要
- Follow-up:
  - `2026-03-03` 対応済み: v2 の netmiko 依存 import を `backend/app` から分離
  - `2026-03-03` 対応済み: legacy な v1 backend 実装コード（`backend/app`）を削除

証跡:

- `main` の `40cc9fe` で CI green（run `22624179626`）
- CI integration job で docker-backed mock SSH テスト成功
