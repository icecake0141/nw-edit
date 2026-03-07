# Copyright 2026 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# This file was created or modified with the assistance of an AI (Large Language Model).
# Review required for correctness, security, and licensing.

.PHONY: check check-integration typecheck precommit start-v2 verify
PYTHON ?= python3.12

check:
	PYTHON=$(PYTHON) ./scripts/run_v2_checks.sh

check-integration:
	PYTHON=$(PYTHON) RUN_INTEGRATION=1 ./scripts/run_v2_checks.sh

typecheck:
	$(PYTHON) -m mypy --explicit-package-bases backend_v2/app

precommit:
	PRE_COMMIT_HOME=.pre-commit-cache $(PYTHON) -m pre_commit run --all-files

start-v2:
	./start_v2.sh

verify:
	./verify.sh
