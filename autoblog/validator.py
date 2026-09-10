"""Article QA engine — originality proof, validation scoring, HTML sanitizer.

1. originality_score(): 5-gram shingle containment — final article vs
   source texts. Idi measurable "no copy" proof (prompt hope kadu).
2. sanitize_html(): Gemini output lo ALLOWED tags tappa anni strip.
3. validate_article(): Rank Math-style checks -> score/100 + issues.
"""

import logging
import re
from typing import Dict, List

log = logging.getLogger("autoblog.validator")

ALLOWED_TAGS = {
    "h2", "h3", "p", "ul", "ol", "li", "strong", "em",
    "table", "thead", "tbody", "tr", "th", "td", "a",
}


def strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html)


def _normalize_words(text: str) -> List[str]:
    text = re.sub(r"[^\w\u0c00-\u0c7f]+", " ", text.lower())
    return re.sub(r"\s+", " ", text).split()


def text_shingles(text: str, n: int = 5) -> set:
    words = _normalize_words(text)
    return {" ".join(words[i:i + n]) for i in range(len(words) - n + 1)}


def originality_score(article_html: str, source_texts: List[str]) -> float:
    """100 = fully original. Worst-case containment across sources."""
    art_shingles = text_shingles(strip_tags(article_html))
    if not art_shingles:
        return 100.0
    worst = 0.0
    for src in source_texts or []:
        src_shingles = text_shingles(src)
        if not src_shingles:
            continue
        overlap = len(art_shingles & src_shingles)
        containment = overlap / min(len(art_shingles), len(src_shingles))
        worst = max(worst, containment)
    return round(100.0 * (1.0 - worst), 1)


def sanitize_html(html: str) -> str:
    """Allowed tags tappa anni strip (content ni preserve chesi)."""
    if not html:
        return html
    # full script/style blocks remove
    html = re.sub(r"<(script|style|iframe|form)[^>]*>.*?</\1>", "", html,
                  flags=re.S | re.I)
    html = re.sub(r"</?(html|head|body|!doctype)[^>]*>", "", html, flags=re.I)
    # markdown artifacts
    html = html.replace("```html", "").replace("```", "")

    def _keep(m: re.Match) -> str:
        return m.group(0) if m.group(1).lower() in ALLOWED_TAGS else ""

    html = re.sub(r"</?([a-zA-Z][a-zA-Z0-9]*)[^>]*>", _keep, html)
    # XSS hardening: event-handler attributes + javascript:/data: URLs strip
    # (allowed tags kuda attributes lo danger untayi — 1000x audit finding)
    html = re.sub(r"\s+on[a-zA-Z]+\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s>]+)", "", html,
                  flags=re.I)
    html = re.sub(r"(href|src)\s*=\s*(\"|')?\s*(javascript|vbscript|data):[^\s\"'>]*[\"']?",
                  r'\1="#"', html, flags=re.I)
    # empty paragraphs / excess newlines clean
    html = re.sub(r"<p>\s*</p>", "", html)
    html = re.sub(r"\n{3,}", "\n\n", html)
    return html.strip()


def word_count(html: str) -> int:
    return len(_normalize_words(strip_tags(html)))


def reading_minutes(words: int) -> int:
    return max(1, round(words / 200))


def validate_article(article: Dict, final_html: str = "") -> Dict:
    """Rank Math-style QA score. Returns {score, issues, words, reading_min}."""
    issues: List[str] = []
    html = final_html or article.get("content_html", "")
    plain = strip_tags(html)
    words = word_count(html)
    kw = (article.get("focus_keyword") or "").strip()

    def add(ok: bool, points: int, msg: str) -> int:
        if not ok:
            issues.append(msg)
        return points if ok else 0

    score = 0
    score += add(bool(kw), 5, "focus_keyword ledu")
    if kw:
        title = article.get("title", "")
        tlow = title.lower()
        score += add(kw.lower() in tlow, 6, "focus keyword title lo ledu")
        # Rank Math: keyword title FIRST HALF lo + number in title
        half = tlow[: max(1, len(tlow) // 2)]
        score += add(kw.lower() in half, 3, "focus keyword title first-half lo ledu")
        score += add(bool(re.search(r"\d", title)), 3, "title lo number ledu (year/vacancies)")
        first_p = re.search(r"<p>(.*?)</p>", html, flags=re.S)
        first_txt = strip_tags(first_p.group(1)) if first_p else ""
        score += add(kw.lower() in first_txt.lower(), 10,
                     "focus keyword first paragraph lo ledu")
        h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)
        kw_in_h2 = sum(1 for h in h2s if kw.lower() in strip_tags(h).lower())
        score += add(kw_in_h2 >= 1, 10, "focus keyword subheadings lo ledu")
        # Rank Math sweet spot ~1-2.5%
        density = plain.lower().count(kw.lower()) / max(1, words)
        score += add(0.008 <= density <= 0.025, 5,
                     f"keyword density out of range ({density:.3f})")

    score += add(words >= 1500, 10, f"word count takkuva ({words} < 1500)")
    score += add("<table" in html, 5, "table ledu (snippet eligibility)")
    score += add(len(article.get("faq") or []) >= 3, 10, "FAQ 3+ kavali")
    score += add(bool(article.get("external_links")), 4, "external links ledu")
    site_host = ""
    try:
        from urllib.parse import urlparse as _up
        from . import config as _cfg
        site_host = _up(_cfg.WP_SITE).netloc
    except Exception:
        pass
    links = re.findall(r'href="(http[^"]+)"', html)
    n_internal = sum(1 for l in links if site_host and site_host in l) if site_host else (1 if links else 0)
    score += add(n_internal >= 1, 4, "internal links ledu (Rank Math check)")
    meta_desc = article.get("meta_description") or ""
    score += add(120 <= len(meta_desc) <= 170 and (not kw or kw.lower() in meta_desc.lower()),
                 8, "meta description length/keyword problem")
    score += add(5 <= len(article.get("tags") or []) <= 8, 4, "tags 5-8 kavali")
    score += add(bool(article.get("quick_answer")), 5, "quick_answer ledu (snippet bait)")
    score += add(len(article.get("secondary_keywords") or []) >= 3, 4,
                 "secondary keywords 3+ kavali")
    # Rank Math readability: prathi paragraph 160 words kanna takkuva
    para_words = [len(strip_tags(m).split()) for m in re.findall(r"<p>(.*?)</p>", html, flags=re.S)]
    long_paras = sum(1 for w_ in para_words if w_ > 160)
    score += add(long_paras == 0 and len(para_words) >= 3, 6,
                 f"{long_paras} paragraphs too long (160+ words)" if long_paras else
                 "paragraphs structure weak")

    return {
        "score": min(100, score),
        "issues": issues,
        "words": words,
        "reading_min": reading_minutes(words),
    }


# ---------------------------------------------------------------- v18
# Real Rank Math panel lu check chese exact items — mana custom QA kaadu.
# Score normalize /100 + fixes list (auto-refine prompt ki veltundi).
TITLE_POWER_WORDS = ("best", "top", "easy", "complete", "free", "ultimate",
                     "proven", "simple", "guide", "aeguvu", "bestu", "pakka")
TRANSITION_MARKS = ("\u0c15\u0c3e\u0c28\u0c40", "\u0c05\u0c28\u0c4d\u0c26\u0c41\u0c35\u0c32\u0c4d\u0c32",
                    "\u0c2e\u0c30\u0c4b\u0c35\u0c48\u0c2a\u0c41", "\u0c05\u0c28\u0c4d\u0c24\u0c47\u0c15\u0c3e\u0c15\u0c41\u0c02\u0c21",
                    "\u0c1a\u0c3f\u0c35\u0c30\u0c17\u0c3e", "\u0c09\u0c26\u0c3e\u0c39\u0c30\u0c23\u0c15\u0c41",
                    "\u0c05\u0c32\u0c3e\u0c17\u0c47", "\u0c15\u0c3e\u0c2c\u0c1f\u0c4d\u0c1f\u0c3f", "\u0c05\u0c2f\u0c3f\u0c24\u0c47")


def rankmath_strict(article: Dict, final_html: str = "") -> Dict:
    """Rank Math content-analysis checks — honest score + actionable fixes."""
    html = final_html or article.get("content_html", "") or ""
    title = (article.get("title") or "").strip()
    kw = (article.get("focus_keyword") or "").strip()
    kw_l = kw.lower()
    meta = (article.get("meta_description") or "").strip()
    slug = (article.get("slug") or "").lower()
    plain = strip_tags(html)
    words = len(_normalize_words(plain))
    paras = re.findall(r"<p[^>]*>(.*?)</p>", html, flags=re.S)
    results = []

    def check(name, ok, pts, fix=""):
        results.append({"item": name, "ok": bool(ok), "points": pts, "fix": fix})
        return bool(ok)

    check("focus-keyword", bool(kw), 4,
          "focus_keyword set cheyandi (exact search phrase)")
    if kw:
        tl = title.lower()
        check("kw-in-title", kw_l in tl, 10, "title lo focus keyword undali")
        _pos = tl.find(kw_l)
        check("kw-title-start", _pos != -1
              and _pos <= max(0, len(tl) // 2 - len(kw_l)), 5,
              "focus keyword TITLE MODALO (first half) vundali")
        check("title-length", 40 <= len(title) <= 62, 5,
              f"title {len(title)} chars — 40-60 chars madhya pettandi")
        check("title-number", bool(re.search(r"\d", title)), 5,
              "title lo number (year / vacancy count) undali")
        check("title-power-word",
              any(w in tl for w in TITLE_POWER_WORDS), 4,
              "title lo power word add (Best/Top/Easy/Complete/Free)")
        md = meta.lower()
        check("kw-in-meta", kw_l in md, 8, "meta description lo focus keyword undali")
        check("meta-length", 110 <= len(meta) <= 160, 4,
              f"meta description {len(meta)} chars — 110-156 ki madhya")
        kw_tokens = [t for t in re.sub(r"[^\w]+", " ", kw_l).split() if len(t) > 2]
        hits = sum(1 for t in kw_tokens if t in slug) if kw_tokens else 1
        check("kw-in-url", bool(slug) and hits >= min(2, len(kw_tokens) or 1), 5,
              "URL/slug lo focus keyword tokens undali")
        first = strip_tags(paras[0]).lower() if paras else ""
        check("kw-first-para", kw_l in first, 8,
              "first paragraph lo focus keyword rawali")
        dens = plain.lower().count(kw_l) / max(1, words)
        check("kw-density", 0.004 <= dens <= 0.03, 8,
              f"keyword density {dens:.2%} — exact phrase ga 8-14 sarlu repeat cheyandi")
        h2s = re.findall(r"<h2[^>]*>(.*?)</h2>", html, flags=re.S)
        check("kw-in-h2",
              sum(1 for h in h2s if kw_l in strip_tags(h).lower()) >= 2, 5,
              "2+ H2 headings lo focus keyword undali")
    check("content-length", words >= 1500, 8,
          f"content {words} words — 1600+ rayandi")
    lis = [strip_tags(x).split()
           for x in re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.S)]
    bad_li = sum(1 for w in lis if len(w) > 12)
    check("list-items-short", bad_li == 0, 6,
          f"{bad_li} list items 12+ wordsunnayi — prathi step 10 words ki menta short cheyandi")
    pws = [len(strip_tags(p).split()) for p in paras] if paras else []
    big = sum(1 for n in pws if n > 120)
    check("paragraph-length", big <= max(0, len(pws) // 10), 6,
          f"{big} paragraphs peddayi — 2-3 sentences ki seema")
    seg = re.split(r"<h[23][^>]*>", html)
    long_seg = sum(1 for ss in seg[1:] if len(strip_tags(ss).split()) > 300)
    check("subheadings-distribution", long_seg == 0, 5,
          f"{long_seg} sections 300+ words — kotha H2/H3 divisions add cheyandi")
    sents = [x for x in re.split(r"[.!?\u0964]\s", plain) if len(x.split()) >= 4]
    trans = sum(1 for x in sents if any(t in x for t in TRANSITION_MARKS))
    t_ratio = trans / max(1, len(sents))
    check("transition-words", t_ratio >= 0.25, 5,
          f"connectives {int(t_ratio * 100)}% matrame — కానీ/అందువల్ల/మరోవైపు/అలాగే/చివరగా peruganga vaadi")
    check("tables", html.count("<table") >= 1, 3, "okka comparison tableaina add cheyandi")
    check("faq-answers", html.count("<h3") >= 3 or len(article.get("faq") or []) >= 3, 3,
          "FAQ section lo 3+ questions")
    links = re.findall(r'href="(http[^"]+)"', html)
    ext = [l for l in links if config_site_host() not in l] if links else []
    check("external-links", len(ext) >= 1, 3, "oka real official website link add cheyandi")
    check("internal-links", len(links) - len(ext) >= 1, 3,
          "mana site lōki okka internal linkaina kavali")

    earned = sum(r["points"] for r in results if r["ok"])
    possible = sum(r["points"] for r in results) or 1
    fails = [r for r in results if not r["ok"]]
    return {
        "score": min(100, round(100 * earned / possible)),
        "issues": [r["item"] for r in fails],
        "fixes": [r["fix"] for r in fails if r["fix"]],
        "words": words,
    }


def config_site_host() -> str:
    try:
        from urllib.parse import urlparse as _up
        from . import config as _cfg
        return _up(_cfg.WP_SITE).netloc
    except Exception:
        return ""

# ---------------------------------------------------------------- v19
# Near-duplicate detection (Google "scaled content abuse" policy): swapped-
# name / only-date-changed pages — mana own published posts tho compare.
# Method: unique 3-word shingles of first slice → containment overlap
# |A∩B| / min(|A|,|B|) — robust even when lengths differ.
def fingerprint_tokens(text: str, limit: int = 400) -> list:
    words = [w for w in re.findall(r"[a-z0-9\u0c00-\u0c7f]+",
                                   (text or "").lower())
             if len(w) >= 2]
    grams, seen = [], set()
    for i in range(max(0, len(words) - 2)):
        g = " ".join(words[i:i + 3])
        if g not in seen:
            seen.add(g)
            grams.append(g)
    if len(grams) > limit:  # deterministic downsample
        step = len(grams) / limit
        grams = [grams[int(i * step)] for i in range(limit)]
    return grams


def near_duplicate(title: str, content_html: str,
                   stored: list, threshold: float = 0.62):
    """stored: [{"slug":..., "t":[shingles]}]. Returns (overlap, matched_slug)."""
    mine = set(fingerprint_tokens(
        (title or "") + ". " + strip_tags(content_html)))
    if len(mine) < 60:
        return 0.0, ""  # too short to judge — false-positive kaadu
    best, slug = 0.0, ""
    for row in stored or []:
        theirs = set(row.get("t") or [])
        if len(theirs) < 60:
            continue
        ov = len(mine & theirs) / min(len(mine), len(theirs))
        if ov > best:
            best, slug = ov, row.get("slug", "")
    return best, slug


# ---------------------------------------------------------------- v21
# Fact guard: article lo verify-avga data (dates, vacancy counts) leak
# rayakudadu — Google News + AdSense trust ki idi #1 requirement.
_MONTH_NAMES = ["january", "february", "march", "april", "may", "june",
               "july", "august", "september", "october", "november",
               "december"]
_MONTHS = {}
for _i, _mn in enumerate(_MONTH_NAMES, 1):
    _MONTHS[_mn] = _i
    _MONTHS[_mn[:3]] = _i  # "15-Nov-2026" type abbreviations kuda


def _date_tuples(text: str) -> set:
    """All (y, m, d) date shapes in text — numeric + English month formats."""
    out = set()
    t = (text or "").lower()
    for m in re.finditer(r"(\d{4})-(\d{1,2})-(\d{1,2})", t):
        y, mo, d = map(int, m.groups())
        out.add((y, mo, d))
    for m in re.finditer(r"(\d{1,2})[/.-](\d{1,2})[/.-](\d{2,4})", t):
        d, mo, y = map(int, m.groups())
        if y < 100:
            y += 2000
        out.add((y, mo, d))
    for m in re.finditer(
            r"(\d{1,2})\s*(?:st|nd|rd|th)?[\s./-]*([a-z]+)[\s./-]*(\d{4})",
            t):
        d, mon, y = m.groups()
        if mon in _MONTHS:
            out.add((int(y), _MONTHS[mon], int(d)))
    for m in re.finditer(
            r"([a-z]+)\s+(\d{1,2}),?\s*(\d{4})", t):
        mon, d, y = m.groups()
        if mon in _MONTHS:
            out.add((int(y), _MONTHS[mon], int(d)))
    return {x for x in out if 2020 <= x[0] <= 2035 and 1 <= x[1] <= 12
            and 1 <= x[2] <= 31}


def fact_guard(article_html: str, source_texts: list) -> list:
    """Returns human-fix strings for dates/counts NOT present in sources."""
    if not source_texts:
        return []  # schedule-generated (no reference) — guard N/A
    src_dates = set()
    for st in source_texts:
        src_dates |= _date_tuples(st or "")
    art_text = strip_tags(article_html or "")
    bad = []
    for (y, mo, d) in sorted(_date_tuples(art_text) - src_dates):
        bad.append(f"{d:02d}-{mo:02d}-{y} (date source lo ledu)")
    # vacancy counts: "1234 posts/vacancies/positions/upadhis" 
    src_nums = set(re.findall(r"\d[\d,]{1,7}", " ".join(source_texts)))
    src_nums_nocomma = {n.replace(",", "") for n in src_nums}
    for m in re.finditer(
            r"([\d,]{2,8})\s*(?:posts|vacanc|position|upadhi|అవకాశ)",
            art_text, flags=re.I):
        n = m.group(1).replace(",", "")
        if n not in src_nums_nocomma and not any(n in x for x in src_nums):
            bad.append(f"{m.group(1)} count source lo verify kaledu")
    return bad[:8]
