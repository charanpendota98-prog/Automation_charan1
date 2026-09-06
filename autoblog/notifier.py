"""Notifications: Telegram (with action buttons) + WhatsApp (CallMeBot).

Telegram = full interactive review (Publish/Delete buttons handled by
approval_bot). WhatsApp = text-only alert (no buttons possible).
"""

import html
import logging
from typing import Optional
from urllib.parse import quote

import requests

from . import config

log = logging.getLogger("autoblog.notify")


# ------------------------------------------------------------------ helpers

def _tg_api(token: str, method: str) -> str:
    return f"{config.TELEGRAM_API_BASE}/bot{token}/{method}"


def send_telegram(
    text_html: str,
    chat_id: Optional[str] = None,
    buttons: Optional[dict] = None,
) -> bool:
    """Send HTML-formatted message. buttons = inline keyboard dict."""
    token = config.TELEGRAM_BOT_TOKEN
    chat = chat_id or config.TELEGRAM_CHAT_ID
    if not chat:
        # approval bot /start tho register ayyina chat id fallback
        from . import state

        chat = state.meta_get(config.STATE_PATH, "telegram_chat_id") or ""
    if not token or not chat:
        log.info("Telegram not configured — skipping notification")
        return False
    payload = {
        "chat_id": chat,
        "text": text_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }
    if buttons:
        payload["reply_markup"] = buttons
    try:
        resp = requests.post(_tg_api(token, "sendMessage"), json=payload,
                             timeout=config.HTTP_TIMEOUT)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        log.error("Telegram sendMessage failed: %s", resp.text[:300])
    except Exception:
        log.exception("Telegram sendMessage error")
    return False


def send_whatsapp(text: str) -> bool:
    """CallMeBot free WhatsApp alert (text only, no buttons)."""
    base = config.WHATSAPP_CALLMEBOT_URL
    if not base:
        return False
    url = base + ("&" if "?" in base else "?") + "text=" + quote(text[:900])
    try:
        resp = requests.get(url, timeout=config.HTTP_TIMEOUT)
        ok = resp.status_code == 200
        if not ok:
            log.error("WhatsApp alert failed: %s %s", resp.status_code, resp.text[:200])
        return ok
    except Exception:
        log.exception("WhatsApp alert error")
    return False


def esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def post_buttons(post_id: int, link: str) -> dict:
    """Inline keyboard for a draft post awaiting review."""
    return {
        "inline_keyboard": [
            [
                {"text": "✅ Publish", "callback_data": f"pub:{post_id}"},
                {"text": "🗑️ Delete", "callback_data": f"del:{post_id}"},
            ],
            [
                {"text": "✏️ Edit in WordPress",
                 "url": f"{config.WP_SITE}/wp-admin/post.php?post={post_id}&action=edit"},
                {"text": "🏠 Site", "url": config.WP_SITE},
            ],
            [
                {"text": "🔄️ Improve + Research (kotha info add)",
                 "callback_data": f"upd:{post_id}"},
            ],
        ]
    }


# ------------------------------------------------------------------ main API

def daily_digest(count: int, last_posts: list) -> None:
    """Roji end-of-day summary (scheduler pampistundi)."""
    if not (config.TELEGRAM_BOT_TOKEN or config.WHATSAPP_CALLMEBOT_URL):
        return
    lines = ["📅 <b>Daily Digest — studentup.in</b>", "",
             f"Aaj posts create ayyayi: <b>{count}</b>"]
    if last_posts:
        lines += ["", "Latest:"]
        for p in last_posts[:5]:
            status = p.get("status", "")
            mark = "🟢" if status == "publish" else "📝"
            lines.append(f"{mark} {esc(str(p.get('title', ''))[:60])}")
    lines += ["", "Pending drafts: /pending"]
    send_telegram("\n".join(lines))
    if config.WHATSAPP_CALLMEBOT_URL:
        plain = (f"Daily Digest: {count} posts create ayyayi. "
                 + " · ".join(str(p.get("title", ""))[:40] for p in (last_posts or [])[:3]))
        send_whatsapp(plain)


def notify_updated_post(article: dict, result: dict) -> None:
    """Post update notification (content refresh)."""
    if not (config.TELEGRAM_BOT_TOKEN or config.WHATSAPP_CALLMEBOT_URL):
        return
    qa = article.get("_qa") or {}
    notes = (article.get("update_notes") or "").strip()
    lines = [
        "🔄 <b>POST UPDATED</b> <i>(content refresh — same URL)</i>",
        "",
        f"<b>{esc(article.get('title', ''))}</b>",
    ]
    if notes:
        lines += ["🆕 <b>Kotha info add ayyindi:</b>", esc(notes), ""]
    if qa:
        lines.append(f"📊 QA: <b>{qa.get('score', '-')}/100</b> · "
                     f"📝 {qa.get('words', '-')} words · ⏱️ ~{qa.get('reading_min', '-')} min")
    if result.get("link"):
        lines += ["", f"🔗 {esc(result['link'])}"]
    send_telegram("\n".join(lines))
    if config.WHATSAPP_CALLMEBOT_URL:
        send_whatsapp(f"Post updated: {article.get('title', '')[:80]}\n{result.get('link', '')}")


def notify_new_post(article: dict, result: dict) -> None:
    """Notify about a newly created post (draft or published)."""
    if not (config.TELEGRAM_BOT_TOKEN or config.WHATSAPP_CALLMEBOT_URL):
        log.info("Notifications disabled (no Telegram/WhatsApp config)")
        return

    status = result.get("status", "draft")
    post_id = result.get("id")
    title = article.get("title", "")
    cat = article.get("category", "")
    tags = ", ".join(article.get("tags", [])[:5])
    excerpt = (article.get("meta_description", "") or "")[:200]

    if status == "draft":
        emoji = "📝"
        head = "NEW DRAFT — Review cheyandi"
    else:
        emoji = "🚀"
        head = "PUBLISHED — Live ayyindi!"

    lines = [
        f"{emoji} <b>{esc(head)}</b>",
        "",
        f"<b>{esc(title)}</b>",
        f"📂 Category: {esc(cat)}",
        f"🏷️ Tags: {esc(tags)}",
    ]
    # QA report — review easy ga avtaniki
    qa = article.get("_qa") or {}
    qa_bits = []
    if qa:
        qa_bits.append(f"📊 QA: <b>{qa.get('score', '-')}/100</b>")
        qa_bits.append(f"📝 {qa.get('words', '-')} words · ⏱️ ~{qa.get('reading_min', '-')} min")
    if article.get("_orig") is not None:
        qa_bits.append(f"🛡️ Originality: <b>{article['_orig']}%</b> (no-copy proof)")
    if qa_bits:
        lines.append(" · ".join(qa_bits))
    if article.get("source_url"):
        lines.append(f"📰 Source (original rewrite): {esc(article['source_url'])}")
    lines += ["", f"{esc(excerpt)}"]
    if result.get("link"):
        lines += ["", f"🔗 {esc(result['link'])}"]
    if status == "draft":
        lines += ["", "⬇️ Review chesi button click cheyandi:"]
    text = "\n".join(lines)

    # Telegram with buttons (draft) or plain (published)
    if config.TELEGRAM_BOT_TOKEN and (config.TELEGRAM_CHAT_ID or status == "draft"):
        buttons = post_buttons(post_id, result.get("link", "")) if status == "draft" else None
        send_telegram(text, buttons=buttons)

    # WhatsApp text-only alert
    if config.WHATSAPP_CALLMEBOT_URL:
        plain = (f"{emoji} {head}\n\n{title}\nCategory: {cat}\n"
                 + (f"Link: {result['link']}" if result.get("link") else "")
                 + ("\n(Review kosam WordPress dashboard lokelli publish cheyandi)"
                    if status == "draft" else ""))
        send_whatsapp(plain)
