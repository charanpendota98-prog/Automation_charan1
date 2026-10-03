#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Local demo server for the WorldClass v2 preview (v191).

Enduku: Arena live-preview (e2b proxy) ni phone / laptop lo open chesinappudu
nerugaa kotha design kanipinchali. Ee server repo root ni serve chestundi kaani
"/" ni preview/worldclass/index.html ki redirect chestundi — so CSS paths
(../../wordpress-theme/...) break avvavu.

v191.1 fix: HTTP/1.1 + Content-Length + no-store — reverse proxy/Cloudflare
vaddu "502 bad gateway" raakunda (HTTP/1.0 responses tho keep-alive break ayyi
proxy error icchedi).

Usage:  python3 tools/preview_server.py [port]     (default 8123)
"""
from __future__ import annotations

import os
import sys
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEMO = "/preview/worldclass/index.html"


class DemoHandler(SimpleHTTPRequestHandler):
    """Repo root serve + "/" → demo page redirect. HTTP/1.1 (proxy-safe)."""

    protocol_version = "HTTP/1.1"          # keep-alive + Content-Length aware
    server_version = "StudentUpPreview/1.1"

    def end_headers(self):
        # proxy/browser cache valla purathana page kanipinchakunda
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Preview", "worldclass-v2")
        super().end_headers()

    def do_GET(self):  # noqa: N802 - stdlib naming
        if self.path in ("/", "/index.html"):
            self.send_response(302)
            self.send_header("Location", DEMO)
            self.send_header("Content-Length", "0")
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, fmt, *args):  # quiet-ish, but keep errors visible
        status = str(args[1]) if len(args) > 1 else ""
        if status not in ("200", "302", "304"):
            sys.stderr.write("preview %s\n" % (fmt % args))


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8123
    handler = partial(DemoHandler, directory=ROOT)
    httpd = ThreadingHTTPServer(("0.0.0.0", port), handler)
    httpd.daemon_threads = True
    print("StudentUp preview → http://0.0.0.0:%d%s" % (port, DEMO), flush=True)
    httpd.serve_forever()
