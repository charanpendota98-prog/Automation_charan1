"""Telegram approval bot — review drafts & publish with one tap.

Runs 24/7 (systemd service, long-polling). No extra dependencies.

Setup:
  1. Telegram lo @BotFather -> /newbot -> token teesuko -> .env lo
     TELEGRAM_BOT_TOKEN pettandi
  2. Bot ni open chesi /start cheyandi — bot meeku automatic ga
     register avtundi (chat id save chestundi)
  3. Ippudu prathi draft ki buttons tho message vastundi

Commands:
  /start     – bot ni register cheyandi
  /pending   – unreviewed drafts list (publish buttons tho)
  /stats     – poster statistics
"""

import json
import logging
import sys
import time

import requests

from . import config, notifier, state
from .wordpress_client import WordPressClient, WordPressError

log = logging.getLogger("autoblog.approval")

OFFSET_KEY = "tg_offset"
CHAT_KEY = "telegram_chat_id"


class ApprovalBot:
    def __init__(self):
        self.wp = WordPressClient()
        self.tg_base = f"{config.TELEGRAM_API_BASE}/bot{config.TELEGRAM_BOT_TOKEN}"

    # ------------------------------------------------------------- telegram

    def tg(self, method: str, payload: dict) -> dict:
        resp = requests.post(f"{self.tg_base}/{method}", json=payload,
                             timeout=config.HTTP_TIMEOUT)
        data = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
        if not data.get("ok"):
            log.error("Telegram %s failed: %s %s", method, resp.status_code, str(data)[:200])
        return data

    def registered_chat(self) -> str:
        return config.TELEGRAM_CHAT_ID or (state.meta_get(config.STATE_PATH, CHAT_KEY) or "")

    # ------------------------------------------------------------- handlers

    def process_update(self, update: dict) -> None:
        if "callback_query" in update:
            self.on_callback(update["callback_query"])
        elif "message" in update:
            self.on_message(update["message"])

    def on_message(self, msg: dict) -> None:
        chat_id = str(msg.get("chat", {}).get("id", ""))
        text = (msg.get("text") or "").strip()
        if not chat_id:
            return

        registered = self.registered_chat()
        if not registered:
            # first user to talk to the bot becomes the owner
            state.meta_set(config.STATE_PATH, CHAT_KEY, chat_id)
            registered = chat_id
            log.info("Telegram owner registered: %s", chat_id)
        elif chat_id != registered:
            self.tg("sendMessage", {"chat_id": chat_id,
                                    "text": "⚠️ Ee bot already owner ni untundi. Access ledu."})
            return

        if text.startswith("/start"):
            self.tg("sendMessage", {
                "chat_id": chat_id,
                "text": ("👋 Namaskaram! studentup.in Auto-Blogger lo ki welcome!\n\n"
                         "Prathi draft post ki ikkada message vastundi — "
                         "✅ Publish / 🗑️ Delete buttons tho.\n\n"
                         "🔗 VERE SITE URL paste cheyandi — aa article ni 100% "
                         "original ga (no copy) advanced SEO article ga marchi draft "
                         "chestundi!\n\n"
                         "Commands:\n/pending – review avasaram leni drafts\n"
                         "/stats – statistics\n/help – help"),
            })
        elif text.startswith("/pending"):
            self.send_pending(chat_id)
        elif text.startswith("/stats"):
            self.send_stats(chat_id)
        elif text.startswith("/help"):
            self.tg("sendMessage", {
                "chat_id": chat_id,
                "text": ("Commands: /pending, /stats, /help\n\n"
                         "URL paste cheyste → source article ni 100% original "
                         "SEO article ga marchi draft create chestundi "
                         "(✅ Publish button tho approve cheyochu)."),
            })
        elif text.startswith("http://") or text.startswith("https://"):
            self.handle_source_url(chat_id, text)
        else:
            self.tg("sendMessage", {"chat_id": chat_id,
                                    "text": "Ardham kaledu 🤔 — /help try cheyandi."})

    def handle_source_url(self, chat_id: str, url: str) -> None:
        """User pasted URL -> 100% original rewrite -> draft + buttons."""
        from . import pipeline, sources as sources_mod

        url = url.split()[0]  # URL tarvata extra text unte drop
        if not sources_mod.is_valid_source_url(url):
            self.tg("sendMessage", {"chat_id": chat_id,
                                    "text": "⚠️ URL valid kadu — http/https link ivvandi."})
            return
        if state.source_done(config.STATE_PATH, url):
            self.tg("sendMessage", {"chat_id": chat_id,
                                    "text": "ℹ️ Ee URL already process chesayi."})
            return
        self.tg("sendMessage", {
            "chat_id": chat_id,
            "text": ("🌐 Source article teegutunnanu...\n"
                     "🔍 Internet lo same topic research (extra sources)...\n"
                     "✍️ 100% original + MERGE & BEAT: anni sources kante "
                     "complete article + Rank Math 100% SEO\n"
                     "(2-3 nimishalu patinchandi)"),
        })
        try:
            mock = not config.GEMINI_API_KEY
            pipeline.create_from_source(url, mock=mock)
            # draft aite notify_new_post buttons tho message already pampestundi
        except ValueError as exc:
            self.tg("sendMessage", {"chat_id": chat_id,
                                    "text": f"⚠️ {exc}"})
        except Exception as exc:
            log.exception("Source URL processing failed")
            self.tg("sendMessage", {
                "chat_id": chat_id,
                "text": f"❌ Source process cheyaledu: {str(exc)[:200]}",
            })

    def on_callback(self, cb: dict) -> None:
        cb_id = cb.get("id", "")
        chat_id = str(cb.get("message", {}).get("chat", {}).get("id", ""))
        data = cb.get("data", "")
        registered = self.registered_chat()
        if registered and chat_id and chat_id != registered:
            self.tg("answerCallbackQuery", {"callback_query_id": cb_id,
                                            "text": "⚠️ Access ledu!"})
            return

        try:
            action, _, raw_id = data.partition(":")
            post_id = int(raw_id)
        except ValueError:
            self.tg("answerCallbackQuery", {"callback_query_id": cb_id,
                                            "text": "Invalid action"})
            return

        if action == "pub":
            self.do_publish(cb, post_id)
        elif action == "del":
            self.do_delete(cb, post_id)
        else:
            self.tg("answerCallbackQuery", {"callback_query_id": cb_id,
                                            "text": "Unknown action"})

    # ------------------------------------------------------------- actions

    def _wp_post_status(self, post_id: int, status: str) -> dict:
        resp = self.wp._request("POST", f"posts/{post_id}", json={"status": status})
        if resp.status_code not in (200, 201):
            raise WordPressError(f"WP {resp.status_code}: {resp.text[:200]}")
        return resp.json()

    def _finish(self, cb: dict, text: str, answer: str) -> None:
        msg = cb.get("message", {})
        self.tg("editMessageText", {
            "chat_id": msg.get("chat", {}).get("id"),
            "message_id": msg.get("message_id"),
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": "true",
        })
        self.tg("answerCallbackQuery", {"callback_query_id": cb.get("id", ""),
                                        "text": answer})

    def do_publish(self, cb: dict, post_id: int) -> None:
        try:
            data = self._wp_post_status(post_id, "publish")
            link = data.get("link", "")
            title = (data.get("title") or {}).get("rendered", f"post {post_id}")
            log.info("Approved & published post %s: %s", post_id, link)
            self._finish(
                cb,
                f"🚀 <b>PUBLISHED ✔</b>\n\n<b>{notifier.esc(title)}</b>\n🔗 {notifier.esc(link)}",
                "Publish ayyindi! 🚀",
            )
        except WordPressError as exc:
            log.error("Publish failed for %s: %s", post_id, exc)
            self.tg("answerCallbackQuery", {"callback_query_id": cb.get("id", ""),
                                            "text": f"Failed: {str(exc)[:150]}"})

    def do_delete(self, cb: dict, post_id: int) -> None:
        try:
            self._wp_post_status(post_id, "trash")
            log.info("Moved post %s to trash", post_id)
            self._finish(cb, f"🗑️ Draft #{post_id} trash lo pettanu.", "Delete ayyindi 🗑️")
        except WordPressError as exc:
            log.error("Delete failed for %s: %s", post_id, exc)
            self.tg("answerCallbackQuery", {"callback_query_id": cb.get("id", ""),
                                            "text": f"Failed: {str(exc)[:150]}"})

    # ------------------------------------------------------------- commands

    def send_pending(self, chat_id: str) -> None:
        try:
            resp = self.wp._request("GET", "posts",
                                    params={"status": "draft", "per_page": 5,
                                            "orderby": "date", "order": "desc"})
            posts = resp.json() if resp.status_code == 200 else []
        except Exception:
            posts = []
        if not posts:
            self.tg("sendMessage", {"chat_id": chat_id,
                                    "text": "✅ Emi pending drafts ledu — antha clear!"})
            return
        for p in posts:
            pid = p["id"]
            title = (p.get("title") or {}).get("rendered", f"post {pid}")
            self.tg("sendMessage", {
                "chat_id": chat_id,
                "parse_mode": "HTML",
                "text": f"📝 <b>{notifier.esc(title)}</b>",
                "reply_markup": notifier.post_buttons(pid, p.get("link", "")),
            })

    def send_stats(self, chat_id: str) -> None:
        summary = state.status_summary(config.STATE_PATH)
        lines = [f"📊 <b>studentup.in Auto-Blogger</b>", "",
                 f"Total posts: <b>{summary['total']}</b>"]
        for p in summary["last"][:5]:
            lines.append(f"• [{p['status']}] {notifier.esc(p['title'][:60])}")
        self.tg("sendMessage", {"chat_id": chat_id, "parse_mode": "HTML",
                                "text": "\n".join(lines)})

    # ------------------------------------------------------------- polling

    def poll_once(self, timeout: int = 25) -> int:
        offset = state.meta_get(config.STATE_PATH, OFFSET_KEY)
        params = {"timeout": timeout, "allowed_updates": json.dumps(["message", "callback_query"])}
        if offset:
            params["offset"] = offset
        resp = requests.get(f"{self.tg_base}/getUpdates", params=params,
                            timeout=timeout + 15)
        data = resp.json()
        if not data.get("ok"):
            log.error("getUpdates failed: %s", str(data)[:200])
            return 0
        updates = data.get("result", [])
        for upd in updates:
            try:
                self.process_update(upd)
            except Exception:
                log.exception("Error processing update %s", upd.get("update_id"))
            state.meta_set(config.STATE_PATH, OFFSET_KEY, str(upd["update_id"] + 1))
        return len(updates)

    def run(self) -> None:
        log.info("Approval bot started (long-polling Telegram)...")
        if not config.TELEGRAM_BOT_TOKEN:
            log.error("TELEGRAM_BOT_TOKEN ledu — bot start avvalemu.")
            sys.exit(2)
        while True:
            try:
                self.poll_once()
            except requests.RequestException as exc:
                log.warning("Network error: %s — 10s tarvata retry", exc)
                time.sleep(10)
            except Exception:
                log.exception("Unexpected poll error — 30s tarvata retry")
                time.sleep(30)


def main() -> int:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        stream=sys.stdout,
    )
    state.init(config.STATE_PATH)
    bot = ApprovalBot()
    bot.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
