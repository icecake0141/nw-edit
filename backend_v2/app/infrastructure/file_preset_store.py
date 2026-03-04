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
"""JSON file-based execution preset store."""

from __future__ import annotations

import json
import uuid
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional

from backend_v2.app.application.events import utc_now
from backend_v2.app.domain.models import ExecutionPreset


class PresetConflictError(ValueError):
    """Raised when preset uniqueness constraints are violated."""


class FilePresetStore:
    """Thread-safe preset store persisted in a local JSON file."""

    def __init__(self, path: str) -> None:
        self._lock = Lock()
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        if not self._path.exists():
            self._write_items([])

    def list_presets(self, os_model: Optional[str] = None) -> List[ExecutionPreset]:
        with self._lock:
            items = self._read_items()
        presets = [self._from_item(item) for item in items]
        if os_model is None:
            return presets
        return [preset for preset in presets if preset.os_model == os_model]

    def list_os_models(self) -> List[str]:
        with self._lock:
            items = self._read_items()
        models = sorted(
            {str(item.get("os_model", "")) for item in items if item.get("os_model")}
        )
        return models

    def create(
        self,
        name: str,
        os_model: str,
        commands: List[str],
        verify_commands: List[str],
    ) -> ExecutionPreset:
        with self._lock:
            items = self._read_items()
            self._ensure_unique(items, name=name, os_model=os_model)
            now = utc_now()
            item: Dict[str, Any] = {
                "preset_id": str(uuid.uuid4()),
                "name": name,
                "os_model": os_model,
                "commands": list(commands),
                "verify_commands": list(verify_commands),
                "created_at": now,
                "updated_at": now,
            }
            items.append(item)
            self._write_items(items)
        return self._from_item(item)

    def update(
        self,
        preset_id: str,
        name: str,
        os_model: str,
        commands: List[str],
        verify_commands: List[str],
    ) -> Optional[ExecutionPreset]:
        with self._lock:
            items = self._read_items()
            self._ensure_unique(
                items,
                name=name,
                os_model=os_model,
                exclude_preset_id=preset_id,
            )
            for index, item in enumerate(items):
                if str(item.get("preset_id")) != preset_id:
                    continue
                updated = {
                    **item,
                    "name": name,
                    "os_model": os_model,
                    "commands": list(commands),
                    "verify_commands": list(verify_commands),
                    "updated_at": utc_now(),
                }
                items[index] = updated
                self._write_items(items)
                return self._from_item(updated)
        return None

    def _ensure_unique(
        self,
        items: list[dict[str, object]],
        *,
        name: str,
        os_model: str,
        exclude_preset_id: Optional[str] = None,
    ) -> None:
        for item in items:
            item_id = str(item.get("preset_id", ""))
            if exclude_preset_id and item_id == exclude_preset_id:
                continue
            if (
                str(item.get("name", "")) == name
                and str(item.get("os_model", "")) == os_model
            ):
                raise PresetConflictError(
                    f"Preset already exists for name={name} os_model={os_model}"
                )

    def _read_items(self) -> List[Dict[str, Any]]:
        with self._path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, list):
            return []
        return [item for item in payload if isinstance(item, dict)]

    def _write_items(self, items: List[Dict[str, Any]]) -> None:
        tmp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(items, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        tmp_path.replace(self._path)

    @staticmethod
    def _from_item(item: Dict[str, Any]) -> ExecutionPreset:
        return ExecutionPreset(
            preset_id=str(item.get("preset_id", "")),
            name=str(item.get("name", "")),
            os_model=str(item.get("os_model", "")),
            commands=[str(value) for value in item.get("commands", []) or []],
            verify_commands=[
                str(value) for value in item.get("verify_commands", []) or []
            ],
            created_at=str(item.get("created_at", "")),
            updated_at=str(item.get("updated_at", "")),
        )
