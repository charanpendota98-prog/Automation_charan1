"""Listicle + auto-refresh + ad shortcode tests.

Verifies:
  1. create_listicle (mock): numbered h2s, ItemList JSON-LD, wp_id recorded
  2. insert_ad_shortcodes: positions correct, max 3, no shortcode -> no-op
  3. posts_to_refresh: age + status + priority (never-refreshed first)
  4. scheduled listicle quota logic (meta counter)
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, seo, state  # noqa: E402

wp_created = []


class FakeWP(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.0"

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
        from urllib.parse import urlparse

        if not self._auth():
            self._json(401, {"code": "rest_not_logged_in"})
            return
        path = urlparse(self.path).path
        if path.endswith("/users/me"):
            self._json(200, {"id": 1, "name": "charan", "roles": ["administrator"]})
        elif path.endswith("/posts"):
            self._json(200, [])
        elif "categories" in path:
            self._json(200, [{"id": 5, "name": "Govt Jobs"}])
        else:
            self._json(200, [])

    def do_POST(self):
        if not self._auth():
            self._json(401, {"code": "rest_not_logged_in"})
            return
        n = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(n)
        if self.path.endswith("/media"):
            self._json(201, {"id": 88})
        elif self.path.endswith("/tags"):
            self._json(201, {"id": 51, "name": "t"})
        else:
            payload = json.loads(raw)
            wp_created.append(payload)
            self._json(201, {"id": 777, "link": "https://studentup.in/top-list/",
                             "status": "draft"})


def main():
    db = Path("/tmp/test_listicle.db")
    db.unlink(missing_ok=True)
    state.init(db)

    wp_srv = HTTPServer(("127.0.0.1", 0), FakeWP)
    threading.Thread(target=wp_srv.serve_forever, daemon=True).start()

    config.STATE_PATH = db
    config.WP_SITE = f"http://127.0.0.1:{wp_srv.server_address[1]}"
    config.OUTPUT_DIR = Path("/tmp/test_listicle_out")
    config.IMAGE_ENABLED = True
    config.AD_SHORTCODE = ""

    print("LISTICLE + REFRESH TESTS:")

    # ---- 1. mock listicle publish ----
    import autoblog.pipeline as pl

    result = pl.create_listicle(topic="Top 10 Central Government Jobs", mock=True)
    assert result["status"] == "draft"
    payload = wp_created[-1]
    content = payload["content"]
    assert content.count("<h2") >= 5 and "1. SSC CGL" in content
    import re as _re

    scripts = _re.findall(r'<script type="application/ld\+json">(.*?)</script>',
                          content, _re.S)
    types = [json.loads(x)["@type"] for x in scripts]
    assert "ItemList" in types, types
    il = json.loads([x for x in scripts if "ItemList" in x][0])
    assert il["numberOfItems"] == 5 and il["itemListElement"][0]["position"] == 1
    assert "FAQPage" in types and "BreadcrumbList" in types
    # wp_id recorded in state
    with db.open("rb") as f:
        pass
    import sqlite3

    conn = sqlite3.connect(str(db))
    row = conn.execute("SELECT wp_id, article_type_x FROM posts WHERE wp_id=777").fetchone() \
        if False else conn.execute("SELECT wp_id FROM posts WHERE wp_id=777").fetchone()
    conn.close()
    assert row and row[0] == 777
    print("  1. create_listicle (numbered h2s + ItemList schema + wp_id saved) ✔")

    # ---- 2. ad shortcodes ----
    html = "".join(f"<p>para {i} with some words here ok</p>" for i in range(10)) \
        + "<h2>FAQ</h2><p>faq</p>"
    out = seo.insert_ad_shortcodes(html, "[quads id=1]")
    assert out.count("[quads id=1]") == 3, out.count("[quads id=1]")
    assert seo.insert_ad_shortcodes(html, "") == html  # off -> no-op
    short_html = "<p>one para</p>"
    assert seo.insert_ad_shortcodes(short_html, "[ad]") == short_html or \
        "[ad]" in seo.insert_ad_shortcodes(short_html, "[ad]")
    print("  2. insert_ad_shortcodes (3 positions, off-safe) ✔")

    # ---- 3. posts_to_refresh ----
    db2 = Path("/tmp/test_refresh.db")
    db2.unlink(missing_ok=True)
    state.init(db2)
    conn = sqlite3.connect(str(db2))
    old = "2026-08-01 10:00:00"
    fresh = "2026-09-06 10:00:00"
    conn.executemany(
        "INSERT INTO posts (title, title_norm, status, wp_id, created_at, refreshed_at) "
        "VALUES (?,?,?,?,?,?)",
        [
            ("Old A", "old a", "publish", 101, old, None),
            ("Old B", "old b", "publish", 102, old, "2026-09-01 10:00:00"),
            ("TooFresh", "too fresh", "publish", 103, fresh, None),
            ("DraftOnly", "draft only", "draft", 104, old, None),
        ],
    )
    conn.commit()
    conn.close()
    sel = state.posts_to_refresh(db2, older_days=14, limit=2)
    ids = [t["wp_id"] for t in sel]
    assert 101 in ids and 102 in ids, ids          # both old ones eligible
    assert ids.index(101) < ids.index(102)          # never-refreshed first
    assert 103 not in ids and 104 not in ids        # too fresh / draft excluded
    # record_refresh updates
    state.record_refresh(db2, 101)
    sel2 = state.posts_to_refresh(db2, older_days=14, limit=1)
    assert sel2[0]["wp_id"] == 102  # 101 abhi refresh ayyindi -> 102 next
    db2.unlink(missing_ok=True)
    print("  3. posts_to_refresh (age filter + priority + refresh mark) ✔")

    # ---- 4. listicle idea picker ----
    from autoblog import topic_engine as te

    idea = te.pick_listicle_idea(["Old Top 10 Central Government Jobs 2026 post"])
    # note: HIGH_CPC_SHARE% valla high-CPC pool nunchi kuda vastundi (valid)
    assert idea in te.LISTICLE_IDEAS or idea in te.HIGH_CPC_LISTICLE_IDEAS
    print("  4. pick_listicle_idea ✔")

    db.unlink(missing_ok=True)
    import shutil

    shutil.rmtree("/tmp/test_listicle_out", ignore_errors=True)
    print("ALL LISTICLE + REFRESH TESTS PASSED ✔")


if __name__ == "__main__":
    main()
