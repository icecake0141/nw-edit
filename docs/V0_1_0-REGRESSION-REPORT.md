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
# v0.1.0 基準 機能差分再評価レポート（挙動粒度）

## 1. 目的と判定基準

- 判定基準: `v0.1.0` 完全準拠
- 評価対象: 機能 + UI（APIパス互換は評価対象外）
- 判定ラベル:
  - `一致`: v0.1.0 と同等挙動
  - `差分`: 挙動が異なる
  - `条件付き差分`: 実装は存在するが運用条件・経路差で実効挙動が異なる
  - `評価対象外`: APIパス互換のように今回スコープ外
- 優先度:
  - `P0`: 運用停止/誤操作/安全性に直結
  - `P1`: 主要ユースケース劣化
  - `P2`: 補助機能やUX差分

## 2. 差分マトリクス（再評価後）

`ID | 領域 | v0.1.0挙動 | 現行挙動 | 判定 | 影響度 | 証跡`

| ID | 領域 | v0.1.0挙動 | 現行挙動 | 判定 | 影響度 | 証跡 |
|---|---|---|---|---|---|---|
| API-01 | APIベース | `/api/*` 一式 | `/api/v2/*` 主体 | 評価対象外 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-02 | デバイス取込進捗API | `POST /api/devices/import/progress` | `POST /api/v2/devices/import/progress`（機能同等） | 評価対象外 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-03 | ステータスコマンドAPI | `POST /api/commands/exec` | `POST /api/v2/commands/exec`（機能同等） | 評価対象外 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-04 | ジョブ作成フロー | 作成後に実行可能（UIは一括実行導線あり） | `POST /api/v2/jobs` + `/run` or `/run/async`（UIは一括実行導線あり） | 一致 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py), [frontend_v2/public/app.js](../frontend_v2/public/app.js) |
| API-05 | 単一ジョブロック | active job があれば作成を `409` | 同等に `409` 拒否 | 一致 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-06 | CSV失敗行の扱い | 失敗行混在時でも継続寄り | 1件でも失敗行があれば全体 `400`（fail-fast） | 差分（意図変更） | - | [backend_v2/app/application/device_import_service.py](../backend_v2/app/application/device_import_service.py) |
| API-07 | 端末接続可否チェック | インポート時に実接続検証 | デフォルト `netmiko` 化済みで実接続検証 | 一致 | - | [start_v2.sh](../start_v2.sh), [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-08 | canary指定 | 明示必須 + 対象内整合 | `canary` 必須化 + 対象内チェック追加 | 一致 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-09 | 終了操作 | `terminate` | `/api/v2/jobs/{job_id}/terminate` で同等操作 | 一致 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| API-10 | 取込CSV列 | `host,...,verify_cmds` | `host_vars` 追加。旧CSV互換（余剰列/空行/ヘッダ揺れ）を許容 | 条件付き差分 | P2 | [backend_v2/app/application/device_import_service.py](../backend_v2/app/application/device_import_service.py) |
| UI-01 | タブ構成 | Import/Create/Monitor/Task History/Status Command | Import/Create/Monitor/History/Status Command/Detail | 条件付き差分 | P2 | [frontend_v2/public/index.html](../frontend_v2/public/index.html) |
| UI-02 | Create入力（canary） | canary選択あり | canary選択UIを復元済み | 一致 | - | [frontend_v2/public/index.html](../frontend_v2/public/index.html), [frontend_v2/public/app.js](../frontend_v2/public/app.js) |
| UI-03 | Create入力（verify mode） | `canary/all/none` | 同等UI/反映を復元済み | 一致 | - | [frontend_v2/public/index.html](../frontend_v2/public/index.html), [frontend_v2/public/api-client.js](../frontend_v2/public/api-client.js) |
| UI-04 | Create入力（concurrency/stagger/stop_on_error） | ユーザー入力可 | 同等UI/反映を復元済み | 一致 | - | [frontend_v2/public/index.html](../frontend_v2/public/index.html), [frontend_v2/public/api-client.js](../frontend_v2/public/api-client.js) |
| UI-05 | Active job開始ブロック | 実行中は開始不可バナー | バナー + 実行ボタン抑止を復元済み | 一致 | - | [frontend_v2/public/index.html](../frontend_v2/public/index.html), [frontend_v2/public/app.js](../frontend_v2/public/app.js) |
| UI-06 | Monitor表示 | デバイス別カード + pre/post/diff | 同等のデバイス粒度表示へ復元 | 一致 | - | [frontend_v2/public/app.js](../frontend_v2/public/app.js), [frontend_v2/public/index.html](../frontend_v2/public/index.html) |
| UI-07 | History詳細 | 詳細深掘り可能 | 要約制限除去。raw詳細表示を拡張済み | 一致 | - | [frontend_v2/public/app.js](../frontend_v2/public/app.js) |
| UI-08 | Import進捗表示 | 段階進捗（x/y） | `x/y` 表示を復元済み | 一致 | - | [backend_v2/app/api/main.py](../backend_v2/app/api/main.py), [frontend_v2/public/app.js](../frontend_v2/public/app.js) |
| BHV-01 | CSV接続検証方式 | 実接続検証（Netmiko） | デフォルト実接続（Netmiko） | 一致 | - | [start_v2.sh](../start_v2.sh), [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |
| BHV-02 | CSV検証実行順序 | 実質逐次 | 並列（3 workers） | 差分（意図変更） | - | [backend_v2/app/application/device_import_service.py](../backend_v2/app/application/device_import_service.py) |
| BHV-03 | Preset/host_vars | なし | あり（追加機能） | 差分（追加・採用） | - | [frontend_v2/public/index.html](../frontend_v2/public/index.html), [backend_v2/app/api/main.py](../backend_v2/app/api/main.py) |

## 3. 重点セクション詳細（再評価後）

### 3.1 CSVインポート

- 解消済み
  - デフォルト接続検証モードは `netmiko` に変更済み。
  - 進捗表示（`x/y`）は API/UI とも復元済み。
  - 旧CSV互換（余剰列・空行・ヘッダ揺れ）を受理。
- 意図差分（採用）
  - 失敗行1件で全体失敗（fail-fast）。採用理由: 不正データの混入を防ぐため。
  - 検証実行は並列（3 workers）。採用理由: 取り込み処理時間の短縮を優先。
- 運用影響
  - fail-fast 方針を採る運用では問題なし。
  - 部分成功を期待する運用では CSV 分割投入が必要。

### 3.2 ジョブ作成/実行

- 解消済み
  - UI上の Run 導線で v0.1.0 相当の一括実行体験を維持。
  - active job 排他（作成時 `409`）を復元。
  - canary 必須・対象内整合を API/UI 両面で復元。
  - verify mode / concurrency / stagger / stop_on_error を UI から反映可能。

### 3.3 モニタリング

- 解消済み
  - デバイス別カード表示、pre/apply/post/diff 表示を復元。
  - 監視状態管理を一本化し、実行中〜完了までの表示整合を確保。

### 3.4 履歴

- 解消済み
  - `logs` 先頭2件制限を撤廃し、raw詳細を展開表示。

### 3.5 ステータスコマンド

- 解消済み
  - UI/API を復元済み。

## 4. 回帰候補一覧（優先度付き・現時点）

### P0

- 該当なし（fail-fast は意図仕様として確定）。

### P1

- 該当なし（今回再評価時点）。

### P2

- 該当なし（現行実装優先で意図差分として採用）。

## 5. 意図差分（採用）

- CSV接続検証の並列化（逐次から3並列へ）。採用理由: スループット改善。
- `host_vars` / Preset など追加機能。採用理由: 運用自動化と再利用性の向上。
- UIの `Detail` タブ追加。採用理由: 詳細情報を監視導線と分離して可読性を上げるため。

## 6. 差分判定向けテストシナリオ（再掲）

1. CSVインポート
   - 正常行のみ
   - 不正行混在
   - 接続不可行混在
   - ヘッダ欠落
   - 余剰列
   - `host_vars` JSON不正
2. 実機ログイン検証
   - 同一CSVを `simulated` と `netmiko` で投入し結果比較
3. Job実行
   - 単一ジョブ制約
   - canary指定反映
   - verify mode反映
   - concurrency/stagger/stop_on_error反映
4. UI反映
   - 入力値がpayloadに載るか
   - 画面が結果の必要項目を表示するか

## 7. 今回の更新サマリ

- 前回 `差分` 判定だった主要項目の多くは実装反映により `一致` へ更新。
- 既存差分は「回帰候補」ではなく、現行実装優先の意図差分として確定。
- CSVインポート挙動差分は本レポートで必須ハイライトとして維持。
