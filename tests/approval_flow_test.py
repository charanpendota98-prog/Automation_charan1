"""End-to-end test of the notification + approval flow.

Fakes: Telegram Bot API server + WordPress REST server.
Verifies:
  1. Draft notification has Publish/Delete inline buttons
  2. Tap "Publish" (callback) -> WP post status becomes publish,
     Telegram message edited to "PUBLISHED"
  3. Foreign chat id is rejected
  4. WhatsApp CallMeBot alert URL is called
"""

import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import config, notifier, state  # noqa: E402
from autoblog.approval_bot import ApprovalBot  # noqa: E402
from autoblog.wordpress_client import WordPressClient  # noqa: E402

tg_calls = {"sendMessage": [], "editMessageText": [], "answerCallbackQuery": []}
wp_calls = {"publish": [], "trash": []}
wa_calls = []


class FakeTelegram(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _ok(self, obj=None):
        body = json.dumps({"ok": True, "result": obj or {}}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        method = self.path.rsplit("/", 1)[-1].split("?")[0]
        if method in tg_calls:
            tg_calls[method].append(payload)
        self._ok()


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

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        payload = json.loads(self.rfile.read(n) or b"{}")
        if "/posts/" in self.path:
            post_id = int(self.path.rstrip("/").rsplit("/", 1)[-1])
            if payload.get("status") == "publish":
                wp_calls["publish"].append((post_id, payload))
                self._json(200, {"id": post_id, "status": "publish",
                                 "link": "https://studentup.in/test-draft/",
                                 "title": {"rendered": "Test Draft Post"}})
            elif payload.get("status") == "trash":
                wp_calls["trash"].append((post_id, payload))
                self._json(200, {"id": post_id, "status": "trash"})
            else:
                self._json(400, {"code": "bad"})


class FakeWhatsApp(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        qs = parse_qs(urlparse(self.path).query)
        wa_calls.append(qs.get("text", [""])[0])
        self.send_response(200)
        self.send_header("Content-Length", "2")
        self.end_headers()
        self.wfile.write(b"OK")


def main():
    db = Path("/tmp/test_approval.db")
    db.unlink(missing_ok=True)
    state.init(db)
    config.STATE_PATH = db

    tg = HTTPServer(("127.0.0.1", 0), FakeTelegram)
    wp = HTTPServer(("127.0.0.1", 0), FakeWP)
    wa = HTTPServer(("127.0.0.1", 0), FakeWhatsApp)
    for srv in (tg, wp, wa):
        threading.Thread(target=srv.serve_forever, daemon=True).start()

    config.TELEGRAM_BOT_TOKEN = "TESTTOKEN"
    config.TELEGRAM_CHAT_ID = "555"
    config.TELEGRAM_API_BASE = f"http://127.0.0.1:{tg.server_address[1]}"
    config.WP_SITE = f"http://127.0.0.1:{wp.server_address[1]}"
    config.WHATSAPP_CALLMEBOT_URL = (
        f"http://127.0.0.1:{wa.server_address[1]}/whatsapp.php?phone=+91123&apikey=k"
    )

    # ---- 1) draft notification with buttons ----
    article = {
        "title": "SSC <New> 2026 – Test టైటిల్",
        "category": "Govt Jobs",
        "tags": ["ssc", "jobs"],
        "meta_description": "Test description",
    }
    result = {"id": 123, "status": "draft", "link": "https://studentup.in/?p=123"}
    notifier.notify_new_post(article, result)

    assert len(tg_calls["sendMessage"]) == 1, tg_calls["sendMessage"]
    sent = tg_calls["sendMessage"][0]
    assert sent["chat_id"] == "555"
    assert "SSC &lt;New&gt; 2026" in sent["text"], sent["text"]
    kb = sent["reply_markup"]["inline_keyboard"]
    assert kb[0][0]["callback_data"] == "pub:123"
    assert kb[0][1]["callback_data"] == "del:123"
    assert kb[1][0]["url"].endswith("/wp-admin/post.php?post=123&action=edit")

    assert len(wa_calls) == 1 and "Test" in wa_calls[0], wa_calls

    # ---- 2) approval bot: tap Publish ----
    bot = ApprovalBot()
    bot.tg_base = f"http://127.0.0.1:{tg.server_address[1]}/botTESTTOKEN"
    bot.wp = WordPressClient(site=config.WP_SITE, username="u", password="p a")
    # register owner chat
    state.meta_set(db, "telegram_chat_id", "555")

    callback = {
        "id": "cb1",
        "message": {"message_id": 42, "chat": {"id": 555}},
        "data": "pub:123",
    }
    bot.on_callback(callback)

    assert wp_calls["publish"] == [(123, {"status": "publish"})], wp_calls
    assert len(tg_calls["editMessageText"]) == 1
    edited = tg_calls["editMessageText"][0]
    assert "PUBLISHED" in edited["text"] and "test-draft" in edited["text"], edited
    assert len(tg_calls["answerCallbackQuery"]) == 1

    # ---- 3) foreign chat rejected ----
    foreign = {
        "id": "cb2",
        "message": {"message_id": 43, "chat": {"id": 999}},
        "data": "pub:123",
    }
    bot.on_callback(foreign)
    assert wp_calls["publish"] == [(123, {"status": "publish"})]  # no new publish
    rejected = tg_calls["answerCallbackQuery"][-1]
    assert "Access" in rejected["text"]

    # ---- 4) delete flow ----
    bot.on_callback({"id": "cb3",
                     "message": {"message_id": 44, "chat": {"id": 555}},
                     "data": "del:123"})
    assert wp_calls["trash"] == [(123, {"status": "trash"})]

    # ---- 5) /start registers owner when nothing configured ----
    config.TELEGRAM_CHAT_ID = ""
    state.meta_set(db, "telegram_chat_id", "")
    bot.on_message({"chat": {"id": 777}, "text": "/start"})
    assert state.meta_get(db, "telegram_chat_id") == "777"
    assert "Namaskaram" in tg_calls["sendMessage"][-1]["text"]

    db.unlink(missing_ok=True)
    print("ALL NOTIFICATION + APPROVAL TESTS PASSED ✔")
    print("  - draft buttons (pub:123 / del:123) ✔")
    print("  - one-tap publish -> WP live ✔")
    print("  - foreign chat blocked ✔")
    print("  - delete -> trash ✔")
    print("  - /start auto-registration ✔")
    print("  - WhatsApp alert sent ✔")


if __name__ == "__main__":
    main()
