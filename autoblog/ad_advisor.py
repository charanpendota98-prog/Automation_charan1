"""v57 — Ad advisor: network eligibility ni AUTOMATIC ga track chesi suggest chestundi.

"Eppudu e network ki apply cheyyali?" ani bot eppudu cheptundi:
  * traffic source: logs/traffic.json (GA4 CSV import / manual) leda .env (AD_MONTHLY_VIEWS)
  * prathi network threshold cross ayinappudu — Telegram alert (once per milestone)
  * AdSense approval (ADSENSE_APPROVED=1) ayinappudu — checklist alert
  * daari lo next enti, enta dooram undi, aa tarvata publisher id paristhiti

Nijam: traffic numbers mee GA4 nunchi ravali — bot guess cheyyadu. Data lekapote
"data ledu" ani cheptundi (fake numbers ivvadu). Approvals/revenue garanty kaavu.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from . import config, notifier

log = logging.getLogger(__name__)

# name, min pageviews/month, min sessions/month, min Tier-1 share, (rpm_low, rpm_high), note
NETWORKS = (
    dict(key="adsense", name="Google AdSense", min_views=0, min_sessions=0, tier1=0.0,
         rpm=(40, 250), note="approval-based · no traffic minimum"),
    dict(key="ezoic", name="Ezoic (Access Now)", min_views=0, min_sessions=1_000, tier1=0.0,
         rpm=(60, 350), note="header bidding + AdX · AdSense good standing kavali"),
    dict(key="monumetric", name="Monumetric", min_views=10_000, min_sessions=0, tier1=0.30,
         rpm=(80, 400), note="10k pageviews · mid-tier fill"),
    dict(key="adversal", name="Adversal / Revcontent", min_views=50_000, min_sessions=0,
         tier1=0.30, rpm=(40, 150), note="50k pageviews · native/video add-on"),
    dict(key="raptive", name="Raptive (ex-AdThrive)", min_views=25_000, min_sessions=0,
         tier1=0.50, rpm=(250, 900), rpm_tier1=(600, 3000),
         note="25k pageviews + ~50% Tier-1 · managed, exclusive"),
    dict(key="mediavine", name="Mediavine", min_views=0, min_sessions=50_000, tier1=0.50,
         rpm=(250, 900), rpm_tier1=(800, 3500),
         note="50k SESSIONS (~65-80k pageviews) + Tier-1 majority · Net-65, exclusive"),
)

PREMIUM = ("raptive", "mediavine")

# apply order when thresholds are met (practical, from AD_NETWORKS_PLAN.md)
APPLY_ORDER = ("adsense", "ezoic", "monumetric", "adversal", "raptive", "mediavine")

PUBLISHER_ID_NOTE = (
    "Publisher ID mareadu — mee AdSense account ki 'ca-pub-…' okate shaashvata id "
    "(account ki oka id, site ki kotha id ledu). Ezoic mee AdSense account ne vaadutundi "
    "(kotha pub id avasaram ledu; vaalla ads.txt partner lines add avutayi). "
    "Raptive/Mediavine vaalla sonta tags istharu — appudu AdSense line ads.txt nunchi "
    "thiyyali (exclusive), kaani mee AdSense account migilipotundi (vere site ki vaadukovachu)."
)


# --------------------------------------------------------------- traffic source
def parse_views(text: Any) -> int:
    t = str(text).strip().lower().replace(",", "")
    mult = 1
    if t.endswith("k"):
        mult, t = 1_000, t[:-1]
    elif t.endswith("l"):
        mult, t = 100_000, t[:-1]
    elif t.endswith("m"):
        mult, t = 1_000_000, t[:-1]
    return int(float(t) * mult)


def default_sessions(views: int) -> int:
    """Typical 1.6 pageviews/session (Mediavine counts sessions)."""
    return int(views / 1.6)


def traffic_path() -> Path:
    return Path(getattr(config, "AD_TRAFFIC_PATH", config.BASE_DIR / "logs" / "traffic.json"))


def state_path() -> Path:
    return Path(getattr(config, "AD_ADVISOR_STATE",
                        config.BASE_DIR / "logs" / "ad_advisor_state.json"))


def load_traffic(views: Optional[int] = None, sessions: Optional[int] = None,
                 tier1: Optional[float] = None) -> Dict[str, Any]:
    """Priority: CLI args → .env → logs/traffic.json. Data lekapote 'unknown'."""
    out: Dict[str, Any] = {"pageviews": 0, "sessions": 0, "tier1_share": 0.0,
                           "source": "unknown", "month": ""}
    path = traffic_path()
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            out.update({
                "pageviews": int(raw.get("pageviews") or raw.get("views") or 0),
                "sessions": int(raw.get("sessions") or 0),
                "tier1_share": float(raw.get("tier1_share") or 0.0),
                "source": str(raw.get("source") or "logs/traffic.json"),
                "month": str(raw.get("month") or ""),
            })
        except (OSError, ValueError) as exc:
            log.warning("traffic.json chadavaleka poyindi: %s", exc)
    env_views = int(getattr(config, "AD_MONTHLY_VIEWS", 0) or 0)
    if env_views:
        out.update({"pageviews": env_views, "source": ".env AD_MONTHLY_VIEWS",
                    "sessions": int(getattr(config, "AD_MONTHLY_SESSIONS", 0) or 0)
                    or default_sessions(env_views),
                    "tier1_share": float(getattr(config, "AD_TIER1_SHARE", 0.0) or 0.0)})
    if views:
        out.update({"pageviews": int(views), "source": "cli --traffic-views",
                    "sessions": int(sessions or default_sessions(int(views))),
                    "tier1_share": float(tier1 if tier1 is not None else out["tier1_share"])})
    if not out["sessions"] and out["pageviews"]:
        out["sessions"] = default_sessions(out["pageviews"])
    if sessions:
        out["sessions"] = int(sessions)
    if tier1 is not None:
        out["tier1_share"] = max(0.0, min(1.0, float(tier1)))
    out["known"] = bool(out["pageviews"])
    return out


def save_traffic(pageviews: int, sessions: int = 0, tier1_share: float = 0.0,
                 source: str = "manual", month: str = "") -> Path:
    path = traffic_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"month": month or datetime.now(timezone.utc).strftime("%Y-%m"),
               "pageviews": int(pageviews),
               "sessions": int(sessions or default_sessions(int(pageviews))),
               "tier1_share": round(max(0.0, min(1.0, float(tier1_share))), 4),
               "source": source,
               "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat()}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def import_ga4_csv(csv_path: str | Path) -> Dict[str, Any]:
    """GA4 / simple CSV → logs/traffic.json.

    Enoppulu: 'pageviews,views' · 'sessions' · 'tier1_share,tier1' · 'month,date'
    Numbers commas/thousands separators tho unna parvaledu.
    """
    import csv as _csv

    rows = list(_csv.DictReader(open(csv_path, encoding="utf-8-sig")))  # noqa: SIM115
    if not rows:
        raise ValueError("CSV khali undi")
    heads = {(h or "").strip().lower(): h for h in rows[0].keys()}

    def col(*names):
        for n in names:
            for low, orig in heads.items():
                if n in low:
                    return orig
        return None

    c_views, c_sessions = col("pageviews", "views", "screen_page_views"), col("sessions")
    c_tier, c_month = col("tier1", "tier_1", "tier-1"), col("month", "date")
    if not c_views and not c_sessions:
        raise ValueError("CSV lo 'pageviews'/'sessions' enoppulu kanipinchaledu — "
                         "GA4 export leda simple CSV (pageviews,sessions,tier1_share) vaadandi")

    def num(row, colname) -> int:
        if not colname:
            return 0
        raw = str(row.get(colname) or "0").replace(",", "").strip()
        try:
            return int(float(raw))
        except ValueError:
            return 0

    views = sum(num(r, c_views) for r in rows)
    sessions = sum(num(r, c_sessions) for r in rows)
    tier1 = 0.0
    if c_tier:
        vals = []
        for r in rows:
            raw = str(r.get(c_tier) or "").replace("%", "").strip()
            try:
                vals.append(float(raw))
            except ValueError:
                continue
        if vals:
            tier1 = max(vals) / 100.0 if max(vals) > 1 else max(vals)
    month = ""
    if c_month and rows:
        month = str(rows[-1].get(c_month) or "")[:7]
    path = save_traffic(views, sessions, tier1, source=f"ga4_csv:{Path(csv_path).name}", month=month)
    return {"pageviews": views, "sessions": sessions or default_sessions(views),
            "tier1_share": tier1, "path": str(path), "rows": len(rows)}


# --------------------------------------------------------------- advice engine
def assess(pageviews: int, sessions: int, tier1: float) -> List[Dict[str, Any]]:
    rows = []
    for n in NETWORKS:
        reasons = []
        if pageviews < n["min_views"]:
            reasons.append(f"{n['min_views']:,}+ pageviews/నెల కావాలి")
        if sessions < n["min_sessions"]:
            reasons.append(f"{n['min_sessions']:,}+ sessions/నెల కావాలి")
        if tier1 < n["tier1"]:
            reasons.append(f"{int(n['tier1'] * 100)}%+ Tier-1 (US/UK/Gulf) ట్రాఫిక్ కావాలి")
        eligible = not reasons
        rpm = n.get("rpm_tier1", n["rpm"]) if (eligible and tier1 >= n["tier1"]) else n["rpm"]
        rows.append({
            "key": n["key"], "name": n["name"], "eligible": eligible, "reasons": reasons,
            "rpm": rpm, "note": n["note"],
            "revenue_low": int(pageviews / 1000 * rpm[0]),
            "revenue_high": int(pageviews / 1000 * rpm[1]),
            "needs": {"pageviews": n["min_views"], "sessions": n["min_sessions"],
                      "tier1": n["tier1"]},
        })
    return rows


def uplift(base: Dict[str, Any], other: Dict[str, Any]) -> Tuple[int, int]:
    lo = (int(round((other["revenue_low"] / base["revenue_low"] - 1) * 100))
          if base["revenue_low"] else 0)
    hi = (int(round((other["revenue_high"] / base["revenue_high"] - 1) * 100))
          if base["revenue_high"] else 0)
    return lo, hi


def gap_to_next(rows: List[Dict[str, Any]], pageviews: int, sessions: int,
                tier1: float) -> List[Dict[str, Any]]:
    """Eligible kaani networks — enta dooram undo (views/sessions/tier1)."""
    out = []
    for r in rows:
        if r["eligible"]:
            continue
        need = r["needs"]
        if need["pageviews"] and pageviews < need["pageviews"]:
            out.append({"key": r["key"], "name": r["name"], "kind": "pageviews",
                        "need": need["pageviews"], "have": pageviews,
                        "gap": need["pageviews"] - pageviews})
        elif need["sessions"] and sessions < need["sessions"]:
            out.append({"key": r["key"], "name": r["name"], "kind": "sessions",
                        "need": need["sessions"], "have": sessions,
                        "gap": need["sessions"] - sessions})
        elif need["tier1"] and tier1 < need["tier1"]:
            out.append({"key": r["key"], "name": r["name"], "kind": "tier1",
                        "need": round(need["tier1"], 2), "have": round(tier1, 2),
                        "gap": 0})
    out.sort(key=lambda x: (x["kind"] != "pageviews", x["gap"]))
    return out


def next_action(rows: List[Dict[str, Any]], pageviews: int, sessions: int,
                tier1: float, adsense_approved: bool) -> Dict[str, Any]:
    """Ippudu cheyyalsina pani okati (priority order lo)."""
    elig = {r["key"]: r for r in rows if r["eligible"]}
    if not adsense_approved:
        return {"key": "adsense", "title": "AdSense ki apply cheyyandi (mundu ide)",
                "detail": ("AdSense approval tarvata ne Ezoic/Raptive/Mediavine channels "
                           "open avutayi (AdSense 'good standing' kavali)."),
                "steps": ["studentup.in live + policy pages (✅ ready)",
                          "Google Search Console + GA4 connect",
                          "AdSense account create → site add → verification code",
                          "Approval tarvata: .env ADSENSE_CLIENT_ID=ca-pub-… + "
                          "python tools/build_policy_pages.py (ads.txt auto) + ADSENSE_APPROVED=1"]}
    # eligible networks lo best per-view value (premium unte adi) → apply order fallback
    def _rank(key):
        r = elig[key]
        return (0 if key in PREMIUM else 1, -r["rpm"][1], APPLY_ORDER.index(key))

    for key in sorted(elig, key=_rank):
        if key in APPLY_ORDER[1:]:
            r = elig[key]
            premium = key in PREMIUM
            return {"key": key, "title": f"{r['name']} ki apply cheyyandi",
                    "detail": (f"Eligible ✔ · అంచనా ₹{r['revenue_low']:,}–₹{r['revenue_high']:,}/నెల"
                               + (" · EXCLUSIVE (AdSense ni replace chestundi)" if premium else "")),
                    "steps": (["Network site lo GA4 access amodinchandi (read-only)",
                               "VA/PA details + payment method (Net-30/45/65)",
                               "Approve ayyaka: partner lines ads/ads_txt_extra.txt lo paste → "
                               "python tools/build_policy_pages.py",
                               "Vaalla script/tags WordPress lo pettandi (WP_ADVANCED_CUSTOMIZATION.md)"]
                              if not premium else
                              ["Network site lo GA4 access + traffic proof (Tier-1 share)",
                               "Exclusive contract chaduvandi — AdSense tags thiyyali",
                               "Approve ayyaka ads.txt lo AdSense line thiyyandi + vaalla tags pettandi"])}
    gaps = gap_to_next(rows, pageviews, sessions, tier1)
    if gaps:
        g = gaps[0]
        if g["kind"] == "pageviews":
            detail = (f"Next: {g['name']} — {g['need']:,} pageviews kavali "
                      f"(ippudu {g['have']:,} · inka {g['gap']:,} dooram)")
        elif g["kind"] == "sessions":
            detail = (f"Next: {g['name']} — {g['need']:,} SESSIONS kavali "
                      f"(ippudu {g['have']:,} · inka {g['gap']:,}) — sessions penchalante "
                      f"ప్రతి విజిట్‌లో ఎక్కువ పేజీలు (hubs, quiz, related links)")
        else:
            detail = (f"Next: {g['name']} — Tier-1 ట్రాఫిక్ share "
                      f"{int(g['need']*100)}%+ kavali (ippudu {int(g['have']*100)}%) — "
                      f"విదేశీ ఉద్యోగాలు/NRI కంటెంట్ add cheyyandi")
        return {"key": g["key"], "title": "Traffic penchadam (automatic: bot roju 3–5 posts)",
                "detail": detail, "steps": ["Roju posts + shares (WhatsApp/Telegram groups)",
                                            "పాత పోస్టులు refresh + GSC lo submit",
                                            "Tier-1 ki: విదేశీ ఉద్యోగాలు, IELTS, visa pillars"]}
    return {"key": "sponsors", "title": "Anni networks eligible — direct sponsors ki dhigi",
            "detail": "Rate card (₹1,000–₹8,000/నెల) + leads — per-view value highest",
            "steps": ["SALES_KIT_ADVERTISERS.md templates tho roju 2 messages"]}


# --------------------------------------------------------------- milestones
def _load_state() -> Dict[str, Any]:
    path = state_path()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"milestones": {}, "notified": {}}


def _save_state(data: Dict[str, Any]) -> None:
    path = state_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check_milestones(pageviews: int, sessions: int, tier1: float,
                     notify: bool = False, rows: Optional[List[Dict[str, Any]]] = None
                     ) -> List[Dict[str, Any]]:
    """Kotha ga eligible ayyina networks (okka sari matrame notify)."""
    rows = rows or assess(pageviews, sessions, tier1)
    st = _load_state()
    fresh = []
    for r in rows:
        if not r["eligible"] or r["key"] == "adsense":
            continue
        if st["notified"].get(f"milestone:{r['key']}"):
            continue
        fresh.append(r)
        st["notified"][f"milestone:{r['key']}"] = datetime.now(timezone.utc).isoformat()[:19]
        st["milestones"][r["key"]] = {"pageviews": pageviews, "sessions": sessions,
                                      "tier1": tier1,
                                      "at": datetime.now(timezone.utc).isoformat()[:19]}
    if fresh:
        _save_state(st)
        if notify:
            for r in fresh:
                _notify_milestone(r, pageviews)
    return fresh


def _notify_milestone(r: Dict[str, Any], pageviews: int) -> None:
    extra = " · ⚠️ EXCLUSIVE (AdSense tags thiyyali)" if r["key"] in PREMIUM else ""
    text = (f"🎉 <b>Ad network milestone</b>{extra}\n\n"
            f"<b>{r['name']}</b> ki ippudu apply cheyyagalaru ✔\n"
            f"ట్రాఫిక్: {pageviews:,} pageviews/నెల\n"
            f"అంచనా: ₹{r['revenue_low']:,}–₹{r['revenue_high']:,}/నెల\n\n"
            f"Cheyyalsinadi:\n"
            f"1) GA4 read-only access ivvandi\n"
            f"2) Network application lo mee site details\n"
            f"3) Approve ayyaka partner lines → ads/ads_txt_extra.txt → "
            f"python tools/build_policy_pages.py\n\n"
            f"<i>Approval/revenue గ్యారంటీ కాదు — mee GA4 numbers verify chesukondi.</i>")
    notifier.send_telegram(text)


def notify_adsense_approved(notify: bool = False) -> bool:
    """ADSENSE_APPROVED=1 ayyaka okkasari checklist alert."""
    if not getattr(config, "ADSENSE_APPROVED", False):
        return False
    st = _load_state()
    if st["notified"].get("adsense:approved"):
        return False
    st["notified"]["adsense:approved"] = datetime.now(timezone.utc).isoformat()[:19]
    _save_state(st)
    if notify:
        from . import adsense_kit
        status, detail = adsense_kit.ads_txt_status()
        notifier.send_telegram(
            "💰 <b>AdSense APPROVED</b> — ippudu ee 4 panulu:\n\n"
            "1) .env: ADSENSE_CLIENT_ID=ca-pub-… (mee publisher id — idi mareadu)\n"
            "2) python tools/build_policy_pages.py → ads.txt live line auto\n"
            f"3) ads.txt status: {status} — {detail}\n"
            "4) ADSENSE_APPROVED=1 + CMP/consent verify (ADSENSE_CONSENT_PROVIDER)\n\n"
            "<i>Auto Ads ON undi; posta ki 2 ads cap (policy safe).</i>")
    return True


# --------------------------------------------------------------- rendering
def advice(pageviews: Optional[int] = None, sessions: Optional[int] = None,
           tier1: Optional[float] = None, notify: bool = False) -> Dict[str, Any]:
    t = load_traffic(pageviews, sessions, tier1)
    rows = assess(t["pageviews"], t["sessions"], t["tier1_share"])
    fresh = check_milestones(t["pageviews"], t["sessions"], t["tier1_share"],
                             notify=notify, rows=rows)
    adsense_notified = notify_adsense_approved(notify=notify)
    action = next_action(rows, t["pageviews"], t["sessions"], t["tier1_share"],
                         bool(getattr(config, "ADSENSE_APPROVED", False)))
    return {"traffic": t, "networks": rows, "action": action,
            "new_milestones": [r["key"] for r in fresh],
            "adsense_approved_notified": adsense_notified,
            "gaps": gap_to_next(rows, t["pageviews"], t["sessions"], t["tier1_share"]),
            "publisher_id_note": PUBLISHER_ID_NOTE}


def human(n: int) -> str:
    return f"{n:,}"


def render(result: Dict[str, Any]) -> str:
    t = result["traffic"]
    out = []
    A = out.append
    A("=" * 78)
    A("  AD ADVISOR — eppudu e network ki apply cheyyali (automatic)")
    A("=" * 78)
    if t["known"]:
        A(f"  ట్రాఫిక్ : {human(t['pageviews'])} pageviews · {human(t['sessions'])} sessions "
          f"· Tier-1 {int(t['tier1_share'] * 100)}%  (source: {t['source']})")
    else:
        A("  ట్రాఫిక్ : ❓ data ledu — GA4 CSV import leda logs/traffic.json pettandi:")
        A("            python run.py --ad-advisor --traffic-csv ga4.csv")
        A("            leda .env lo AD_MONTHLY_VIEWS=25000")
    A("")
    A(f"  {'నెట్‌వర్క్':<24} {'స్థితి':<14} {'నెలవారీ అంచనా':<20}")
    for r in result["networks"]:
        status = "✅ apply" if r["eligible"] else "⏳ " + (r["reasons"][0][:26] if r["reasons"] else "")
        A(f"  {r['name']:<24} {status:<14} "
          f"₹{human(r['revenue_low'])}–₹{human(r['revenue_high'])}")
    A("")
    act = result["action"]
    A(f"  ▶ IPPUDU CHEYYALSINADI: {act['title']}")
    A(f"    {act['detail']}")
    for i, s in enumerate(act["steps"], 1):
        A(f"      {i}. {s}")
    if result["new_milestones"]:
        A("")
        A(f"  🎉 KOTHA MILESTONE: {', '.join(result['new_milestones'])} — Telegram alert pampindi "
          f"(configure unte)")
    if result["gaps"]:
        A("")
        A("  ── Next thresholds (dooram) ──")
        for g in result["gaps"][:4]:
            if g["kind"] == "pageviews":
                A(f"    • {g['name']}: {human(g['need'])} pageviews kavali "
                  f"(inka {human(g['gap'])} dooram)")
            elif g["kind"] == "sessions":
                A(f"    • {g['name']}: {human(g['need'])} sessions kavali ({human(g['gap'])} dooram)")
            else:
                A(f"    • {g['name']}: Tier-1 {int(g['need'] * 100)}%+ kavali "
                  f"(ippudu {int(g['have'] * 100)}%) — 'విదేశీ ఉద్యోగాలు "
                  f"(Abroad Jobs)' pillar posts tho perugutundi")
    A("")
    A("  ── Publisher ID vishayam ──")
    A("    " + result["publisher_id_note"])
    A("")
    A("  Ee advisor bot roju okkasari automatic ga run avutundi (ADVISOR_HOUR) + prathi kotha")
    A("  milestone ki Telegram alert. ⚠️ Approval/RPM/revenue ఏవీ గ్యారంటీ కావు.")
    A("=" * 78)
    return "\n".join(out)
