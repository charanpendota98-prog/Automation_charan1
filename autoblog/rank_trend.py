# -*- coding: utf-8 -*-
"""v181 — GSC TIME-SERIES → DECAY DETECTION → REFRESH QUEUE.

Mundu unna `gsc_refresh` okka snapshot ni chusi "opportunity" cheppedi;
`gsc_api` okkasari "previous sync" tho polchedi. Kaani top sites **time-series**
naduputayi: page scoring lo *padutunda, perugutunda* ani 7/28-day trend chustaru.

Ee module:
  1. prathi GSC Pages CSV (leda API rows) ni **history snapshot** ga save chestundi
     (`logs/rank-history.json`, date-wise; same date malli vaste replace — idempotent).
  2. latest vs 7/28-day baseline ni polchi prathi URL ni classify chestundi:
     NEW · RISING · FLAT · DECAYING.
  3. **decaying pages → refresh queue** (`output/refresh-queue.json`) + gsc_refresh
     priority store lo scores ni update chestundi — so mee existing `--update`
     pipeline data-driven avutundi (age-batti kaadu, traffic loss batti).

Honest limits: GSC data lo unna pages matrame · small samples (clicks < 3) ni
DECAY ani cheppadu · emi auto-publish/auto-rewrite cheyyadu (queue → human gate).

CLI:
    python run.py --rank-trend --csv Pages.csv        # ingest + trend + queue
    python run.py --rank-trend --csv Pages.csv --notify
    python run.py --rank-trend                        # history report (no ingest)
"""
from __future__ import annotations

import json
import logging
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import config, gsc_refresh, state

log = logging.getLogger("autoblog.rank_trend")

# Classification thresholds (documented, conservative — false alarms tagginchadaniki)
DECAY_CLICK_DROP = 0.25      # clicks 25%+ padithe
DECAY_POS_DROP = 5.0         # leda avg position 5+ spots padithe
RISE_CLICK_GAIN = 0.20       # clicks 20%+ perigithe
RISE_POS_GAIN = 3.0
MIN_CLICKS = 3               # ee chinna sample tho decay cheppamu


# ------------------------------------------------------------------ storage

def _path(path: Optional[Path] = None) -> Path:
    return Path(path or config.RANK_HISTORY_PATH)


def load_history(path: Optional[Path] = None) -> Dict:
    p = _path(path)
    if not p.exists():
        return {"snapshots": []}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data.get("snapshots"), list):
            return {"snapshots": []}
        return data
    except (OSError, ValueError):
        return {"snapshots": []}


def save_history(data: Dict, path: Optional[Path] = None) -> Path:
    p = _path(path)
    snaps = sorted(data.get("snapshots", []), key=lambda s: s.get("date", ""))
    data["snapshots"] = snaps[-config.RANK_HISTORY_MAX_SNAPSHOTS:]
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return p


def _slim(rows: List[Dict]) -> List[Dict]:
    """Rows ni compact shape ki (url, clicks, impressions, ctr, position, score)."""
    out = []
    for r in rows:
        if not r.get("url"):
            continue
        out.append({"url": r["url"], "clicks": int(r.get("clicks", 0)),
                    "impressions": int(r.get("impressions", 0)),
                    "ctr": round(float(r.get("ctr", 0.0)), 5),
                    "position": round(float(r.get("position", 0.0)), 2),
                    "score": round(float(r.get("score", 0.0)), 1)})
    return sorted(out, key=lambda r: r["url"])


def ingest(rows: List[Dict], day: Optional[str] = None,
           path: Optional[Path] = None) -> Dict:
    """Snapshot add/replace (same date → replace; sort + cap)."""
    day = day or date.today().isoformat()
    data = load_history(path)
    data["snapshots"] = [s for s in data["snapshots"] if s.get("date") != day]
    data["snapshots"].append({"date": day, "rows": _slim(rows)})
    save_history(data, path)
    return data


def ingest_csv(csv_path: str, day: Optional[str] = None,
               path: Optional[Path] = None) -> Dict:
    """GSC Pages CSV → snapshot (parse gsc_refresh tho — single source of truth)."""
    rows = gsc_refresh.parse(csv_path)
    ingest(rows, day=day, path=path)
    # mee existing refresh pipeline kuda ee fresh numbers tho update avvali
    state.meta_set(config.STATE_PATH, gsc_refresh.KEY,
                   json.dumps({"source": "rank-trend-csv", "rows": rows},
                              ensure_ascii=False))
    return {"rows": len(rows), "day": day or date.today().isoformat(),
            "history": load_history(path)}


# ------------------------------------------------------------------- trend

def _by_url(snapshot: Dict) -> Dict[str, Dict]:
    return {r["url"]: r for r in snapshot.get("rows", []) if r.get("url")}


def _baseline(snapshots: List[Dict], latest_date: str, window: int) -> Optional[Dict]:
    """latest_date - window ki daggaraga unna snapshot (lekapote earliest)."""
    try:
        target = datetime.fromisoformat(latest_date).date() - timedelta(days=window)
    except ValueError:
        return None
    older = [s for s in snapshots if s.get("date", "") < latest_date]
    if not older:
        return None
    return min(older, key=lambda s: abs((datetime.fromisoformat(s["date"]).date()
                                         - target).days))


def trend(window: int = 7, path: Optional[Path] = None) -> Dict:
    """latest snapshot ni window-day baseline tho polchi movements."""
    data = load_history(path)
    snaps = sorted(data.get("snapshots", []), key=lambda s: s.get("date", ""))
    if len(snaps) < 2:
        return {"ready": False, "need": 2, "have": len(snaps),
                "latest": snaps[-1]["date"] if snaps else "",
                "hint": "Roju/weekly GSC CSV ingest cheyandi — window fill avutundi"}
    latest = snaps[-1]
    base = _baseline(snaps, latest["date"], window)
    if base is None:
        return {"ready": False, "need": 2, "have": len(snaps), "latest": latest["date"],
                "hint": "baseline snapshot ledu"}
    now, before = _by_url(latest), _by_url(base)
    moves = []
    for url, cur in now.items():
        old = before.get(url)
        if old is None:
            moves.append({"url": url, "state": "NEW", "clicks": cur["clicks"],
                          "clicks_before": 0, "clicks_delta": cur["clicks"],
                          "position": cur["position"], "position_before": 0.0,
                          "position_delta": 0.0,
                          "impressions": cur["impressions"]})
            continue
        cb, cc = old["clicks"], cur["clicks"]
        pb, pc = old["position"], cur["position"]
        click_delta = cc - cb
        pos_delta = round(pc - pb, 2)          # + = padindi (worse)
        pct = (click_delta / cb) if cb else (1.0 if cc else 0.0)
        state_ = "FLAT"
        if cb >= MIN_CLICKS and (pct <= -DECAY_CLICK_DROP or pos_delta >= DECAY_POS_DROP):
            state_ = "DECAYING"
        elif cc >= MIN_CLICKS and (pct >= RISE_CLICK_GAIN or pos_delta <= -RISE_POS_GAIN):
            state_ = "RISING"
        elif cb < MIN_CLICKS and cc >= MIN_CLICKS:
            state_ = "RISING"
        moves.append({"url": url, "state": state_, "clicks": cc, "clicks_before": cb,
                      "clicks_delta": click_delta, "click_pct": round(pct, 3),
                      "position": pc, "position_before": pb, "position_delta": pos_delta,
                      "impressions": cur["impressions"]})
    bucket = lambda s: sorted([m for m in moves if m["state"] == s],
                              key=lambda m: m["clicks_delta"])  # noqa: E731
    decaying = [m for m in moves if m["state"] == "DECAYING"]
    decaying.sort(key=lambda m: (m["clicks_delta"], -m["position_delta"]))
    return {"ready": True, "latest": latest["date"], "baseline": base["date"],
            "window": window, "urls": len(moves),
            "decaying": decaying, "rising": [m for m in moves if m["state"] == "RISING"],
            "new": [m for m in moves if m["state"] == "NEW"],
            "flat": len([m for m in moves if m["state"] == "FLAT"])}


def queue_refresh(rep: Dict, path: Optional[Path] = None) -> Optional[Path]:
    """Decaying pages ni refresh queue ki (merge + first_seen preserve)."""
    if not rep.get("ready") or not rep.get("decaying"):
        return None
    path = Path(path or config.RANK_REFRESH_QUEUE)
    existing: Dict[str, Dict] = {}
    if path.exists():
        try:
            for row in json.loads(path.read_text(encoding="utf-8")).get("queue", []):
                existing[row.get("url", "")] = row
        except (OSError, ValueError):
            existing = {}
    today = date.today().isoformat()
    for m in rep["decaying"]:
        row = existing.get(m["url"]) or {"url": m["url"], "first_seen": today,
                                         "status": "new"}
        row.update({"clicks_before": m["clicks_before"], "clicks": m["clicks"],
                    "clicks_delta": m["clicks_delta"],
                    "position_before": m["position_before"], "position": m["position"],
                    "position_delta": m["position_delta"], "last_seen": today,
                    "baseline": rep["baseline"]})
        existing[m["url"]] = row
    queue = sorted(existing.values(), key=lambda r: int(r.get("clicks_delta", 0)))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"updated": datetime.now().isoformat(timespec="seconds"),
                                "window": rep["window"], "queue": queue},
                               ensure_ascii=False, indent=1), encoding="utf-8")
    return path


def refresh_scores(rep: Dict, path: Optional[Path] = None) -> int:
    """gsc_refresh store lo unna decaying URLs scores ni fresh data tho update.

    Existing pipeline (`--update`, auto-refresh) ide store chaduvutundi — so
    data-driven priority automatic ga apply avutundi. Kotha URLs add cheyyamu
    (CSV ingest appude chestundi).
    """
    if not rep.get("ready"):
        return 0
    data = load_history(path)
    latest = [s for s in data["snapshots"] if s["date"] == rep["latest"]]
    if not latest:
        return 0
    fresh = {r["url"]: r for r in latest[0]["rows"]}
    try:
        store = gsc_refresh.load()
    except Exception:  # noqa: BLE001
        return 0
    changed = 0
    for m in rep["decaying"]:
        row = fresh.get(m["url"])
        if not row or m["url"] not in store:
            continue
        store[m["url"]].update({"clicks": row["clicks"], "impressions": row["impressions"],
                                "ctr": row["ctr"], "position": row["position"],
                                "score": gsc_refresh.score(row["impressions"], row["clicks"],
                                                           row["ctr"], row["position"])})
        changed += 1
    if changed:
        state.meta_set(config.STATE_PATH, gsc_refresh.KEY,
                       json.dumps({"source": "rank-trend-refresh",
                                   "rows": list(store.values())}, ensure_ascii=False))
    return changed


def report_text(rep: Dict, queue_path: Optional[Path] = None) -> str:
    if not rep.get("ready"):
        return ("<b>📉 RANK TREND</b>\nData saripoyindi ledu: "
                f"{rep.get('have', 0)} snapshot(s) unnayi, 2+ kavali.\n{rep.get('hint', '')}")
    lines = ["<b>📉 RANK TREND (GSC)</b>",
             f"{rep['baseline']} → {rep['latest']} ({rep['window']}d) · URLs: {rep['urls']}",
             f"🟢 rising {len(rep['rising'])} · 🔴 decaying {len(rep['decaying'])} "
             f"· 🆕 new {len(rep['new'])} · flat {rep['flat']}"]
    for m in rep["decaying"][:5]:
        lines.append(f"  🔴 {m['url'].split('/')[-2] if m['url'].endswith('/') else m['url'].split('/')[-1]}"
                     f" — {m['clicks_before']}→{m['clicks']} clicks "
                     f"(pos {m['position_before']}→{m['position']})")
    for m in rep["rising"][:3]:
        lines.append(f"  🟢 +{m['clicks_delta']} clicks — {m['url'].split('/')[-1]}")
    if queue_path:
        lines.append(f"refresh queue: {queue_path}")
    lines.append("Note: refresh = human-reviewed update (auto-rewrite ledu).")
    return "\n".join(lines)


# --------------------------------------------------------------------- CLI

def run_cli(csv_path: str = "", window: int = 7, notify: bool = False,
            queue: bool = True, days_note: str = "") -> int:
    print("=" * 74)
    print("  📉 RANK TREND LOOP (v181) — GSC time-series → decay → refresh queue")
    print("=" * 74)
    if csv_path:
        try:
            res = ingest_csv(csv_path)
        except (OSError, ValueError) as exc:
            print(f"  ❌ CSV: {exc}")
            print("     Search Console > Performance > Pages > Export (CSV) use cheyandi")
            return 1
        print(f"  ✅ snapshot: {res['day']} · {res['rows']} pages "
              f"(history {len(res['history']['snapshots'])} snapshots)")
    rep = trend(window=window)
    if not rep.get("ready"):
        print(f"  ⏳ trend ki inka data ledu — {rep.get('have', 0)} snapshot(s). "
              f"{rep.get('hint', '')}")
        print(f"     history: {config.RANK_HISTORY_PATH}")
        return 0
    print(f"  baseline {rep['baseline']} → {rep['latest']} ({rep['window']}d) · "
          f"URLs {rep['urls']}")
    print("-" * 74)
    print(f"  🟢 rising {len(rep['rising'])} · 🔴 decaying {len(rep['decaying'])} "
          f"· 🆕 new {len(rep['new'])} · flat {rep['flat']}")
    for m in rep["decaying"][:12]:
        print(f"     🔴 {m['url']}")
        print(f"        clicks {m['clicks_before']} → {m['clicks']} "
              f"({m['clicks_delta']:+d}) · position {m['position_before']} → "
              f"{m['position']} ({m['position_delta']:+.1f})")
    for m in rep["rising"][:6]:
        print(f"     🟢 +{m['clicks_delta']} clicks · {m['url']}")
    qp = queue_refresh(rep) if queue else None
    updated = refresh_scores(rep)
    if qp:
        print("-" * 74)
        print(f"  📝 refresh queue: {qp}")
        print(f"     ({len(rep['decaying'])} pages — mee --update pipeline veetini "
              f"data-driven priority tho teesukuntundi)")
    if updated:
        print(f"  🔄 gsc_refresh priority store: {updated} URL scores updated")
    if notify:
        from . import notifier

        ok = notifier.send_telegram(report_text(rep, qp))
        print(f"  📨 Telegram: {'pampamu' if ok else 'skip (token/chat ledu)'}")
    return 0
