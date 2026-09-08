"""Update-flow tests: existing post -> kotha info merge -> same URL update.

Fakes: WP server (get/update post), source site, Telegram.
Verifies:
  1. update_post: WP update payload — same title, NO slug change, fresh SEO
  2. Old helper sections (TOC/schema) not duplicated after re-enhance
  3. Telegram "POST UPDATED" message with update notes + Improve button exists
  4. --update CLI arg parsing
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, notifier, state  # noqa: E402

wp_calls = {"updated": []}
tg_sent = []

EXISTING_CONTENT = (
    '<p>SSC CGL 2026 apply process existing content mundu para.</p>'
    '<h2 id="table-of-contents">విషయ సూచిక (Table of Contents)</h2><ul><li>x</li></ul>'
    "<h2>Eligibility</h2><p>old eligibility info</p>"
    "<h2>How to Apply</h2><ol><li>old step</li></ol>"
    '<script type="application/ld+json">{"@type":"FAQPage"}</script>'
    '<p><em>⏱️ Reading Time: ~5 నిమిషాలు</em></p>'
)


class FakeWP(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _auth(self):
        return self.headers.get("Authorization", "").startswith("Basic ")

    def do_GET(self):
        if not self._auth():
            self._json(401, {"code": "rest_not_logged_in"})
            return
        path = self.path.split("?")[0]
        if path.endswith("/users/me"):
            self._json(200, {"id": 1, "name": "charan", "roles": ["administrator"]})
        elif path.endswith("/posts"):
            self._json(200, [])
        elif "/posts/" in path:
            pid = int(path.rstrip("/").rsplit("/", 1)[-1])
            self._json(200, {
                "id": pid,
                "slug": "ssc-cgl-2026-guide",
                "link": "https://studentup.in/ssc-cgl-2026-guide/",
                "status": "publish",
                "title": {"raw": "SSC CGL 2026 Complete Guide Telugu lo"},
                "content": {"raw": EXISTING_CONTENT},
                "meta": {"rank_math_focus_keyword": "SSC CGL 2026, apply online"},
            })
        else:
            self._json(200, [])

    def do_POST(self):
        if not self._auth():
            self._json(401, {"code": "rest_not_logged_in"})
            return
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        path = self.path.split("?")[0]
        if "/posts/" in path:
            pid = int(path.rstrip("/").rsplit("/", 1)[-1])
            payload = json.loads(raw)
            wp_calls["updated"].append((pid, payload))
            self._json(200, {"id": pid, "status": "publish",
                             "link": "https://studentup.in/ssc-cgl-2026-guide/"})
        else:
            self._json(404, {"code": "rest_no_route"})


class FakeSite(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        html = ("<html><head><title>SSC CGL 2026 New Update</title>"
                '<meta property="og:site_name" content="NewsSite"></head><body>'
                "<article><h1>SSC CGL 2026 New Update</h1>"
                + "".join(f"<p>Tier 2 exam pattern changed and application fee "
                          f"revised details paragraph {i} with enough length.</p>"
                          for i in range(12))
                + "</article></body></html>")
        body = html.encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


class FakeTG(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        tg_sent.append(json.loads(self.rfile.read(n) or b"{}"))
        body = json.dumps({"ok": True, "result": {}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main():
    db = Path("/tmp/test_update.db")
    db.unlink(missing_ok=True)
    state.init(db)

    wp_srv = HTTPServer(("127.0.0.1", 0), FakeWP)
    site = HTTPServer(("127.0.0.1", 0), FakeSite)
    tg_srv = HTTPServer(("127.0.0.1", 0), FakeTG)
    for s in (wp_srv, site, tg_srv):
        threading.Thread(target=s.serve_forever, daemon=True).start()

    config.STATE_PATH = db
    config.WP_SITE = f"http://127.0.0.1:{wp_srv.server_address[1]}"
    config.TELEGRAM_BOT_TOKEN = "TEST"
    config.TELEGRAM_CHAT_ID = "555"
    config.TELEGRAM_API_BASE = f"http://127.0.0.1:{tg_srv.server_address[1]}"
    config.OUTPUT_DIR = Path("/tmp/test_update_out")
    config.IMAGE_ENABLED = True
    config.RESEARCH_ENABLED = False  # mock lo auto-research skip

    print("UPDATE FLOW TESTS:")
    new_url = f"http://127.0.0.1:{site.server_address[1]}/ssc-update"

    import autoblog.pipeline as pl

    result = pl.update_post(555, new_source_urls=[new_url], mock=True)
    assert result["link"] == "https://studentup.in/ssc-cgl-2026-guide/"

    pid, payload = wp_calls["updated"][-1]
    assert pid == 555
    # title preserved, slug NOT in payload (URL safe)
    assert payload["title"] == "SSC CGL 2026 Complete Guide Telugu lo"
    assert "slug" not in payload
    content = payload["content"]
    # fresh SEO sections exactly once (old ones strip + re-add, no duplicates)
    assert content.count("విషయ సూచిక") == 1, content.count("విషయ సూచిక")
    assert content.count("FAQPage") == 1
    assert content.count("Quick Answer") <= 2  # h2 + TOC entry
    assert content.count("About This Article") == 1
    assert "Last Updated" in content
    # Rank Math meta present on update too
    assert payload["meta"]["rank_math_focus_keyword"].startswith("test guide 2026")

    # Telegram updated message
    upd_msgs = [m for m in tg_sent if "POST UPDATED" in m["text"]]
    assert upd_msgs and "ssc-cgl-2026-guide" in upd_msgs[-1]["text"]
    assert "Kotha info" in upd_msgs[-1]["text"] and "QA" in upd_msgs[-1]["text"]
    print("  1. update_post (same URL, fresh SEO, no dup sections, meta, TG) ✔")

    # Improve button on notifications
    buttons = notifier.post_buttons(999, "https://studentup.in/x/")
    flat = [b.get("callback_data") for row in buttons["inline_keyboard"] for b in row]
    assert "pub:999" in flat and "del:999" in flat and "upd:999" in flat
    print("  2. post_buttons Improve (upd:999) ✔")

    # CLI arg parsing
    import subprocess

    r = subprocess.run(
        [str(Path(".venv/bin/python")), "run.py", "--help"],
        capture_output=True, text=True, timeout=60,
    )
    assert "--update" in r.stdout and "--add-source" in r.stdout
    print("  3. CLI --update / --add-source args ✔")

    db.unlink(missing_ok=True)
    import shutil

    shutil.rmtree("/tmp/test_update_out", ignore_errors=True)
    print("ALL UPDATE FLOW TESTS PASSED ✔")


if __name__ == "__main__":
    main()
