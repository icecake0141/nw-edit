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
# GitHub Issue Templates for Improvement Proposals

以下は、IMPROVEMENTS.ja.md に記載された改良提案をGitHub Issueとして作成するためのテンプレートです。
各提案をコピーしてIssueとして作成できます。

---

## Issue 1: 設定バックアップ・履歴管理機能の実装

**ラベル**: `enhancement`, `priority-high`, `security`

**説明**:

設定変更前の自動バックアップと変更履歴の保存機能を追加します。

### 概要
設定変更前に自動的にバックアップを作成し、変更履歴を保存することで、手動ロールバックを可能にします。

### 実装内容
- ジョブ実行時（事前検証フェーズ）に自動的にバックアップを作成
- オンデマンドバックアップ用のエンドポイント `POST /api/devices/backup?host={host}&port={port}` を追加
- 各デバイスの変更前設定を自動的にファイルシステムに保存
- タイムスタンプ付きでバックアップファイルを管理（例: `backups/{device_id}/{timestamp}/running-config`）
- バックアップ一覧取得API `GET /api/backups?device={host}:{port}` を追加
- 特定バックアップ取得API `GET /api/backups/{backup_id}` でバックアップ内容を表示
- WebUIに「バックアップ作成」と「バックアップから復元」ボタンを追加

### メリット
- 手動ロールバックが可能になる
- 変更履歴の追跡が容易
- コンプライアンス要件への対応が向上

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案1-設定バックアップ履歴管理機能) を参照

---

## Issue 2: ジョブテンプレート・スケジューリング機能の実装

**ラベル**: `enhancement`, `priority-medium`

**説明**:

よく使う設定変更をテンプレート化し、スケジュール実行できる機能を追加します。

### 概要
定期メンテナンス作業の自動化と手順の標準化を実現します。

### 実装内容
- ジョブテンプレート保存API `POST /api/templates` を追加
- テンプレート一覧・取得API `GET /api/templates`, `GET /api/templates/{template_id}` を追加
- テンプレートからのジョブ作成 `POST /api/jobs/from-template/{template_id}` を追加
- cron式によるスケジュール設定機能（APSchedulerなどを使用）
- スケジュール管理API `POST /api/schedules`, `GET /api/schedules`, `DELETE /api/schedules/{schedule_id}`
- WebUIにテンプレート管理画面とスケジュール設定画面を追加

### メリット
- 定期メンテナンス作業の自動化
- 手順の標準化とヒューマンエラー削減
- 夜間メンテナンスウィンドウでの無人実行が可能

### 実装難易度
中〜高

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案2-ジョブテンプレートスケジューリング機能) を参照

---

## Issue 3: 実行結果のエクスポート・レポート機能の実装

**ラベル**: `enhancement`, `priority-high`

**説明**:

ジョブ実行結果を様々な形式でエクスポートし、レポート生成する機能を追加します。

### 概要
変更作業の証跡管理と監査対応を容易にします。

### 実装内容
- ジョブ結果エクスポートAPI `GET /api/jobs/{job_id}/export?format={json|csv|pdf|html}` を追加
- PDF/HTMLレポート生成（成功/失敗デバイス一覧、差分サマリー、実行時間など）
- CSV形式での結果ダウンロード（監査用）
- WebUIにダウンロードボタンを追加（複数形式対応）
- メール送信機能（オプション、環境変数でSMTP設定）

### メリット
- 変更作業の証跡管理が容易
- 上長への報告資料作成が簡単
- 監査対応の向上

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案3-実行結果のエクスポートレポート機能) を参照

---

## Issue 4: ドライランモード（シミュレーション実行）の実装

**ラベル**: `enhancement`, `priority-high`

**説明**:

実際には設定を適用せず、何が起こるかをシミュレーションする機能を追加します。

### 概要
本番実行前のリスク低減とコマンドの誤りを事前に発見できるようにします。

### 実装内容
- ジョブ作成時に `dry_run: true` パラメータを追加
- ドライランモードでは：
  - デバイスへの接続確認のみ実施
  - コマンドの構文チェック（デバイスタイプに応じた簡易バリデーション）
  - 想定される実行時間の推定
  - 影響を受けるデバイス数のサマリー
- WebUIに「ドライラン実行」ボタンを追加
- 実行結果に「これはドライラン実行です」というバナーを表示

### メリット
- 本番実行前のリスク低減
- コマンドの誤りを事前に発見
- 実行時間の事前見積もりが可能

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案4-ドライランモードシミュレーション実行) を参照

---

## Issue 5: 高度な通知・アラート機能の実装

**ラベル**: `enhancement`, `priority-medium`

**説明**:

ジョブの状態変化や重要なイベントをリアルタイムで通知する機能を追加します。

### 概要
ジョブ監視のための常時画面監視を不要にし、問題発生時の迅速な対応を可能にします。

### 実装内容
- 通知設定API `POST /api/notifications/settings` を追加
- 通知チャネル：Webhook（Slack, Microsoft Teams, 汎用Webhook）、メール（SMTP経由）、Syslog
- 通知トリガー：ジョブ開始、ジョブ完了（成功/失敗）、カナリアデバイス失敗、X%以上のデバイスで失敗、特定デバイスでの失敗
- テンプレート化された通知メッセージ
- WebUIに通知設定画面を追加

### メリット
- ジョブ監視のための常時画面監視が不要
- 問題発生時の迅速な対応が可能
- チーム全体への情報共有が容易

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案5-高度な通知アラート機能) を参照

---

## Issue 6: デバイスグルーピング・タグ管理機能の実装

**ラベル**: `enhancement`, `priority-medium`

**説明**:

デバイスをグループやタグで管理し、一括選択を容易にする機能を追加します。

### 概要
大量デバイス管理を容易にし、ロケーション、役割、環境別の管理を可能にします。

### 実装内容
- デバイスモデルに `tags` フィールド（文字列配列）を追加
- デバイスグループ管理API：
  - `POST /api/device-groups` - グループ作成
  - `GET /api/device-groups` - グループ一覧
  - `PUT /api/device-groups/{group_id}/devices` - グループへのデバイス追加/削除
- タグベースのフィルタリング `GET /api/devices?tags=production,core-router`
- CSV importでタグカラムをサポート
- WebUIでタグによるフィルタリングとグループ一括選択機能

### メリット
- 大量デバイス管理が容易
- ロケーション、役割、環境別の管理が可能
- ジョブ作成時の対象デバイス選択が効率的

### 実装難易度
低〜中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案6-デバイスグルーピングタグ管理機能) を参照

---

## Issue 7: 変更承認ワークフロー機能の実装

**ラベル**: `enhancement`, `priority-medium`, `governance`

**説明**:

重要な変更に対する多段階承認プロセスを実装します。

### 概要
ガバナンス強化と誤操作や不正な変更の防止を実現します。

### 実装内容
- ジョブステータスに `pending_approval` 状態を追加
- 承認者設定API `POST /api/jobs/{job_id}/approvers` を追加
- 承認/却下API `POST /api/jobs/{job_id}/approve`, `POST /api/jobs/{job_id}/reject`
- 承認履歴の保存
- メール/Webhook通知による承認依頼
- WebUIに承認待ちジョブ一覧と承認画面を追加
- 承認者の権限レベル設定（環境変数やconfigファイル）

### メリット
- ガバナンス強化
- 誤操作や不正な変更の防止
- 変更管理プロセスの標準化

### 実装難易度
中〜高

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案7-変更承認ワークフロー機能) を参照

---

## Issue 8: 拡張ロギング・監査証跡機能の実装

**ラベル**: `enhancement`, `priority-high`, `security`, `compliance`

**説明**:

詳細な監査ログとユーザー操作履歴の記録を実装します。

### 概要
セキュリティインシデント調査とコンプライアンス要件への対応を可能にします。

### 実装内容
- すべてのAPI呼び出しの監査ログ記録
- ログ項目：タイムスタンプ、ユーザー、操作、対象リソース、結果
- ログストレージのオプション：ローカルファイル（JSON Lines形式）、Syslog、外部ログ管理システム（Elasticsearch, Splunkなど）
- 監査ログ検索API `GET /api/audit-logs?start_time=&end_time=&user=&action=`
- WebUIに監査ログビューアーを追加
- ログローテーション設定

### メリット
- セキュリティインシデント調査が可能
- コンプライアンス要件への対応
- ユーザー行動の追跡と分析

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案8-拡張ロギング監査証跡機能) を参照

---

## Issue 9: 設定差分の高度な可視化機能の実装

**ラベル**: `enhancement`, `priority-medium`, `ui/ux`

**説明**:

変更前後の差分をより見やすく、理解しやすい形式で表示する機能を追加します。

### 概要
変更内容の理解を容易にし、レビューの品質を向上させます。

### 実装内容
- 構文ハイライト付き差分表示（デバイスタイプに応じた構文）
- サイドバイサイド比較モード
- 変更箇所のサマリー（追加行数、削除行数、変更行数）
- 重要な変更の自動検出（例：ACLの変更、ルーティング設定の変更）
- 差分のフィルタリング（空白変更を無視など）
- WebUIに切り替え可能な複数の差分表示モード

### メリット
- 変更内容の理解が容易
- レビューの品質向上
- 意図しない変更の発見が容易

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案9-設定差分の高度な可視化機能) を参照

---

## Issue 10: パフォーマンス監視・最適化機能の実装

**ラベル**: `enhancement`, `priority-low`, `performance`

**説明**:

ジョブ実行のパフォーマンスメトリクスを収集・表示する機能を追加します。

### 概要
パフォーマンス問題の早期発見と最適な並行実行数の決定を可能にします。

### 実装内容
- メトリクス収集：
  - デバイスごとの接続時間、コマンド実行時間
  - 並行実行スレッドの使用状況
  - メモリ使用量
  - ジョブ実行時間の統計（平均、最小、最大）
- メトリクス表示API `GET /api/metrics/jobs/{job_id}`
- システム全体のメトリクス `GET /api/metrics/system`
- WebUIにパフォーマンスダッシュボード追加
- Prometheus互換のメトリクスエンドポイント `/metrics`（オプション）
- ボトルネックの自動検出と推奨事項の提示

### メリット
- パフォーマンス問題の早期発見
- 最適な並行実行数の決定が容易
- システムリソースの適切な管理

### 実装難易度
中

### 参照
詳細は [IMPROVEMENTS.ja.md](IMPROVEMENTS.ja.md#提案10-パフォーマンス監視最適化機能) を参照

---

## 使用方法

1. 各Issueテンプレートをコピー
2. GitHubリポジトリで新しいIssueを作成
3. タイトルと説明をテンプレートから貼り付け
4. 適切なラベルを設定
5. マイルストーンやアサインを設定（必要に応じて）

## 優先順位による実装順序の推奨

### フェーズ1（高優先度）
- Issue 1: 設定バックアップ・履歴管理機能
- Issue 3: 実行結果のエクスポート・レポート機能
- Issue 4: ドライランモード
- Issue 8: 拡張ロギング・監査証跡機能

### フェーズ2（中優先度）
- Issue 2: ジョブテンプレート・スケジューリング機能
- Issue 5: 高度な通知・アラート機能
- Issue 6: デバイスグルーピング・タグ管理機能
- Issue 7: 変更承認ワークフロー機能
- Issue 9: 設定差分の高度な可視化機能

### フェーズ3（低優先度）
- Issue 10: パフォーマンス監視・最適化機能
