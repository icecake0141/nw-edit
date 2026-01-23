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
# LLM生成コードについて

## 概要

本リポジトリには、大規模言語モデル（LLM: Large Language Model）の支援により生成されたコードが含まれる可能性があります。このドキュメントでは、LLM生成コードの取り扱いに関する方針と推奨事項を説明します。

## LLM生成コードとは

LLM生成コードとは、GitHub Copilot、ChatGPT、Claude などの大規模言語モデルツールによって提案または生成されたソースコードを指します。これらのツールは、既存のコードパターンや公開されているコードベースを学習しているため、生成されたコードには以下の特性があります：

- 既存の公開コードと類似したパターンを含む可能性がある
- 人間による監督とレビューが推奨される
- 意図しないバグやセキュリティ上の問題を含む可能性がある

## 推奨されるソースファイルヘッダ

LLMによって生成されたコード、または LLM の支援を受けたコードには、以下のようなヘッダを追加することを推奨します。

### Python ファイルの例

```python
# Copyright 2026 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# This file may contain code generated with the assistance of a Large Language Model (LLM).
```

### JavaScript/TypeScript ファイルの例

```javascript
// Copyright 2026 icecake0141
// SPDX-License-Identifier: Apache-2.0
//
// This file may contain code generated with the assistance of a Large Language Model (LLM).
```

### HTML/XML ファイルの例

```html
<!--
  Copyright 2026 icecake0141
  SPDX-License-Identifier: Apache-2.0

  This file may contain code generated with the assistance of a Large Language Model (LLM).
-->
```

より詳細なヘッダテンプレートについては、リポジトリルートの `../LICENSE-HEADER.txt` を参照してください。

## 取り扱い方針

### 1. 人によるレビューの重要性

LLM生成コードは、必ず人間の開発者によってレビューされ、以下の点を確認する必要があります：

- コードの正確性と意図した動作の実現
- セキュリティ上の脆弱性の有無
- プロジェクトのコーディング規約との整合性
- パフォーマンスへの影響
- テストカバレッジの十分性

### 2. サードパーティコードの確認

LLMは公開されているコードから学習しているため、生成されたコードがサードパーティのコードと類似している可能性があります。以下の点に注意してください：

- 生成されたコードが既存のオープンソースプロジェクトのコードと酷似していないか確認する
- 特に複雑なアルゴリズムや特殊な実装については、元となるコードが存在しないか調査する
- 疑義がある場合は、該当部分を書き直すか、適切なライセンス表示を行う

### 3. 法務面での注意事項

組織で本コードを利用する場合は、以下の点について法務部門や専門家に相談することを推奨します：

- LLM生成コードの著作権に関する方針
- ライセンスコンプライアンスの確認
- 特許侵害リスクの評価
- 規制要件への適合性

## 免責事項

本リポジトリの貢献者は、LLM生成コードの正確性、安全性、法的コンプライアンスについて、いかなる保証も行いません。LLM生成コードの使用は、ユーザー自身の責任において行ってください。

Apache License 2.0 の免責条項および責任制限条項が適用されます。詳細については、LICENSE ファイルを参照してください。

## 変更履歴

- **2026-01-11**: 初回作成。LLM生成コードに関する方針と推奨事項を定義。
