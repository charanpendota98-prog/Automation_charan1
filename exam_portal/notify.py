"""v39 Exam Portal — multi-channel notifications (anni channel lo perfect ga).

Channels:
  1. In-app  — student page lo live banner + admin log (eppudu pani chestundi).
  2. Telegram — bot token + chat id unte (repo `.env` nunchi auto reuse).
  3. Webhook  — generic JSON POST → WhatsApp Business API / SMS gateway /
                Slack / Google Chat / n8n / Zapier (mee provider ki wire cheyandi).
  4. Copy-paste — WhatsApp/Telegram/SMS message templates admin dashboard lo
                (college staff groups ki direct paste cheyyadaniki).

Rule: notification fail aithe exam flow EPPUDU aagadu — status log avutundi.
"""

from __future__ import annotations

import json
import logging
import os
from typing import Dict, List, Optional

log = logging.getLogger("exam_portal.notify")

PUBLIC_URL = os.environ.get("EXAM_PUBLIC_URL", "").rstrip("/")

EVENT_TITLES = {
    "published": "📋 Exam published",
    "started": "🚀 Exam STARTED",
    "closing_soon": "⏳ Exam closing soon",
    "closed": "🔒 Exam CLOSED",
    "results": "🏆 Results published",
    "extended": "⏱️ Extra time added",
    "announcement": "📢 Announcement",
}


def exam_link(exam: Dict) -> str:
    base = PUBLIC_URL
    path = f"/exam/{exam['code']}"
    return f"{base}{path}" if base else path


def student_message(exam: Dict, event: str, extra: str = "") -> str:
    """Telugu + English message students ki (WhatsApp/Telegram/SMS ready)."""
    link = exam_link(exam)
    head = f"{exam['college']} — {exam['title']}".strip(" —")
    if event == "published":
        return (f"📋 {head}\n\nExam code: {exam['code']}\n"
                f"Duration: {exam['duration_min']} nimishalu\n"
                f"Join link: {link}\n\n"
                "Roll number tho join avvandi (password avasaram ledu). "
                "Exam start ayye varaku wait cheyandi — timer college nunchi control "
                "avutundi.")
    if event == "started":
        return (f"🚀 Exam START ayyindi!\n{head}\n\n"
                f"Ventane join avvandi: {link}\n"
                f"Code: {exam['code']} · Duration: {exam['duration_min']} nimishalu\n\n"
                "Answers prathi click ki auto-save avutayi. Time ayyaka automatic "
                "submit avutundi.")
    if event == "closing_soon":
        return (f"⏳ Exam close avvadaniki {extra or 'konni nimishalu'} migilinayi.\n"
                f"{head}\nStudent link: {link}\n\n"
                "Answers save chesi submit cheyandi — time ayyaka auto-submit avutundi.")
    if event == "closed":
        return (f"🔒 Exam CLOSED — {head}\n\nEe exam ki inka join avvaleru. "
                "Results publish ayyaka link lo kanipistayi.")
    if event == "results":
        return (f"🏆 Results publish ayyayi — {head}\n\n"
                f"Mee result chudandi: {link}\nRoll number + join chesina device tho "
                "open cheyandi.")
    if event == "extended":
        return (f"⏱️ Extra time add ayyindi ({extra}). {head}\nKotha end time mee "
                f"screen lo timer lo update avutundi: {link}")
    if event == "announcement":
        return f"📢 {head}\n\n{extra}\n\nLink: {link}"
    return f"{head} — {event}\n{link}"


def short_message(exam: Dict, event: str, extra: str = "") -> str:
    """One-line SMS/WhatsApp-status style message."""
    link = exam_link(exam)
    label = EVENT_TITLES.get(event, event)
    tail = f" {extra}" if extra else ""
    return f"{label}: {exam['title']} ({exam['code']}){tail} — {link}"


def admin_message(exam: Dict, event: str, extra: str = "") -> str:
    return (f"[Exam Portal] {EVENT_TITLES.get(event, event)}\n"
            f"College: {exam['college'] or '-'}\nExam: {exam['title']} "
            f"({exam['code']})\nStatus: {exam['status']}{(' · ' + extra) if extra else ''}")


# ----------------------------------------------------------------- channels

def _telegram_config() -> Dict[str, str]:
    token = os.environ.get("EXAM_TELEGRAM_BOT_TOKEN", "")
    chat = os.environ.get("EXAM_TELEGRAM_CHAT_ID", "")
    if not token:
        try:                                  # repo .env reuse (zero config)
            from autoblog import config as repo_config

            token = token or getattr(repo_config, "TELEGRAM_BOT_TOKEN", "")
            chat = chat or getattr(repo_config, "TELEGRAM_CHAT_ID", "")
        except Exception:                     # noqa: BLE001
            pass
    return {"token": token, "chat": chat}


def send_telegram(text: str) -> Dict:
    cfg = _telegram_config()
    if not cfg["token"] or not cfg["chat"]:
        return {"status": "skipped", "detail": "telegram not configured"}
    url = f"https://api.telegram.org/bot{cfg['token']}/sendMessage"
    payload = {"chat_id": cfg["chat"], "text": text[:4000],
               "disable_web_page_preview": False}
    try:
        import requests

        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200 and r.json().get("ok"):
            return {"status": "sent", "detail": "telegram"}
        return {"status": "failed", "detail": f"HTTP {r.status_code}: {r.text[:120]}"}
    except Exception as exc:                  # noqa: BLE001 — never break the exam
        return {"status": "failed", "detail": str(exc)[:160]}


def send_webhook(payload: Dict) -> Dict:
    url = os.environ.get("EXAM_WEBHOOK_URL", "").strip()
    if not url:
        return {"status": "skipped", "detail": "webhook not configured"}
    try:
        import requests

        r = requests.post(url, json=payload, timeout=15)
        ok = 200 <= r.status_code < 300
        return {"status": "sent" if ok else "failed",
                "detail": f"HTTP {r.status_code}"}
    except Exception as exc:                  # noqa: BLE001
        return {"status": "failed", "detail": str(exc)[:160]}


def broadcast_event(store, exam: Optional[Dict], event: str,
                    extra: str = "", channels: bool = True) -> Dict:
    """Event ni anni configured channels ki pampu + log chey.

    Return: {message, results: [{channel, status, detail}]}
    """
    if not exam:
        return {"message": "", "results": []}
    message = student_message(exam, event, extra)
    results: List[Dict] = [{"channel": "in_app", "status": "ok", "detail": "banner"}]
    if channels:
        tg = send_telegram(f"{message}\n\n— {admin_message(exam, event, extra)}")
        results.append({"channel": "telegram", **tg})
        hook = send_webhook({
            "event": event, "exam_code": exam["code"], "title": exam["title"],
            "college": exam["college"], "status": exam["status"],
            "link": exam_link(exam), "message": message,
            "short_message": short_message(exam, event, extra),
            "students_message": message, "extra": extra,
        })
        results.append({"channel": "webhook", **hook})
    for r in results:
        try:
            store.log_notification(exam["id"] if exam else None, r["channel"],
                                   message, r["status"], r.get("detail", ""))
        except Exception:                     # noqa: BLE001
            pass
    log.info("notify %s/%s -> %s", exam["code"], event,
             ", ".join(f"{r['channel']}:{r['status']}" for r in results))
    return {"message": message, "short": short_message(exam, event, extra),
            "results": results}


def test_channels() -> Dict:
    """Doctor/CLI test: configured channels ki ping pampu."""
    out = {}
    out["telegram"] = send_telegram(
        "🧪 Exam Portal test message — channels ready ✔ (studentup.in)")
    out["webhook"] = send_webhook({"event": "test",
                                   "message": "Exam Portal channel test ✔"})
    return out


def templates(exam: Dict) -> Dict[str, str]:
    """Copy-paste templates (WhatsApp group / SMS / notice board)."""
    link = exam_link(exam)
    return {
        "whatsapp_group": student_message(exam, "published"),
        "sms": short_message(exam, "published"),
        "start_alert": student_message(exam, "started"),
        "results_alert": student_message(exam, "results"),
        "notice_board": (
            f"EXAM NOTICE — {exam['college']}\n"
            f"{exam['title']}\nCode: {exam['code']} | Duration: "
            f"{exam['duration_min']} minutes | Questions: see portal\n"
            f"Join: {link}\nRoll number tho join avvandi. "
            f"{exam['instructions'] or ''}".strip()),
        "email_line": (f"Subject: {exam['title']} — exam link ({exam['code']})\n"
                       f"Dear student, join with your roll number: {link}"),
        "json": json.dumps({"code": exam["code"], "title": exam["title"],
                            "link": link, "duration_min": exam["duration_min"]},
                           ensure_ascii=False),
    }
