# -*- coding: utf-8 -*-
"""v91: TELEGRAM TOOLS — owner-facing Telegram toolbox (theme 1.9.2).

Bot already sends review buttons + channel broadcasts automatically
(`autoblog/notifier.py` + `approval_bot.py`). Ee module = MANUAL tools:

  python run.py --tg-test                  bot ↔ owner chat connectivity ping
  python run.py --tg-broadcast "MESSAGE"   channel ki manual announcement
                                           (private -100… channels supported;
                                           long text auto-split, truncate kaadu)
  python run.py --tg-alert code "MESSAGE" [--tg-severity info|warn|critical]
                                           site-side v90 notify queue ki push
                                           (WP REST studentup/v1/notify) —
                                           critical aithe public banner avutundi

Design rules (v89 PART-45 "notify never breaks cron" principle):
  * missing creds = clear message + exit 0 (cron lo fail kaadu)
  * network errors = handled, summary print
  * broadcasts chunk-split at paragraph boundaries (Telegram 4096 limit lo
    message cut avvadu — full text multiple messages ga vellutundi)
"""

from __future__ import annotations

import datetime as dt
import logging
from typing import List, Tuple

from . import config
from . import notifier

log = logging.getLogger("autoblog.telegram_tools")

# Telegram hard limit 4096 chars — safe chunk (HTML tags overhead kosam margin)
TG_CHUNK_LIMIT = 3800


# --------------------------------------------------------------------- utils

def channel_configured() -> bool:
    """Channel broadcast ki kavalsina config unda?"""
    return bool(config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHANNEL_CHAT_ID)


def _split_chunks(text_html: str, limit: int = TG_CHUNK_LIMIT) -> List[str]:
    """Long text ni paragraph boundaries lo split (word cut kaadu).

    Enduku: notifier.send_telegram 4000+ ayithe TRUNCATE chestundi (v84 —
    reports ki correct). Broadcasts ki full text kavali → split into parts.
    """
    text_html = (text_html or "").strip()
    if len(text_html) <= limit:
        return [text_html] if text_html else []
    chunks: List[str] = []
    buf = ""
    for para in text_html.split("\n"):
        # okka paragraph eh limit kante pedda aithe hard-split
        while len(para) > limit:
            if buf:
                chunks.append(buf)
                buf = ""
            chunks.append(para[:limit])
            para = para[limit:]
        if len(buf) + len(para) + 1 > limit:
            chunks.append(buf)
            buf = para
        else:
            buf = (buf + "\n" + para) if buf else para
    if buf:
        chunks.append(buf)
    return chunks


# ------------------------------------------------------------------ commands

def tg_test() -> Tuple[bool, str]:
    """Connectivity ping — bot token + owner chat verify."""
    if not config.TELEGRAM_BOT_TOKEN:
        return False, "TELEGRAM_BOT_TOKEN ledu (.env lo pettandi)"
    if not (config.TELEGRAM_CHAT_ID or _registered_chat()):
        return False, "TELEGRAM_CHAT_ID ledu — bot ki /start pampinchandi"
    now = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    msg = (f"🏓 <b>StudentUp Telegram test</b>\n"
           f"Time: {now}\n"
           f"Channel broadcast: {'✅ configured' if channel_configured() else '⚠️ not configured'}\n"
           f"v91 tools: OK")
    ok = notifier.send_telegram(msg)
    return ok, "ping pampinchindi ✅" if ok else "sendMessage fail (token/chat id check)"


def _registered_chat() -> str:
    """approval_bot /start fallback chat id."""
    try:
        from . import state
        return state.meta_get(config.STATE_PATH, "telegram_chat_id") or ""
    except Exception:  # noqa: BLE001
        return ""


def tg_broadcast(message: str) -> Tuple[bool, str]:
    """Channel ki manual announcement (chunks ga, full text)."""
    message = (message or "").strip()
    if not message:
        return False, "message khali ga undi"
    if not channel_configured():
        return False, ("TELEGRAM_BOT_TOKEN + TELEGRAM_CHANNEL_CHAT_ID kavali "
                       "(private channel aithe -100… id; bot channel lo admin ga undali)")
    from .notifier import esc
    chunks = _split_chunks(esc(message))
    sent = 0
    for i, part in enumerate(chunks, 1):
        body = part if len(chunks) == 1 else f"{part}\n<i>({i}/{len(chunks)})</i>"
        if notifier.send_telegram(body, chat_id=config.TELEGRAM_CHANNEL_CHAT_ID):
            sent += 1
        else:
            return False, f"chunk {i}/{len(chunks)} fail ayyindi"
    return True, f"channel ki {sent}/{len(chunks)} message(s) pampinchindi ✅"


def tg_alert(code: str, message: str, severity: str = "info") -> Tuple[bool, str]:
    """Site-side v90 notify queue ki push (WP REST studentup/v1/notify).

    critical aithe theme public banner render chestundi (notify_banner ON lo).
    WP unreachable aite warning return — cron break kaadu.
    """
    import requests

    code = (code or "").strip().lower().replace(" ", "_")
    message = (message or "").strip()
    if not code or not message:
        return False, "code + message rendu kavali"
    if severity not in ("info", "warn", "critical"):
        severity = "info"
    site = (config.WP_SITE or "").rstrip("/")
    if not site or not config.WP_USERNAME or not config.WP_APP_PASSWORD:
        return False, "WP creds ledu (WP_SITE + WP_USERNAME + WP_APP_PASSWORD)"
    url = f"{site}/wp-json/studentup/v1/notify"
    try:
        resp = requests.post(
            url,
            json={"code": code[:60], "message": message[:300], "severity": severity},
            auth=(config.WP_USERNAME, config.WP_APP_PASSWORD),
            timeout=config.HTTP_TIMEOUT,
        )
        if resp.status_code == 200 and resp.json().get("ok"):
            extra = " → public banner (critical)" if severity == "critical" else ""
            return True, f"notify queue ki push ayyindi: {code}{extra} ✅"
        return False, f"WP respond: {resp.status_code} {resp.text[:120]}"
    except requests.RequestException as exc:
        return False, f"WP reach avvaledu: {type(exc).__name__}"


def tg_whoami() -> Tuple[bool, str]:
    """getMe — bot identity verify (debug)."""
    if not config.TELEGRAM_BOT_TOKEN:
        return False, "TELEGRAM_BOT_TOKEN ledu"
    import requests
    try:
        resp = requests.get(
            f"{config.TELEGRAM_API_BASE}/bot{config.TELEGRAM_BOT_TOKEN}/getMe",
            timeout=config.HTTP_TIMEOUT,
        )
        data = resp.json() if resp.status_code == 200 else {}
        if data.get("ok"):
            me = data.get("result", {})
            return True, f"@{me.get('username')} (id {me.get('id')})"
        return False, f"getMe fail: {resp.text[:120]}"
    except requests.RequestException as exc:
        return False, f"network: {type(exc).__name__}"


# ------------------------------------------------------------------- CLI glue

def run_cli(args) -> int:
    """main.py nunchi call — oka command matrame run avutundi."""
    if getattr(args, "tg_test", False):
        ok, detail = tg_test()
        who_ok, who = tg_whoami()
        print(f"  tg-test: {detail}")
        if who_ok:
            print(f"  bot identity: {who}")
        print("  ℹ️  creds lekapoina exit 0 — cron break kaadu")
        return 0
    if getattr(args, "tg_broadcast", None):
        ok, detail = tg_broadcast(args.tg_broadcast)
        print(f"  tg-broadcast: {detail}")
        return 0
    if getattr(args, "tg_alert", None):
        parts = str(args.tg_alert).split("|", 1)
        if len(parts) == 2:
            code, message = parts[0], parts[1]
        else:
            code, message = "manual_alert", parts[0]
        sev = getattr(args, "tg_severity", "info") or "info"
        ok, detail = tg_alert(code, message, sev)
        print(f"  tg-alert: {detail}")
        return 0
    return 1
