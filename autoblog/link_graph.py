# -*- coding: utf-8 -*-
"""v99 — INTERNAL LINK GRAPH OPTIMIZER (orphan posts → real crawl equity).

NIJAMAINA PROBLEM (v98 varaku):
  `seo.enhance()` prathi **kotha** post lo internal links pedutundi. Kaani adi
  **okka direction** matrame — kotha post nunchi **purana** posts ki. Purana
  post ni **evaru link cheyyaru** (adi publish ayinappudu daani tarvata vachhe
  posts inka lev). Result:

    · **ORPHAN posts** — site lo unnayi kaani **inbound internal link ZERO**.
      Googlebot vaatini crawl cheyyadaniki sitemap meeda matrame depend
      avutundi → crawl priority takkuva, ranking weak, konnisarlu index
      kuda kaavu.
    · Link equity (PageRank) **homepage + kotha posts** daggara pogu avutundi;
      purana money posts (results/hall ticket pages) ki flow avvadu.

  Idi Rank Math score lo **kanipinchadu** (adi single page ni matrame chustundi)
  — site-level graph problem. Anduke ippati varaku miss ayindi.

IDI EM CHESTUNDI:
  1. **CRAWL** — live posts + vaati content nunchi nijamaina internal link
     graph build chestundi (guess kaadu, actual `<a href>` parse).
  2. **DIAGNOSE** — orphans (inbound 0), weak (inbound 1), dead-ends
     (outbound 0), hub-heavy distribution report.
  3. **FIX** — prathi orphan ki, **relevant** donor posts (same category /
     shared keywords) kanukkoni, vaati content lo **contextual link**
     insert chestundi — natural anchor text tho (orphan title nunchi), post
     chivara "related" dump kaadu.

SAFETY (idi live content ni touch chestundi — anduke strict):
  · `--apply` lekapothe **edi marchadu** (dry-run default).
  · Prathi donor post ki **max 1** kotha link per run (spam kaadu).
  · Anchor text orphan title nunchi — **exact-match keyword stuffing ledu**.
  · Already link unte **skip** (duplicate links raavu).
  · Nested `<a>` lopala insert cheyyadu (invalid HTML).
  · Headings/quick-answer/CTA/ad blocks lopala insert cheyyadu.
  · Self-link eppudu cheyyadu.
  · Donor ki already `MAX_OUT` links unte skip (over-linking = spam signal).

CLI:
  python run.py --link-graph              # report matrame (edi marchadu)
  python run.py --link-graph --link-graph-apply
"""
from __future__ import annotations

import html as _html
import logging
import re
from typing import Dict, List, Optional, Sequence, Tuple

from . import config, seo

log = logging.getLogger("autoblog.linkgraph")

#: Oka donor post lo motham entha internal links varaku OK (over-linking guard).
MAX_OUT = 12
#: Okka run lo okka donor ki entha kotha links add cheyyochu.
MAX_NEW_PER_DONOR = 1
#: Okka orphan ki entha inbound links build cheyyali.
TARGET_INBOUND = 2
#: Anchor ga vadataniki minimum title words (chala chinna anchor = weak signal).
MIN_ANCHOR_WORDS = 3

#: Anchor/insert cheyyakoodani zones (ivi lopala link pedithe layout/policy issue).
_SKIP_BLOCKS = re.compile(
    r"<(h[1-6]|figure|table|script|style|form|button)\b[^>]*>.*?</\1>",
    re.I | re.S)
_SKIP_DIVS = re.compile(
    r'<div[^>]*class="[^"]*(su-quick|su-cta|su-join|su-sharebar|su-ad|'
    r'su-trust|su-toc|su-keyfacts|su-upnext)[^"]*"[^>]*>.*?</div>',
    re.I | re.S)

_STOP = {
    "the", "and", "for", "with", "from", "this", "that", "your", "you", "are",
    "was", "will", "how", "what", "when", "which", "all", "new", "latest",
    "full", "check", "here", "info", "details", "complete", "online", "direct",
    "link", "download", "telugu", "lo", "ki", "ni", "2024", "2025", "2026",
    "2027", "notification", "apply", "date", "last", "news", "update",
}


# --------------------------------------------------------------- normalise

def _norm_url(url: str) -> str:
    """Compare cheyyadaniki URL normalise (scheme/host/trailing slash/query)."""
    u = (url or "").strip()
    u = re.sub(r"[?#].*$", "", u)
    u = re.sub(r"^https?://", "", u)
    u = re.sub(r"^www\.", "", u)
    return u.rstrip("/").lower()


def _is_internal(url: str, site: str) -> bool:
    n, s = _norm_url(url), _norm_url(site)
    if not n:
        return False
    if n.startswith("/"):
        return True
    return bool(s) and n.split("/")[0] == s.split("/")[0]


def _tokens(text: str) -> List[str]:
    text = re.sub(r"<[^>]+>", " ", text or "")
    text = _html.unescape(text).lower()
    words = re.findall(r"[a-z0-9\u0c00-\u0c7f]+", text)
    return [w for w in words if len(w) > 2 and w not in _STOP]


def extract_links(html: str, site: str = "") -> List[str]:
    """Content lopala unna INTERNAL link URLs (normalised)."""
    site = site or getattr(config, "WP_SITE", "")
    out: List[str] = []
    for m in re.finditer(r'<a\b[^>]*href="([^"]+)"', html or "", re.I):
        href = m.group(1)
        if href.startswith(("mailto:", "tel:", "#", "javascript:")):
            continue
        if _is_internal(href, site):
            n = _norm_url(href)
            if n and n not in out:
                out.append(n)
    return out


# ------------------------------------------------------------------- graph

def build_graph(posts: Sequence[Dict], site: str = "") -> Dict:
    """Live posts nunchi nijamaina internal-link graph.

    `posts`: [{id, link, title, content, categories}]
    Returns: {nodes, out, inbound, orphans, weak, dead_ends}
    """
    site = site or getattr(config, "WP_SITE", "")
    nodes: Dict[str, Dict] = {}
    for p in posts:
        key = _norm_url(p.get("link", ""))
        if key:
            nodes[key] = dict(p)
            nodes[key]["_key"] = key

    out: Dict[str, List[str]] = {}
    inbound: Dict[str, List[str]] = {k: [] for k in nodes}
    for key, p in nodes.items():
        links = [u for u in extract_links(p.get("content", ""), site)
                 if u in nodes and u != key]     # self-link count cheyyakudadu
        out[key] = links
        for tgt in links:
            if key not in inbound[tgt]:
                inbound[tgt].append(key)

    orphans = sorted(k for k in nodes if not inbound[k])
    weak = sorted(k for k in nodes if len(inbound[k]) == 1)
    dead = sorted(k for k in nodes if not out.get(k))
    return {"nodes": nodes, "out": out, "inbound": inbound,
            "orphans": orphans, "weak": weak, "dead_ends": dead}


def relevance(a: Dict, b: Dict) -> float:
    """Rendu posts entha related (0..1) — shared keywords + category."""
    ta, tb = set(_tokens(a.get("title", ""))), set(_tokens(b.get("title", "")))
    if not ta or not tb:
        return 0.0
    overlap = len(ta & tb) / len(ta | tb)
    ca = set(a.get("categories") or [])
    cb = set(b.get("categories") or [])
    if ca and cb and (ca & cb):
        overlap += 0.25
    return min(1.0, overlap)


def anchor_for(title: str) -> str:
    """Natural anchor text — exact-match stuffing kaadu.

    Title ni clean chesi, chala podugu unte trim chestam. Anchor eppudu
    **readable phrase** ga undali (Google exact-match anchor spam ni
    penalise chestundi).
    """
    t = re.sub(r"<[^>]+>", "", title or "")
    t = _html.unescape(t)
    t = re.sub(r"\s*[|–—-]\s*(studentup|studentup\.in).*$", "", t, flags=re.I)
    t = re.sub(r"\s+", " ", t).strip()
    words = t.split()
    if len(words) > 10:
        t = " ".join(words[:10])
    return t


# ------------------------------------------------------------------ insert

def _safe_zones(html: str) -> List[Tuple[int, int]]:
    """Insert cheyyadaniki SAFE (start,end) ranges — paragraphs matrame."""
    blocked: List[Tuple[int, int]] = []
    for rx in (_SKIP_BLOCKS, _SKIP_DIVS):
        for m in rx.finditer(html):
            blocked.append((m.start(), m.end()))
    for m in re.finditer(r"<a\b.*?</a>", html, re.I | re.S):
        blocked.append((m.start(), m.end()))

    zones: List[Tuple[int, int]] = []
    for m in re.finditer(r"<p\b[^>]*>(.*?)</p>", html, re.I | re.S):
        s, e = m.start(1), m.end(1)
        if any(bs < e and s < be for bs, be in blocked):
            continue
        if e - s < 120:            # chala chinna para lo link awkward
            continue
        zones.append((s, e))
    return zones


def insert_link(html: str, url: str, anchor: str) -> Optional[str]:
    """Donor content lo contextual link insert (safe zone lo matrame).

    Already ee URL ki link unte `None` (duplicate raadu). Safe zone lekapothe
    `None` — force cheyyamu (broken HTML kanna link leకpovadam better).
    """
    if not url or not anchor:
        return None
    if _norm_url(url) in extract_links(html, config.WP_SITE):
        return None                                   # already linked
    zones = _safe_zones(html)
    if not zones:
        return None
    # Madhya zone — intro/outro kaakunda content madhyalo natural ga.
    s, e = zones[len(zones) // 2]
    para = html[s:e]
    sentences = re.split(r"(?<=[.!?])\s+", para.strip())
    link = (f'<a href="{_html.escape(url, quote=True)}">'
            f'{_html.escape(anchor)}</a>')
    add = f' <span class="su-rel">Related: {link}</span>'
    if len(sentences) > 1:
        para = para.rstrip() + add
    else:
        para = para.rstrip() + add
    return html[:s] + para + html[e:]


# -------------------------------------------------------------------- plan

def plan_fixes(graph: Dict, target_inbound: int = TARGET_INBOUND,
               max_new_per_donor: int = MAX_NEW_PER_DONOR) -> List[Dict]:
    """Orphan/weak posts ki donor posts pick chesi fix plan build.

    Deterministic: same input → same plan (tests + reproducible runs).
    """
    nodes, out, inbound = graph["nodes"], graph["out"], graph["inbound"]
    budget: Dict[str, int] = {k: 0 for k in nodes}
    plan: List[Dict] = []

    # Orphans mundu (inbound 0), tarvata weak (inbound 1).
    targets = graph["orphans"] + graph["weak"]
    for tgt in targets:
        need = target_inbound - len(inbound[tgt])
        if need <= 0:
            continue
        tnode = nodes[tgt]
        cands: List[Tuple[float, str]] = []
        for key, node in nodes.items():
            if key == tgt or key in inbound[tgt]:
                continue
            if len(out.get(key, [])) >= MAX_OUT:
                continue                       # over-linked donor
            if budget[key] >= max_new_per_donor:
                continue
            score = relevance(node, tnode)
            if score <= 0:
                continue
            cands.append((score, key))
        # score desc, then key asc → deterministic
        cands.sort(key=lambda x: (-x[0], x[1]))
        for score, donor in cands[:need]:
            budget[donor] += 1
            inbound[tgt].append(donor)
            plan.append({
                "donor": donor,
                "donor_id": nodes[donor].get("id"),
                "target": tgt,
                "target_url": nodes[tgt].get("link", ""),
                "anchor": anchor_for(nodes[tgt].get("title", "")),
                "score": round(score, 3),
                "reason": "orphan" if tgt in graph["orphans"] else "weak",
            })
    return plan


# -------------------------------------------------------------------- run

def run(apply: bool = False, limit: int = 100, wp=None) -> Dict:
    """Crawl → diagnose → (optional) fix. `apply=False` lo edi marchadu."""
    if wp is None:
        from .wordpress_client import WordPressClient

        wp = WordPressClient()
    posts = _load_posts(wp, limit)
    if not posts:
        return {"posts": 0, "orphans": 0, "weak": 0, "dead_ends": 0,
                "plan": [], "applied": 0,
                "note": "live posts raledu (WP creds / network check cheyandi)"}
    graph = build_graph(posts)
    plan = plan_fixes(graph)
    applied = 0
    if apply:
        for fix in plan:
            node = graph["nodes"][fix["donor"]]
            new_html = insert_link(node.get("content", ""),
                                   fix["target_url"], fix["anchor"])
            if not new_html:
                fix["skipped"] = "no safe zone / already linked"
                continue
            try:
                wp.update_post(node["id"], new_html)
                node["content"] = new_html
                fix["applied"] = True
                applied += 1
            except Exception as exc:  # noqa: BLE001 — okati fail = migatavi continue
                fix["skipped"] = f"update fail: {exc}"
                log.warning("link fix fail (post %s): %s", node.get("id"), exc)
    return {"posts": len(posts), "orphans": len(graph["orphans"]),
            "weak": len(graph["weak"]), "dead_ends": len(graph["dead_ends"]),
            "plan": plan, "applied": applied, "dry": not apply}


def _load_posts(wp, limit: int) -> List[Dict]:
    """Live posts + content (graph ki content kavali)."""
    out: List[Dict] = []
    try:
        base = wp.get_recent_published(per_page=limit) or []
    except Exception as exc:  # noqa: BLE001
        log.warning("posts load fail: %s", exc)
        return []
    for p in base:
        item = dict(p)
        if "content" not in item:
            try:
                full = wp.get_post(p["id"])
                item["content"] = ((full.get("content") or {}).get("raw")
                                   or (full.get("content") or {}).get("rendered")
                                   or "")
            except Exception:  # noqa: BLE001
                item["content"] = ""
        out.append(item)
    return out


def run_cli(apply: bool = False, limit: int = 100) -> int:
    line = "=" * 74
    print(line)
    print("  🔗 INTERNAL LINK GRAPH OPTIMIZER (orphan posts → crawl equity)")
    print(line)
    rep = run(apply=apply, limit=limit)
    if rep.get("note"):
        print(f"  ⚠️  {rep['note']}")
        print(line)
        return 0
    print(f"  posts crawled : {rep['posts']}")
    print(f"  🚨 orphans    : {rep['orphans']}  (inbound internal links ZERO)")
    print(f"  ⚠️  weak       : {rep['weak']}  (inbound 1 matrame)")
    print(f"  ↩️  dead ends  : {rep['dead_ends']}  (outbound internal links ZERO)")
    print("-" * 74)
    if not rep["plan"]:
        print("  ✅ fix cheyyalsinadi ledu — graph healthy")
        print(line)
        return 0
    print(f"  plan: {len(rep['plan'])} kotha internal links")
    for f in rep["plan"][:25]:
        mark = "✔" if f.get("applied") else ("✘" if f.get("skipped") else "·")
        print(f"   {mark} {f['reason']:<6} {f['donor'][:34]:<34} → {f['target'][:30]}")
        if f.get("skipped"):
            print(f"       skip: {f['skipped']}")
    print("-" * 74)
    if apply:
        print(f"  ✅ applied: {rep['applied']} links (live posts update ayyayi)")
    else:
        print("  DRY RUN — edi marchaledu. Apply cheyyadaniki:")
        print("     python run.py --link-graph --link-graph-apply")
    print(line)
    return 0
