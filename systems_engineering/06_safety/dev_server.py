#!/usr/bin/env python3
"""
OSR Safety Dashboard — Dev Server
===================================
Lightweight HTTP server (stdlib only) that serves the safety dashboard and
model viewer HTML files and exposes endpoints to regenerate them in-place
with configurable sweep parameters.

Usage
-----
    cd systems_engineering/06_safety
    python3 dev_server.py

Then open:
    http://localhost:8765/safety_report.html
    http://localhost:8765/model_viewer.html

Endpoints
---------
    GET  /ping                              → {"ok": true}
    GET  /safety_report.html               → serve the dashboard HTML
    GET  /model_viewer.html                → serve the model viewer HTML
    POST /regen/safety?n=300&method=lhs&seed=42
                                           → regenerate safety_report.html
    POST /regen/model                      → regenerate model_viewer.html

All responses include CORS headers so the HTML files can call the server
even when opened from file://.
"""

from __future__ import annotations

import http.server
import json
import socketserver
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

PORT       = 8765
SAFETY_DIR = Path(__file__).resolve().parent
MODEL_DIR  = SAFETY_DIR.parent / "MBSE_workspace"


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class _Handler(http.server.BaseHTTPRequestHandler):

    # ── CORS preflight ──────────────────────────────────────────────────────
    def do_OPTIONS(self):
        self.send_response(204)
        self._cors()
        self.end_headers()

    # ── GET ─────────────────────────────────────────────────────────────────
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path.lstrip("/")

        if path in ("", "ping"):
            self._json({"ok": True})
            return

        if path == "safety_report.html":
            self._serve_file(SAFETY_DIR / "safety_report.html", "text/html; charset=utf-8")
            return

        if path == "model_viewer.html":
            self._serve_file(MODEL_DIR / "model_viewer.html", "text/html; charset=utf-8")
            return

        self._json({"ok": False, "error": f"unknown path: {path}"}, status=404)

    # ── POST ────────────────────────────────────────────────────────────────
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path   = parsed.path

        if path == "/regen/safety":
            qs     = urllib.parse.parse_qs(parsed.query)
            n      = int(qs.get("n",      ["300"])[0])
            method = str(qs.get("method", ["lhs"])[0])
            seed   = int(qs.get("seed",   ["42"])[0])

            # Validate method
            if method not in ("lhs", "montecarlo", "grid"):
                method = "lhs"

            cmd = [
                sys.executable,
                str(SAFETY_DIR / "generate_safety_report.py"),
                "--sweep-n",      str(n),
                "--sweep-method", method,
                "--sweep-seed",   str(seed),
            ]
            self._run_cmd(cmd, cwd=SAFETY_DIR)
            return

        if path == "/regen/model":
            cmd = [sys.executable, str(MODEL_DIR / "generate_model_viewer.py")]
            self._run_cmd(cmd, cwd=MODEL_DIR)
            return

        self._json({"ok": False, "error": f"unknown path: {path}"}, status=404)

    # ── Helpers ─────────────────────────────────────────────────────────────
    def _run_cmd(self, cmd: list[str], cwd: Path):
        t0 = time.monotonic()
        try:
            proc = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(cwd),
            )
            elapsed = round(time.monotonic() - t0, 2)
            ok      = proc.returncode == 0
            self._json({
                "ok":       ok,
                "elapsed_s": elapsed,
                "stdout":   proc.stdout[-4000:],
                "stderr":   proc.stderr[-2000:],
            }, status=200 if ok else 500)
        except Exception as exc:
            self._json({"ok": False, "error": str(exc)}, status=500)

    def _json(self, data: dict, status: int = 200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type",  "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _serve_file(self, file_path: Path, content_type: str):
        if not file_path.exists():
            self._json({"ok": False, "error": f"file not found: {file_path.name}"}, status=404)
            return
        body = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type",  content_type)
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def _cors(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def log_message(self, fmt, *args):  # compact logging
        print(f"  [{self.address_string()}]  {fmt % args}")


class _Server(socketserver.TCPServer):
    allow_reuse_address = True


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    print(f"OSR Dev Server")
    print(f"  Safety Dashboard : http://localhost:{PORT}/safety_report.html")
    print(f"  Model Viewer     : http://localhost:{PORT}/model_viewer.html")
    print(f"  Regen safety     : POST /regen/safety?n=300&method=lhs&seed=42")
    print(f"  Regen model      : POST /regen/model")
    print(f"  Press Ctrl-C to stop.\n")

    with _Server(("", PORT), _Handler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nStopped.")


if __name__ == "__main__":
    main()
