# Copyright 2026 icecake0141
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# This file was created or modified with the assistance of an AI (Large Language Model).
# Review required for correctness, security, and licensing.
"""Unit tests for execution control store."""

from backend_v2.app.infrastructure.in_memory_control_store import InMemoryControlStore


def test_get_or_create_returns_stable_instance():
    store = InMemoryControlStore()
    a = store.get_or_create("j1")
    b = store.get_or_create("j1")
    c = store.get_or_create("j2")

    assert a is b
    assert a is not c
