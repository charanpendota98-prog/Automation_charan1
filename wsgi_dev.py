#!/usr/bin/env python3
"""Dev runner: exam portal as a WSGI app on :8090 (same app MilesWeb/cPanel serves).

Local preview:  http://localhost:8090/         (landing)
                http://localhost:8090/healthz
Lead form API:  POST http://localhost:8090/lead

Production (MilesWeb cPanel) uses passenger_wsgi.py — this file is ONLY for the
sandbox/dev preview so the website's poll + lead forms have something to talk to.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from wsgiref.simple_server import make_server          # noqa: E402

from exam_portal.wsgi import make_app                  # noqa: E402

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8090


def main() -> int:
    app = make_app()
    server = make_server("0.0.0.0", PORT, app)
    print(f"exam portal (WSGI) → http://0.0.0.0:{PORT}  ·  db={app.db_path}", flush=True)
    server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
