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

## 1. backend v2 を起動

```bash
uvicorn backend_v2.app.api.main:app --reload --port 8010
```

モード設定:

```bash
export NW_EDIT_V2_WORKER_MODE=simulated    # または netmiko
export NW_EDIT_V2_VALIDATOR_MODE=simulated # または netmiko
export NW_EDIT_V2_SIMULATED_DELAY_MS=200   # 任意（simulated worker の遅延）
```

## 2. frontend v2 を起動

```bash
cd frontend_v2/public
python3 -m http.server 3010
```

`http://127.0.0.1:3010` を開いてください。

## 3. 基本的な API フロー

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
  -d '{"commands":["show version"]}'
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

## 4. ローカル検証ショートカット

```bash
make check
make check-integration
```
