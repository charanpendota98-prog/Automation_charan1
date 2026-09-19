# -*- coding: utf-8 -*-
"""v65: GOOGLE VISIBILITY — Trends (RSS) + Suggest (autocomplete) capture.

Enduku (mee requirement: "trending lo undali, Google mana blog ni suggest cheyali"):
  Google lo fast ga rank avvadaniki **Google ee roju chupistunna topics** meeda
  rayali + **autocomplete lo unnattu** (users type chese laage) phrases vaadali.
  Ee module rendu capture chesi, mana TS/AP student niche ki filter chesi,
  **topic queue** lo pettundi — bot aa queue nunchi next post select chestundi.

  · Google Trends daily RSS :  https://trends.google.com/trending/rss?geo=IN
  · Google Suggest (autocomplete): suggestqueries.google.com (te-IN accepted)

Rules (honest + safe):
  · Network lekapote [] return — bot crash avvadu, puratana queue continue.
  · Ee data "Google ranking guarantee" kaadu; idi **demand signal** mattrame.
  · Invent cheyyadu: feed lo unna vi mattrame queue ki veltayi (dedupe + niche filter).

Run proof: python run.py --trends            (capture + print, queue rాయadu)
           python run.py --trends --trends-queue   (queue ki rasi, 3 roju dedupe)
"""
from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional

from . import config

log = logging.getLogger("autoblog.trends")

TRENDS_RSS = "https://trends.google.com/trending/rss?geo={geo}"
SUGGEST_URL = ("https://suggestqueries.google.com/complete/search"
               "?client=firefox&hl=te&gl=in&q={q}")
QUEUE_PATH = Path(getattr(config, "BASE_DIR", ".")) / "output" / "trend_queue.json"
USER_AGENT = "studentup-bot/1.0 (+https://studentup.in)"

# TS/AP student niche — ee patterns unna trends mattrame teesukuntamu
NICHE_WORDS = (
    "job", "jobs", "recruitment", "notification", "notifications", "vacancy",
    "vacancies", "apply", "application", "last date", "result", "results",
    "hall ticket", "admit card", "exam", "exams", "syllabus", "answer key",
    "cutoff", "cut off", "merit list", "counselling", "counseling", "admission",
    "admissions", "scholarship", "scholarships", "apprentice", "walk-in",
    "walk in", "interview", "police", "constable", "si ", "group 1", "group 2",
    "group-2", "dsc", "tspsc", "appsc", "ssc", "upsc", "rrb", "ibps", "neet",
    "jee", "eamcet", "polycet", "inter", "degree", "b.ed", "tet", "dsc",
    "gurukul", "sachivalayam", "village", "mro", "panchayat", "railway",
    "railways", "bank", "defence", "army", "navy", "airforce", "apprentice",
    "telangana", "andhra", "hyderabad", "vijayawada", "visakhapatnam", "warangal",
)

# Suggest expansion seeds — mana 17 pillars nunchi (student searches)
DEFAULT_SEEDS = (
    "tspsc group 2 notification",
    "ap dsc 2026",
    "ts police constable recruitment",
    "today current affairs telugu",
    "govt jobs for degree holders telangana",
    "ssc cgl apply online",
)


# --------------------------------------------------------------------- fetch

def _http_get(url: str, timeout: int = 8) -> str:
    """requests tho GET — fail ayithe '' (bot crash avvadu)."""
    try:
        import requests

        resp = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200:
            return resp.text
        log.info("trends fetch HTTP %s — %s", resp.status_code, url[:60])
    except Exception as exc:  # noqa: BLE001 — offline/SSL lo silent skip
        log.info("trends fetch skip (%s) — %s", type(exc).__name__, url[:60])
    return ""


def _text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _strip_ns(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


# --------------------------------------------------------------------- parse

def parse_trends_rss(xml: str) -> List[Dict[str, str]]:
    """Google Trends RSS → [{'title','traffic','link','pub','news'}].

    Namespace/profile batti structure marutundi — ee parser rendu handle chestundi
    (ht:approx_traffic + ht:news_item title).
    """
    if not xml or "<item" not in xml:
        return []
    out: List[Dict[str, str]] = []
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        # v65 fallback: unbound prefix / odd feed → regex parser (feed structure
        # eppudu marutundo telidu, kaani <item><title> format stable)
        log.info("trends RSS ET fail (%s) — regex fallback", str(exc)[:60])
        rows: List[Dict[str, str]] = []
        for blk in re.findall(r"<item>(.*?)</item>", xml, flags=re.S):
            def _g(tag):
                m = re.search(tag + r">(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</" + tag,
                              blk, flags=re.S)
                return _text(m.group(1)) if m else ""
            title = _g("title")
            if not title:
                continue
            rows.append({"title": title, "traffic": _g("approx_traffic"),
                         "link": _g("link"), "pub": _g("pubDate"),
                         "news": _g("news_item_title")})
        return rows
    for item in root.iter():
        if _strip_ns(item.tag) != "item":
            continue
        row = {"title": "", "traffic": "", "link": "", "pub": "", "news": ""}
        news = []
        for child in item:
            name = _strip_ns(child.tag)
            text = (child.text or "").strip()
            if name == "title" and not row["title"]:
                row["title"] = text
            elif name == "approx_traffic":
                row["traffic"] = text
            elif name == "link":
                row["link"] = text
            elif name == "pubDate":
                row["pub"] = text
            elif name == "news_item":
                for sub in child:
                    if _strip_ns(sub.tag) == "news_item_title" and (sub.text or "").strip():
                        news.append((sub.text or "").strip())
            elif name == "picture" and text:
                row["picture"] = text
        row["news"] = " | ".join(news[:2])
        if row["title"]:
            out.append(row)
    return out


def parse_suggest(text: str) -> List[str]:
    """Google Suggest (client=firefox) JSON → list of phrases."""
    if not text:
        return []
    try:
        data = json.loads(text)
    except Exception:  # noqa: BLE001
        return []
    if isinstance(data, list) and len(data) > 1 and isinstance(data[1], list):
        return [str(x).strip() for x in data[1] if str(x).strip()]
    return []


# --------------------------------------------------------------------- API

def fetch_trends(geo: str = "", fetcher: Optional[Callable[[str], str]] = None,
                 limit: int = 40) -> List[Dict[str, str]]:
    """Google Trends (IN) — mundu existing topic_engine parser, tarvata mana RSS.

    Rendu okate RSS ni parse chestayi (duplicate logic kaadu — reuse); fetcher
    inject cheste (tests lo) deterministic ga mana parser vadutundi.
    """
    geo = geo or getattr(config, "TRENDS_GEO", "IN")
    if fetcher is None:
        try:
            from . import topic_engine

            rows = topic_engine.fetch_trending_topics() or []
            if rows:
                return [{"title": str(r.get("title", "")),
                         "traffic": str(r.get("traffic", "")),
                         "link": str(r.get("link", "")),
                         "pub": str(r.get("pub", "")),
                         "news": str(r.get("news_title", ""))} for r in rows][:limit]
        except Exception as exc:  # noqa: BLE001
            log.info("topic_engine fetch skip (%s) — mana parser", type(exc).__name__)
    get = fetcher or _http_get
    return parse_trends_rss(get(TRENDS_RSS.format(geo=geo)))[:limit]


def fetch_suggest(query: str, fetcher: Optional[Callable[[str], str]] = None,
                  limit: int = 10) -> List[str]:
    if not query.strip():
        return []
    get = fetcher or _http_get
    url = SUGGEST_URL.format(q=re.sub(r"\s+", "+", query.strip()))
    return parse_suggest(get(url))[:limit]


def expand_seeds(seeds: Optional[List[str]] = None,
                 fetcher: Optional[Callable[[str], str]] = None,
                 per_seed: int = 6) -> List[str]:
    out: List[str] = []
    for seed in (seeds or DEFAULT_SEEDS):
        for phrase in fetch_suggest(seed, fetcher=fetcher, limit=per_seed):
            if phrase not in out:
                out.append(phrase)
    return out


# --------------------------------------------------------------------- filter

def is_niche(text: str) -> bool:
    low = (text or "").lower()
    if any(w in low for w in NICHE_WORDS):
        return True
    # Telugu script unte (mana readers) — niche likely
    return bool(re.search(r"[\u0c00-\u0c7f]", text or ""))


def relevant(items: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Trends lo TS/AP student niche ki sambandhinchina vi mattrame."""
    keep = []
    for it in items:
        blob = f"{it.get('title','')} {it.get('news','')} {it.get('traffic','')}"
        if is_niche(blob):
            keep.append(it)
    return keep


def score_topic(title: str) -> int:
    """Demand proxy (0-100) — traffic + niche words + specificity (heuristic)."""
    low = (title or "").lower()
    score = 40
    hits = sum(1 for w in NICHE_WORDS if w in low)
    score += min(30, hits * 8)
    if re.search(r"\b20\d{2}\b", low):
        score += 8
    if re.search(r"[\u0c00-\u0c7f]", title or ""):
        score += 8
    if len(low.split()) >= 4:
        score += 6
    return max(0, min(100, score))


# --------------------------------------------------------------------- queue

def _load(path: Optional[Path] = None) -> Dict[str, list]:
    path = Path(path or QUEUE_PATH)
    if not path.exists():
        return {"topics": [], "used": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        data.setdefault("topics", [])
        data.setdefault("used", [])
        return data
    except Exception:  # noqa: BLE001
        return {"topics": [], "used": []}


def _save(data: Dict[str, list], path: Optional[Path] = None) -> Path:
    path = Path(path or QUEUE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def queue_topics(items: List[Dict[str, str]], suggestions: Optional[List[str]] = None,
                 path: Optional[Path] = None, keep_days: int = 3) -> Dict[str, object]:
    """Trends + suggestions ni queue ki — dedupe + puratana vi cleanup.

    Returns {"added": n, "total": n, "path": "..."}.
    """
    data = _load(path)
    today = date.today().isoformat()
    cutoff = (date.today() - timedelta(days=keep_days)).isoformat()
    data["used"] = [u for u in data["used"] if str(u.get("used_on", today)) >= cutoff]

    seen = {str(t.get("title", "")).lower() for t in data["topics"]}
    seen |= {str(u.get("title", "")).lower() for u in data["used"]}
    added = 0
    for it in items:
        title = str(it.get("title", "")).strip()
        if not title or title.lower() in seen:
            continue
        data["topics"].append({
            "title": title,
            "source": "google-trends",
            "traffic": it.get("traffic", ""),
            "news": it.get("news", ""),
            "link": it.get("link", ""),
            "score": score_topic(title),
            "captured_on": today,
        })
        seen.add(title.lower())
        added += 1
    for phrase in suggestions or []:
        low = phrase.lower()
        if not phrase.strip() or low in seen:
            continue
        data["topics"].append({
            "title": phrase.strip(),
            "source": "google-suggest",
            "traffic": "",
            "news": "",
            "link": "",
            "score": score_topic(phrase),
            "captured_on": today,
        })
        seen.add(low)
        added += 1
    data["topics"].sort(key=lambda t: (-int(t.get("score", 0)), t.get("title", "")))
    data["topics"] = data["topics"][:120]
    saved = _save(data, path)
    return {"added": added, "total": len(data["topics"]), "path": str(saved)}


def next_topics(limit: int = 5, path: Optional[Path] = None) -> List[Dict[str, object]]:
    """Queue lo top-priority topics (bot ee list nunchi post select chestundi)."""
    data = _load(path)
    return data["topics"][:limit]


def consume(title: str, path: Optional[Path] = None) -> bool:
    """Topic ni 'used' ki move (malli ade topic raakunda)."""
    data = _load(path)
    for i, t in enumerate(data["topics"]):
        if str(t.get("title", "")).lower() == (title or "").lower():
            row = data["topics"].pop(i)
            row["used_on"] = date.today().isoformat()
            data["used"].append(row)
            _save(data, path)
            return True
    return False


# --------------------------------------------------------------------- run

def capture(geo: str = "", queue: bool = False, use_suggest: bool = True,
            fetcher: Optional[Callable[[str], str]] = None) -> Dict[str, object]:
    """Okka call lo: trends + suggest capture → filter → (optional) queue."""
    trends = relevant(fetch_trends(geo=geo, fetcher=fetcher))
    sugg = expand_seeds(fetcher=fetcher) if use_suggest else []
    sugg = [s for s in sugg if is_niche(s)]
    out: Dict[str, object] = {
        "trends": len(trends), "suggest": len(sugg),
        "top": (trends[:5] + [{"title": s, "source": "google-suggest"} for s in sugg[:3]]),
    }
    if queue and (trends or sugg):
        out["queue"] = queue_topics(trends, sugg)
    return out


def main() -> int:
    capture_result = capture(queue=True)
    print("=" * 70)
    print("  📈 GOOGLE VISIBILITY — Trends + Suggest capture (v65)")
    print("=" * 70)
    print(f"  Google Trends (niche) : {capture_result['trends']}")
    print(f"  Google Suggest (niche): {capture_result['suggest']}")
    q = capture_result.get("queue") or {}
    print(f"  queue: +{q.get('added', 0)} · total {q.get('total', 0)} → {q.get('path', '')}")
    rows = next_topics(limit=8)
    if rows:
        print("-" * 70)
        for t in rows:
            print(f"    [{t.get('score'):>3}] {t.get('source'):<15} {str(t.get('title'))[:52]}")
    else:
        print("  (network lekapote queue khali — sandbox lo idi normal; "
              "mee server lo radar 4x/day run ayyaka nimpuddi)")
    print("=" * 70)
    print(f"  queue file: {QUEUE_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
