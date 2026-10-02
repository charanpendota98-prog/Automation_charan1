# -*- coding: utf-8 -*-
"""v183 — Daily forward list (WhatsApp-ready).

Enduku idi: bot post chestundi, kaani **reader daggara ki** velladaniki
WhatsApp groups #1 channel (students andaru akkade unnaru). Telegram digest
HTML (`<b>`, `<a href>`) — WhatsApp avi render cheyyadu (raw tags kanipistayi).

Ee module:
  - WordPress nunchi active opportunities teesukoni, category-wise
    (TS · AP · Central · Walk-in · **Outsourcing** · Scholarships · Results ·
    Hall Tickets · ...) plain-text list build chestundi,
  - `output/forward-list-YYYY-MM-DD.txt` (roju file) + `output/forward-list.txt`
    (latest) lo save chestundi — meeru copy chesi groups ki forward cheyyachu,
  - `--forward-send` tho Telegram/WhatsApp ki kuda pampagaladu (optional).

Doctrine: ee list **published posts** nunchi mattrame vastundi (auto-publish
ledu) · deadline/expiry gating same (expired posts list lo kanipinchavu) ·
stats/facts fabricate cheyyadu — title + mee site link matrame.
"""
from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List

IST = timezone(timedelta(hours=5, minutes=30))


def _today() -> date:
    return datetime.now(IST).date()


def build_whatsapp(site: str, rows: Iterable[Dict], today: date | None = None,
                   per_section: int = 6, today_block: bool = True) -> str:
    """Single copy-paste message (WhatsApp groups/status ki best)."""
    from . import opportunity_digest as od

    return od.render_whatsapp(site, rows, today=today, per_section=per_section,
                              today_block=today_block)


def build_telegram(site: str, rows: Iterable[Dict], today: date | None = None,
                   per_section: int = 6) -> List[str]:
    """Telegram HTML chunks (existing v121 digest format)."""
    from . import opportunity_digest as od

    return od.render_digest_messages(site, rows, today=today, per_section=per_section)


def build(fmt: str, site: str, rows: Iterable[Dict], today: date | None = None,
          per_section: int = 6) -> List[str]:
    """fmt = 'wa' (plain text) leda 'tg' (HTML chunks)."""
    fmt = (fmt or "wa").strip().lower()
    if fmt in ("tg", "telegram", "html"):
        return build_telegram(site, rows, today=today, per_section=per_section)
    text = build_whatsapp(site, rows, today=today, per_section=per_section)
    return [text] if text else []


def save(chunks: List[str], path: Path | None = None, today: date | None = None) -> List[Path]:
    """Roju file + latest file — rendu save (backup + copy-paste convenience)."""
    from . import config

    today = today or _today()
    written: List[Path] = []
    body = "\n\n".join(chunks).strip() + "\n"
    base = Path(path) if path else Path(getattr(config, "FORWARD_LIST_PATH",
                                                config.OUTPUT_DIR / "forward-list.txt"))
    daily = base.with_name(f"{base.stem}-{today.isoformat()}{base.suffix}")
    for target in (daily, base):
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(body, encoding="utf-8")
        written.append(target)
    return written


def gather(per_page: int = 100, max_pages: int = 2) -> List[Dict]:
    """WordPress nunchi active opportunities (published posts mattrame)."""
    from .wordpress_client import WordPressClient

    wp = WordPressClient()
    return wp.published_opportunities(max_pages=max_pages, per_page=per_page)


def run_cli(fmt: str = "wa", per_section: int = 6, send: bool = False,
            save_files: bool = True, today: date | None = None) -> int:
    """CLI: list ni build chesi print + save (+ optional send). rc 0 ok, 1 empty."""
    from . import config, notifier

    try:
        rows = gather()
    except Exception as exc:  # noqa: BLE001 — WP lekunda kuda honest message
        print(f"  ❌ WordPress nunchi rows teesukolekapoyamu: {exc}")
        print("     (WP_SITE / WP_APP_PASSWORD set aa? --forward-list offline lo")
        print("      pani cheyyadu — idi live site list.)")
        return 1

    chunks = build(fmt, config.WP_SITE, rows, today=today, per_section=per_section)
    if not chunks:
        print("  ℹ️  Active opportunities levu (posts publish avvaledu leda anni expire).")
        return 1

    print("\n".join(chunks))
    labels: List[str] = []
    if save_files:
        for target in save(chunks, today=today):
            labels.append(str(target))
        print("  📄 saved: " + " · ".join(labels))
    if send:
        ok = True
        if fmt in ("tg", "telegram", "html"):
            for chunk in chunks:
                ok = notifier.send_telegram(chunk) and ok
        else:
            # WhatsApp plain text: CallMeBot URL limit chinnadi → items madhya lo
            # split chesi pampistam (max 3 messages — spam kaadu).
            for chunk in chunks[:3]:
                for piece in _split_for_whatsapp(chunk, 850):
                    ok = notifier.send_whatsapp(piece) and ok
        print(("  📨 sent" if ok else "  ⚠️ send partial/failed") +
              " (Telegram/WhatsApp keys verify cheyyandi)")
    return 0


def _split_for_whatsapp(text: str, limit: int = 850) -> List[str]:
    """Chinnadi CallMeBot limit ki saripoyela item boundaries lo split."""
    if len(text) <= limit:
        return [text]
    pieces: List[str] = []
    current = ""
    for line in text.splitlines():
        if current and len(current) + 1 + len(line) > limit:
            pieces.append(current)
            current = line
        else:
            current = f"{current}\n{line}" if current else line
    if current:
        pieces.append(current)
    return pieces
