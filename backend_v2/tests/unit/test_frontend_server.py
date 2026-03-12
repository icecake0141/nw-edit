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
"""Unit tests for the hardened frontend server."""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import Thread
from typing import Iterator
from urllib.error import HTTPError
from urllib.request import urlopen

from backend_v2.app.frontend_server import build_server


@contextmanager
def run_server(public_dir: Path) -> Iterator[str]:
    """Start a local frontend server bound to an ephemeral port."""
    server = build_server(host="127.0.0.1", port=0, directory=public_dir)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        host, port = server.server_address
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_root_path_serves_index_with_security_headers(tmp_path: Path):
    (tmp_path / "index.html").write_text(
        "<!doctype html><title>ok</title>", encoding="utf-8"
    )

    with run_server(tmp_path) as base_url:
        with urlopen(f"{base_url}/") as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
            assert body == "<!doctype html><title>ok</title>"
            assert response.headers["Content-Security-Policy"].startswith(
                "default-src 'self'"
            )
            assert response.headers["X-Content-Type-Options"] == "nosniff"
            assert response.headers["Referrer-Policy"] == "no-referrer"
            assert response.headers["X-Frame-Options"] == "DENY"
            assert response.headers["Cross-Origin-Opener-Policy"] == "same-origin"


def test_static_asset_preserves_javascript_content_type(tmp_path: Path):
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('ok');", encoding="utf-8")

    with run_server(tmp_path) as base_url:
        with urlopen(f"{base_url}/app.js") as response:
            assert response.status == 200
            assert response.headers["Content-Type"].startswith("application/javascript")


def test_unknown_paths_return_404(tmp_path: Path):
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")

    with run_server(tmp_path) as base_url:
        try:
            urlopen(f"{base_url}/missing.txt")
        except HTTPError as exc:
            assert exc.code == 404
        else:
            raise AssertionError("Expected 404 for unknown asset path")


def test_directory_requests_do_not_expose_listing(tmp_path: Path):
    (tmp_path / "index.html").write_text("ok", encoding="utf-8")
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "secret.txt").write_text("hidden", encoding="utf-8")

    with run_server(tmp_path) as base_url:
        try:
            urlopen(f"{base_url}/nested/")
        except HTTPError as exc:
            body = exc.read().decode("utf-8")
            assert exc.code == 404
            assert "Directory listing" not in body
            assert "secret.txt" not in body
        else:
            raise AssertionError("Expected 404 for directory path")
