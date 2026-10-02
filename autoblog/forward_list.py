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

v184 — list management (open · expire · kotha):
  - **Expired out:** last date ayyipoyina posts list lo ki raavu (`is_active`).
  - **Stale out:** deadline cheppakapoyina 120+ rojula puratana posts teesestam
    (`OPPORTUNITY_STALE_DAYS`, 0 = off) — almost close ayyi untayi.
  - **Supersede:** same recruitment ki kotha post vaste puratana di list nunchi
    teesestam (`supersede()` — same section + title key, newest wins).
  - **State diff:** `output/forward-list-state.json` lo per-post first/last seen
    store avutundi → roju "🆕 kotha 4 · ❌ 3 out" + **enduku poyindi** reason
    (last date / stale / kotha version) CLI lo kanipistundi.
  - **Neat add:** kotha items ki 🆕 marker, 3 rojula lopu close avutunna vaatiki
    ⏰ "2 days left", section headers ki counts.

Doctrine: ee list **published posts** nunchi mattrame vastundi (auto-publish
ledu) · deadline/expiry gating same (expired posts list lo kanipinchavu) ·
stats/facts fabricate cheyyadu — title + mee site link matrame.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

IST = timezone(timedelta(hours=5, minutes=30))


def _today() -> date:
    return datetime.now(IST).date()


def build_whatsapp(site: str, rows: Iterable[Dict], today: date | None = None,
                   per_section: int = 6, today_block: bool = True,
                   new_ids: Iterable[object] | None = None,
                   changes: Dict | None = None) -> str:
    """Single copy-paste message (WhatsApp groups/status ki best)."""
    from . import opportunity_digest as od

    return od.render_whatsapp(site, rows, today=today, per_section=per_section,
                              today_block=today_block, new_ids=new_ids,
                              changes=changes)


def build_telegram(site: str, rows: Iterable[Dict], today: date | None = None,
                   per_section: int = 6) -> List[str]:
    """Telegram HTML chunks (existing v121 digest format)."""
    from . import opportunity_digest as od

    return od.render_digest_messages(site, rows, today=today, per_section=per_section)


def build(fmt: str, site: str, rows: Iterable[Dict], today: date | None = None,
          per_section: int = 6, new_ids: Iterable[object] | None = None,
          changes: Dict | None = None) -> List[str]:
    """fmt = 'wa' (plain text) leda 'tg' (HTML chunks)."""
    fmt = (fmt or "wa").strip().lower()
    if fmt in ("tg", "telegram", "html"):
        return build_telegram(site, rows, today=today, per_section=per_section)
    text = build_whatsapp(site, rows, today=today, per_section=per_section,
                          new_ids=new_ids, changes=changes)
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


def _print_changes(new_items: List[Dict], gone_items: List[Dict], state_file: Path) -> None:
    """Owner ki 'em marindo' report — WhatsApp message lo noise kaadu, CLI lo mattrame."""
    print("  📈 CHANGES (ninna list tho compare):")
    if new_items:
        print(f"     🆕 kothaga add ayyinavi ({len(new_items)}):")
        for row in new_items[:15]:
            print(f"        ➕ {str(row.get('title') or '')[:70]}  · {row.get('section')}")
    else:
        print("     🆕 kotha emi ledu")
    if gone_items:
        print(f"     ❌ list nunchi poyindi ({len(gone_items)}):")
        for row in gone_items[:15]:
            print(f"        ➖ {str(row.get('title') or '')[:60]}  — {row.get('reason')}")
    else:
        print("     ❌ poyindi emi ledu")
    print(f"     📄 state: {state_file}")


def run_cli(fmt: str = "wa", per_section: int = 6, send: bool = False,
            save_files: bool = True, today: date | None = None,
            show_changes: bool = True) -> int:
    """CLI: list ni build chesi print + save (+ optional send). rc 0 ok, 1 empty."""
    from . import config, notifier

    try:
        rows = gather()
    except Exception as exc:  # noqa: BLE001 — WP lekunda kuda honest message
        print(f"  ❌ WordPress nunchi rows teesukolekapoyamu: {exc}")
        print("     (WP_SITE / WP_APP_PASSWORD set aa? --forward-list offline lo")
        print("      pani cheyyadu — idi live site list.)")
        return 1

    try:
        new_items, gone_items, _data, state_file = diff_and_update(rows, today=today)
        changes = change_summary(new_items, gone_items)
        new_ids = [r.get("id") for r in new_items]
    except Exception as exc:  # noqa: BLE001 — diff fail aithe list eppudu vastundi
        print(f"  ⚠️ state diff fail ({exc}) — list continue avutundi")
        changes, new_ids, state_file = None, None, state_path()

    chunks = build(fmt, config.WP_SITE, rows, today=today, per_section=per_section,
                   new_ids=new_ids, changes=changes)
    if not chunks:
        if show_changes:
            _print_changes([], [], state_file)
        print("  ℹ️  Active opportunities levu (posts publish avvaledu leda anni expire).")
        return 1

    if show_changes:
        _print_changes(new_items, gone_items, state_file)
        print()
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

# ---------------------------------------------------------------------------
# v184: state + diff (ninna list tho compare — em kotha, em poyindi + enduku)
# ---------------------------------------------------------------------------

STATE_MAX_ITEMS = 500
STATE_KEEP_DAYS = 90


def state_path(path: Path | None = None) -> Path:
    from . import config

    if path:
        return Path(path)
    return Path(getattr(config, "FORWARD_LIST_STATE_PATH",
                        config.OUTPUT_DIR / "forward-list-state.json"))


def load_state(path: Path | None = None) -> Dict:
    target = state_path(path)
    if not target.exists():
        return {"updated": "", "items": {}}
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001 — corrupt file → fresh start (list eppudu block avvadu)
        return {"updated": "", "items": {}}
    if not isinstance(data, dict) or not isinstance(data.get("items"), dict):
        return {"updated": "", "items": {}}
    return data


def save_state(data: Dict, path: Path | None = None) -> Path:
    target = state_path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return target


def _reason_gone(entry: Dict, today: date, stale_days: int,
                 today_keys: Dict[str, Dict]) -> str:
    """Puratana post enduku list nunchi poyindi — honest reason (guess cheyyadu)."""
    from . import opportunity_digest as od

    last = od.parse_last_date(entry.get("last_date"))
    if last and last < today.isoformat():
        d = datetime.strptime(last, "%Y-%m-%d").date()
        return f"last date {d.strftime('%d %b')} ayyindi"
    key = f"{entry.get('section')}|{od.title_key(entry.get('title'))}"
    newer = today_keys.get(key)
    if newer and str(newer.get("id")) != str(entry.get("id")):
        return "kotha version vachindi (same recruitment)"
    published = od.parse_post_date(entry.get("date"))
    if published and stale_days and (today - published).days > stale_days:
        return f"{stale_days}+ rojula puratana (stale)"
    return "list nunchi teesaamu (active kaadu)"


def diff_and_update(rows: Iterable[Dict], today: date | None = None,
                    path: Path | None = None, stale_days: int | None = None
                    ) -> Tuple[List[Dict], List[Dict], Dict, Path]:
    """Roju list ni ninna state tho compare → (new_items, gone_items, state, path).

    new  = ippudu list lo unnayi, state lo eppudu ledu.
    gone = state lo unnayi, ippudu list lo levu + **enduku** poyindo reason.
    """
    from . import opportunity_digest as od

    today = today or _today()
    stale = od.stale_days_default() if stale_days is None else max(0, int(stale_days))
    active = od.normalize_rows(rows, today=today, stale_days=stale)
    data = load_state(path)
    items = dict(data.get("items") or {})
    today_ids = {str(r.get("id")): r for r in active if str(r.get("id") or "").strip()}
    today_keys = {f"{r.get('section')}|{od.title_key(r.get('title'))}": r for r in active}

    new_items: List[Dict] = []
    for rid, row in today_ids.items():
        entry = items.get(rid)
        if entry is None:
            new_items.append(row)
            items[rid] = {
                "section": row.get("section"), "title": row.get("title"),
                "last_date": row.get("last_date"), "date": str(row.get("date") or "")[:10],
                "first_seen": today.isoformat(),
            }
        items[rid]["last_seen"] = today.isoformat()
        items[rid]["section"] = row.get("section")
        items[rid]["title"] = row.get("title")
        items[rid]["last_date"] = row.get("last_date")

    gone_items: List[Dict] = []
    for rid, entry in list(items.items()):
        if rid in today_ids:
            continue
        entry = dict(entry)
        entry["id"] = rid
        entry["reason"] = _reason_gone(entry, today, stale, today_keys)
        gone_items.append(entry)
        if entry.get("reason", "").startswith("list nunchi teesaamu"):
            # Mullu gurthu: ippudu list lo ledu → state nunchi teesestam, kaani
            # ee run lo "gone" ga report chestam (variance kanipinchali).
            items.pop(rid, None)
        else:
            items.pop(rid, None)

    # prune: 90+ rojula nunchi kanipinchadam ledu → state lo pettukovadam waste
    cutoff = (today - timedelta(days=STATE_KEEP_DAYS)).isoformat()
    for rid in [k for k, v in items.items()
                if str(v.get("last_seen") or "") < cutoff]:
        items.pop(rid, None)
    if len(items) > STATE_MAX_ITEMS:
        keep = sorted(items.items(), key=lambda kv: str(kv[1].get("last_seen") or ""),
                      reverse=True)[:STATE_MAX_ITEMS]
        items = dict(keep)

    data = {"updated": today.isoformat(), "items": items}
    target = save_state(data, path)
    return new_items, gone_items, data, target


def change_summary(new_items: List[Dict], gone_items: List[Dict]) -> Dict:
    return {"new": len(new_items), "gone": len(gone_items)}
