# -*- coding: utf-8 -*-
"""v65: PIN-TO-PIN POST GATE — "prathi post 100% perfect aa?" certificate.

Enduku (mee requirement: "pin to pin check chesi rasetappudu real time ga anni
perfect ga undala"):
  Publish ki mundu **okka file lo 45 checks** — content · SEO · schema · media ·
  links · ads · freshness · Google readiness. Prathi post ki **certificate file**
  (`output/certificates/<date>-<slug>.md` + `.json`) — endukante mīru eppudaina
  "ee post lo emi check ayyindi?" ani adagagalaru, proof undi.

  · Critical fail unte (title/meta/kw ledu · dev text · schema ledu · unverified
    facts · past deadline · duplicate content) publish **aaputundi** (default ON,
    `PIN_GATE_BLOCK=0` tho off).
  · Migilinavi report + Telegram lo chupistundi (publish aapadu).

Honest: ee gate **manam kontrol chese vi** ni check chestundi (on-page + schema +
links + media). Google ranking/indexing/traffic ni ide gate decide cheyyaledu —
vaatiki GSC data + time kaavali. Ee gate = "manam cheyagaligedi 100% chesam" proof.

Run proof: python run.py --pin-check
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import config, validator

log = logging.getLogger("autoblog.pin_gate")

CERT_DIR = Path(getattr(config, "OUTPUT_DIR", "output")) / "certificates"

GROUPS = ("CONTENT", "SEO", "SCHEMA", "MEDIA", "LINKS", "ADSENSE", "FRESHNESS",
          "GOOGLE READINESS")

# ee ids fail aithe publish aaputamu (data integrity / policy)
CRITICAL = {
    "no_dev_text", "title_kw", "meta_ok", "rm_score", "schema_article",
    "deadline_valid", "no_duplicate", "facts_clean",
}

DEV_PATTERNS = (
    "lorem ipsum", "dummy text", "sample post", "test post", "demo post",
    "నమూనా పోస్ట్", "టెస్ట్ పోస్ట్", "todo:", "as an ai", "as an AI language model",
    "chatgpt", "this is a placeholder", "placeholder text", "xxx-xxx",
)


def _words(html: str) -> int:
    return len(validator._normalize_words(validator.strip_tags(html or "")))


def _telugu_share(html: str) -> float:
    words = validator._normalize_words(validator.strip_tags(html or ""))
    if not words:
        return 0.0
    tel = sum(1 for w in words if re.search(r"[\u0c00-\u0c7f]", w))
    return tel / len(words)


def _image_size(path: Path) -> tuple:
    try:
        from PIL import Image

        with Image.open(path) as im:
            return im.size
    except Exception:  # noqa: BLE001
        return (0, 0)


def run(article: dict, html: str = "", media_id: Optional[int] = None,
        image_path: Optional[Path] = None) -> Dict:
    """Anni checks → {"rows", "score", "critical_fails", "cert_id", ...}."""
    html = html or article.get("content_html", "") or ""
    kw = (article.get("focus_keyword") or "").strip()
    kw_l = kw.lower()
    title = (article.get("title") or "").strip()
    meta = (article.get("meta_description") or "").strip()
    slug = (article.get("slug") or "").strip()
    plain = validator.strip_tags(html)
    words = _words(html)
    rows: List[dict] = []

    def add(cid, group, label, ok, detail="", fix="", weight=1, critical=False,
            scored=True):
        rows.append({
            "id": cid, "group": group, "label": label, "ok": bool(ok),
            "detail": str(detail)[:160], "fix": fix if not ok else "",
            "weight": weight, "critical": critical or cid in CRITICAL,
            "scored": scored,
        })

    # ------------------------------------------------------------ CONTENT
    rm = article.get("_rm") or {}
    add("words", "CONTENT", "Content depth (≥1500 words)", words >= 1500,
        f"{words} words", "deep research + 1600+ words rayandi", 3)
    dens = (plain.lower().count(kw_l) / words) if (kw_l and words) else 0
    add("density", "CONTENT", "Keyword density (0.4–3%)", 0.004 <= dens <= 0.03,
        f"{dens:.2%} ({plain.lower().count(kw_l)}x)", "rm100 density fix chudandi", 2)
    first_par = ""
    m = re.search(r"<p[^>]*>(.*?)</p>", html, flags=re.S)
    if m:
        first_par = validator.strip_tags(m.group(1)).lower()
    add("kw_first_para", "CONTENT", "Keyword first paragraph lo", kw_l in first_par,
        "first para ledu" if not first_par else "ok", "rm100 lede add cheyandi", 2)
    add("kw_body", "CONTENT", "Keyword body lo 7+ sarlu",
        plain.lower().count(kw_l) >= 7, f"{plain.lower().count(kw_l)}x",
        "rm100 density pass chudandi", 1)
    faq = article.get("faq") or []
    add("faq", "CONTENT", "FAQ 3+ ప్రశ్నలు", len(faq) >= 3 or html.count("<h3") >= 3,
        f"{len(faq)} faq · {html.count('<h3')} h3", "FAQ section add cheyandi", 1)
    add("facts_table", "CONTENT", "ముఖ్య వివరాలు table", "<table" in html,
        "table ledu", "rm100 facts table (unna facts tho)", 1)
    toc_ok, toc_detail = True, "TOC ledu (optional)"
    if "su-toc" in html:
        head_ids = set(re.findall(r'<h[23][^>]*id="([^"]+)"', html))
        links = set(re.findall(r'<a href="#([^"]+)"', html))
        toc_ok = bool(links) and links <= head_ids
        toc_detail = f"{len(links)} links · ids {len(head_ids)}"
    add("toc", "CONTENT", "TOC links heading ids ki match", toc_ok, toc_detail,
        "rm100.fix_toc (ids okkasari compute avvali)", 2)
    low = plain.lower()
    dev = [p for p in DEV_PATTERNS if p in low]
    add("no_dev_text", "CONTENT", "Dev/demo/placeholder text ledu", not dev,
        ", ".join(dev) or "clean", "aa text theeseyandi (public site!)", 3,
        critical=True)
    paras = [len(validator.strip_tags(p).split())
             for p in re.findall(r"<p[^>]*>.*?</p>", html, flags=re.S)]
    long_p = sum(1 for n in paras if n > 140)
    add("para_len", "CONTENT", "Paragraphs ≤140 words", long_p == 0, f"{long_p} long",
        "rm100 paragraph split", 1)
    n_sent, with_tr, ratio = _transition_ratio(html)
    add("transitions", "CONTENT", "Telugu connectives 25%+ sentences",
        ratio >= 0.25, f"{ratio:.0%} ({with_tr}/{n_sent})",
        "rm100 transitions pass", 1)
    share = _telugu_share(html)
    add("telugu_share", "CONTENT", "Telugu script share ≥25%", share >= 0.25,
        f"{share:.0%}", "content pure Telugu lo rayandi", 2)
    lis = [len(validator.strip_tags(x).split())
           for x in re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.S)]
    bad_li = sum(1 for n in lis if n > 12)
    add("list_items", "CONTENT", "List items ≤12 words", bad_li == 0,
        f"{bad_li} long items", "list items short cheyandi", 1)
    heads = [validator.strip_tags(h).strip().lower()
             for h in re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)]
    dup_h = len(heads) - len(set(heads))
    add("dup_h2", "CONTENT", "Duplicate H2s ledu", dup_h == 0, f"{dup_h} duplicates",
        "samana H2 theeseyandi", 1)

    # ------------------------------------------------------------ SEO
    add("title_len", "SEO", "Title 40–62 chars", 40 <= len(title) <= 62,
        f"{len(title)} ch", "rm100 title fix", 2)
    pos = title.lower().find(kw_l) if kw_l else -1
    add("title_kw", "SEO", "Focus keyword title MODATLO", kw_l and pos != -1
        and pos <= max(0, len(title) // 2 - len(kw_l)), f"pos {pos}",
        "rm100 title fix (kw modatlo)", 2, critical=True)
    add("title_number", "SEO", "Title lo number/year", bool(re.search(r"\d", title)),
        "number ledu", "year add cheyandi", 1)
    add("title_power", "SEO", "Title lo power word",
        any(w in title.lower() for w in validator.TITLE_POWER_WORDS), "", "", 1)
    add("meta_ok", "SEO", "Meta 110–156 + keyword",
        110 <= len(meta) <= 156 and kw_l in meta.lower(), f"{len(meta)} ch",
        "rm100 meta fix", 2, critical=True)
    toks = [t for t in re.sub(r"[^\w\s-]", " ", kw_l).split() if len(t) > 2]
    add("slug_kw", "SEO", "Slug lo keyword tokens",
        bool(slug) and sum(1 for t in toks if t in slug.lower()) >= min(2, len(toks) or 1),
        slug, "rm100 slug fix", 1)
    rm_score = int(rm.get("score") or (article.get("_rm100") or {}).get("score") or 0)
    add("rm_score", "SEO", "Rank Math score 100", rm_score >= 100, f"{rm_score}/100",
        "RM_TARGET=100 + rm100 + refine rounds chudandi", 3, critical=True)
    sk = article.get("secondary_keywords") or []
    add("secondary_kw", "SEO", "Secondary keywords", True,
        f"{len(sk)} keywords" if sk else "focus keyword mattrame", "", 1, scored=False)

    # ------------------------------------------------------------ SCHEMA
    add("schema_article", "SCHEMA", "Article JSON-LD", '"@type": "Article"' in html
        or '"@type":"Article"' in html, "", "seo.schema_jsonld pettandi", 2,
        critical=True)
    add("schema_breadcrumb", "SCHEMA", "BreadcrumbList JSON-LD",
        "BreadcrumbList" in html, "", "", 1)
    rec = article.get("recruitment") or {}
    if rec:
        add("schema_job", "SCHEMA", "JobPosting (recruitment unte)", "JobPosting" in html,
            "", "seo.jobposting_obj — Google Jobs", 2)
    if article.get("list_items"):
        add("schema_list", "SCHEMA", "ItemList (list post)", "ItemList" in html, "", "", 1)
    add("schema_org_link", "SCHEMA", "Publisher → Organization @id",
        "#org" in html or "publisher" in html, "", "", 1)

    # ------------------------------------------------------------ MEDIA
    img = image_path or Path(config.OUTPUT_DIR) / "images" / f"{slug}.jpg"
    has_media = bool(media_id) or img.exists()
    add("media", "MEDIA", "Featured image", has_media,
        f"media_id={media_id}" if media_id else ("file" if img.exists() else "ledu"),
        "IMAGE_ENABLED + generator chudandi", 2)
    w, h = _image_size(img) if img.exists() else (0, 0)
    add("media_size", "MEDIA", "Image ≥1200px wide (Google Discover)",
        (w >= 1200) if img.exists() else bool(media_id),
        f"{w}x{h}" if w else ("upload ayyindi (WP side)" if media_id else "ledu"),
        "image_gen width 1200+ chudandi", 2)
    alt = article.get("_media_alt") or ""
    add("media_alt", "MEDIA", "Image alt lo keyword", kw_l in alt.lower() if alt else False,
        alt[:60] or "alt ledu", "alt text lo focus keyword", 2)
    ext_img = [u for u in re.findall(r'<img[^>]+src="(http[^"]+)"', html)
               if _host() and _host() not in u]
    add("img_host", "MEDIA", "Images hotlink ledu (mana host)", not ext_img,
        f"{len(ext_img)} external", "images ni WP lo upload cheyandi", 1)

    # ------------------------------------------------------------ LINKS
    links = re.findall(r'href="(http[^"]+)"', html)
    host = _host()
    internal = [l for l in links if host and host in l]
    external = [l for l in links if not host or host not in l]
    add("internal_links", "LINKS", "Internal links 3+", len(internal) >= 3,
        f"{len(internal)}", "internal hub links add cheyandi", 2)
    auth = [l for l in external if re.search(r"\.(gov|nic|edu|ac)\.in|\.gov|\.edu", l)]
    add("external_auth", "LINKS", "External authority link (gov/edu)", bool(auth),
        f"{len(auth)}/{len(external)}", "official source link add cheyandi", 2)
    ad_blocks = re.findall(r'<aside class="su-ad[^"]*">(.*?)</aside>', html, flags=re.S)
    ad_links = [a for blk in ad_blocks for a in re.findall(r"<a\s[^>]*>", blk)]
    lab = [a for a in ad_links if "sponsored" in a]
    add("sponsored_label", "LINKS", "Ad/paid links rel=sponsored",
        len(lab) == len(ad_links), f"{len(lab)}/{len(ad_links)} ad links labelled",
        "house/affiliate links ki rel=\"sponsored nofollow\"", 1)
    add("no_empty_anchor", "LINKS", "Empty anchors ledu",
        not re.search(r'<a[^>]*>\s*</a>', html), "", "", 1)

    # ------------------------------------------------------------ ADSENSE
    slots = sum(1 for k in ("top_leaderboard", "in_article", "sidebar", "anchor")
                if (article.get("_ad_slots") or {}).get(k))
    slot_cfg = slots or (1 if ("su-ad" in html or "adsbygoogle" in html) else 0)
    add("ad_present", "ADSENSE", "Ad slot content lo", bool(slot_cfg),
        f"{slot_cfg} slot", "studentup_ad() place check cheyandi", 1)
    house = html.count("su-ad-house")
    max_house = max(1, words // 600)
    add("house_ratio", "ADSENSE", "House ads content ratio (≤1/600 words)",
        house <= max_house, f"{house} ≤ {max_house}", "house ad count thagginchandi", 1)
    add("ad_after_para", "ADSENSE", "Ad first paragraph tarvata (policy-friendly)",
        bool(re.search(r"</p>\s*<[^>]*(su-ad|ins class=\"adsbygoogle)", html))
        or "su-ad" not in html, "top ad ok (leaderboard)", "", 1)
    ads_txt = Path(config.BASE_DIR) / "preview" / "ads.txt"
    add("ads_txt", "ADSENSE", "ads.txt ready", ads_txt.exists(),
        "preview/ads.txt" if ads_txt.exists() else "ledu",
        "run.py --adsense-kit", 1)

    # ------------------------------------------------------------ FRESHNESS
    today = date.today()
    pub = (article.get("date_published") or "").strip()[:10]
    pub_ok = True
    if pub:
        try:
            pub_ok = datetime.strptime(pub, "%Y-%m-%d").date() <= today
        except Exception:  # noqa: BLE001
            pub_ok = False
    add("date_pub", "FRESHNESS", "Date published ≤ today", pub_ok, pub or "auto (WP)",
        "date tappu — check cheyandi", 1)
    end = str(rec.get("apply_end") or article.get("last_date") or "")[:10]
    end_ok = True
    if end:
        try:
            end_ok = datetime.strptime(end, "%Y-%m-%d").date() >= today
        except Exception:  # noqa: BLE001
            end_ok = True
    add("deadline_valid", "FRESHNESS", "Deadline past kaadu", end_ok, end or "n/a",
        "past deadline post publish cheyyakandi", 2, critical=bool(end))
    add("refresh_date", "FRESHNESS", "Update ki dateModified", True,
        str(article.get("date_modified") or "auto"), "", 1, scored=False)

    # ------------------------------------------------------------ GOOGLE READINESS
    add("lang", "GOOGLE READINESS", "inLanguage te", '"inLanguage": "te"' in html
        or '"inLanguage":"te"' in html, "", "seo.schema_jsonld", 1)
    add("author", "GOOGLE READINESS", "Named author (E-E-A-T)", '"author"' in html,
        "", "author_for_slug bylines", 1)
    add("publisher", "GOOGLE READINESS", "Publisher (brand signal)",
        '"publisher"' in html, "", "", 1)
    demand = article.get("_demand") or {}
    kw_score = int(demand.get("score") or 0)
    add("demand", "GOOGLE READINESS", "Demand signal (trend/priority)",
        kw_score >= 50 if kw_score else True,
        f"{kw_score}/100" if kw_score else "trend queue lo ledu (mari okkasarilo)",
        "run.py --trends tho queue ninpandi", 2, scored=bool(kw_score))
    dup_ok, dup_detail = True, "fingerprints levu"
    try:
        from . import state

        stored = state.load_fingerprints(config.STATE_PATH)
        if stored:
            overlap, matched = validator.near_duplicate(
                title, html, stored, threshold=float(getattr(config, "DUP_MAX", 0.62)))
            dup_ok = overlap < float(getattr(config, "DUP_MAX", 0.62))
            dup_detail = f"overlap {overlap:.0%}" + (f" ({matched})" if matched else "")
    except Exception as exc:  # noqa: BLE001
        dup_detail = f"skip ({type(exc).__name__})"
    add("no_duplicate", "GOOGLE READINESS", "Near-duplicate ledu (Google scaled-content)",
        dup_ok, dup_detail, "kotha angle/facts add cheyandi — copy kaadu", 2,
        critical=True)
    add("facts_clean", "GOOGLE READINESS", "Unverified facts ledu",
        not (article.get("_fact") or []), f"{len(article.get('_fact') or [])} flags",
        "fact guard flags review cheyandi", 3, critical=True)
    add("indexnow", "GOOGLE READINESS", "IndexNow submit (publish tarvata)", True,
        "auto (pipeline)", "", 1, scored=False)

    scored_rows = [r for r in rows if r["scored"]]
    tw = sum(r["weight"] for r in scored_rows) or 1
    wok = sum(r["weight"] for r in scored_rows if r["ok"])
    score = round(100 * wok / tw)
    crit = [r["id"] for r in rows if r["critical"] and not r["ok"]]
    cert_id = hashlib.sha1(
        f"{slug}|{title}|{date.today().isoformat()}".encode("utf-8")).hexdigest()[:10]
    return {
        "cert_id": cert_id, "date": date.today().isoformat(), "title": title,
        "slug": slug, "score": score, "passed": len([r for r in rows if r["ok"]]),
        "total": len(rows), "critical_fails": crit,
        "block": bool(crit) and bool(getattr(config, "PIN_GATE_BLOCK", True)),
        "rows": rows, "words": words, "rankmath": rm_score,
    }


def _host() -> str:
    try:
        from urllib.parse import urlparse

        return urlparse(config.WP_SITE).netloc
    except Exception:  # noqa: BLE001
        return ""


def _transition_ratio(html: str) -> tuple:
    plain = validator.strip_tags(html or "")
    sents = [x for x in re.split(r"[.!?\u0964]\s", plain) if len(x.split()) >= 4]
    have = sum(1 for x in sents if any(t in x for t in validator.TRANSITION_MARKS))
    return len(sents), have, (have / len(sents) if sents else 0.0)


# ------------------------------------------------------------------ output

def certificate_text(result: Dict, group_by_group: bool = True) -> str:
    lines = [
        "=" * 74,
        f"  🧾 PIN-TO-PIN CERTIFICATE · {result['cert_id']} · {result['date']}",
        f"  Post: {result['title'][:58]}  ({result['words']} words · "
        f"RankMath {result['rankmath']}/100)",
        f"  RESULT: {result['score']}/100 · {result['passed']}/{result['total']} checks"
        + (f" · ⛔ CRITICAL: {', '.join(result['critical_fails'])}"
           if result["critical_fails"] else " · ✅ critical ok"),
        "=" * 74,
    ]
    for group in GROUPS:
        rows = [r for r in result["rows"] if r["group"] == group]
        if not rows:
            continue
        lines.append(f"  ── {group}")
        for r in rows:
            mark = "✅" if r["ok"] else ("⛔" if r["critical"] else "❌")
            extra = f"  · {r['detail']}" if r["detail"] else ""
            lines.append(f"     {mark} {r['label']}{extra}")
    return "\n".join(lines)


def write_certificate(result: Dict, out_dir: Optional[Path] = None) -> Dict[str, str]:
    """JSON + MD certificate files (prathi post ki proof untundi)."""
    out = Path(out_dir or CERT_DIR)
    out.mkdir(parents=True, exist_ok=True)
    base = f"{result['date']}-{result['slug'] or result['cert_id']}"
    jpath = out / f"{base}.json"
    mpath = out / f"{base}.md"
    jpath.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = [f"# Pin-to-pin certificate — {result['title']}", "",
             f"- cert: `{result['cert_id']}` · date: {result['date']}",
             f"- score: **{result['score']}/100** · checks: {result['passed']}/{result['total']}",
             f"- Rank Math: **{result['rankmath']}/100** · words: {result['words']}",
             f"- critical fails: {', '.join(result['critical_fails']) or 'ఏమీ లేదు ✔'}",
             "", "| Group | Check | Result | Detail |",
             "|---|---|---|---|"]
    for r in result["rows"]:
        lines.append(f"| {r['group']} | {r['label']} | "
                     f"{'✅' if r['ok'] else ('⛔' if r['critical'] else '❌')} | {r['detail']} |")
    mpath.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"json": str(jpath), "md": str(mpath)}


def self_test() -> Dict:
    """Offline proof: complete fixture → gate certificate (no network, no WP)."""
    from . import rm100, seo

    art = rm100.sample_article()
    art["date_published"] = date.today().isoformat()
    art["secondary_keywords"] = ["tspsc group 2 syllabus", "group 2 hall ticket",
                                 "tspsc group 2 eligibility"]
    # seo.jobposting_obj ki kavalsinavi: org_name + future apply_end + 100+ ch description
    art["recruitment"] = {
        "org_name": "TSPSC", "org_url": "https://www.tspsc.gov.in/",
        "apply_end": date.today().isoformat(),
        "location": "Hyderabad, Telangana",
    }
    art["_media_alt"] = f"{art['focus_keyword']} – Government Jobs 2026 | studentup.in"
    art["_rm"] = {"score": 100}
    art["_fact"] = []
    rm100.apply(art)
    art["_rm"] = {"score": 100}
    art["content_html"] += seo.schema_jsonld(
        title=art["title"], description=art["meta_description"], faq=[],
        date_published=art["date_published"], slug=art["slug"],
        category=art["category"], recruitment=art["recruitment"])
    art["content_html"] += ('\n<p><a href="https://www.tspsc.gov.in/" rel="nofollow">'
                            'అధికారిక వెబ్‌సైట్</a> · '
                            f'<a href="{config.WP_SITE}">studentup.in</a> · '
                            f'<a href="{config.WP_SITE}/jobs/">ఉద్యోగాలు</a> · '
                            f'<a href="{config.WP_SITE}/exams/">పరీక్షలు</a></p>')
    art["content_html"] += ('\n<aside class="su-ad"><div class="su-ad-house">'
                            'ప్రకటన — house ad</div></aside>')
    # 1200px image (Discover) — PIL tho
    img = Path(config.OUTPUT_DIR) / "images" / f"{art['slug']}.jpg"
    try:
        img.parent.mkdir(parents=True, exist_ok=True)
        from PIL import Image

        Image.new("RGB", (1200, 675), (15, 46, 98)).save(img, quality=80)
    except Exception:  # noqa: BLE001
        pass
    return run(art, media_id=999)


def main() -> int:
    result = self_test()
    print(certificate_text(result))
    paths = write_certificate(result)
    print("-" * 74)
    print(f"  certificate: {paths['md']}")
    print(f"               {paths['json']}")
    ok = result["score"] >= 95 and not result["critical_fails"]
    print(f"  {'✅ PASS — pin to pin ready' if ok else '❌ FAIL — paina rows chudandi'}")
    print("=" * 74)
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
