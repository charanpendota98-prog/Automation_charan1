# -*- coding: utf-8 -*-
"""v164 — Revenue plan: okate prioritised action list (₹ impact tho).

Manaki ippudu chala reports unnayi — `--rpm-report`, `--ctr-boost`,
`--slot-lab`, `--live-seo`. Kani owner ki kavalsindi report kaadu:
**"reepu nenu emi cheyyali, danivalla enta vastundi"**.

Ee module rendu real exports ni join chestundi:

  GSC CSV      : page, clicks, impressions, ctr, position
  AdSense CSV  : page, pageviews/impressions, revenue

...and moodu rakala opportunities ni ₹ upside batti rank chestundi:

  1. CTR GAP   — impressions ekkuva, CTR position ki radaa takkuva.
                 Title/meta rewrite → extra clicks → extra ₹ (site RPM batti).
  2. RPM GAP   — pageviews ekkuva, RPM site average kanna chala takkuva.
                 Ad layout problem. Site average ki thechhi enta vastundo.
  3. POSITION  — position 11-20 (page 2). Konchem content/internal links tho
                 page 1 ki vasthe clicks pedda jump.

**Prati ₹ number mee sonta data nunchi ne.** Industry benchmark ledu,
"3x penchutundi" laanti promise ledu. Data lekapothe plan ledu — adi ne
cheptundi.

CLI: python run.py --revenue-plan gsc.csv --adsense adsense.csv
"""
from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

MIN_IMPRESSIONS = 300      # ee lopu data noise
MIN_VIEWS = 300
PAGE2_MIN, PAGE2_MAX = 10.5, 20.5

# Position -> realistic organic CTR. Ivi mana sonta average nunchi
# calibrate avutayi (kinda chudandi) - hardcoded benchmark kaadu.
_CTR_CURVE = {1: 0.28, 2: 0.16, 3: 0.11, 4: 0.08, 5: 0.06,
              6: 0.05, 7: 0.04, 8: 0.035, 9: 0.03, 10: 0.025}

_URL_KEYS = ("page", "url", "landing page", "top pages", "address")
_CLICK_KEYS = ("clicks", "click")
_IMPR_KEYS = ("impressions", "impression")
_POS_KEYS = ("position", "average position", "avg. position")
_VIEW_KEYS = ("pageviews", "page views", "views", "impressions")
_REV_KEYS = ("revenue", "earnings", "estimated earnings")


def _pick(row: Dict, keys: Tuple[str, ...]) -> Optional[str]:
    low = {str(k).strip().lower(): v for k, v in row.items() if k}
    for key in keys:
        if key in low and str(low[key]).strip() != "":
            return str(low[key]).strip()
    for key in keys:
        for col, val in low.items():
            if key in col and str(val).strip() != "":
                return str(val).strip()
    return None


def _num(raw: Optional[str]) -> float:
    if raw is None:
        return 0.0
    txt = str(raw).replace(",", "").replace("%", "")
    cleaned = re.sub(r"[^\d.\-]", "", txt)
    try:
        return float(cleaned) if cleaned not in ("", "-", ".") else 0.0
    except ValueError:
        return 0.0


def _slug(url: str) -> str:
    """Rendu exports lo URL format veru untundi — path matrame compare."""
    url = re.sub(r"^https?://[^/]+", "", url.strip())
    url = url.split("?")[0].split("#")[0]
    return "/" + url.strip("/")


def read_gsc(path: Path) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    with path.open(newline="", encoding="utf-8-sig", errors="ignore") as fh:
        for row in csv.DictReader(fh):
            url = _pick(row, _URL_KEYS)
            if not url:
                continue
            out[_slug(url)] = {
                "clicks": _num(_pick(row, _CLICK_KEYS)),
                "impressions": _num(_pick(row, _IMPR_KEYS)),
                "position": _num(_pick(row, _POS_KEYS)),
            }
    return out


def read_adsense(path: Path) -> Dict[str, Dict]:
    out: Dict[str, Dict] = {}
    with path.open(newline="", encoding="utf-8-sig", errors="ignore") as fh:
        for row in csv.DictReader(fh):
            url = _pick(row, _URL_KEYS)
            if not url:
                continue
            out[_slug(url)] = {
                "views": _num(_pick(row, _VIEW_KEYS)),
                "revenue": _num(_pick(row, _REV_KEYS)),
            }
    return out


def expected_ctr(position: float, curve: Dict[int, float]) -> float:
    if position <= 0:
        return 0.0
    slot = int(round(position))
    if slot in curve:
        return curve[slot]
    return 0.012 if slot <= 20 else 0.005


def calibrate(gsc: Dict[str, Dict]) -> Dict[int, float]:
    """Mana sonta data nunchi CTR curve. Data sariponi positions ki default."""
    buckets: Dict[int, List[float]] = {}
    for row in gsc.values():
        if row["impressions"] < MIN_IMPRESSIONS or row["position"] <= 0:
            continue
        slot = int(round(row["position"]))
        if slot > 10:
            continue
        buckets.setdefault(slot, []).append(row["clicks"] / row["impressions"])
    curve = dict(_CTR_CURVE)
    for slot, values in buckets.items():
        if len(values) >= 3:      # 3 pages kanna thakkuva unte noise
            curve[slot] = sum(values) / len(values)
    return curve


def build(gsc: Dict[str, Dict], ads: Dict[str, Dict]) -> Dict:
    total_views = sum(a["views"] for a in ads.values())
    total_rev = sum(a["revenue"] for a in ads.values())
    site_rpm = (total_rev / total_views * 1000.0) if total_views else 0.0
    curve = calibrate(gsc)

    actions: List[Dict] = []

    for url, g in gsc.items():
        a = ads.get(url, {})
        views = a.get("views", 0.0)
        rev = a.get("revenue", 0.0)
        rpm = (rev / views * 1000.0) if views else 0.0

        # 1) CTR gap
        if g["impressions"] >= MIN_IMPRESSIONS and g["position"] > 0:
            have = g["clicks"] / g["impressions"]
            want = expected_ctr(g["position"], curve)
            if want > have:
                extra_clicks = (want - have) * g["impressions"]
                if extra_clicks >= 10:
                    actions.append({
                        "type": "CTR",
                        "url": url,
                        "detail": (f"pos {g['position']:.1f} · CTR {have*100:.1f}% "
                                   f"vs {want*100:.1f}% expected"),
                        "fix": "title + meta description rewrite (python run.py --ctr-boost)",
                        "gain_clicks": round(extra_clicks),
                        "gain_inr": round(extra_clicks * site_rpm / 1000.0, 2),
                    })

        # 2) Page-2 positions
        if g["impressions"] >= MIN_IMPRESSIONS and PAGE2_MIN <= g["position"] <= PAGE2_MAX:
            # Page 2 -> position ~8 vasthe CTR ~3.5%
            extra_clicks = max(0.0, (curve.get(8, 0.035) - (g["clicks"] / max(1.0, g["impressions"])))
                               * g["impressions"])
            if extra_clicks >= 10:
                actions.append({
                    "type": "PAGE2",
                    "url": url,
                    "detail": f"pos {g['position']:.1f} — page 2 lo undi, {int(g['impressions'])} impressions",
                    "fix": "content deepen + internal links (python run.py --link-graph)",
                    "gain_clicks": round(extra_clicks),
                    "gain_inr": round(extra_clicks * site_rpm / 1000.0, 2),
                })

        # 3) RPM gap
        if views >= MIN_VIEWS and site_rpm > 0 and rpm < site_rpm * 0.6:
            actions.append({
                "type": "RPM",
                "url": url,
                "detail": f"RPM {rpm:.1f} vs site {site_rpm:.1f} · {int(views)} views",
                "fix": "ad layout chudandi (python run.py --slot-lab / --rpm-report)",
                "gain_clicks": 0,
                "gain_inr": round((site_rpm - rpm) * views / 1000.0, 2),
            })

    # Oke URL ki CTR and PAGE2 rendu vasthe upside rendu sarlu lekka
    # avutundi — kani rendintiki fix okate page. Pedda dhaanini ne unchutam;
    # total ni inflate cheyyadam ante meeku tappu plan ivvadam.
    best_organic: Dict[str, Dict] = {}
    kept: List[Dict] = []
    for a in actions:
        if a["type"] == "RPM":
            kept.append(a)
            continue
        prev = best_organic.get(a["url"])
        if prev is None or a["gain_inr"] > prev["gain_inr"]:
            best_organic[a["url"]] = a
    kept.extend(best_organic.values())
    actions = kept

    actions.sort(key=lambda a: a["gain_inr"], reverse=True)
    return {
        "site_rpm": round(site_rpm, 2),
        "total_views": int(total_views),
        "total_revenue": round(total_rev, 2),
        "matched_pages": len([u for u in gsc if u in ads]),
        "actions": actions,
        "upside_inr": round(sum(a["gain_inr"] for a in actions), 2),
    }


def run_cli(gsc_csv: str = "", adsense_csv: str = "", top: int = 12) -> int:
    print("=" * 74)
    print("  REVENUE PLAN — reepu emi cheyyalo, enta vastundo")
    print("=" * 74)

    if not gsc_csv or not adsense_csv:
        print("  Rendu exports kavali:")
        print("    GSC     → Search results → Pages → Export CSV")
        print("    AdSense → Reports → Pages → CSV (pageviews + earnings)")
        print("\n    python run.py --revenue-plan gsc.csv --adsense adsense.csv")
        print("-" * 74)
        print("  Data lekunda plan ivvanu — adi guess avutundi, plan kaadu.")
        return 1

    gp, ap = Path(gsc_csv), Path(adsense_csv)
    for p in (gp, ap):
        if not p.exists():
            print(f"  ❌ CSV dorakaledu: {p}")
            return 1

    rep = build(read_gsc(gp), read_adsense(ap))
    print(f"  Site RPM ₹{rep['site_rpm']} · {rep['total_views']:,} views · "
          f"₹{rep['total_revenue']:,.2f} · {rep['matched_pages']} pages matched")

    if not rep["matched_pages"]:
        print("-" * 74)
        print("  ⚠️  Rendu CSV lo oke URL dorakaledu — GSC full URL, AdSense path")
        print("      kavachu. Rendintlo 'Page' column unda ani chudandi.")
        return 1
    if not rep["actions"]:
        print("-" * 74)
        print("  ✅ Ee data lo clear opportunity ledu — data penchandi.")
        return 0

    print("-" * 74)
    icon = {"CTR": "🎯", "PAGE2": "📈", "RPM": "💰"}
    for i, a in enumerate(rep["actions"][:top], 1):
        clicks = f" (+{a['gain_clicks']} clicks)" if a["gain_clicks"] else ""
        print(f"\n  {i:2d}. {icon[a['type']]} {a['type']}  ₹{a['gain_inr']:,.2f}{clicks}")
        print(f"      {a['url']}")
        print(f"      {a['detail']}")
        print(f"      → {a['fix']}")

    print("\n" + "-" * 74)
    print(f"  Motham upside: ₹{rep['upside_inr']:,.2f} "
          f"({len(rep['actions'])} actions, ee period data batti)")
    print("  Idi mee sonta numbers nunchi — benchmark kaadu, promise kaadu.")
    print("  Traffic/RPM marithe ee plan kuda marutundi; nela ki okasari run cheyandi.")
    return 0
