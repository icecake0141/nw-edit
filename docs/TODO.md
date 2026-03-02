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
# TODO

## v2 Migration Priority Tasks

- [x] Expand Netmiko integration tests for async `pause` / `resume` / `cancel` flows.
- [x] Add per-device total timeout handling and explicit timeout error categories.
- [x] Normalize connection/command failures into structured status codes.
- [x] Ensure `pre_output`, `apply_output`, `post_output`, and `diff` are always populated consistently.
- [x] Add diff truncation limits and response metadata for large outputs.
- [ ] Split `frontend_v2` into dedicated pages (Import, Create, Monitor, History, Detail).
- [ ] Replace ad-hoc frontend fetch calls with a typed API client.
- [ ] Finalize migration notes and v2 release checklist.
- [ ] Switch default docs/start flow to v2 and mark v1 as deprecated.
