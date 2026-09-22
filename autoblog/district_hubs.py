"""v96: DISTRICT JOB HUBS — TS 33 + AP 26 districts ki local landing pages.

Mee brief: "every distcrts pages jobs and job melas and local jobs".

Enduku idi kavali (honest reasoning, hype kaadu):
  · "Karimnagar jobs", "Guntur job mela", "Nizamabad notification" lanti
    LOCAL queries ki competition chala takkuva — national sites ee intent ni
    cover cheyyavu. Mana radar already 59 districts ni scan chestundi
    (`news_radar`), kaani aa items category posts loki matrame velthayi —
    district ki **okka landing page kuda ledu**. So aa long-tail traffic
    motham miss avutundi.
  · Ee module prathi district ki okka hub page build chestundi: aa district
    posts + TS/AP state pillars + job-mela section + neighbouring districts
    cross-links (topical cluster + internal-link depth).

THIN-PAGE GUARD (chala important — Google "scaled content abuse" +
AdSense "low value content" rules): district ki `MIN_POSTS` (default 3)
kanna takkuva posts unte aa page **create avvadu**. Khali shelves
publish cheyyam — 59 empty pages = spam signal, approval ki direct risk.

CLI:
  python run.py --district-hubs              # dry-run plan (network light)
  python run.py --district-hubs --apply      # WordPress lo pages upsert
"""
from __future__ import annotations

import logging
import re
from datetime import date
from typing import Dict, List, Optional

from . import config, news_radar, seo
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.district_hubs")

#: Thin page guard — inni posts unte matrame hub publish avutundi.
MIN_POSTS = int(getattr(config, "DISTRICT_HUB_MIN_POSTS", 3) or 3)

#: Prathi district page lo max posts list (page bloat + crawl budget).
MAX_POSTS = 14

STATE_NAME = {"TS": "Telangana", "AP": "Andhra Pradesh"}


def districts(state: str = "") -> List[tuple]:
    """(district, state-code) list — state="TS"/"AP" filter optional."""
    state = (state or "").strip().upper()
    if state == "TS":
        return [(d, "TS") for d in news_radar.TS_DISTRICTS]
    if state == "AP":
        return [(d, "AP") for d in news_radar.AP_DISTRICTS]
    return list(news_radar.ALL_DISTRICTS)


def hub_slug(district: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", (district or "").lower()).strip("-")
    return f"{base or 'district'}-jobs"[:60]


def hub_title(district: str, state: str, year: int) -> str:
    """≤70 chars (Rank Math title-length check) — keyword modata."""
    title = f"{district} Jobs {year} – Notifications, Job Melas & Results"
    if len(title) <= 70:
        return title
    return f"{district} Jobs {year} – Notifications & Job Melas"[:70]


def neighbours(district: str, state: str, limit: int = 6) -> List[str]:
    """Same-state districts (deterministic rotation) — cross-link cluster.

    Alphabetical list lo ee district tarvata vachchevi teesukuntam; chివరకి
    vellite modati nunchi wrap avutundi. Deterministic = prathi rebuild lo
    same links (Google ki stable internal-link graph).
    """
    pool = [d for d, s in districts(state)]
    if district not in pool:
        return pool[:limit]
    i = pool.index(district)
    out = []
    for step in range(1, len(pool)):
        out.append(pool[(i + step) % len(pool)])
        if len(out) >= limit:
            break
    return out


#: Hub lo chupinche update types (label, matching keywords).
_COVERAGE = [
    ("Government notifications", ("notification", "recruitment", "vacanc",
                                  "posts", "ఉద్యోగ", "నియామక")),
    ("Job melas & walk-ins", ("job mela", "mela", "walk-in", "walkin",
                              "job fair", "drive")),
    ("Results & merit lists", ("result", "merit", "cut off", "cutoff",
                               "ఫలిత")),
    ("Hall tickets & admit cards", ("hall ticket", "admit card",
                                    "హాల్ టికెట్")),
    ("Scholarships & fee reimbursement", ("scholarship", "fee reimbursement",
                                          "ఉపకార", "స్కాలర్")),
    ("Admissions & counselling", ("admission", "counselling", "counseling",
                                  "ప్రవేశ")),
]


def _coverage_block(district: str, posts: List[Dict]) -> str:
    """Ee district page lo NIJAMGA em cover avutundo (boilerplate kaadu).

    Prathi type ki live posts count chupistam — reader ki honest expectation,
    Google ki unique (page-specific) content. Okka post kuda leni types ni
    "త్వరలో" ga chupistam (fake claim ledu).
    """
    esc = seo._esc
    blob = " ".join((p.get("title") or "") for p in posts).lower()
    have, soon = [], []
    for label, keys in _COVERAGE:
        hits = sum(1 for p in posts
                   if any(k in (p.get("title") or "").lower() for k in keys))
        if hits:
            have.append(f"<li><strong>{esc(label)}</strong> — ప్రస్తుతం "
                        f"{hits} update{'s' if hits > 1 else ''}</li>")
        else:
            soon.append(f"<li>{esc(label)} — త్వరలో</li>")
    if not have:                       # అన్నీ generic → honest fallback
        have = [f"<li><strong>Local updates</strong> — {len(posts)} posts</li>"]
    rows = "".join(have) + "".join(soon)
    return (
        f'<h2 id="coverage">{esc(district)} — ఏమేమి కవర్ చేస్తున్నాం?</h2>'
        f"<ul>{rows}</ul>"
        "<p>పైన ఉన్న counts ఈ పేజీలో ప్రస్తుతం live గా ఉన్న posts నుంచి "
        "వచ్చినవి — కొత్త notification publish అయిన వెంటనే ఇవి automatic గా "
        "update అవుతాయి. ఏదైనా update missing అనిపిస్తే మాకు email చేయండి.</p>"
    )


def build_hub_html(district: str, state: str, posts: List[Dict],
                   year: Optional[int] = None,
                   site: str = "") -> str:
    """Pure builder — network lekunda testable.

    posts: [{"title":…, "link":…, "date":…}]
    """
    year = year or date.today().year
    site = (site or getattr(config, "WP_SITE", "") or "").rstrip("/")
    esc = seo._esc
    state_full = STATE_NAME.get(state, state)
    rows = "".join(
        '<tr><td><a href="{lk}">{ti}</a></td><td>{dt}</td></tr>'.format(
            lk=esc(p.get("link", "")), ti=esc((p.get("title") or "")[:70]),
            dt=esc((p.get("date") or "")[:10]))
        for p in posts[:MAX_POSTS]
    )
    near = "".join(
        '<li><a href="{base}/{sl}/">{d} Jobs {y}</a></li>'.format(
            base=esc(site), sl=hub_slug(n), d=esc(n), y=year)
        for n in neighbours(district, state)
    ) or "<li>—</li>"
    return (
        f"<p><strong>{esc(district)} జిల్లా</strong> ({esc(state_full)}) "
        f"లోని విద్యార్థులకు {year} లో వచ్చిన <strong>government jobs, "
        "job melas, walk-in drives, results మరియు hall tickets</strong> — "
        "అన్నీ ఒకే పేజీలో. కొత్త notification వచ్చిన 24 గంటల్లో ఈ పేజీకి "
        "add చేస్తాం; bookmark చేసుకోండి.</p>"
        f'<h2 id="latest-updates">{esc(district)} — Latest Updates</h2>'
        "<table><tr><th>Update</th><th>Published</th></tr>"
        f"{rows}</table>"
        f'<h2 id="job-melas">{esc(district)} Job Melas &amp; Walk-ins</h2>'
        "<p>జిల్లా employment exchange, skill development centres మరియు "
        "private companies నిర్వహించే <strong>job melas</strong> గురించి "
        "మేము verify చేసిన సమాచారం మాత్రమే పైన list చేస్తాం. Registration "
        "link, venue, date, eligibility — ప్రతి mela post లో ఉంటాయి. "
        "తేదీ దగ్గరపడే కొద్దీ venue మారే అవకాశం ఉంది, కాబట్టి వెళ్లే ముందు "
        "official notification ఒకసారి check చేసుకోండి.</p>"
        + _coverage_block(district, posts)
        + f'<h2 id="who-can-apply">ఎవరు apply చేయవచ్చు?</h2>'
        "<ul><li>10th / Inter / Degree / PG — qualification వారీగా filter</li>"
        "<li>Local district candidates కి priority ఉన్న notifications</li>"
        "<li>Freshers కి walk-in + job mela options</li>"
        "<li>Outsourcing &amp; contract posts (Anganwadi, ASHA, office staff)</li>"
        "</ul>"
        f'<h2 id="nearby-districts">{esc(state_full)} — Nearby District Pages</h2>'
        f"<ul>{near}</ul>"
        '<p style="font-size:13px;color:#57616B;">🔄 Last updated: '
        f"{date.today().isoformat()} · తప్పు కనిపిస్తే "
        f'<a href="mailto:{esc(config.SUPPORT_EMAIL)}">{esc(config.SUPPORT_EMAIL)}</a>'
        " — 24 గంటల్లో సరిచేస్తాం.</p>"
    )


def plan(state: str = "", wp: Optional[WordPressClient] = None) -> List[Dict]:
    """Prathi district ki emi jarugutundo report (publish cheyyadu).

    Returns: [{district, state, slug, posts, publish(bool), reason}]
    """
    wp = wp or WordPressClient()
    out: List[Dict] = []
    for district, st in districts(state):
        try:
            posts = wp.search_posts(district, per_page=MAX_POSTS) or []
        except Exception as exc:  # noqa: BLE001 — okka district fail skip
            log.warning("district search fail (%s): %s", district, exc)
            posts = []
        ok = len(posts) >= MIN_POSTS
        out.append({
            "district": district,
            "state": st,
            "slug": hub_slug(district),
            "posts": len(posts),
            "publish": ok,
            "reason": "" if ok else f"thin page guard: {len(posts)} < {MIN_POSTS} posts",
            "_posts": posts,
        })
    return out


def rebuild(state: str = "", apply: bool = False,
            wp: Optional[WordPressClient] = None) -> List[Dict]:
    """Hubs build chey. apply=False → dry-run plan matrame."""
    wp = wp or WordPressClient()
    year = date.today().year
    rows = plan(state, wp=wp)
    built = 0
    for row in rows:
        if not row["publish"]:
            log.info("DISTRICT HUB skip: %s — %s", row["district"], row["reason"])
            continue
        html = build_hub_html(row["district"], row["state"], row.pop("_posts"),
                              year=year)
        row["words"] = len(re.sub(r"<[^>]+>", " ", html).split())
        if not apply:
            row["dry"] = True
            continue
        try:
            res = wp.upsert_page(hub_title(row["district"], row["state"], year),
                                 html, row["slug"])
            row["link"] = res.get("link", "")
            built += 1
            log.info("DISTRICT HUB %s ✔ (%d posts) %s", row["slug"],
                     row["posts"], row["link"])
        except Exception as exc:  # noqa: BLE001 — okka page fail motham aapadu
            row["error"] = str(exc)[:160]
            log.warning("DISTRICT HUB %s failed: %s", row["slug"], exc)
    for row in rows:
        row.pop("_posts", None)
    log.info("District hubs: %d eligible · %d published (apply=%s)",
             sum(1 for r in rows if r["publish"]), built, apply)
    return rows


def run_cli(state: str = "", apply: bool = False) -> int:
    rows = rebuild(state, apply=apply)
    eligible = [r for r in rows if r["publish"]]
    skipped = [r for r in rows if not r["publish"]]
    print("=" * 66)
    print(f"  🗺️  DISTRICT JOB HUBS — {len(rows)} districts "
          f"({'APPLY' if apply else 'dry-run'})")
    print("=" * 66)
    for r in eligible[:60]:
        link = r.get("link") or r.get("error") or ("dry-run" if not apply else "")
        print(f"  ✔ {r['district']:<28} {r['posts']:>3} posts  /{r['slug']}  {link}")
    print(f"\n  eligible: {len(eligible)} · skipped (thin-page guard): {len(skipped)}")
    if skipped:
        print("  skipped ivi — inka posts vachaka automatic ga eligible avutayi:")
        print("   ", ", ".join(r["district"] for r in skipped[:12]),
              "…" if len(skipped) > 12 else "")
    if not apply:
        print("\n  Publish cheyyadaniki: python run.py --district-hubs --apply")
    return 0
