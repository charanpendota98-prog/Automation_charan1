"""End-to-end test of wordpress_client against a fake local WP REST server.

Run:  .venv/bin/python tests/fake_wp_test.py
Verifies: auth headers, category/tag search+create, media upload, post create.
"""

import json
import re
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, state  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402

received = {"auth_ok": False, "post_payload": None, "media_bytes": 0, "media_disp": ""}


class FakeWP(BaseHTTPRequestHandler):
    def log_message(self, *a):  # silence
        pass

    def _json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = urlparse(self.path)
        if not self.headers.get("Authorization", "").startswith("Basic "):
            self._json(401, {"code": "rest_not_logged_in"})
            return
        received["auth_ok"] = True
        qs = parse_qs(p.query)
        if p.path == "/wp-json/wp/v2/users/me":
            self._json(200, {"id": 1, "name": "charan", "roles": ["administrator"]})
        elif p.path == "/wp-json/wp/v2/categories":
            self._json(200, [{"id": 5, "name": "Scholarships"}])
        elif p.path == "/wp-json/wp/v2/tags":
            q = (qs.get("search", [""])[0] or "").lower()
            if q == "scholarships":
                self._json(200, [{"id": 9, "name": "Scholarships"}])
            else:
                self._json(200, [])
        else:
            self._json(404, {"code": "rest_no_route"})

    def do_POST(self):
        if not self.headers.get("Authorization", "").startswith("Basic "):
            self._json(401, {"code": "rest_not_logged_in"})
            return
        p = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        if p.path == "/wp-json/wp/v2/media":
            received["media_bytes"] = len(body)
            received["media_disp"] = self.headers.get("Content-Disposition", "")
            ct = self.headers.get("Content-Type", "")
            assert "multipart/form-data" in ct, f"bad content-type {ct}"
            assert b"\xff\xd8" in body, "jpeg bytes missing from multipart body"
            self._json(201, {"id": 77})
        elif p.path == "/wp-json/wp/v2/tags":
            name = json.loads(body).get("name", "")
            self._json(201, {"id": 30 + len(name), "name": name})
        elif p.path == "/wp-json/wp/v2/categories":
            name = json.loads(body).get("name", "")
            self._json(201, {"id": 40 + len(name), "name": name})
        elif p.path == "/wp-json/wp/v2/posts":
            payload = json.loads(body)
            received["post_payload"] = payload
            self._json(201, {"id": 123, "link": "https://studentup.in/test-post/", "status": "publish"})
        else:
            self._json(404, {"code": "rest_no_route"})


def main():
    server = HTTPServer(("127.0.0.1", 0), FakeWP)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    state.init(Path("/tmp/test_state.db"))
    config.STATE_PATH = Path("/tmp/test_state.db")

    wp = WordPressClient(site=f"http://127.0.0.1:{port}", username="charan", password="abcd efgh ijkl")
    wp.check_connection()

    cat_id = wp.get_or_create_term("Scholarships", "categories")
    assert cat_id == 5, f"category id {cat_id}"
    tag_existing = wp.get_or_create_term("Scholarships", "tags")
    assert tag_existing == 9
    tag_new = wp.get_or_create_term("NewTag", "tags")
    assert tag_new > 0

    # make a tiny fake jpg
    img = Path("/tmp/test_feat.jpg")
    img.write_bytes(b"\xff\xd8" + b"x" * 500)

    media_id = wp.upload_media(img, title="Test", alt_text="alt")
    assert media_id == 77
    assert received["media_bytes"] > 500
    assert "filename=" in received["media_disp"], received["media_disp"]
    assert "attachment" in received["media_disp"], received["media_disp"]

    result = wp.create_post(
        title="తెలుగు Test Post",
        content_html="<p>hello</p>",
        slug="telugu-test-post",
        category_id=cat_id,
        tag_ids=[tag_existing, tag_new],
        excerpt="meta desc",
        media_id=media_id,
    )
    assert result["link"] == "https://studentup.in/test-post/"

    payload = received["post_payload"]
    assert payload["title"] == "తెలుగు Test Post"
    assert payload["slug"] == "telugu-test-post"
    assert payload["categories"] == [5]
    assert payload["tags"] == [9, tag_new]
    assert payload["featured_media"] == 77
    assert payload["status"] == "draft", "default status must be draft (review flow)"
    assert payload["excerpt"]["raw"] == "meta desc"

    server.shutdown()
    print("ALL WP CLIENT TESTS PASSED ✔  (auth, category, tags, media, post)")


if __name__ == "__main__":
    main()
