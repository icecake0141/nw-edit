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
"""Hardened static server for frontend_v2."""

from __future__ import annotations

from io import BytesIO
import argparse
import functools
import mimetypes
import os
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, BinaryIO, Final
from urllib.parse import unquote, urlsplit

DEFAULT_FRONTEND_HOST: Final[str] = "127.0.0.1"
DEFAULT_FRONTEND_PORT: Final[int] = 3010
DEFAULT_PUBLIC_DIR: Final[Path] = (
    Path(__file__).resolve().parents[2] / "frontend_v2" / "public"
)
CSP_POLICY: Final[str] = (
    "default-src 'self'; "
    "style-src 'self' 'unsafe-inline'; "
    "connect-src 'self' http://127.0.0.1:8010 ws://127.0.0.1:8010; "
    "img-src 'self' data:; "
    "font-src 'self'; "
    "object-src 'none'; "
    "base-uri 'self'; "
    "frame-ancestors 'none'; "
    "form-action 'self'"
)

mimetypes.add_type("application/javascript", ".js")


def _resolve_public_dir(raw_path: str | os.PathLike[str]) -> Path:
    public_dir = Path(raw_path).resolve()
    if not public_dir.is_dir():
        raise ValueError(f"Frontend public directory does not exist: {public_dir}")
    return public_dir


class HardenedStaticHandler(SimpleHTTPRequestHandler):
    """Static handler that disables directory listing and adds security headers."""

    server_version = "nw-edit-frontend/1.0"

    def __init__(self, *args: Any, directory: str, **kwargs: Any) -> None:
        self._root = _resolve_public_dir(directory)
        super().__init__(*args, directory=str(self._root), **kwargs)

    def translate_path(self, path: str) -> str:
        request_path = unquote(urlsplit(path).path)
        relative = request_path.lstrip("/")
        if not relative:
            candidate = self._root / "index.html"
        else:
            candidate = (self._root / relative).resolve()
            try:
                candidate.relative_to(self._root)
            except ValueError:
                return str(self._root / "__forbidden__")
        return str(candidate)

    def list_directory(self, path: str | os.PathLike[str]) -> None:
        self.send_error(HTTPStatus.NOT_FOUND, "File not found")
        return None

    def send_head(self) -> BytesIO | BinaryIO | None:
        request_path = unquote(urlsplit(self.path).path)
        if request_path in {"", "/"}:
            self.path = "/index.html"
            return super().send_head()

        candidate = Path(self.translate_path(request_path))
        if candidate.is_dir():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        if not candidate.exists():
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        return super().send_head()

    def end_headers(self) -> None:
        self.send_header("Content-Security-Policy", CSP_POLICY)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        super().end_headers()


def build_server(
    host: str = DEFAULT_FRONTEND_HOST,
    port: int = DEFAULT_FRONTEND_PORT,
    directory: str | os.PathLike[str] = DEFAULT_PUBLIC_DIR,
) -> ThreadingHTTPServer:
    """Create the hardened frontend server."""
    handler = functools.partial(HardenedStaticHandler, directory=str(directory))
    return ThreadingHTTPServer((host, port), handler)


def main() -> None:
    """Run the hardened frontend server."""
    parser = argparse.ArgumentParser(
        description="Serve frontend_v2 with hardened defaults"
    )
    parser.add_argument(
        "--host", default=os.getenv("NW_EDIT_V2_FRONTEND_HOST", DEFAULT_FRONTEND_HOST)
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("NW_EDIT_V2_FRONTEND_PORT", str(DEFAULT_FRONTEND_PORT))),
    )
    parser.add_argument(
        "--directory",
        default=os.getenv("NW_EDIT_V2_FRONTEND_DIR", str(DEFAULT_PUBLIC_DIR)),
    )
    args = parser.parse_args()

    public_dir = _resolve_public_dir(args.directory)
    with build_server(host=args.host, port=args.port, directory=public_dir) as server:
        print(f"[v2] frontend server: http://{args.host}:{args.port} -> {public_dir}")
        server.serve_forever()


if __name__ == "__main__":
    main()
