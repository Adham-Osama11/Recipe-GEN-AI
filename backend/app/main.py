from __future__ import annotations

import json
import mimetypes
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Lock
from urllib.parse import urlparse

from app.config import get_settings
from app.routes.generate import handle_generate_request
from app.services.orchestrator import get_orchestrator


class RecipeHTTPRequestHandler(BaseHTTPRequestHandler):
    server_version = "RecipeHTTP/1.0"
    settings = get_settings()
    orchestrator = None
    orchestrator_lock = Lock()
    frontend_root = Path(__file__).resolve().parents[2] / "frontend"

    @classmethod
    def _get_orchestrator(cls):
        if cls.orchestrator is None:
            with cls.orchestrator_lock:
                if cls.orchestrator is None:
                    cls.orchestrator = get_orchestrator()
        return cls.orchestrator

    def do_OPTIONS(self) -> None:  # noqa: N802
        self.send_response(HTTPStatus.NO_CONTENT)
        self._add_cors_headers()
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:  # noqa: N802
        parsed_path = urlparse(self.path)
        path = parsed_path.path

        if path == "/health":
            self._send_json(HTTPStatus.OK, {"status": "ok"})
            return

        self._serve_static(path)

    def do_POST(self) -> None:  # noqa: N802
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        generate_paths = {"/generate", f"{self.settings.api_prefix}/generate"}

        if path not in generate_paths:
            self._send_json(HTTPStatus.NOT_FOUND, {"detail": "Not found"})
            return

        payload, error = self._read_json_body()
        if error is not None:
            self._send_json(HTTPStatus.BAD_REQUEST, {"detail": error})
            return

        try:
            orchestrator = self._get_orchestrator()
        except Exception as exc:
            self._send_json(
                HTTPStatus.SERVICE_UNAVAILABLE,
                {
                    "detail": "Model is not configured. Set GROQ_API_KEY and restart the service.",
                    "error": str(exc),
                },
            )
            return

        status_code, response_data = handle_generate_request(
            payload_data=payload,
            orchestrator=orchestrator,
        )
        self._send_json(status_code, response_data)

    def _read_json_body(self) -> tuple[dict, str | None]:
        raw_length = self.headers.get("Content-Length", "0").strip()
        if not raw_length:
            return {}, None

        try:
            content_length = int(raw_length)
        except ValueError:
            return {}, "Invalid Content-Length header"

        body = self.rfile.read(content_length)
        if not body:
            return {}, None

        try:
            payload = json.loads(body.decode("utf-8"))
            if not isinstance(payload, dict):
                return {}, "JSON body must be an object"
            return payload, None
        except json.JSONDecodeError:
            return {}, "Invalid JSON body"

    def _send_json(self, status_code: int, payload: dict) -> None:
        encoded = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self._add_cors_headers()
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _add_cors_headers(self) -> None:
        request_origin = self.headers.get("Origin", "")
        allowed_origins = self.settings.cors_origins

        if "*" in allowed_origins:
            allow_origin = "*"
        elif request_origin and request_origin in allowed_origins:
            allow_origin = request_origin
        elif allowed_origins:
            allow_origin = allowed_origins[0]
        else:
            allow_origin = "*"

        self.send_header("Access-Control-Allow-Origin", allow_origin)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def _serve_static(self, request_path: str) -> None:
        normalized_path = request_path or "/"
        if normalized_path == "/":
            target = self.frontend_root / "index.html"
        else:
            target = (self.frontend_root / normalized_path.lstrip("/")).resolve()

        frontend_root_resolved = self.frontend_root.resolve()
        try:
            target.relative_to(frontend_root_resolved)
        except ValueError:
            self._send_json(HTTPStatus.NOT_FOUND, {"detail": "Not found"})
            return

        if not target.exists() or not target.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"detail": "Not found"})
            return

        mime_type, _ = mimetypes.guess_type(str(target))
        content = target.read_bytes()

        self.send_response(HTTPStatus.OK)
        self._add_cors_headers()
        self.send_header("Content-Type", f"{mime_type or 'application/octet-stream'}")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def create_server(host: str, port: int) -> ThreadingHTTPServer:
    return ThreadingHTTPServer((host, port), RecipeHTTPRequestHandler)


def run() -> None:
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    server = create_server(host, port)
    print(f"Serving AI Recipe Generator on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
