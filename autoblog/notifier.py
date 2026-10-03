"""Notifications: Telegram (with action buttons) + WhatsApp (CallMeBot).

Telegram = full interactive review (Publish/Delete buttons handled by
approval_bot). WhatsApp = text-only alert (no buttons possible).
"""

import html
import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import quote, urlparse

import requests

from . import config

log = logging.getLogger("autoblog.notify")


# ------------------------------------------------------------------ helpers

def is_channel_chat(chat_id: object) -> bool:
    """Return True if chat_id represents a Telegram channel or broadcast target."""
    s = str(chat_id or "").strip()
    return s.startswith("-100") or s.startswith("@")


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

    # Channel chats forbid callback_data buttons; swap with channel URL buttons
    if buttons and is_channel_chat(chat):
        rows = buttons.get("inline_keyboard", [])
        has_cb = any("callback_data" in b for r in rows for b in r)
        if has_cb:
            buttons = post_buttons(0, "", chat_id=chat)

    # v84: Telegram 4096-char hard limit — long reports cut kakunda truncate
    # (reject ayithe alert motham pothundi — approval miss = money loss).
    if len(text_html) > 4000:
        text_html = text_html[:3950] + "\n…(cut — log lo full undi)"
    disable_preview = "true" if len(text_html) > 2800 else "false"
    payload = {
        "chat_id": chat,
        "text": text_html,
        "parse_mode": "HTML",
        "disable_web_page_preview": disable_preview,
    }
    if buttons:
        payload["reply_markup"] = buttons
    try:
        resp = requests.post(_tg_api(token, "sendMessage"), json=payload,
                             timeout=config.HTTP_TIMEOUT)
        if resp.status_code == 200 and resp.json().get("ok"):
            return True
        # If Telegram rejected due to invalid button types in channel, retry without reply_markup
        if resp.status_code == 400 and ("BUTTON_TYPE_INVALID" in resp.text or
                                        "reply_markup" in resp.text or
                                        "BUTTON_URL_INVALID" in resp.text):
            log.warning("Retrying Telegram sendMessage without reply_markup for %s", chat)
            payload.pop("reply_markup", None)
            retry_resp = requests.post(_tg_api(token, "sendMessage"), json=payload,
                                       timeout=config.HTTP_TIMEOUT)
            if retry_resp.status_code == 200 and retry_resp.json().get("ok"):
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

    Supports remote HTTPS image URLs or local files.
    Captions are intentionally kept below Telegram's 1024-character photo-caption limit.
    """
    token = config.TELEGRAM_BOT_TOKEN
    chat = chat_id or config.TELEGRAM_CHANNEL_CHAT_ID
    if not token or not chat:
        log.info("Telegram photo not configured — skipping channel post")
        return False
    caption_html = str(caption_html or "").strip()
    if len(caption_html) > 1000:
        caption_html = caption_html[:990] + "…"

    # 1. Local file upload support
    try:
        local_p = Path(str(photo_url or ""))
        if local_p.is_file():
            mime = "image/webp" if local_p.suffix.lower() == ".webp" else "image/jpeg"
            with open(local_p, "rb") as f:
                data = {
                    "chat_id": chat,
                    "caption": caption_html,
                    "parse_mode": "HTML",
                }
                if buttons:
                    data["reply_markup"] = json.dumps(buttons)
                resp = requests.post(
                    _tg_api(token, "sendPhoto"),
                    data=data,
                    files={"photo": (local_p.name, f, mime)},
                    timeout=config.HTTP_TIMEOUT,
                )
                if resp.status_code == 200 and resp.json().get("ok"):
                    return True
                log.error("Telegram local sendPhoto failed: %s", resp.text[:300])
    except Exception:
        log.exception("Telegram local sendPhoto error")

    # 2. Remote URL fetch
    parsed = urlparse(str(photo_url or ""))
    if parsed.scheme in ("http", "https") and parsed.netloc:
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


def wa_to_html(text: str) -> str:
    """v189: WhatsApp plain text → Telegram HTML (bold + clickable links intact).

    Morning send lo okate source text rendu channels ki pothundi — WhatsApp lo
    `*bold*`, Telegram lo `<b>`. Escape mundu cheyyadam valla user text lo unna
    `<`/`&` kabhi Telegram markup ga interpret avvadu (injection safe).
    """
    import html as _html
    import re as _re

    out = []
    for line in str(text or "").splitlines():
        esc = _html.escape(line)
        esc = _re.sub(r"\*([^*\n]+)\*", r"<b>\1</b>", esc)
        esc = _re.sub(r"(https?://[^\s<]+)", r'<a href="\1">\1</a>', esc)
        out.append(esc)
    return "\n".join(out)


def wa_clickto(text: str, limit: int = 1400) -> str:
    """v189: wa.me click-to-forward link (owner group/status ni choose cheyyachu)."""
    from urllib.parse import quote as _quote

    body = str(text or "").strip()
    if not body:
        return ""
    return "https://wa.me/?text=" + _quote(body[:limit])


def send_morning_list(text: str, whatsapp: bool = True,
                      telegram: bool = True) -> dict:
    """v189: daily morning list → Telegram (HTML) + WhatsApp (CallMeBot).

    Returns {telegram: bool, whatsapp: bool, channels: int} — caller honest ga
    report cheyyachu (silent failure ledu).
    """
    result = {"telegram": False, "whatsapp": False, "channels": 0}
    body = str(text or "").strip()
    if not body:
        return result
    if telegram and config.TELEGRAM_BOT_TOKEN:
        result["channels"] += 1
        html = wa_to_html(body)
        ok = True
        chunk = ""
        for line in html.splitlines(keepends=True):
            if len(chunk) + len(line) > 3800:
                ok = send_telegram(chunk.rstrip()) and ok
                chunk = ""
            chunk += line
        if chunk.strip():
            ok = send_telegram(chunk.rstrip()) and ok
        result["telegram"] = ok
    if whatsapp and config.WHATSAPP_CALLMEBOT_URL:
        result["channels"] += 1
        ok = True
        piece = ""
        for line in body.splitlines(keepends=True):
            if len(piece) + len(line) > 820:
                ok = send_whatsapp(piece.rstrip()) and ok
                piece = ""
            piece += line
        if piece.strip():
            ok = send_whatsapp(piece.rstrip()) and ok
        result["whatsapp"] = ok
    return result


def esc(text: str) -> str:
    return html.escape(str(text or ""), quote=True)


def post_buttons(post_id: int, link: str, chat_id: Optional[str] = None) -> dict:
    """Inline keyboard for a draft post awaiting review.

    If chat_id is a channel, URL buttons are used to prevent Telegram
    BUTTON_TYPE_INVALID rejection.
    """
    site = (config.WP_SITE or "https://studentup.in").rstrip("/")
    if is_channel_chat(chat_id):
        wp_edit = f"{site}/wp-admin/post.php?post={post_id}&action=edit" if post_id else site
        share_text = quote(link) if link else quote(site)
        wa_share = f"https://api.whatsapp.com/send?text={share_text}"
        tg_channel = getattr(config, "TELEGRAM_CHANNEL_URL", "") or "https://t.me/studentup_in"
        rows = []
        if link:
            rows.append([
                {"text": "📖 పూర్తి వివరాలు & Preview", "url": link},
                {"text": "✏️ Edit in WP", "url": wp_edit},
            ])
        else:
            rows.append([{"text": "✏️ Edit in WP", "url": wp_edit}])
        rows.append([
            {"text": "📲 WhatsApp లో షేర్ చేయండి", "url": wa_share},
            {"text": "📢 StudentUp ఛానల్", "url": tg_channel},
        ])
        return {"inline_keyboard": rows}

    return {
        "inline_keyboard": [
            [
                {"text": "✅ Publish", "callback_data": f"pub:{post_id}"},
                {"text": "🗑️ Delete", "callback_data": f"del:{post_id}"},
            ],
            [
                {"text": "✏️ Edit in WordPress",
                 "url": f"{site}/wp-admin/post.php?post={post_id}&action=edit"},
                {"text": "🏠 Site", "url": site},
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


def extract_article_from_snapshot(snapshot: dict, default_title: str = "", default_link: str = "") -> dict:
    """Extract rich structured metadata from a WordPress post snapshot."""
    import html as _html
    import json as _json

    raw_title = (snapshot.get("title") or {}).get("rendered", default_title)
    clean_title = _html.unescape(str(raw_title or "").strip())
    clean_title = re.sub(r"\s*(?:[—–-]\s*)?(?:Best|Complete|Ultimate|A to Z|Full)\s+(?:Guide|Details|Update|Information)\b", "", clean_title, flags=re.I)
    clean_title = re.sub(r"\s*[—–-]\s*$", "", clean_title).strip()

    raw_excerpt = (snapshot.get("excerpt") or {}).get("rendered", "")
    meta_desc = re.sub(r"<[^>]+>", " ", _html.unescape(raw_excerpt))
    meta_desc = re.sub(r"\s+", " ", meta_desc).strip()

    content_html = (snapshot.get("content") or {}).get("rendered", "")
    link = snapshot.get("link") or default_link or (snapshot.get("guid") or {}).get("rendered", "")

    # Category extraction from _embedded wp:term
    cat_name = ""
    embedded = snapshot.get("_embedded") or {}
    for term_list in (embedded.get("wp:term") or []):
        for term in (term_list or []):
            if isinstance(term, dict) and term.get("taxonomy") == "category":
                tname = str(term.get("name") or "").strip()
                if tname and tname.lower() not in ("uncategorized", "students"):
                    cat_name = tname
                    break
        if cat_name:
            break

    if not cat_name:
        try:
            from . import pipeline
            cat_name = pipeline.classify_category(clean_title, content_html)
        except Exception:
            cat_name = ""

    # Recruitment extraction (JSON-LD schema first, regex table fallback)
    rec = {}
    if "<script" in content_html and "JobPosting" in content_html:
        for m in re.finditer(r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>', content_html, flags=re.S | re.I):
            try:
                data = _json.loads(m.group(1).strip())
                if isinstance(data, dict) and data.get("@type") == "JobPosting":
                    if data.get("title"):
                        rec["role"] = str(data["title"])
                    org = data.get("hiringOrganization") or {}
                    if isinstance(org, dict) and org.get("name"):
                        rec["org_name"] = str(org["name"])
                    addr = (data.get("jobLocation") or {}).get("address") or {}
                    if isinstance(addr, dict) and addr.get("addressLocality"):
                        rec["location"] = str(addr["addressLocality"])
                    if data.get("validThrough"):
                        rec["apply_end"] = str(data["validThrough"])[:10]
                    sal = data.get("baseSalary") or {}
                    if isinstance(sal, dict):
                        val = sal.get("value") or {}
                        if isinstance(val, dict):
                            smin, smax = val.get("minValue"), val.get("maxValue")
                            if smin and smax:
                                rec["salary"] = f"₹{smin:,} – ₹{smax:,}"
                    break
            except Exception:
                continue

    def _find_field(*patterns):
        for pat in patterns:
            m = re.search(pat, content_html, flags=re.I)
            if m:
                val = re.sub(r"<[^>]+>", "", m.group(1)).strip()
                val = re.sub(r"\s+", " ", val)
                if val and len(val) < 80:
                    return val
        return ""

    if not rec.get("org_name"):
        rec["org_name"] = _find_field(
            r"(?:సంస్థ పేరు|సంస్థ|Organization|Company)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:సంస్థ|Organization|Company)</td>\s*<td[^>]*>([^<]+)</td>",
        )
    if not rec.get("role"):
        rec["role"] = _find_field(
            r"(?:ఉద్యోగం|పోస్టు పేరు|Role|Job Title|Designation)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:ఉద్యోగం|పోస్టు|Role|Post Name)</td>\s*<td[^>]*>([^<]+)</td>",
        )
    if not rec.get("vacancies"):
        rec["vacancies"] = _find_field(
            r"(?:ఖాళీలు|Vacancies|Total Posts|No\. of Posts)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:ఖాళీలు|Vacancies)</td>\s*<td[^>]*>([^<]+)</td>",
        )
    if not rec.get("qualification"):
        rec["qualification"] = _find_field(
            r"(?:అర్హత|విద్యార్హత|Eligibility|Qualification)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:అర్హత|Eligibility|Qualification)</td>\s*<td[^>]*>([^<]+)</td>",
        )
    if not rec.get("location"):
        rec["location"] = _find_field(
            r"(?:లొకేషన్|ఉద్యోగ ప్రదేశం|Location|Job Location)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:లొకేషన్|Location)</td>\s*<td[^>]*>([^<]+)</td>",
        )
    if not rec.get("salary"):
        rec["salary"] = _find_field(
            r"(?:జీతం|వేతనం|Salary|Pay Scale|Stipend)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:జీతం|వేతనం|Salary)</td>\s*<td[^>]*>([^<]+)</td>",
        )
    if not rec.get("apply_end"):
        rec["apply_end"] = _find_field(
            r"(?:చివరి తేదీ|దరఖాస్తు ముగింపు|Last Date|Apply End)[:\s*–-]+([^<\n]+)",
            r"<td[^>]*>(?:చివరి తేదీ|Last Date)</td>\s*<td[^>]*>([^<]+)</td>",
        )

    return {
        "title": clean_title,
        "category": cat_name,
        "meta_description": meta_desc,
        "content_html": content_html,
        "recruitment": rec,
        "link": link,
    }


def channel_caption(article: dict, result: dict) -> str:
    """Create the rich, student-first Telugu caption used after live approval.

    Includes full structured breakdown: organization, role, vacancies, eligibility,
    location, salary, deadline, application mode, and direct link.
    """
    article = article or {}
    result = result or {}
    rec = article.get("recruitment") or {}
    if not isinstance(rec, dict):
        rec = {}

    raw_title = article.get("title") or "StudentUp update"
    title = re.sub(r"\s*(?:[—–-]\s*)?(?:Best|Complete|Ultimate|A to Z|Full)\s+(?:Guide|Details|Update|Information)\b", "", str(raw_title), flags=re.I)
    title = re.sub(r"\s*[—–-]\s*$", "", title).strip()
    title = _plain(title, 180)
    link = str(result.get("link") or article.get("link") or "").strip()
    cat = str(article.get("category") or "").strip()

    is_quiz = (cat.lower() == "daily quiz" or "daily quiz" in title.lower() or "క్విజ్" in title)
    if is_quiz:
        questions = ""
        quiz = article.get("_quiz") or {}
        if isinstance(quiz, dict) and quiz.get("questions"):
            questions = str(len(quiz["questions"]))
        lines = ["🧠 <b>Today’s Daily Quiz (డైలీ ప్రాక్టీస్ క్విజ్)</b>", "", f"📚 <b>{esc(title)}</b>"]
        if questions:
            lines.append(f"👉 <b>ప్రశ్నల సంఖ్య:</b> {esc(questions)} Questions (MCQs)")
        lines += [
            "🎯 <b>పరీక్షలు:</b> TSPSC / APPSC / Police / RRB / SSC",
            "💡 <b>విశేషాలు:</b> ప్రతి ప్రశ్నకు తక్షణ వివరణ & స్కోర్ కార్డ్",
            "",
            "✅ <b>ఉచితంగా క్విజ్ రాయండి 👇👇</b>",
        ]
        if link:
            lines.append(f'<a href="{esc(link)}">Start Today’s Quiz Now →</a>')
        lines.append("")
        lines.append("📌 ప్రతిరోజూ ఉచిత ప్రాక్టీస్ క్విజ్. సబ్మిట్ చేసిన వెంటనే వివరణలు చదవండి.")
        return "\n".join(lines)

    # Category icon & theme header
    if "software" in cat.lower() or "సాఫ్ట్" in title.lower():
        icon = "💻"
    elif "private" in cat.lower():
        icon = "🏢"
    elif "ts govt" in cat.lower() or "తెలంగాణ" in title.lower():
        icon = "🏛️"
    elif "ap govt" in cat.lower() or "ఆంధ్ర" in title.lower():
        icon = "🏛️"
    elif "central" in cat.lower():
        icon = "🇮🇳"
    elif "scholarship" in cat.lower() or "స్కాలర్" in title.lower():
        icon = "🎓"
    elif "hall ticket" in cat.lower() or "హాల్" in title.lower():
        icon = "🎫"
    elif "result" in cat.lower() or "ఫలిత" in title.lower():
        icon = "📄"
    elif "abroad" in cat.lower():
        icon = "✈️"
    else:
        icon = "🔥"

    lines = [f"{icon} <b>{esc(title)}</b>", ""]

    org = _source_fact(rec, article, "org_name", "company", "board")
    if org:
        lines.append(f"🏢 <b>సంస్థ (Org):</b> {esc(org)}")

    role = _source_fact(rec, article, "role", "designation", "post_name")
    if role:
        lines.append(f"💼 <b>ఉద్యోగం (Role):</b> {esc(role)}")

    vacancies = _source_fact(rec, article, "vacancies", "vacancy", "post_count", "total_posts")
    if vacancies and re.search(r"\d", vacancies):
        lines.append(f"👉 <b>ఖాళీలు (Vacancies):</b> {esc(vacancies)}")

    eligibility = _source_fact(rec, article, "qualification", "eligibility")
    if eligibility:
        lines.append(f"👉 <b>అర్హత (Eligibility):</b> {esc(eligibility)}")

    deadline = _safe_iso_date(rec.get("apply_end") or article.get("apply_end") or article.get("last_date"))
    if not deadline:
        deadline = _source_fact(rec, article, "last_date", "apply_end")
    lines.append(f"👉 <b>చివరి తేదీ (Last Date):</b> {esc(deadline or 'త్వరలో ముగుస్తుంది (Apply Soon)')}")

    exam_date = _safe_iso_date(rec.get("exam_date") or article.get("exam_date"))
    if exam_date:
        lines.append(f"🗓️ <b>Exam Date:</b> {esc(exam_date)}")

    fee = _source_fact(rec, article, "application_fee", "fee")
    if fee:
        lines.append(f"💳 <b>ఫీజు (Fee):</b> {esc(fee)}")

    location = _source_fact(rec, article, "location")
    if location:
        lines.append(f"📍 <b>జాబ్ లొకేషన్:</b> {esc(location)}")

    salary = _source_fact(rec, article, "salary")
    if not salary and (rec.get("salary_min") is not None or rec.get("salary_max") is not None):
        low, high = rec.get("salary_min"), rec.get("salary_max")
        salary = "₹" + str(low if low is not None else high)
        if high is not None and high != low:
            salary += " – ₹" + str(high)
    if salary:
        lines.append(f"💰 <b>వేతనం (Salary):</b> {esc(salary)}")

    lines.append("📝 <b>దరఖాస్తు విధానం:</b> ఆన్‌లైన్ (Apply Online)")

    summary = _plain(article.get("quick_answer") or article.get("meta_description"), 190)
    if summary:
        lines += ["", f"📌 <i>{esc(summary)}</i>"]

    lines += ["", "✅ <b>పూర్తి వివరాలు & Apply Link 👇👇</b>"]
    if link:
        lines.append(f'<a href="{esc(link)}">👉 అధికారిక నోటిఫికేషన్ & ఆన్‌లైన్ దరఖాస్తు లింక్ కోసం క్లిక్ చేయండి →</a>')

    official = _source_fact(rec, article, "org_url", "official_url")
    if official and official != link and urlparse(official).scheme in ("http", "https"):
        lines.append(f'<a href="{esc(official)}">🌐 Official Website →</a>')

    lines += [
        "",
        "📢 <b>మరిన్ని జాబ్ అప్డేట్స్ కోసం ఫాలో అవ్వండి:</b> @studentup_in",
        "⚠️ <i>Apply చేసే ముందు అధికారిక నోటిఫికేషన్ వివరాలు సరిచూసుకోండి.</i>",
    ]
    return "\n".join(lines)


def channel_post(article: dict, result: dict, image_url: str = "") -> bool:
    """Broadcast one attractive post only after the post is live."""
    if not config.TELEGRAM_CHANNEL_CHAT_ID or not result.get("link"):
        return False
    caption = channel_caption(article, result)
    link = str(result.get("link") or "").strip()
    raw_title = article.get("title") or "StudentUp Update"
    clean_title = re.sub(r"\s*(?:[—–-]\s*)?(?:Best|Complete|Ultimate|A to Z|Full)\s+(?:Guide|Details|Update)\b", "", str(raw_title), flags=re.I).strip()
    clean_title = re.sub(r"\s*[—–-]\s*$", "", clean_title).strip()

    share_text = f"🔥 {clean_title}\n\n👉 Apply Online / పూర్తి వివరాలు ఇక్కడ చూడండి:\n{link}"
    share_tg_url = f"https://t.me/share/url?url={quote(link)}&text={quote(share_text)}"

    buttons = {
        "inline_keyboard": [
            [{"text": "🌐 పూర్తి వివరాలు & Apply Online", "url": link}],
            [{"text": "📲 Friends కి షేర్ చేయండి ↗️", "url": share_tg_url}],
        ]
    }

    image = image_url or article.get("_media_url") or article.get("_image_path") or result.get("image_url") or ""
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


def send_opportunity_digest() -> bool:
    """Send the owner a compact, forward-ready active-opportunities list.

    It targets the review chat, not the public channel. The owner can forward
    it when useful; published article channel cards remain handled separately
    by ``channel_post`` after approval.
    """
    if not config.TELEGRAM_BOT_TOKEN:
        return False
    try:
        from .opportunity_digest import render_digest_messages
        from .wordpress_client import WordPressClient

        wp = WordPressClient()
        rows = wp.published_opportunities()
        messages = render_digest_messages(
            config.WP_SITE, rows,
            per_section=getattr(config, "OPPORTUNITY_DIGEST_PER_SECTION", 6),
        )
        if not messages:
            log.info("Opportunity digest skipped — no active classified posts")
            return False
        results = [send_telegram(message) for message in messages]
        return all(results)
    except Exception:
        log.exception("Opportunity digest failed")
        return False


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
        subhead = "కొత్త పోస్ట్ డ్రాఫ్ట్ సిద్ధమైంది (Review Pending)"
    else:
        emoji = "🚀"
        head = "PUBLISHED — Live ayyindi!"
        subhead = "కొత్త నోటిఫికేషన్ లైవ్ అయింది (Published)"

    rec = article.get("recruitment") or {}
    org = _source_fact(rec, article, "org_name", "company")
    role = _source_fact(rec, article, "role", "designation")
    vacancies = _source_fact(rec, article, "vacancies", "vacancy", "post_count")
    qual = _source_fact(rec, article, "qualification", "eligibility")
    loc = _source_fact(rec, article, "location")
    sal = _source_fact(rec, article, "salary")
    deadline = _safe_iso_date(rec.get("apply_end") or article.get("apply_end") or article.get("last_date"))

    lines = [
        f"{emoji} <b>{esc(head)}</b>",
        f"<i>{esc(subhead)}</i>",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        f"🌟 <b>{esc(title)}</b>",
        "",
        f"📂 <b>కేటగిరీ (Category):</b> {esc(cat)}",
        f"🏷️ <b>Tags:</b> {esc(tags)}",
    ]
    if org:
        lines.append(f"🏢 <b>సంస్థ (Company/Org):</b> {esc(org)}")
    if role:
        lines.append(f"💼 <b>ఉద్యోగం (Role):</b> {esc(role)}")
    if vacancies:
        lines.append(f"👉 <b>Vacancies:</b> {esc(vacancies)}")
    if qual:
        lines.append(f"🎓 <b>విద్యార్హత (Eligibility):</b> {esc(qual)}")
    if loc:
        lines.append(f"📍 <b>లొకేషన్ (Location):</b> {esc(loc)}")
    if sal:
        lines.append(f"💰 <b>వేతనం (Salary):</b> {esc(sal)}")
    if deadline:
        lines.append(f"⏳ <b>చివరి తేదీ (Last Date):</b> {esc(deadline)}")
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
        target_chat = config.TELEGRAM_CHAT_ID or ""
        buttons = post_buttons(post_id, result.get("link", ""), chat_id=target_chat) if status == "draft" else None
        send_telegram(text, chat_id=target_chat, buttons=buttons)

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
