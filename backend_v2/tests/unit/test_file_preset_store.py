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
"""Tests for JSON file-backed preset store."""

from pathlib import Path

import pytest

from backend_v2.app.infrastructure.file_preset_store import (
    FilePresetStore,
    PresetConflictError,
)


def test_store_initializes_file(tmp_path: Path):
    path = tmp_path / "presets.json"
    store = FilePresetStore(str(path))
    assert path.exists()
    assert store.list_presets() == []


def test_store_create_update_and_reload(tmp_path: Path):
    path = tmp_path / "presets.json"
    store = FilePresetStore(str(path))
    created = store.create(
        name="base",
        os_model="cisco_ios",
        commands=["show version"],
        verify_commands=["show run"],
    )
    assert created.name == "base"

    updated = store.update(
        preset_id=created.preset_id,
        name="base",
        os_model="cisco_ios",
        commands=["show clock"],
        verify_commands=["show ip interface brief"],
    )
    assert updated is not None
    assert updated.commands == ["show clock"]
    assert updated.verify_commands == ["show ip interface brief"]

    reloaded = FilePresetStore(str(path))
    all_presets = reloaded.list_presets()
    assert len(all_presets) == 1
    assert all_presets[0].commands == ["show clock"]
    assert all_presets[0].verify_commands == ["show ip interface brief"]


def test_store_rejects_duplicate_name_per_os_model(tmp_path: Path):
    path = tmp_path / "presets.json"
    store = FilePresetStore(str(path))
    store.create(
        name="common",
        os_model="cisco_ios",
        commands=["show version"],
        verify_commands=[],
    )
    with pytest.raises(PresetConflictError):
        store.create(
            name="common",
            os_model="cisco_ios",
            commands=["show clock"],
            verify_commands=[],
        )
