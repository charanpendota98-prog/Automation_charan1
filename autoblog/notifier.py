"""Notifications: Telegram (with action buttons) + WhatsApp (CallMeBot).

Telegram = full interactive review (Publish/Delete buttons handled by
approval_bot). WhatsApp = text-only alert (no buttons possible).
"""

import html
import logging
import re
from datetime import datetime
from typing import Optional
from urllib.parse import quote, urlparse

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
    # v84: Telegram 4096-char hard limit — long reports cut kakunda truncate
    # (reject ayithe alert motham pothundi — approval miss = money loss).
    if len(text_html) > 4000:
        text_html = text_html[:3950] + "\n…(cut — log lo full undi)"
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


def send_telegram_photo(
    photo_url: str,
    caption_html: str,
    chat_id: Optional[str] = None,
    buttons: Optional[dict] = None,
) -> bool:
    """Send a public channel post with the article's featured image.

    Telegram fetches the HTTPS image URL itself, so no image bytes or private
    credentials are uploaded by this process. Captions are intentionally kept
    below Telegram's 1024-character photo-caption limit.
    """
    parsed = urlparse(str(photo_url or ""))
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return False
    token = config.TELEGRAM_BOT_TOKEN
    chat = chat_id or config.TELEGRAM_CHANNEL_CHAT_ID
    if not token or not chat:
        log.info("Telegram photo not configured — skipping channel post")
        return False
    caption_html = str(caption_html or "").strip()
    if len(caption_html) > 1000:
        caption_html = caption_html[:990] + "…"
    payload = {
        "chat_id": chat,
        "photo": str(photo_url),
        "caption": caption_html,
        "parse_mode": "HTML",
    }
    if buttons:
        payload["reply_markup"] = buttons
    try:
        resp = requests.post(_tg_api(token, "sendPhoto"), json=payload,
                             timeout=config.HTTP_TIMEOUT)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        log.error("Telegram sendPhoto failed: %s", resp.text[:300])
    except Exception:
        log.exception("Telegram sendPhoto error")
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


def _plain(value: object, limit: int = 180) -> str:
    """Strip article HTML before putting a value in a Telegram caption."""
    text = html.unescape(re.sub(r"<[^>]+>", " ", str(value or "")))
    text = re.sub(r"\s+", " ", text).strip()
    return text[:limit].rstrip()


def _safe_iso_date(value: object) -> str:
    raw = str(value or "").strip()
    if not re.fullmatch(r"20\d{2}-\d{2}-\d{2}", raw):
        return ""
    try:
        return datetime.strptime(raw, "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return ""


def _source_fact(rec: dict, article: dict, *keys: str) -> str:
    for key in keys:
        value = rec.get(key) if isinstance(rec, dict) else ""
        if not value:
            value = article.get(key, "") if isinstance(article, dict) else ""
        value = _plain(value, 90)
        if value:
            return value
    return ""


def channel_caption(article: dict, result: dict) -> str:
    """Create the short, student-first caption used after live approval.

    Only structured article fields are shown. Missing vacancy, eligibility,
    salary or dates are omitted rather than guessed; the article link remains
    the source of the complete, reviewed details.
    """
    article = article or {}
    result = result or {}
    rec = article.get("recruitment") or {}
    if not isinstance(rec, dict):
        rec = {}
    title = _plain(article.get("title") or "StudentUp update", 180)
    link = str(result.get("link") or article.get("link") or "").strip()
    lines = [f"🔥 <b>{esc(title)}</b>", ""]

    vacancies = _source_fact(rec, article, "vacancies", "vacancy", "post_count", "total_posts")
    if vacancies and re.fullmatch(r"[\d,]+", vacancies):
        lines.append(f"👉 <b>Vacancies:</b> {esc(vacancies)}")
    eligibility = _source_fact(rec, article, "qualification", "eligibility")
    if eligibility:
        lines.append(f"👉 <b>Eligibility:</b> {esc(eligibility)}")
    deadline = _safe_iso_date(rec.get("apply_end") or article.get("apply_end") or article.get("last_date"))
    lines.append(f"👉 <b>Last Date:</b> {esc(deadline or 'Not announced')}")
    exam_date = _safe_iso_date(rec.get("exam_date") or article.get("exam_date"))
    if exam_date:
        lines.append(f"🗓️ <b>Exam Date:</b> {esc(exam_date)}")
    fee = _source_fact(rec, article, "application_fee", "fee")
    if fee:
        lines.append(f"💳 <b>Application Fee:</b> {esc(fee)}")
    location = _source_fact(rec, article, "location")
    if location:
        lines.append(f"📍 <b>Location:</b> {esc(location)}")
    salary = _source_fact(rec, article, "salary")
    if not salary and (rec.get("salary_min") is not None or rec.get("salary_max") is not None):
        low, high = rec.get("salary_min"), rec.get("salary_max")
        salary = "₹" + str(low if low is not None else high)
        if high is not None and high != low:
            salary += " – ₹" + str(high)
    if salary:
        lines.append(f"💰 <b>Salary:</b> {esc(salary)}")

    summary = _plain(article.get("quick_answer") or article.get("meta_description"), 210)
    if summary and len(lines) <= 3:
        lines += ["", f"📌 {esc(summary)}"]
    lines += ["", "✅ <b>Apply / Full Details 👇👇</b>"]
    if link:
        lines.append(f'<a href="{esc(link)}">Open StudentUp article →</a>')
    official = _source_fact(rec, article, "org_url", "official_url")
    if official and official != link and urlparse(official).scheme in ("http", "https"):
        lines.append(f'<a href="{esc(official)}">Official notification →</a>')
    lines += ["", "⚠️ Apply cheyyemundu official notification lo dates, fee & eligibility verify cheyyandi."]
    return "\n".join(lines)


def channel_post(article: dict, result: dict, image_url: str = "") -> bool:
    """Broadcast one attractive post only after the post is live."""
    if not config.TELEGRAM_CHANNEL_CHAT_ID or not result.get("link"):
        return False
    caption = channel_caption(article, result)
    link = result.get("link", "")
    buttons = {"inline_keyboard": [[{"text": "📖 పూర్తి వివరాలు", "url": link}]]}
    image = image_url or article.get("_media_url") or result.get("image_url") or ""
    if image and send_telegram_photo(image, caption, buttons=buttons):
        return True
    # A missing/failed featured image must not lose the approved announcement.
    return send_telegram(caption, chat_id=config.TELEGRAM_CHANNEL_CHAT_ID,
                         buttons=buttons)


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
        lines.append(f"📊 Editorial QA (not Rank Math): <b>{qa.get('score', '-')}/100</b> · "
                     f"📝 {qa.get('words', '-')} words · ⏱️ ~{qa.get('reading_min', '-')} min")
    rm = article.get("_rm") or {}
    if rm:
        missing = result.get("seo_meta_missing") or []
        lines.append("⛔ Rank Math field readback failed: " + esc(", ".join(missing))
                     if missing else
                     "✅ All generated Rank Math fields WordPress readback verified")
        ui_score = result.get("rank_math_ui_score")
        lines.append((f"🎯 Rank Math stored UI score: <b>{ui_score}/100</b> (read-only)"
                      if ui_score is not None else
                      "ℹ️ Rank Math stored UI score unavailable; local estimate hidden"))
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
        qa_bits.append(f"📊 Editorial QA (not Rank Math): <b>{qa.get('score', '-')}/100</b>")
        qa_bits.append(f"📝 {qa.get('words', '-')} words · ⏱️ ~{qa.get('reading_min', '-')} min")
    rm = article.get("_rm") or {}
    if rm:
        missing = result.get("seo_meta_missing") or []
        if missing:
            qa_bits.append("⛔ Rank Math fields WordPress readback FAILED: "
                           + esc(", ".join(missing)))
        else:
            qa_bits.append("✅ All generated Rank Math fields (focus/secondary, title, "
                           "description, social, robots, canonical) WordPress readback verified")
        ui_score = result.get("rank_math_ui_score")
        qa_bits.append((f"🎯 Rank Math stored UI score: <b>{ui_score}/100</b> (read-only)"
                        if ui_score is not None else
                        "ℹ️ Rank Math stored UI score unavailable; local estimate hidden"))
    source_audit = article.get("_source_audit") or {}
    if source_audit.get("applicable"):
        qa_bits.append(
            "🔎 Sources: <b>{}</b> independent · <b>{}</b> official · "
            "confidence <b>{}/100</b> {}".format(
                source_audit.get("independent_domains", 0),
                source_audit.get("official_count", 0),
                source_audit.get("confidence", 0),
                "✅" if source_audit.get("ok") else "⚠️"))
    reader = article.get("_content_quality") or {}
    if reader:
        qa_bits.append("🧹 Reader quality: <b>{}/100</b> · filler {} · repeats {}".format(
            reader.get("score", 0), reader.get("filler_hits", 0),
            len(reader.get("duplicate_sentences", []))))
    gate = article.get("_gate") or {}
    if gate:
        crit = gate.get("critical_fails") or []
        qa_bits.append("🧾 Pin-to-pin: <b>{}/100</b> ({}/{} checks){}".format(
            gate.get("score"), gate.get("passed"), gate.get("total"),
            "" if not crit else " · ⛔ " + ", ".join(crit)))
        if gate.get("_cert_path"):
            pass
    rec = article.get("recruitment") or {}
    if rec.get("apply_end"):
        qa_bits.append("📌 Google Jobs schema + deadline countdown ON "
                       "(closes {})".format(rec["apply_end"]))
    if article.get("_fact"):
        qa_bits.append("⚠️ Fact flags: <b>{}</b> unverified — review "
                       "mundu check: {}".format(
                           len(article["_fact"]),
                           esc(str(article["_fact"][0])[:60])))
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

    # Public channel: exactly one attractive broadcast, and only after live
    # approval. Drafts/mocks never reach students. The featured image is
    # optional; if it fails, the same caption is sent as a text post.
    if (getattr(config, "TELEGRAM_CHANNEL_CHAT_ID", "") and
            status == "publish" and result.get("link") and not article.get("_mock")):
        channel_post(article, result, image_url=article.get("_media_url", ""))

    # WhatsApp text-only alert
    if config.WHATSAPP_CALLMEBOT_URL:
        plain = (f"{emoji} {head}\n\n{title}\nCategory: {cat}\n"
                 + (f"Link: {result['link']}" if result.get("link") else "")
                 + ("\n(Review kosam WordPress dashboard lokelli publish cheyandi)"
                    if status == "draft" else ""))
        send_whatsapp(plain)
