"""Local JSON API + static inspector for Truth."""

from __future__ import annotations

import json
import mimetypes
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from truth.inspect.changes import recent_changes
from truth.inspect.graph import build_graph
from truth.inspect.links import note_links
from truth.inspect.tree import build_tree

_STATIC_DIR = Path(__file__).resolve().parent / "static"


class InspectorHandler(BaseHTTPRequestHandler):
    server_version = "TruthInspector/0.1"

    def log_message(self, fmt: str, *args) -> None:
        # ponytail: quiet default access log; use stderr if debugging
        pass

    def _send_json(self, data: object, status: int = 200) -> None:
        body = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        data = path.read_bytes()
        ctype = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        path = parsed.path
        qs = parse_qs(parsed.query)

        try:
            if path == "/api/tree":
                self._send_json(build_tree())
                return
            if path == "/api/graph":
                self._send_json(build_graph())
                return
            if path == "/api/changes":
                n = int(qs.get("n", ["20"])[0])
                self._send_json(recent_changes(n))
                return
            if path == "/api/links":
                rel = qs.get("path", [""])[0]
                if not rel:
                    self._send_json({"error": "missing path query param"}, status=400)
                    return
                self._send_json(note_links(rel))
                return
            if path in ("/", "/inspector.html"):
                self._send_file(_STATIC_DIR / "inspector.html")
                return
            self.send_error(404)
        except ValueError as exc:
            self._send_json({"error": str(exc)}, status=400)


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    # ponytail: stdlib only; Phase 5 may unify with watcher/indexer serve
    httpd = ThreadingHTTPServer((host, port), InspectorHandler)
    print(f"Truth inspector at http://{host}:{port}/inspector.html", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.", flush=True)
    finally:
        httpd.server_close()


if __name__ == "__main__":
    run_server()
