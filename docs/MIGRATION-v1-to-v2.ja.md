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
# 移行ノート: v1 から v2

英語版: [MIGRATION-v1-to-v2.md](MIGRATION-v1-to-v2.md)

このドキュメントは、v1（`backend` + `frontend`）からv2（`backend_v2` + `frontend_v2`）へ移行する際の挙動差分と運用方針をまとめたものです。

## 現在の推奨

- デフォルト導線: v2（`./start_v2.sh`）
- hard cutover 後は v1 ランタイム導線を削除（`start.sh`、`docs/QUICKSTART.md` は提供終了）。
- `backend/app` 配下の一部モジュールは v2 netmiko アダプタの共通依存として継続利用。

## API差分

- v1 API base: `/api/*`
- v2 API base: `/api/v2/*`
- v2 の追加制御エンドポイント:
  - `POST /api/v2/jobs/{job_id}/run/async`
  - `POST /api/v2/jobs/{job_id}/pause`
  - `POST /api/v2/jobs/{job_id}/resume`
  - `POST /api/v2/jobs/{job_id}/cancel`

## レスポンス差分

- v2 のデバイス実行結果には以下メタデータを追加:
  - `error_code`
  - `diff_truncated`
  - `diff_original_size`
- `pre_output` / `apply_output` / `post_output` / `diff` は常に文字列として返却。

## 実行時の挙動メモ

- v2 は worker/validator のモード切替をサポート:
  - `NW_EDIT_V2_WORKER_MODE=simulated|netmiko`
  - `NW_EDIT_V2_VALIDATOR_MODE=simulated|netmiko`
  - `NW_EDIT_V2_SIMULATED_DELAY_MS=<int>`
- ローカルで mock SSH がない場合、netmiko 統合テストは skip されることがあります。

## ロールアウト手順

1. v2 をローカル/ステージングで `make check` / `make check-integration` で検証
2. netmiko モードで pause/resume/cancel を運用観点で確認
3. 運用Runbook・監視を v2 エンドポイント/メタデータに更新
4. v1 導線を deprecated として明記
5. `V2-MIGRATION-CHECKLIST.md` で sign-off 後に hard cutover を実施し v1 ランタイム導線を削除

## ロールバック方針

- hard cutover 前: 導線を一時的に v1 側へ戻して回避
- hard cutover 後: v1 ランタイム削除コミットを含むリリース差分を revert して復旧

## リリース判定

`GO/NO-GO` 判定は [V2-MIGRATION-CHECKLIST.ja.md](V2-MIGRATION-CHECKLIST.ja.md) を使用。
