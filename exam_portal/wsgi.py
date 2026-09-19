# -*- coding: utf-8 -*-
"""v49 — WSGI entry point for the exam portal.

Why: shared cPanel hosting (MilesWeb / Hostinger / Namecheap …) can serve a
Python app only through "Setup Python App" (Passenger + WSGI). Our normal
runner (`python run.py --exam-portal-demo`) needs a long-lived process, which
shared hosting does not give. This module exposes the exact same portal as a
WSGI application, reusing every route of `exam_portal.server.Handler` — no
duplicate logic, no behaviour drift.

cPanel setup (5 steps):
  1. cPanel → Setup Python App → Create Application
        Python version : 3.9+ (3.11 recommended)
        Application root  : examportal          (folder inside home)
        Application URL   : yourdomain.in/exam  (URI: exam)
        Startup file      : passenger_wsgi.py
  2. Commit/copy this repo's `exam_portal/` + `passenger_wsgi.py` into that root.
  3. In cPanel's "Environment variables" add:
        EXAM_DB=/home/<user>/examportal/exam_portal.db
        EXAM_ADMIN_KEY=<mee secret key>
  4. pip install -r requirements.txt  (the app venv; only stdlib is strictly needed)
  5. Restart the app → open https://yourdomain.in/exam/admin

Locally you can test it like any WSGI app:
    from exam_portal.wsgi import application
"""
from __future__ import annotations

import io
import os
import sys
from email.message import Message
from http.client import responses as HTTP_REASONS
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:  # cPanel runs from the app root, not the repo root
    sys.path.insert(0, str(ROOT))

from exam_portal.server import Handler, Api                    # noqa: E402
from exam_portal.store import Store                            # noqa: E402

__all__ = ["application", "app", "make_app"]


class _WSGIResponse:
    """Captures what Handler._send would have written to a socket."""

    def __init__(self) -> None:
        self.status: int = 200
        self.headers: List[Tuple[str, str]] = []
        self.body: bytes = b""


class WSGIHandler(Handler):
    """Same routes as the HTTP server, but writing into a WSGI response.

    `BaseHTTPRequestHandler.__init__` is deliberately skipped: there is no
    socket here. Only the attributes the routes actually touch are set.
    """

    def __init__(self, environ: Dict[str, Any]) -> None:
        self.environ = environ
        self.resp = _WSGIResponse()
        self.command = str(environ.get("REQUEST_METHOD") or "GET").upper()
        self.path = self._full_path(environ)
        self.client_address = (str(environ.get("REMOTE_ADDR") or "127.0.0.1"), 0)
        self.headers = self._headers_from(environ)
        self.rfile = io.BytesIO(self._read_body(environ))
        self.request_version = "HTTP/1.1"
        self.server_version = "ExamPortal-WSGI/1.0"
        self.close_connection = True

    # ------------------------------------------------------------- helpers
    @staticmethod
    def _full_path(environ: Dict[str, Any]) -> str:
        path = str(environ.get("PATH_INFO") or "/")
        script = str(environ.get("SCRIPT_NAME") or "")
        req_uri = str(environ.get("REQUEST_URI") or "")
        # cPanel/Passenger sometimes leaves PATH_INFO empty or relative —
        # rebuild it from REQUEST_URI (same fix MilesWeb's Django guide uses).
        if (not path.startswith("/") or (script and not path.startswith(script))) and req_uri:
            path = req_uri.split("?", 1)[0]
        if script and path.startswith(script):
            path = path[len(script):] or "/"
        qs = str(environ.get("QUERY_STRING") or "")
        return path + ("?" + qs if qs else "")

    @staticmethod
    def _headers_from(environ: Dict[str, Any]) -> Message:
        msg = Message()
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                name = key[5:].replace("_", "-").title()
                msg[name] = str(value)
        if environ.get("CONTENT_TYPE"):
            msg["Content-Type"] = str(environ["CONTENT_TYPE"])
        if environ.get("CONTENT_LENGTH"):
            msg["Content-Length"] = str(environ["CONTENT_LENGTH"])  # POST body size
        return msg

    @staticmethod
    def _read_body(environ: Dict[str, Any]) -> bytes:
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            length = 0
        stream = environ.get("wsgi.input")
        if not stream or length <= 0:
            return b""
        return stream.read(length) or b""

    # ------------------------------------------------------------ responses
    def _send(self, status: int, body: bytes, content_type: str,
              extra: Optional[Dict[str, str]] = None) -> None:  # type: ignore[override]
        self.resp.status = status
        headers = [("Content-Type", content_type),
                   ("Content-Length", str(len(body))),
                   ("X-Content-Type-Options", "nosniff")]
        for k, v in (extra or {}).items():
            headers.append((str(k), str(v)))
        self.resp.headers = headers
        self.resp.body = b"" if self.command == "HEAD" else body

    def send_response(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover
        return  # never called: _send() is fully overridden

    def address_string(self) -> str:  # noqa: D401 - quieter logs
        return self.client_address[0]

    def log_message(self, fmt: str, *args: Any) -> None:
        return


def _dispatch(environ: Dict[str, Any], store: Store, api: Api) -> WSGIHandler:
    handler = WSGIHandler(environ)
    handler.api = api
    handler.store = store
    method = handler.command
    if method == "OPTIONS":
        handler.do_OPTIONS()
    elif method in ("GET", "HEAD"):
        handler.do_GET()
    elif method == "POST":
        handler.do_POST()
    else:
        handler.json_out({"error": "Method support ledu", "method": method}, 405)
    return handler


def _status_line(code: int) -> str:
    return "%d %s" % (code, HTTP_REASONS.get(int(code), "OK"))


def make_app(db_path: Optional[str] = None, admin_key: Optional[str] = None
             ) -> Callable[..., Iterable[bytes]]:
    """Build a WSGI app bound to one Store/Api (created once per process)."""
    db = db_path or os.environ.get("EXAM_DB") or str(ROOT / "exam_portal.db")
    Path(db).parent.mkdir(parents=True, exist_ok=True)
    store = Store(db)
    store.init()
    key = admin_key or os.environ.get("EXAM_ADMIN_KEY") or ""
    api = Api(store, key) if key else Api(store, _key_from_file() or "")

    def app(environ: Dict[str, Any],
            start_response: Callable[[str, List[Tuple[str, str]]], Any]
            ) -> Iterable[bytes]:
        handler = _dispatch(environ, store, api)
        start_response(_status_line(handler.resp.status), handler.resp.headers)
        return [handler.resp.body]

    app.store = store        # type: ignore[attr-defined]
    app.api = api            # type: ignore[attr-defined]
    app.db_path = db         # type: ignore[attr-defined]
    return app


def _key_from_file() -> str:
    f = ROOT / "exam_portal_admin_key.txt"
    try:
        return f.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


# cPanel/Passenger looks for `application`
application = make_app()
app = application
