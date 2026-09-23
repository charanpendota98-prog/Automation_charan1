# -*- coding: utf-8 -*-
"""v59: బ్రేకింగ్ న్యూస్ feed + "విద్యార్థులు ఎక్కువగా వెతికేవి" order.

Enduku idi:
  student site open cheyagane modati 3 sekundullo "ippude em jarigindi" +
  "నాకు పనికొచ్చేది" kanipinchali. Ee module rendu panulu chestundi:
    1) radar (Google News Telugu + 180 official sources) nunchi vachina
       verified items ni preview/data/breaking.json ga rasi site ticker +
       బ్రేకింగ్ న్యూస్ section ki istundi.
    2) MOST_USED — TS/AP students ekkuvaga vethike category order (bot +
       site + tests anni okate list vaadutayi, so eppudu sync lo untai).

Nijam matrame (fake news ledu): item lekapote feed khali ga untundi, site
"kotha breaking update ledu" ani honest ga cheptundi — fake headline ledu,
clickbait ledu.
"""
from __future__ import annotations

import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import config

log = logging.getLogger("autoblog.breaking")

IST = timezone(timedelta(hours=5, minutes=30))

# ---------------------------------------------------------------------------
# MOST_USED: site lo modati screen lo chupinchе category order (okate source)
# ---------------------------------------------------------------------------
MOST_USED: List[Dict[str, str]] = [
    {"cat": "ts-jobs", "label": "TS Government Jobs", "icon": "🏛",
     "hint": "TSPSC · Police · Gurukul"},
    {"cat": "ap-jobs", "label": "AP Government Jobs", "icon": "🏛",
     "hint": "APPSC · Police · DSC · Secretariat"},
    {"cat": "central-jobs", "label": "Central Govt Jobs", "icon": "🇮🇳",
     "hint": "SSC · UPSC · Railways · Banks"},
    {"cat": "hallticket", "label": "Hall Tickets", "icon": "🎫",
     "hint": "Admit card · key instructions"},
    {"cat": "results", "label": "Results", "icon": "📄",
     "hint": "Board · competitive exams · keys"},
    {"cat": "walkin", "label": "Walk-in Interviews", "icon": "🚶",
     "hint": "This week\u2019s drives · venues"},
    {"cat": "software", "label": "Software Jobs", "icon": "💻",
     "hint": "IT · developer · fresher"},
    {"cat": "private", "label": "Private Jobs", "icon": "🏢",
     "hint": "TCS · Infosys · Off-campus"},
    {"cat": "current", "label": "Current Affairs", "icon": "📰",
     "hint": "Daily GK · for exams"},
]

# ఏ headline ki ఏ tag — site filters ki same names (సీనియర్→జూనియర్ order)
TAG_RULES = [
    ("hallticket", ("హాల్ టికెట్", "hall ticket", "admit card", "అడ్మిట్ కార్డ్",
                    "పరీక్షా కేంద్రం")),
    ("results", ("ఫలితాలు", "ఫలితం", "result", "results", "కటాఫ్", "cut off",
                 "cut-off", "merit list", "మెరిట్", "కీ ", "answer key", "కీలు")),
    ("abroad", ("విదేశ", "గల్ఫ్", "gulf", "visa", "వీసా", "ielts", "pte",
                "study abroad", "అబ్రాడ్")),
    ("scholarship", ("స్కాలర్‌షిప్", "scholarship", "nsp", "యశస్వి", "yasasvi",
                     "ఫీజు రీయింబర్స్‌మెంట్")),
    ("walkin", ("వాక్-ఇన్", "walk-in", "walk in", "వాకిన్")),
    ("software", ("software", "సాఫ్ట్‌వేర్", "developer", "డెవలపర్", "it job",
                  "ప్రోగ్రామర్")),
    ("ap-jobs", ("ఆంధ్రప్రదేశ్", "ఏపీ", "appsc", "andhra", "విజయవాడ", "విశాఖ",
                 "తిరుపతి", "గుంటూరు", "కర్నూలు", "రాజమండ్రి", "నెల్లూరు")),
    ("ts-jobs", ("తెలంగాణ", "టీఎస్", "tspsc", "telangana", "హైదరాబాద్", "వరంగల్",
                 "కరీంనగర్", "నిజామాబాద్", "ఖమ్మం", "నల్గొండ", "మహబూబ్")),
    ("central-jobs", ("కేంద్ర", "ssc", "upsc", "rrb", "ibps", "రైల్వే", "రక్షణ",
                      "army", "navy", "airforce")),
    ("current", ("ప్రస్తుతాంశాలు", "కరెంట్ అఫైర్స్", "current affairs", "జీకే",
                 "gk", "scheme", "పథకం")),
]
DEFAULT_TAG = "current"

MAX_TITLE = 180
MIN_TITLE = 15
MAX_PER_SOURCE = 3


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def feed_path() -> Path:
    """preview/data/breaking.json — site JS idi fetch chestundi."""
    default = Path(config.BASE_DIR) / "preview" / "data" / "breaking.json"
    return Path(getattr(config, "BREAKING_FEED_PATH", default))


def _now() -> datetime:
    return datetime.now(IST)


def _iso(dt: datetime) -> str:
    return dt.astimezone(IST).replace(microsecond=0).isoformat()


def _parse_pub(text: str) -> Optional[str]:
    """RFC822 (Google News pubDate) → IST ISO. Fail ayithe None."""
    text = (text or "").strip()
    if not text:
        return None
    try:
        dt = parsedate_to_datetime(text)
    except (TypeError, ValueError):
        return None
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return _iso(dt)


def clean_title(title: str) -> str:
    """Google News 'Headline - Publisher' lo publisher suffix teesi, spaces clean."""
    t = re.sub(r"\s+", " ", (title or "").strip())
    if " - " in t:
        head, _, tail = t.rpartition(" - ")
        words = tail.split()
        if head and len(words) <= 7 and not any(ch.isdigit() for ch in tail):
            t = head.strip()
    return t[:MAX_TITLE].strip()


def _norm(text: str) -> str:
    return re.sub(r"[^0-9a-zఅ-హ\u0c00-\u0c7f]+", " ", (text or "").lower()).strip()


def classify_tag(text: str, hint: str = "") -> str:
    """Headline (+ official source hint) nunchi tag. Telugu + English rendu."""
    hay = (text or "").lower()
    known = {tag for tag, _ in TAG_RULES} | {"current"}
    if hint in known:
        return hint
    for tag, needles in TAG_RULES:
        if any(n.lower() in hay for n in needles):
            return tag
    return DEFAULT_TAG


def _host(link: str) -> str:
    m = re.match(r"https?://([^/]+)/?", (link or "").strip())
    return (m.group(1) if m else "").lower().replace("www.", "")


# ---------------------------------------------------------------------------
# build + publish
# ---------------------------------------------------------------------------

def build_items(raw: List[dict], limit: int = None) -> List[dict]:
    """Raw radar items → site feed items (dedupe + tag + time + cap).

    Nijamaina link lekunda / chala podugu title unte drop — fake/incomplete
    item site ki vellakudadu.
    """
    limit = int(limit or getattr(config, "BREAKING_MAX", 8) or 8)
    out: List[dict] = []
    seen_title, seen_link, per_host = set(), set(), {}
    for it in raw or []:
        title = clean_title(it.get("title") or "")
        link = (it.get("link") or "").strip()
        if len(title) < MIN_TITLE or not link.startswith("http"):
            continue
        key_t, key_l = _norm(title), link.split("?")[0].lower().rstrip("/")
        if not key_t or key_t in seen_title or key_l in seen_link:
            continue
        host = _host(link)
        if host and per_host.get(host, 0) >= MAX_PER_SOURCE:
            continue
        tag = classify_tag(title, it.get("category_hint") or "")
        when = _parse_pub(it.get("pub") or it.get("time") or "") or _iso(_now())
        source = (it.get("source_name") or it.get("source") or "రాడార్"
                  ).strip()
        item = {"title": title, "link": link, "tag": tag, "source": source,
                "time": when}
        if it.get("district"):
            item["district"] = it["district"]
        out.append(item)
        seen_title.add(key_t)
        seen_link.add(key_l)
        if host:
            per_host[host] = per_host.get(host, 0) + 1
    out.sort(key=lambda x: x.get("time") or "", reverse=True)
    return out[:limit]


def merge_items(new_items: List[dict], old_feed: dict, keep_hours: float = None,
                limit: int = None) -> List[dict]:
    """Kotha items + puratana feed ni kalipi rolling window (ticker khali avvadu).

    Enti: radar sweep lo 'kotha' item ledu ante (ade news mundu queue ayindi)
    ticker band ayyipoyedi — ippudu 18 gantala varaku chivari items nilabadtayi,
    tarvata automatic ga expire avuthayi (పాత headline nilabadadu).
    """
    limit = int(limit or getattr(config, "BREAKING_MAX", 8) or 8)
    keep = float(keep_hours if keep_hours is not None
                 else getattr(config, "BREAKING_KEEP_HOURS", 18))
    cutoff = _now() - timedelta(hours=keep)
    out: List[dict] = []
    seen = set()
    for it in list(new_items or []) + list((old_feed or {}).get("items", [])):
        when = None
        try:
            when = datetime.fromisoformat(str(it.get("time") or ""))
        except (TypeError, ValueError):
            when = None
        if when is not None and when < cutoff:
            continue
        key = _norm(it.get("title") or "")
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(it)
    out.sort(key=lambda x: x.get("time") or "", reverse=True)
    return out[:limit]


def write_feed(items: List[dict], path: Path = None, source: str = "radar",
               note: str = "") -> dict:
    """Feed JSON ni atomic ga rasi, summary return (site + tests iddariki okate)."""
    target = Path(path or feed_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "updated": _iso(_now()),
        "source": source,
        "count": len(items),
        # v72: ee note public site meeda kanipistundi — anduku internal tech maatalu ledu
        "note": note or ("తాజా అప్డేట్‌లు" if items else
                         "ప్రస్తుతం కొత్త బ్రేకింగ్ అప్డేట్‌లు లేవు — "
                         "త్వరలో ఇక్కడ కనిపిస్తాయి."),
        "items": items,
    }
    tmp = target.with_suffix(target.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    os.replace(tmp, target)
    return {"path": str(target), "count": len(items),
            "updated": payload["updated"], "note": payload["note"]}


def publish(raw: List[dict], path: Path = None, source: str = "radar") -> dict:
    """build_items → rolling merge (18h window) → write_feed (radar hook entry)."""
    target = Path(path or feed_path())
    items = merge_items(build_items(raw), read_feed(target))
    res = write_feed(items, path=target, source=source)
    log.info("breaking feed: %d items → %s", res["count"], res["path"])
    return res


def read_feed(path: Path = None) -> dict:
    """Feed chadivi (lekapote khali schema) — CLI/tests/dashboard ki."""
    target = Path(path or feed_path())
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
        if isinstance(data, dict) and isinstance(data.get("items"), list):
            return data
    except Exception as exc:  # noqa: BLE001
        log.debug("breaking feed read fail: %s", exc)
    return {"updated": "", "source": "none", "count": 0, "items": [],
            "note": "feed inka generate avvaledu"}


def most_used() -> List[Dict[str, str]]:
    """Site modati screen order — bot/tests/site okate list vaadali."""
    return [dict(x) for x in MOST_USED]


def most_used_cats() -> List[str]:
    return [x["cat"] for x in MOST_USED]


def stats(path: Path = None) -> dict:
    data = read_feed(path)
    by_tag: Dict[str, int] = {}
    for it in data.get("items", []):
        by_tag[it.get("tag", "?")] = by_tag.get(it.get("tag", "?"), 0) + 1
    return {"file": str(Path(path or feed_path())), "count": len(data.get("items", [])),
            "updated": data.get("updated", ""), "by_tag": by_tag,
            "most_used": most_used_cats()}
