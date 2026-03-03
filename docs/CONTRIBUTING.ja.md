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
# 貢献ガイド

英語版: [CONTRIBUTING.md](CONTRIBUTING.md)

このドキュメントは `docs/CONTRIBUTING.md` の日本語案内版です。詳細ルールは英語版を正本とします。

## 開発セットアップ

```bash
git clone https://github.com/icecake0141/nw-edit.git
cd nw-edit
python3 -m pip install -r backend_v2/requirements-dev.txt
```

## ローカル検証

```bash
make check
make check-integration
```

## コード規約

- Pythonフォーマット: `black`
- Lint: `flake8`
- 型チェック: `mypy`（`backend_v2`）
- pre-commit: `pre-commit run --all-files`

## コミット規約

Conventional Commits を使用:

- `feat:` 新機能
- `fix:` バグ修正
- `docs:` ドキュメント更新
- `test:` テスト更新
- `ci:` CI更新
- `refactor:` リファクタ

## PR要件

- ライセンスヘッダー/SPDX/LLM注記の整合
- 変更理由・テスト結果・後方互換メモの記載
- 検証コマンドの明記
- migration関連変更時は `docs/V2-MIGRATION-CHECKLIST.md` を更新

## 参考

- 英語版: [CONTRIBUTING.md](CONTRIBUTING.md)
- LLM生成コード方針: [LLM-GENERATED-CODE.md](LLM-GENERATED-CODE.md)
