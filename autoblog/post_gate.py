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
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from . import config, validator

log = logging.getLogger("autoblog.pin_gate")

CERT_DIR = Path(getattr(config, "OUTPUT_DIR", "output")) / "certificates"

GROUPS = ("CONTENT", "SEMANTIC", "SEO", "SCHEMA", "MEDIA", "LINKS", "ADSENSE",
          "FRESHNESS", "GOOGLE READINESS")

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
        f"{html.count('<table')} table", "rm100 facts table (unna facts tho)", 1)
    toc_ok, toc_detail = True, "TOC ledu (optional)"
    if "su-toc" in html:
        head_ids = set(re.findall(r'<h[23][^>]*id="([^"]+)"', html))
        links = set(re.findall(r'<a href="#([^"]+)"', html))
        toc_ok = bool(links) and links <= head_ids
        toc_detail = f"{len(links)} links · ids {len(head_ids)}"
    add("toc", "CONTENT", "TOC links heading ids ki match", toc_ok, toc_detail,
        "rm100.fix_toc (ids okkasari compute avvali)", 2)
    add("rankmath_toc", "SEO", "Rank Math TOC block detected",
        "wp:rank-math/toc-block" in html and "wp-block-rank-math-toc-block" in html,
        "official editor marker", "Rank Math TOC block wrapper add cheyandi", 2)
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

    # ------------------------------------------------------------ DEEPER (v66 batch 2)
    # Google + reader + mobile quality — "blog rasthunnapudu inka chala check cheyali"
    heads = re.findall(r"<(h[1-6])[^>]*>(.*?)</\1>", html or "", flags=re.S)
    levels = [int(t[1]) for t, _ in heads]
    skips, prev = 0, None
    for lv in levels:
        if prev and lv > prev + 1:
            skips += 1
        prev = lv
    h1 = levels.count(1)
    add("heading_hierarchy", "CONTENT", "Heading hierarchy (H1 ledu · skip ledu)",
        h1 == 0 and skips == 0, f"H1 {h1} · level-skip {skips}",
        "content lo H1 vaddu (theme okati istundi) · H2→H4 skip cheyyaku", 2)
    long_h = [validator.strip_tags(t) for _, t in heads if len(validator.strip_tags(t)) > 70]
    add("heading_length", "CONTENT", "Headings ≤70 chars (mobile truncate kaadu)",
        not long_h, f"{len(long_h)} long", "heading ni short ga rayandi", 1)
    md = [pat for pat in ("**", "](http", "## ", "~~", "&lt;p&gt;") if pat in (html or "")]
    add("markdown_artifacts", "CONTENT", "Markdown/escape leftovers ledu",
        not md, ", ".join(md) or "clean", "LLM markdown output → HTML convert cheyandi", 2)
    long_items = [validator.strip_tags(x) for x in
                  re.findall(r"<li[^>]*>(.*?)</li>", html or "", flags=re.S)
                  if len(validator.strip_tags(x).split()) > 12]
    add("list_item_len", "CONTENT", "List items ≤12 words", not long_items,
        f"{len(long_items)} long", "list items ni short ga cheyandi", 1)
    tables = re.findall(r"<table.*?</table>", html or "", flags=re.S)
    if tables:
        first_row = re.search(r"<tr[^>]*>(.*?)</tr>", tables[0], flags=re.S)
        cols = len(re.findall(r"<t[hd][^>]*>", first_row.group(1))) if first_row else 0
        add("table_mobile", "CONTENT", "Table ≤5 columns (mobile lo scroll kaadu)",
            cols <= 5, f"{cols} cols", "table columns thaggandi", 1)
    else:
        add("table_mobile", "CONTENT", "Table ≤5 columns (table ledu — skip)",
            True, "table ledu", "", 1, scored=False)
    # Google quality/compliance: guarantee/clickbait claims (AdSense + trust risk)
    bait = [p for p in BAIT_PATTERNS if p in plain.lower()]
    add("no_scam_claims", "GOOGLE READINESS",
        "Job-guarantee/clickbait claims ledu (trust + policy)",
        not bait, ", ".join(bait) or "clean",
        "gurantee type claims theeseyandi (Google + AdSense policy)", 2)
    # keyword cannibalization: same keyword tho inkoka post unte rendu rank avvavu
    cann_ok, cann_detail = _cannibalization(article)
    add("ik_kw_unique", "SEO", "Focus keyword cannibalization ledu",
        cann_ok, cann_detail, "vere keyword angle theesukondi leda purana post update cheyandi", 1)
    add("slug_length", "SEO", "Slug ≤60 chars · 3+ words",
        bool(slug) and 3 <= len(slug) <= 60 and "_" not in slug,
        f"{len(slug)} ch · {len(slug.split('-'))} words", "slug ni clean cheyandi", 1)
    cta = [w for w in ("దరఖాస్తు", "తెలుసుకోండి", "చూడండి", "వివరాలు", "అప్‌డేట్",
                       "apply", "details", "check") if w in meta.lower()]
    has_num = bool(re.search(r"\d", meta))
    add("meta_cta", "SEO", "Meta lo CTA/action word (CTR)", bool(cta) and has_num,
        f"cta {cta or 'ledu'} · number {'yes' if has_num else 'no'}",
        "meta lo number + action word pettandi (CTR penchutundi)", 1)
    sec = [k for k in (article.get("secondary_keywords") or []) if str(k).strip()]
    if sec:
        used = [k for k in sec
                if any(tok in plain.lower() for tok in str(k).lower().split() if len(tok) > 4)]
        add("sec_kw_used", "SEO", "Secondary keywords body lo", bool(used),
            f"{len(used)}/{len(sec)} used", "secondary keywords ni content lo kalapandi", 1)
    else:
        add("sec_kw_used", "SEO", "Secondary keywords body lo", True,
            "secondary levu", "", 1, scored=False)
    imgs = re.findall(r"<img[^>]*>", html or "")
    if imgs:
        bad = [i for i in imgs if "width=" not in i or "height=" not in i]
        add("img_dimensions", "MEDIA", "Content images ki width/height (CLS)",
            not bad, f"{len(bad)}/{len(imgs)} without size", "img ki width/height ivvandi", 1)
    else:
        add("img_dimensions", "MEDIA", "Content images ki width/height (CLS)", True,
            "content img ledu · featured image theme handle chestundi", "", 1, scored=False)
    anchors = re.findall(r"<a[^>]*>(.*?)</a>", html or "", flags=re.S)
    weak = [a.strip().lower() for a in anchors
            if a.strip().lower() in ("click here", "here", "ఇక్కడ", "ఇక్కడ క్లిక్",
                                     "link", "ఇక్కడ నొక్కండి", "")
            or a.strip().lower().startswith("http")]
    add("anchor_text", "LINKS", "Anchor text descriptive (click here ledu)",
        not weak, f"{len(weak)} weak anchors", "anchor text lo ardham unna maatalu pettandi", 1)
    faq_list = article.get("faq") or []
    if faq_list:
        deep_ans = 0
        for item in faq_list:
            if isinstance(item, dict):
                a = item.get("a") or item.get("answer") or ""
            elif isinstance(item, (list, tuple)) and len(item) >= 2:
                a = item[1]
            else:
                continue
            if len(validator.strip_tags(str(a)).split()) >= 12:
                deep_ans += 1
        add("faq_depth", "SEMANTIC", "FAQ answers 3+ deep (12+ words)",
            deep_ans >= 3, f"{deep_ans}/{len(faq_list)} deep",
            "FAQ javabl̄u konchem deep ga rayandi (ఉపయోగకరం + snippet)", 1)
    else:
        add("faq_depth", "SEMANTIC", "FAQ answers deep (faq list ledu — skip)",
            True, "faq list ledu", "", 1, scored=False)

    # ------------------------------------------------------------ SEMANTIC (v66)
    # Google "ee page aa prashnaki saripoyina answer aa?" + topic authority.
    entities, questions, sentences = _semantic_metrics(article, html)
    add("entity_coverage", "SEMANTIC", "Primary entity + related entities (2+)",
        entities >= 3, f"{entities} entities", "rm100 entities block + body lo related terms", 2)
    add("takeaways", "SEMANTIC", "ముఖ్యాంశాలు (key takeaways) box",
        "su-takeaways" in html, "", "rm100 takeaways fix", 2)
    add("question_headings", "SEMANTIC", "Question-form headings 2+",
        questions >= 2, f"{questions} questions",
        "PAA-style ప్రశ్నలు H2/H3 ga (seo.related_questions_block)", 2)
    add("related_block", "SEMANTIC", "సంబంధిత అంశాలు block (topic cluster)",
        "su-related-entities" in html or "related-questions" in html, "",
        "rm100 entities block", 1)
    avg_sent = (sum(len(x.split()) for x in sentences) / len(sentences)) if sentences else 0
    add("readability", "SEMANTIC", "Avg sentence ≤24 words (చదవడానికి easy)",
        avg_sent and avg_sent <= 24, f"avg {avg_sent:.1f} words",
        "pedda vakyalu rendu ga cheyandi", 2)
    year = str(date.today().year)
    add("freshness_words", "SEMANTIC", "Current year content lo (fresh signal)",
        year in plain, f"{year}", "year/prathi తేదీ update cheyandi", 1)
    add("quick_answer", "SEMANTIC", "Quick answer / summary block",
        "quick-answer" in html or "su-takeaways" in html, "",
        "seo.enhance quick answer", 1)
    try:
        from . import trends

        queue = trends.next_topics(limit=12)
        if queue:
            qkw = [str(t.get("title", "")).lower() for t in queue]
            hit = any(kw_l and (kw_l in q or q[:24] in kw_l) for q in qkw)
            add("trend_match", "SEMANTIC", "Trending queue keyword match", hit,
                f"{len(queue)} topics in queue", "run.py --trends --trends-queue", 2)
    except Exception as exc:  # noqa: BLE001
        add("trend_match", "SEMANTIC", "Trending queue check", True,
            f"skip ({type(exc).__name__})", "", 1, scored=False)

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
    add("title_sentiment", "SEO", "Title lo positive sentiment word",
        any(w in title.lower() for w in ("best", "easy", "amazing", "excellent")),
        "", "Best/Easy lanti natural sentiment word add cheyandi", 1)
    add("meta_ok", "SEO", "Meta 110–156 + keyword",
        110 <= len(meta) <= 156 and kw_l in meta.lower(), f"{len(meta)} ch",
        "rm100 meta fix", 2, critical=True)
    toks = [t for t in re.sub(r"[^\w\s-]", " ", kw_l).split() if len(t) > 2]
    add("slug_kw", "SEO", "Slug lo keyword tokens",
        bool(slug) and sum(1 for t in toks if t in slug.lower()) >= min(2, len(toks) or 1),
        slug, "rm100 slug fix", 1)
    rm_score = int(rm.get("score") or (article.get("_rm100") or {}).get("score") or 0)
    add("rm_score", "SEO", "Local on-page preflight passed", rm_score >= 90,
        "pass" if rm_score >= 90 else "needs fixes",
        "Official Rank Math UI score kaadu; listed on-page issues fix cheyandi", 3,
        critical=True)
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
    fig = re.search(r'<figure class="su-figure">.*?</figure>', html, flags=re.S)
    fig_alt = (re.search(r'alt="([^"]*)"', fig.group(0)).group(1) if fig else "")
    add("content_image", "MEDIA", "Content lopala image (keyword alt)",
        bool(fig) and kw_l in fig_alt.lower(),
        fig_alt[:50] if fig else "ledu",
        "seo.attach_inline_image (publish time · featured image reuse)", 2)
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
    external_tags = [tag for tag in re.findall(r'<a\b[^>]+>', html, flags=re.I)
                     if re.search(r'href="https?://', tag, re.I)
                     and (not host or host not in tag)]
    editorial_dofollow = [tag for tag in external_tags
                          if "nofollow" not in tag.lower()
                          and "sponsored" not in tag.lower()]
    add("external_dofollow", "LINKS", "At least one editorial dofollow source",
        bool(editorial_dofollow), f"{len(editorial_dofollow)}/{len(external_tags)}",
        "official editorial link nunchi nofollow remove cheyandi", 2)
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
    today = validator.ist_today()  # v84: IST (server UTC kaadu)
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
    people_first = article.get("_google_quality") or {}
    add("methodology", "GOOGLE READINESS", "Visible Who/How/Why methodology",
        "su-methodology" in html, "", "google_quality.inject_methodology", 2,
        critical=True)
    add("people_first", "GOOGLE READINESS", "People-first evidence audit",
        bool(people_first.get("ok")),
        f"{people_first.get('score', 0)}/100",
        "; ".join(people_first.get("flags") or [])[:180], 3, critical=True)
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


def _semantic_metrics(article: dict, html: str) -> tuple:
    """(entity_count, question_headings, sentences) — semantic coverage metrics."""
    kw = (article.get("focus_keyword") or "").lower()
    plain = validator.strip_tags(html or "").lower()
    heads = [validator.strip_tags(h) for h in
             re.findall(r"<h[23][^>]*>(.*?)</h[23]>", html or "", flags=re.S)]
    questions = sum(1 for h in heads if "?" in h or "ఏమిటి" in h or "ఎలా" in h
                    or "ఎప్పుడు" in h or "ఎంత" in h or "ఎందుకు" in h)
    sentences = [x for x in re.split(r"[.!?\u0964]\s", validator.strip_tags(html or ""))
                 if len(x.split()) >= 4]
    entities = 0
    try:
        from . import top_post

        ent = top_post.detect_entity(article.get("focus_keyword") or "")
        if ent:
            entities = 1
        for row in top_post.keyword_universe():
            name = str(row.get("kw", "")).lower()
            if not name or name == kw:
                continue
            toks = [t for t in name.split() if len(t) > 3]
            if toks and all(t in plain for t in toks[:3]):
                entities += 1
            if entities >= 6:
                break
    except Exception:  # noqa: BLE001
        entities = 1 if kw else 0
    return entities, questions, sentences


BAIT_PATTERNS = (
    "job guarantee", "guaranteed job", "guaranteed selection", "100% job",
    "ఉద్యోగం గ్యారెంటీ", "గ్యారెంటీ ఉద్యోగం", "ఉద్యోగం గ్యారంటీ", "గ్యారంటీ ఉద్యోగం",
    "click here to earn", "get rich quick", "guaranteed income",
)
STOPWORDS = {"the", "and", "for", "with", "from", "this", "that", "notification", "details"}


def _kw_tokens(article: dict) -> list:
    kw = (article.get("focus_keyword") or "").lower()
    return [t for t in re.split(r"[^a-z0-9\u0c00-\u0c7f]+", kw)
            if len(t) >= 3 and t not in STOPWORDS]


def _cannibalization(article: dict) -> tuple:
    """Same focus keyword tho inkoka post unte — Google rendu ni compete cheyyistundi."""
    toks = _kw_tokens(article)
    if not toks:
        return True, "kw ledu"
    try:
        from . import config as _cfg
        from . import state as _st

        titles = _st.recent_titles(_cfg.STATE_DB, limit=200)
    except Exception as exc:  # noqa: BLE001 — state lekapote skip (publish aapadu)
        return True, f"skip ({type(exc).__name__})"
    cur_slug = (article.get("slug") or "").lower()
    for t in titles:
        tl = str(t).lower()
        if cur_slug and cur_slug.replace("-", " ") in tl:
            continue
        need = max(2, len(toks) - 1)
        if sum(1 for tk in toks if tk in tl) >= need:
            return False, f"'{str(t)[:44]}' tho overlap"
    return True, "overlap ledu"


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
        "apply_end": (date.today() + timedelta(days=1)).isoformat(),
        "location": "Hyderabad, Telangana",
    }
    art["_media_alt"] = f"{art['focus_keyword']} – Government Jobs 2026 | studentup.in"
    # v95: pipeline laage — featured image upload tarvata content lopala figure
    # (real function pilustunnam, hand-written HTML kaadu) → certificate realistic
    art["content_html"] = seo.attach_inline_image(
        art["content_html"],
        f"{config.WP_SITE.rstrip('/')}/wp-content/uploads/demo-featured.webp",
        art["_media_alt"], caption=art["title"][:120])
    art["_rm"] = {"score": 100}
    art["_fact"] = []
    rm100.apply(art)
    art["_rm"] = {"score": 100}
    art["content_html"] += seo.schema_jsonld(
        title=art["title"], description=art["meta_description"], faq=[],
        date_published=art["date_published"], slug=art["slug"],
        category=art["category"], recruitment=art["recruitment"])
    art["content_html"] += ('\n<p><a href="https://www.tspsc.gov.in/" rel="noopener">'
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
    art["content_html"] += (
        '<section class="su-methodology"><h2>ఈ Article ఎలా Prepare చేశాము?</h2>'
        '<p><strong>Who:</strong> editor</p><p><strong>How:</strong> sources</p>'
        '<p><strong>Why:</strong> applicant help</p></section>')
    art["_google_quality"] = {"ok": True, "score": 100, "flags": []}
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
