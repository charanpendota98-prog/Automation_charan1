"""v43 — Advanced Ad Manager (owner ads: college banners, shop, services).

100% AdSense/FTC policy-safe self-serve ads that fill the slot space
before Google AdSense approval (and a capped complement after it).

Rules (hard, no overrides that would break policy):
  * Every ad block carries a visible "SPONSORED" label + disclosure line.
  * Every external link: rel="sponsored nofollow noopener" + target="_blank".
  * Count cap: MAX_PERSONAL_AD_SLOTS (default 2). If ADSENSE_APPROVED=1,
    cap drops to 1 (AdSense keeps 2 of the 3 in-content slots).
  * Never insert an ad within LINK_ADJACENCY of another <a> tag
    (AdSense "links near ads" rule — adjacent clicks ruin CTR + policy).
  * All text html.escaped; links must be absolute http(s) (XSS-safe).
  * Deterministic daily rotation (date hash) — no session state needed.
  * CLS-safe: every block reserves min-height (Core Web Vitals + viewability).

Inventory: ads/inventory.json (repo-tracked, owner-editable).
CLI:     run.py --ads        → inventory status + slot plan (dry)
         run.py --ads-demo   → output/ads-preview.html (visible sample)
"""
from __future__ import annotations

import hashlib
import html as _html
import json
import os
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

from . import config

ROOT = Path(__file__).resolve().parent.parent

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INVENTORY = REPO_ROOT / "ads" / "inventory.json"
LINK_ADJACENCY = 150  # chars — no other <a> may sit this close to an ad


# ---------------------------------------------------------------- inventory

def inventory_path() -> Path:
    p = (getattr(config, "ADS_INVENTORY_PATH", "") or "").strip()
    return Path(p) if p else DEFAULT_INVENTORY


def load_inventory(path: Optional[Path] = None) -> Dict:
    """Load ads/inventory.json. Missing/broken file → empty inventory
    (never blocks publishing — owner ads are revenue, not requirement)."""
    fp = path or inventory_path()
    try:
        data = json.loads(fp.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": 1, "policy": {}, "ads": []}
    if not isinstance(data, dict) or not isinstance(data.get("ads"), list):
        return {"version": 1, "policy": {}, "ads": []}
    data.setdefault("policy", {})
    return data


def policy_of(inv: Dict) -> Dict:
    p = dict(inv.get("policy") or {})
    p.setdefault("max_personal_ads_per_post", 2)
    p.setdefault("label", "Sponsored")
    p.setdefault("rel", "sponsored nofollow noopener")
    p.setdefault("utm_source", "studentup.in")
    return p


def active_ads(inv: Dict, today: Optional[date] = None) -> List[Dict]:
    today = today or date.today()
    out = []
    for ad in inv.get("ads", []):
        if not isinstance(ad, dict) or not ad.get("active", False):
            continue
        try:
            start = datetime.strptime(ad.get("start") or "2000-01-01", "%Y-%m-%d").date()
            end = datetime.strptime(ad.get("end") or "2999-12-31", "%Y-%m-%d").date()
        except ValueError:
            continue
        if start <= today <= end and (ad.get("link") or "").strip():
            out.append(ad)
    return out


# ---------------------------------------------------------------- selection

def _day_seed(art: Dict) -> int:
    """Deterministic daily rotation seed (date + category)."""
    key = f"{date.today().isoformat()}|{(art.get('category') or '')[:40]}"
    return int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16) % 10_000


def _matches(ad: Dict, art: Dict) -> bool:
    cats = (ad.get("categories") or "").strip()
    if not cats:
        return True  # no targeting = eligible everywhere
    cat = (art.get("category") or "").strip().lower()
    blob = f"{art.get('title', '')} {cat}".lower()
    return any(c.strip().lower() in blob for c in cats.split(","))


def _rotation_path() -> Path:
    """Where per-ad 'last shown' dates live (next to the inventory file)."""
    inv = Path(config.ADS_INVENTORY_PATH) if getattr(config, "ADS_INVENTORY_PATH", "") \
        else ROOT / "ads" / "inventory.json"
    return inv.parent / "rotation.json"


def _load_rotation() -> Dict[str, str]:
    try:
        data = json.loads(_rotation_path().read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:  # noqa: BLE001 — missing/corrupt rotation never blocks posting
        return {}


def _mark_shown(ads: List[Dict], today: date) -> None:
    """Remember when each ad last ran → next slot goes to the one waiting longest."""
    if not ads:
        return
    data = _load_rotation()
    for ad in ads:
        ad_id = ad.get("id")
        if ad_id:
            data[ad_id] = today.isoformat()
    try:
        path = _rotation_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                       encoding="utf-8")
        os.replace(tmp, path)
    except OSError:
        pass  # rotation is best-effort bookkeeping, never a publish blocker


def _fairness_key(ad: Dict, rot: Dict[str, str]) -> str:
    """Oldest-shown first; ads never shown sort first ('' < any date)."""
    return rot.get(ad.get("id") or "", "")


def house_ads_path() -> Path:
    """House ads (StudentUp sonta promos) — sponsor ad lekapoyinappudu ivi."""
    env = (getattr(config, "HOUSE_ADS_PATH", "") or "").strip()
    if env:
        return Path(env)
    return _rotation_path().parent / "house.json"


def load_house_ads(path: Optional[Path] = None) -> List[Dict]:
    """Load active house ads; missing/broken file → empty (never blocks posting)."""
    if getattr(config, "HOUSE_AD_ENABLED", True) is False:
        return []
    p = path or house_ads_path()
    try:
        data = json.loads(Path(p).read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return []
    out = []
    for ad in (data.get("ads") or []):
        if isinstance(ad, dict) and ad.get("active", True) and (ad.get("link") or "").strip():
            ad = dict(ad)
            ad["house"] = True
            out.append(ad)
    return out


def select_house_ads(inv: Optional[Dict] = None, today: Optional[date] = None,
                     limit: int = 1, record: bool = True,
                     path: Optional[Path] = None) -> List[Dict]:
    """Rotating house ads — paid sponsors always win, house fills the gap."""
    ads = load_house_ads(path)
    if not ads:
        return []
    today = today or date.today()
    rot = _load_rotation()
    ads = sorted(ads, key=lambda a: (_fairness_key(a, rot), a.get("id", "")))
    picked = ads[:max(1, limit)]
    if picked and record:
        _mark_shown(picked, today)
    return picked


def select_ads(art: Dict, inv: Dict, today: Optional[date] = None,
               record: bool = True) -> List[Dict]:
    """Pick which ads go into this article.

    Rules (all policy-safe):
      1. category-matched ads first, daily-rotated, deduped, capped by policy;
      2. NEVER MISS: when no active ad matches the category, fall back to the
         active ad that has waited longest — a sponsored slot is never
         silently dropped while at least one active ad exists;
      3. real partner ads outrank demo placeholders.
    """
    pol = policy_of(inv)
    cap = min(int(pol["max_personal_ads_per_post"]),
              int(getattr(config, "MAX_PERSONAL_AD_SLOTS", 2)))
    if getattr(config, "ADSENSE_APPROVED", False):
        cap = min(cap, 1)
    today = today or date.today()
    live = active_ads(inv, today)
    if not live:
        return []  # nothing active anywhere → honest empty
    rot = _load_rotation()
    seed = _day_seed(art)

    def _order(pool: List[Dict]) -> List[Dict]:
        return sorted(pool, key=lambda a: (0 if not a.get("demo") else 1,
                                           _fairness_key(a, rot),
                                           (seed + len(a.get("id", ""))) % max(len(pool), 1)))

    out: List[Dict] = []
    for ad in _order([a for a in live if _matches(a, art)]):
        if ad.get("id") in {x.get("id") for x in out}:
            continue
        out.append(ad)
        if len(out) >= cap:
            break
    if not out and getattr(config, "AD_FALLBACK_ALWAYS", True):
        # Category miss must not mean "no ad" unless the owner turned fallback off.
        out = _order(live)[:cap]
    if out and record:
        _mark_shown(out, today)
    return out


# ---------------------------------------------------------------- rendering

def utm_url(link: str, ad_id: str, slot: str, pol: Dict,
            medium: str = "sponsored") -> str:
    """Tag the click so GA4/GSC can measure it. Preserves existing query."""
    parsed = urlparse(link)
    if not parsed.netloc:
        return link
    q = dict(re.findall(r"([^&=]+)=([^&]*)", parsed.query or ""))
    for key, val in (("utm_source", pol["utm_source"]),
                     ("utm_medium", medium),
                     ("utm_campaign", ad_id),
                     ("utm_content", slot)):
        q.setdefault(key, val)
    sep = "&" if parsed.query else "?"
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path or '/'}{sep}{urlencode(q)}"


def _esc(s: str, quote: bool = True) -> str:
    return _html.escape((s or "").strip(), quote=quote)


def render_ad(ad: Dict, slot: str, pol: Dict) -> str:
    """Render one CLS-safe, labeled, XSS-safe ad block.

    layout: banner (full-width) | card (compact). Image optional —
    gradient fallback keeps the block clean without assets.
    """
    layout = (ad.get("layout") or "banner").strip()
    is_house = bool(ad.get("house"))
    # v52: house ads are StudentUp's own promos — never labelled "Sponsored"
    label = (_esc(ad.get("label")) or "StudentUp") if is_house \
        else (_esc(pol["label"]) or "Sponsored")
    kicker = _esc(ad.get("label") or ad.get("type") or "Advertisement")
    title = _esc(ad.get("title") or ad.get("name") or "")
    desc = _esc(ad.get("description") or "")
    cta = _esc(ad.get("cta") or "Know More")
    link = (ad.get("link") or "").strip()
    parsed = urlparse(link)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return ""  # unsafe link → drop the block entirely
    url = _esc(utm_url(link, ad.get("id", "ad"), slot, pol,
                       medium="house" if is_house else "sponsored"), quote=True)
    # paid partner links carry rel="sponsored nofollow"; own promos do not
    rel = _esc("noopener") if is_house else _esc(pol["rel"])
    demo_note = ('<span class="su-ad-note">demo</span>'
                 if ad.get("demo") else "")
    # v73: ad chrome English (UI text) — article body Telugu ga undochu
    aria = "StudentUp · our service" if is_house else "Sponsored content"
    img = (ad.get("image") or "").strip()
    img_html = ""
    if img:
        ip = urlparse(img)
        if ip.scheme in ("http", "https") and ip.netloc:
            img_html = (f'<img src="{_esc(img, quote=True)}" alt="{title}" '
                        f'loading="lazy" width="1200" height="360" '
                        f'style="width:100%;height:200px;object-fit:cover;'
                        f'border-radius:12px;display:block">')
    if layout == "card":
        return (
            f'<aside class="su-ad su-ad-card" aria-label="{aria}" '
            f'data-ad="{_esc(ad.get("id", ""), quote=True)}" data-slot="{_esc(slot)}">'
            f'<div class="su-ad-kicker">{label} · {kicker}{demo_note}</div>'
            f'<div class="su-ad-title">{title}</div>'
            + (f'<p class="su-ad-desc">{desc}</p>' if desc else "")
            + f'<a class="su-ad-cta" href="{url}" target="_blank" rel="{rel}">{cta} →</a>'
            + ('<div class="su-ad-disc">StudentUp\'s own publication — not a paid '
               'advertisement; about our services only.</div></aside>' if is_house else
               '<div class="su-ad-disc">Advertisement — direct link to our partner; '
               'our content stays separate.</div></aside>')
        )
    # banner (default)
    return (
        f'<section class="su-ad su-ad-banner" aria-label="{aria}" '
        f'data-ad="{_esc(ad.get("id", ""), quote=True)}" data-slot="{_esc(slot)}" '
        'style="min-height:150px">'
        f'<div class="su-ad-kicker">{label} · {kicker}{demo_note}</div>'
        + (img_html or '<div class="su-ad-grad" aria-hidden="true"></div>')
        + f'<div class="su-ad-title">{title}</div>'
        + (f'<p class="su-ad-desc">{desc}</p>' if desc else "")
        + f'<a class="su-ad-cta" href="{url}" target="_blank" rel="{rel}">{cta} →</a>'
        + ('<div class="su-ad-disc">StudentUp\'s own publication — not a paid '
           'advertisement; about our services only.</div></section>' if is_house else
           '<div class="su-ad-disc">Sponsored — this advertisement does not change our '
           'content; official notification links appear only in the site\'s main '
           'content.</div></section>')
    )


AD_CSS = """
<style>
.su-ad{margin:22px 0;border:1px solid #E4E9F1;border-radius:16px;overflow:hidden;
  background:linear-gradient(135deg,#F7FAFF,#FFF8F0);font-size:14px}
.su-ad-kicker{font-size:10px;font-weight:800;letter-spacing:.14em;color:#93711D;
  padding:9px 16px 0;display:flex;gap:8px;align-items:center}
.su-ad-note{background:#E8842B;color:#fff;border-radius:99px;padding:1px 8px;
  font-size:9px;letter-spacing:.08em}
.su-ad-title{font-size:16px;font-weight:800;color:#12356B;padding:6px 16px 0;
  line-height:1.35}
.su-ad-desc{color:#5A6472;font-size:13px;line-height:1.55;padding:5px 16px 0;margin:0}
.su-ad-cta{display:inline-block;background:#E8842B;color:#fff;font-weight:800;
  font-size:13px;text-decoration:none;border-radius:999px;padding:9px 18px;
  margin:10px 16px 0;box-shadow:0 6px 14px rgba(232,132,43,.25)}
.su-ad-cta:hover{transform:translateY(-1px)}
.su-ad-disc{font-size:10px;color:#8B97A8;padding:8px 16px 12px;line-height:1.5}
.su-ad-grad{height:110px;background:linear-gradient(120deg,#12356B 0%,#1D4D91 55%,#E8842B 130%)}
.su-ad-card{background:#fff;border-left:4px solid #E8842B}
.su-ad-card .su-ad-kicker{padding:10px 14px 0}
.su-ad-card .su-ad-title{padding:5px 14px 0;font-size:14px}
.su-ad-card .su-ad-desc{padding:4px 14px 0;font-size:12px}
.su-ad-card .su-ad-cta{margin:8px 14px 0;padding:7px 14px;font-size:12px}
.su-ad-card .su-ad-disc{padding:6px 14px 10px}
@media(max-width:600px){.su-ad-banner .su-ad-title{font-size:15px}
  .su-ad-banner .su-ad-cta{margin-left:14px}}
body.su-dark .su-ad{background:#182235;border-color:#33445E}
body.su-dark .su-ad-title{color:#E8EEF7}
body.su-dark .su-ad-desc,body.su-dark .su-ad-disc{color:#B9C5D6}
</style>
"""


# ---------------------------------------------------------------- injection

def _near_link(html: str, pos: int) -> bool:
    window = html[max(0, pos - LINK_ADJACENCY): pos + LINK_ADJACENCY]
    return "<a " in window or "<a>" in window


def _find_top(html: str) -> int:
    """Best top slot: right after the Quick Answer box (value first, ad second).

    Matches the real pipeline markup (seo.quick_answer_block →
    <section class="su-quick-answer-card">…</section>), then any element
    with id="quick-answer", then the first meaningful paragraph (50+ words).
    """
    m = re.search(r'<section class="su-quick-answer-card".*?</section>', html, re.S)
    if m:
        return m.end()
    m = re.search(r'<[^>]+id="quick-answer"[^>]*>', html)
    if m:
        close = re.search(r"</(section|div)>", html[m.end():])
        if close:
            return m.end() + close.end()
    for pm in re.finditer(r"<p[^>]*>(.*?)</p>", html, re.S):
        if len(re.sub(r"<[^>]+>", " ", pm.group(1)).split()) >= 50:
            return pm.end()
    return -1


def _find_mid(html: str) -> int:
    """Best mid slot: after the first CONTENT H2 + its paragraph (natural pause).

    Skips the Quick Answer section's own h2 (it's UI, not article content).
    """
    start = 0
    qa = re.search(r'<section class="su-quick-answer-card".*?</section>', html, re.S)
    if qa:
        start = qa.end()
    m = re.search(r"</h2>", html[start:])
    if m:
        pos = start + m.end()
    else:
        m = re.search(r"</h2>", html)
        if not m:
            return -1
        pos = m.end()
    nxt = re.search(r"</p>", html[pos:])
    if not nxt:
        return pos
    return pos + nxt.end()


def _find_bottom(html: str) -> int:
    """Bottom slot: before the monetize/related blocks or JSON-LD, else end."""
    for marker in ('<h2 id="related-articles"', '<h2 id="recommended-resources"',
                   '<script type="application/ld+json"'):
        idx = html.find(marker)
        if idx != -1:
            return idx
    return len(html)


def inject(html_in: str, art: Dict, inv: Optional[Dict] = None,
           dry: bool = False) -> Tuple[str, List[Dict]]:
    """Inject selected ads at the best slots. Returns (html, report).

    No-op (empty report, same html) when: disabled, no inventory, quiz
    post, or zero eligible ads.
    """
    if getattr(config, "AD_MANAGER_ENABLED", True) is False:
        return html_in, []
    inv = inv if inv is not None else load_inventory()
    ads = select_ads(art, inv)
    house = False
    if not ads:
        # v52: sponsor lekapoyina slot khali ga undakudadu → house ads (own promos)
        ads = select_house_ads(today=None, limit=1)
        house = bool(ads)
        if not ads:
            return html_in, []
    # CSS once
    if "su-ad-kicker" not in html_in:
        html_in = html_in + AD_CSS if html_in.rstrip().endswith("</body>") \
            else AD_CSS + html_in
    slots = ("top", "mid", "bottom")[: len(ads)]
    anchors = {
        "top": _find_top(html_in),
        "mid": _find_mid(html_in),
        "bottom": _find_bottom(html_in),
    }
    # bottom inserted first (positions shift), then mid, then top
    report: List[Dict] = []
    for slot, ad in sorted(zip(slots, ads), key=lambda kv: slots.index(kv[0]),
                           reverse=True):
        pos = anchors[slot]
        block = render_ad(ad, slot, policy_of(inv))
        if not block:
            continue
        if pos == -1 or _near_link(html_in, pos):
            report.append({"ad": ad.get("id"), "slot": slot, "status": "skipped",
                           "reason": "no safe anchor / link adjacency"})
            continue
        html_in = html_in[:pos] + "\n" + block + "\n" + html_in[pos:]
        report.append({"ad": ad.get("id"), "slot": slot, "status":
                       "inserted" if not dry else "planned",
                       "layout": ad.get("layout") or "banner",
                       "kind": "house" if ad.get("house") else "sponsor"})
    return html_in, report


def plan(art: Dict, inv: Optional[Dict] = None) -> Dict:
    """Dry plan for --ads CLI (no html required)."""
    inv = inv if inv is not None else load_inventory()
    pol = policy_of(inv)
    cap = min(int(pol["max_personal_ads_per_post"]),
              int(getattr(config, "MAX_PERSONAL_AD_SLOTS", 2)))
    if getattr(config, "ADSENSE_APPROVED", False):
        cap = min(cap, 1)
    pool = [a for a in active_ads(inv) if _matches(a, art)]
    picked = select_ads(art, inv, record=False)
    return {
        "enabled": getattr(config, "AD_MANAGER_ENABLED", True) is not False,
        "adsense_approved": bool(getattr(config, "ADSENSE_APPROVED", False)),
        "cap": cap,
        "eligible": [a.get("id") for a in pool],
        "picked": [a.get("id") for a in picked],
        "slot_map": {a.get("id"): s for s, a in
                     zip(("top", "mid", "bottom")[: len(picked)], picked)},
    }


# ---------------------------------------------------------------- demo page

def demo_page(inv: Dict, out_path: Optional[Path] = None) -> Path:
    """Build a visible sample article with every ad layout rendered."""
    inv = inv if inv is not None else load_inventory()
    pol = policy_of(inv)
    arts = [
        {"title": "Demo Article — Ad Placements", "category": "Admissions",
         "content_html": (
             '<section class="su-quick-answer-card" aria-labelledby="quick-answer">'
             '<h2 id="quick-answer">Quick Answer – Demo</h2>'
             '<p class="su-qa"><strong>Ikkada quick answer untundi — value first, '
             'ad second. (top slot ivi taruvata pettali)</strong></p>'
             '<p><em>Last Updated: today | studentup.in</em></p></section>'
             "<p>Article first paragraph — 50 words kante chala content "
             "vastundi. Ee paragraph ni readers parugu taruvata matrame okka "
             "ad block vasthundi, content dominance safe ga untundi. "
             "Students ki useful info first, monetization second — idi "
             "AdSense policy matrame, AdSense approval taruvata kuda same "
             "rule follow cheyyali. Content-dominant site (70%+ real value) "
             "matrame long-term rankings + approval get chesthundi.</p>"
             "<h2>Section 1 — Eligibility</h2>"
             "<p>Ee section lo eligibility details untayi. Mid slot ivi "
             "taruvata vasthundi (natural pause point).</p>"
             "<h2>Section 2 — Documents</h2>"
             "<p>Documents list unna section. Bottom slot related blocks "
             "mundu vasthundi.</p>"
             '<h2 id="related-articles">Related Articles</h2>'
             "<p>Related links block (ad ivi MUTYAMI mundu undali).</p>")},
    ]
    all_ads = active_ads(inv) or inv.get("ads", [])
    html = f"""<!doctype html><html lang="te"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Ad Manager Preview — studentup.in (v43)</title></head>
<body style="max-width:820px;margin:24px auto;font-family:system-ui,
'Noto Sans Telugu',sans-serif;color:#22303F;line-height:1.7">
<h1 style="color:#12356B">📢 Ad Manager Preview (v43)</h1>
<p><b>Inventory:</b> {len(all_ads)} ads ({sum(1 for a in all_ads if a.get('active'))} active) ·
<b>Cap:</b> {plan(arts[0], inv)['cap']} per post ·
<b>Policy:</b> labeled + rel="sponsored" + CLS-safe + no-link-adjacency</p>
<hr>
<h2>1. BANNER layout (top/mid slot)</h2>
{''.join(render_ad(a, 'top', pol) for a in all_ads[:2] if (a.get('layout') or 'banner') == 'banner' and a.get('link')) or '<p>(banner ads inventory lo ledu)</p>'}
<h2>2. CARD layout (sidebar slot)</h2>
{''.join(render_ad(a, 'mid', pol) for a in all_ads if (a.get('layout') or 'banner') == 'card' and a.get('link')) or '<p>(card ads inventory lo ledu)</p>'}
<h2>3. FULL SAMPLE ARTICLE — live placement engine</h2>
"""
    sample_html, report = inject(arts[0]["content_html"], arts[0], inv)
    html += sample_html
    html += f"""
<hr><h2>Placement report (this render)</h2>
<ul>{''.join(f'<li>{r["ad"]} → <b>{r["slot"]}</b> ({r["status"]})</li>' for r in report) or "<li>none</li>"}</ul>
{AD_CSS}
</body></html>"""
    out = out_path or (REPO_ROOT / "output" / "ads-preview.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    return out


def run_cli(mode: str) -> int:
    """mode: 'status' | 'demo'"""
    inv = load_inventory()
    pol = policy_of(inv)
    print("=" * 70)
    print("  📢 AD MANAGER (v43) — owner ads: college banners · shop · services")
    print("=" * 70)
    print(f"  Inventory file : {inventory_path()}")
    print(f"  Ads total/active: {len(inv.get('ads', []))}/{len(active_ads(inv))}")
    print(f"  Cap/post       : {min(int(pol['max_personal_ads_per_post']), 2)}"
          + (" (ADSENSE_APPROVED=1 → 1)" if getattr(config, "ADSENSE_APPROVED", False) else ""))
    print(f"  Policy         : label='{pol['label']}' · rel='{pol['rel']}' · "
          f"utm_source='{pol['utm_source']}'")
    for a in inv.get("ads", []):
        flag = "✅" if a.get("active") else "⛔"
        demo = " [demo]" if a.get("demo") else ""
        print(f"   {flag} {a.get('id'):<28} layout={a.get('layout') or 'banner':<7} "
              f"→ {a.get('title') or a.get('name') or ''}{demo}")
        tgt = a.get("categories") or "all categories"
        print(f"      target: {tgt} · {a.get('start')}→{a.get('end')}")
    print("-" * 70)
    print("  Sample slot plans:")
    for cat in ("Scholarships", "Admissions", "Govt Jobs", "Results"):
        p = plan({"category": cat, "title": f"{cat} sample"}, inv)
        print(f"   {cat:<15} → {p['picked'] or '(none eligible)'} "
              f"slots={p['slot_map']}")
    print("-" * 70)
    if mode == "demo":
        out = demo_page(inv)
        print(f"  📄 Demo page written: {out}")
        print("     Browser lo open cheyandi — layouts + live placement kanipisthundi.")
    print("  Next: real ads ads/inventory.json lo add cheyandi (demo:true remove).")
    print("        Strategy: AD_STRATEGY_ADVANCED.md lo full playbook.")
    print("=" * 70)
    return 0
