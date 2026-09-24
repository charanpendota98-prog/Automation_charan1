# -*- coding: utf-8 -*-
"""v64: RANK MATH 100 ENGINE — post publish ki mundu mechanical SEO fixes.

Enduku (mee requirement: "post ki Rank Math 100 vachela score high kosam"):
  Draft ni Gemini rayagane Rank Math tests anni pass avvavu (title lo number ledu,
  TOC ledu, keyword density takkuva, table/FAQ ledu...). Ee module **deterministic**
  ga (LLM avasaram ledu) aa mechanical items ni fix chestundi:

    title      → focus keyword title MODATLO + number(year) + power word + 40-62 chars
    seo_title  → title sync (Rank Math title tag)
    meta       → focus keyword + 110-156 chars
    slug       → keyword tokens (URL test)
    lede       → first paragraph lo keyword (natural Telugu vakya)
    TOC        → H2/H3 anchor ids + "విషయ సూచిక" jump links (UX + snippet chance)
    H2s        → 2+ H2 headings lo keyword
    density    → exact keyword 7-14 sarlu (0.4%-0.8% band — natural sentences)
    table      → "ముఖ్య వివరాలు" summary table (unnna facts thone — invent cheyyadu)
    FAQ        → 3+ ప్రశ్నలు (article['faq'] nunchi)
    links      → 1 external (source url) + 1 internal (site hub) — kotha URL invent ledu
    transitions→ Telugu connectives (అలాగే/అందువల్ల/చివరగా) 25%+ sentences ki
    paragraphs → 100+ word paragraphs ni sentence boundary lo split (~70-word chunks)

  Tarvata LLM refine (RM_REFINE_ROUNDS) migilinavi (words count, list items) fix
  chestundi; publish ki mundu **score malli compute** avutundi (state + Telegram +
  private diagnostics only; it is never presented as Rank Math's UI score).

Honest note: idi "Rank Math UI score ni hack" kaadu — Rank Math content tests
(mechanically checkable vi) anni nijamaina content structure tho pass ayye la
chestundi. Content nijam ga bagundaali (facts + depth) — adi LLM + sources pani.

Run proof: python run.py --rm100
"""
from __future__ import annotations

import html as _html
import re
from datetime import date
from typing import Dict, List
from urllib.parse import urlencode

from . import config, validator

TOC_MARK = "su-toc"
LEDE_MARK = "su-lede"
TELUGU_TAIL = "Complete Guide · Important Dates · Eligibility · Apply Online"
CONNECTIVES = ("అలాగే", "అందువల్ల", "ఇంకా", "చివరగా", "కాబట్టి", "మరోవైపు")
# keyword density band (validator: 0.4% - 3.0% ok). Target ~0.6% = natural.
DENSITY_TARGET = 0.006
DENSITY_MIN, DENSITY_MAX = 7, 15


# ------------------------------------------------------------------ helpers

def _text(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


def _words(s: str) -> int:
    return len(validator._normalize_words(validator.strip_tags(s or "")))


def _kw(article: dict) -> str:
    return _text(article.get("focus_keyword") or "")



def _kw_title(kw: str) -> str:
    """Keyword ni title-la ready cheyyadam — already proper-case (TSPSC) unte as-is."""
    out = []
    for w in kw.split():
        if any("\u0c00" <= ch <= "\u0c7f" for ch in w):
            out.append(w)                       # Telugu as-is
        elif w.islower() and len(w) > 1:
            out.append(w.capitalize())          # all-lower → capitalize
        else:
            out.append(w)                       # TSPSC / Group / 2 → as-is
    return " ".join(out)

def _count(text: str, needle: str) -> int:
    return text.lower().count(needle.lower()) if needle else 0


def _anchor_id(text: str, used: set) -> str:
    s = _text(validator.strip_tags(text)).lower()
    # v86: ASCII-only anchors (Telugu ids → copy-link/share ugly + parsers;
    # pure-Telugu headings ki stable section-N fallback).
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    s = s[:60] or f"section-{len(used) + 1}"
    base, i = s, 2
    while s in used:
        s = f"{base}-{i}"
        i += 1
    used.add(s)
    return s


def _host() -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(config.WP_SITE).netloc
    except Exception:
        return ""


def analyze(article: dict, html: str = "") -> dict:
    """validator.rankmath_strict wrapper (okka chota)."""
    return validator.rankmath_strict(article, html or article.get("content_html", ""))


# ------------------------------------------------------------------ fixers


def fix_title(article: dict) -> bool:
    """kw modatlo + number + power word + length 40-62 — guaranteed (tail priority).

    Rank Math tests: kw-in-title · kw-title-start · title-length · title-number ·
    title-power-word. Power word ni LAST lo pettadam valla trim lo povadu.
    """
    kw = _kw(article)
    if not kw:
        return False
    kt = _kw_title(kw)
    title = _text(article.get("title") or kt)

    # 1) keyword ledu → front lo pettali
    if kw.lower() not in title.lower():
        title = f"{kt} {title}"
    # 2) keyword first half (ideally start) lo undali
    pos = title.lower().find(kw.lower())
    if pos > max(0, len(title) // 2 - len(kw)):
        rest = _text(re.sub(re.escape(kw), "", title, count=1, flags=re.I))
        title = _text(f"{kt} {rest}") if rest else kt
    # 3) number/year — keyword tarvata VENTANE (trim lo povaddu)
    head = title
    if not re.search(r"\d", head):
        yr = re.search(r"\b(20\d{2})\b", kw) or re.search(r"\b(20\d{2})\b", title)
        year = yr.group(1) if yr else str(date.today().year)
        rest = _text(head[len(kt):]) if head.lower().startswith(kt.lower()) else head
        head = _text(f"{kt} {year} {rest}") if rest else _text(f"{kt} {year}")
    # 4) power + positive sentiment words. Rank Math scores these separately;
    # "Complete" is a power word but not a sentiment word in its analyzer.
    low = head.lower()
    has_power = any(w in low for w in validator.TITLE_POWER_WORDS)
    has_sentiment = any(w in low for w in ("best", "easy", "amazing", "excellent"))
    if (not has_power or not has_sentiment) and "—" in head:
        # Replace an old generic tail rather than stacking multiple hooks.
        old_head, old_tail = [x.strip() for x in head.split("—", 1)]
        if any(x in old_tail.lower() for x in
               ("complete", "guide", "details", "full information")):
            head = old_head
            low = head.lower()
            has_power = any(w in low for w in validator.TITLE_POWER_WORDS)
            has_sentiment = any(w in low for w in
                                ("best", "easy", "amazing", "excellent"))
    mid = ""
    tail = ""
    if not (has_power and has_sentiment):
        tail = "Best Guide"
    # 5) compose under 62 — power word ki space RESERVE (Telugu tail trim avvali)
    new = ""
    for t in ([tail] if tail else []) + [None]:
        pass
    if tail:
        budget = 62 - 3 - len(tail)
        h = head
        if len(h) > budget:                      # Telugu bhagam trim (kw intact)
            if len(kt) <= budget:
                keep = h[:budget]
                h2 = keep.rsplit(" ", 1)[0] if " " in keep else kt
                h = h2 if len(h2) >= len(kt) else kt
            else:                                # kw ne peddaga undi → shortest tail
                tail = "Best"
                budget = 62 - 3 - len(tail)
                h = head[:budget].rsplit(" ", 1)[0]
        new = f"{h} — {tail}"
    else:
        new = head
    if mid and len(new) + 3 + len(mid) <= 62:
        new = new.replace(" — ", f" — {mid} — ", 1) if " — " in new else f"{new} — {mid}"
    if len(new) > 62:                             # mid/th esthe kuda pedda → word boundary
        cut = new[:62]
        new = cut.rsplit(" ", 1)[0] if " " in cut[:-1] else cut
    if len(new) < 40:                             # 40 chars minimum (Rank Math)
        extra = TELUGU_TAIL.split(" · ")
        for e in extra:
            if len(new) + 3 + len(e) > 62:
                break
            new = f"{new} · {e}"
        while len(new) < 40 and tail == "":
            new = f"{new} · {kw}"
        if len(new) < 40:
            new = (new + " · " + TELUGU_TAIL)[:62].rsplit(" ", 1)[0]
    article["title"] = new.strip(" -—·") or kt
    # Keep the actual Rank Math SEO title in lockstep with the tested title;
    # stale LLM seo_title values were a common reason the editor disagreed.
    article["seo_title"] = article["title"][:62].rstrip(" -—·")
    return True

def fix_meta(article: dict) -> bool:
    kw = _kw(article)
    meta = _text(article.get("meta_description") or "")
    if not kw:
        return False
    if kw.lower() not in meta.lower():
        meta = _text(f"{_kw_title(kw)} గురించి పూర్తి వివరాలు: {meta}")
    if len(meta) < 110:
        meta = _text(f"{meta} Important Dates, Eligibility, Apply Online Process, Official Link ఇక్కడ ఉన్నాయి.")
    if len(meta) > 156:
        cut = meta[:156]
        meta = cut.rsplit(" ", 1)[0] if " " in cut[:-1] else cut
        if kw.lower() not in meta.lower():  # trim lo keyword poyindi ante mundu pettali
            meta = _text(f"{_kw_title(kw)}: {meta}")[:156]
    article["meta_description"] = meta
    return True


def _trim_slug(slug: str, limit: int = 75) -> str:
    """v95: slug ni 75 chars lopala (hyphen boundary) — Rank Math URL test.

    Google SERP lo URL cut avvadam + Rank Math "URL length" fail — rendu
    ee helper tho fix (keyword tokens pakkana pettakunda, 20 chars minimum).
    """
    slug = re.sub(r"-{2,}", "-", (slug or "").strip("-"))
    if len(slug) <= limit:
        return slug
    cut = slug[:limit]
    if "-" in cut[20:]:
        cut = cut[:cut.rfind("-")]
    return cut.strip("-")


def fix_slug(article: dict) -> bool:
    kw = _kw(article)
    if not kw:
        return False
    # v85: ASCII-only tokens (Telugu keyword → %E0.. URL-encoded slug vaddu;
    # English kebab-case = share/CTR safe). LLM slug English unte touch kaadu.
    toks = [t for t in re.sub(r"[^a-z0-9\s-]", " ", kw.lower()).split() if len(t) > 2]
    slug = (article.get("slug") or "").lower()
    need = min(2, len(toks)) if toks else 1
    have = sum(1 for t in toks if t in slug)
    if slug and have >= need:
        # v95: keyword tokens unna kuda URL pedda unte trim (Rank Math URL test)
        if len(slug) <= 75:
            return False
        article["slug"] = _trim_slug(slug)
        return True
    prefix = "-".join(toks) or re.sub(r"[^a-z0-9]+", "-", kw.lower()).strip("-")
    if not prefix:
        return False  # pure-Telugu keyword — existing slug ne keep (corrupt vaddu)
    slug_ascii = re.sub(r"[^a-z0-9-]+", "-", slug).strip("-")
    article["slug"] = _trim_slug(
        re.sub(r"-{2,}", "-", f"{prefix}-{slug_ascii}").strip("-"), 70)
    return True


def fix_lede(article: dict, html: str) -> str:
    """First paragraph lo keyword (already unte as-is)."""
    kw = _kw(article)
    if not kw or LEDE_MARK in html:
        return html
    paras = re.findall(r"<p[^>]*>.*?</p>", html, flags=re.S)
    first = paras[0].lower() if paras else ""
    if kw.lower() in validator.strip_tags(first).lower():
        return html
    lede = (f'<p class="{LEDE_MARK}"><strong>{_kw_title(kw)} — Quick Overview:</strong> '
            f"ఈ పోస్ట్‌లో {kw} కి సంబంధించిన Important Dates, Eligibility, Apply Online Process, "
            f"అధికారిక లింక్‌లు పూర్తిగా ఇచ్చాము.</p>\n")
    if paras:
        return html.replace(paras[0], lede + paras[0], 1)
    return lede + html


def fix_toc(article: dict, html: str) -> str:
    """H2/H3 ki ids + 'విషయ సూచిక' jump list (first paragraph tarvata).

    Ids OKKASARI compute avutayi — TOC link lekka ne heading id (mismatch = broken
    jump links). Bot content lo TOC already unte as-is (idempotent).
    """
    if TOC_MARK in html:
        return html
    heads = list(re.finditer(r"<h([23])([^>]*)>(.*?)</h\1>", html, flags=re.S))
    if len(heads) < 3:
        return html

    used: set = set()
    ids, rows = [], []
    for m in heads:
        attrs, inner = m.group(2), m.group(3)
        existing = re.search(r'id="([^"]+)"', attrs)
        if existing:
            aid = existing.group(1)
            used.add(aid)
        else:
            aid = _anchor_id(inner, used)
        ids.append(aid)
        txt = _text(validator.strip_tags(inner))
        if txt:
            rows.append((m.group(1), aid, txt))

    counter = {"i": 0}

    def _add_id(m):
        aid = ids[counter["i"]]
        counter["i"] += 1
        tag, attrs, inner = m.group(1), m.group(2), m.group(3)
        if "id=" in attrs:
            return m.group(0)
        return f'<h{tag}{attrs} id="{aid}">{inner}</h{tag}>'

    new_html = re.sub(r"<h([23])([^>]*)>(.*?)</h\1>", _add_id, html, flags=re.S)
    items = [f'<li><a href="#{aid}">{_html.escape(txt)}</a></li>'
             for tag, aid, txt in rows]
    if len(items) < 3:
        return new_html
    # Rank Math's editor recognizes its own TOC block marker. We keep the
    # accessible StudentUp markup inside it, so one TOC serves both readers and
    # the official Content Readability check (no duplicate plugin TOC needed).
    toc = ('<!-- wp:rank-math/toc-block {"title":"Table of Contents"} -->'
           '<div class="wp-block-rank-math-toc-block ' + TOC_MARK + '" '
           'role="navigation" aria-label="Table of Contents">'
           '<div class="su-toc-title">విషయ సూచిక (Table of Contents)</div><ol>'
           + "".join(items[:12]) + "</ol></div>"
           '<!-- /wp:rank-math/toc-block -->\n')
    paras = re.findall(r"<p[^>]*>.*?</p>", new_html, flags=re.S)
    if paras:
        return new_html.replace(paras[0], paras[0] + "\n" + toc, 1)
    return toc + new_html

def fix_h2_keyword(article: dict, html: str) -> str:
    """2+ H2 headings lo keyword (natural: 'అర్హతలు (TSPSC Group 2 Notification)')."""
    kw = _kw(article)
    if not kw:
        return html
    kt = _kw_title(kw)
    h2s = list(re.finditer(r"<h2([^>]*)>(.*?)</h2>", html, flags=re.S))
    with_kw = [m for m in h2s if kw.lower() in validator.strip_tags(m.group(2)).lower()]
    need = max(0, 2 - len(with_kw))
    if not need:
        return html
    for m in h2s:
        if need <= 0:
            break
        inner = m.group(2)
        if kw.lower() in validator.strip_tags(inner).lower():
            continue
        plain = _text(validator.strip_tags(inner))
        if len(plain) > 46:  # heading peddaga unte keyword addition vaddu (UX)
            continue
        html = html.replace(m.group(0), f'<h2{m.group(1)}>{inner} ({kt})</h2>', 1)
        need -= 1
    return html


def fix_density(article: dict, html: str) -> str:
    """Never manufacture paragraphs only to increase keyword density.

    Older versions inserted several ``su-kw`` paragraphs. They improved an
    internal score but read like filler. Generation/refinement must use the
    phrase naturally in useful sections; this pass only removes legacy padding.
    """
    return re.sub(r'\s*<p[^>]*class="[^"]*su-kw[^"]*"[^>]*>.*?</p>\s*',
                  "\n", html, flags=re.S | re.I)


_TE_MONTHS = ("జనవరి|ఫిబ్రవరి|మార్చి|ఏప్రిల్|మే|జూన్|జులై|ఆగస్టు|"
               "సెప్టెంబర్|అక్టోబర్|నవంబర్|డిసెంబర్")
_EN_MONTHS = ("January|February|March|April|May|June|July|August|"
              "September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|"
              "Aug|Sep|Sept|Oct|Nov|Dec")
_DATE = rf"(?:{_TE_MONTHS}|{_EN_MONTHS})\s+\d{{1,2}}(?:,?\s*\d{{4}})?|\d{{1,2}}[-/]\d{{1,2}}(?:[-/]\d{{2,4}})?"


def extract_facts(html: str) -> dict:
    """v78: content nunchi job-facts extract (Telugu+English regex).

    Table/FAQ fallback kosam — LLM table marchipoina kuda job posts ki
    summary table + FAQs GUARANTEE. Invent cheyyadu: content lo dorikina
    phrases ne return (dorakkapothe key undadu — honest skip).
    Keys: last_date · exam_date · vacancies · fee · age · qualification · salary.
    """
    plain = re.sub(r"\s+", " ", validator.strip_tags(html or ""))
    facts: dict = {}

    def _grab(pat: str):
        m = re.search(pat, plain, flags=re.I)
        return _text(m.group(1)) if m else ""

    last = _grab(rf"(?:చివరి తేదీ|last\s*date|ఆఖరి\s*తేదీ)[^.:\n]{{0,30}}?[:\-–]?\s*({_DATE})")
    if last:
        facts["last_date"] = last
    exam = _grab(rf"(?:పరీక్ష\s*తేదీ|exam\s*date)[^.:\n]{{0,30}}?[:\-–]?\s*({_DATE})")
    if exam:
        facts["exam_date"] = exam
    vac = _grab(r"(?:మొత్తం\s+)?(\d[\d,]*)\s*(?:ఖాళీలు|ఖాళీ|పోస్టులు|పోస్టులు|vacanc(?:y|ies)|posts?)\b")
    if not vac:
        vac = _grab(r"(?:ఖాళీలు|ఖాళీ|vacanc(?:y|ies)|posts?)\s*[:\-–]?\s*(\d[\d,]*)")
    if vac:
        facts["vacancies"] = vac
    fee = _grab(r"(?:ఫీజు|అప్లికేషన్\s*ఫీజు|application\s*fee|fee)[^.₹\d\n]{0,30}?((?:₹\s*)?\d[\d,]*\s*(?:రూపాయలు|రూ|rupees|rs\.?)?)")
    if fee and re.search(r"\d", fee):
        facts["fee"] = fee.strip()
    age = _grab(r"(?:వయస్సు|వయోపరిమితి|age\s*limit|age)\D{0,20}?(\d{1,2}\s*(?:నుండి|to|-|–)\s*\d{1,2})")
    if age:
        facts["age"] = age
    qual = _grab(r"(?:అర్హత|అర్హతలు|qualification|eligibility)[^.\n]{0,80}?"
                 r"(డిగ్రీ|డిప్లొమా|ఇంటర్|ఇంటర్మీడియట్|టెన్త్|ఐటీఐ|degree|diploma|"
                 r"inter(?:mediate)?|10th|12th|ITI|B\.?Tech|M\.?Tech|PG|post[\s-]?graduation|graduation)")
    if not qual:
        # reverse order: "డిగ్రీ ఉత్తీర్ణులై ఉండాలి" (అర్హత word lekunna)
        qual = _grab(r"(డిగ్రీ|డిప్లొమా|ఇంటర్|ఇంటర్మీడియట్|టెన్త్|ఐటీఐ|degree|"
                     r"diploma|inter(?:mediate)?|10th|12th|ITI|B\.?Tech|M\.?Tech|"
                     r"PG|post[\s-]?graduation|graduation)\s*(?:ఉత్తీర్ణ|pass)")
    if qual:
        facts["qualification"] = qual
    sal = _grab(r"(?:వేతనం|జీతం|salary|pay\s*scale)[^₹\d.\n]{0,20}?((?:₹\s*)?\d[\d,]*(?:\s*[-–]\s*(?:₹\s*)?\d[\d,]*)?)")
    if sal and re.search(r"\d", sal):
        facts["salary"] = sal.strip()
    return facts


_FACT_LABELS = (("last_date", "Last Date"),
                ("exam_date", "Exam Date"),
                ("vacancies", "Vacancies"),
                ("fee", "Application Fee"),
                ("age", "Age Limit"),
                ("qualification", "Eligibility"),
                ("salary", "Salary"))

_FAQ_TPL = (("last_date", "Last Date ఎప్పుడు?",
             "చివరి తేదీ {v}. గడువు ముగిసేలోపు దరఖాస్తు చేయండి."),
            ("vacancies", "మొత్తం Vacancies ఎన్ని?",
             "మొత్తం {v} ఖాళీలు ఉన్నాయి."),
            ("fee", "Application Fee ఎంత?",
             "ఫీజు {v}. కేటగిరీ ప్రకారం మారవచ్చు — నోటిఫికేషన్ చూడండి."),
            ("age", "Age Limit ఎంత?",
             "వయస్సు {v} మధ్య ఉండాలి. రిజర్వేషన్ ప్రకారం సడలింపు ఉంటుంది."),
            ("qualification", "Eligibility ఏమిటి?",
             "{v} ఉత్తీర్ణులై ఉండాలి. పూర్తి వివరాలు నోటిఫికేషన్‌లో చూడండి."),
            ("exam_date", "Exam Date ఎప్పుడు?",
             "పరీక్ష తేదీ {v}. హాల్ టికెట్ వివరాలు అధికారిక సైట్‌లో చూడండి."))


def fix_table(article: dict, html: str) -> str:
    """'ముఖ్య వివరాలు' table — unna facts thone (invent cheyyadu)."""
    if "<table" in html:
        return html
    rows: List[tuple] = []
    title = _text(article.get("title") or "")
    if title:
        rows.append(("Topic", _kw_title(_kw(article)) or title))
    cat = _text(article.get("category") or "")
    if cat:
        rows.append(("Category", cat))
    for key, label in (("last_date", "Last Date"),
                       ("exam_date", "Exam Date"),
                       ("vacancies", "Vacancies"),
                       ("salary", "Salary")):
        val = _text(str(article.get(key) or ""))
        if val:
            rows.append((label, val))
    src = _text(article.get("source_url") or "")
    if src:
        rows.append(("Official Source", _host_of(src)))
    if len(rows) < 3:
        # v78 fallback: content nunchi extract chesina facts (invent kaadu)
        have = {r[0] for r in rows}
        facts = extract_facts(html)
        for key, label in _FACT_LABELS:
            if label in have:
                continue
            val = _text(str(article.get(key) or "")) or facts.get(key, "")
            if val:
                rows.append((label, val))
                if len(rows) >= 8:
                    break
    if len(rows) < 3:
        return html
    body = "".join(f"<tr><th>{_html.escape(k)}</th><td>{_html.escape(v)}</td></tr>"
                   for k, v in rows)
    table = ('<h2>Quick Overview: ముఖ్య వివరాలు</h2>\n<table class="su-facts"><tbody>'
             + body + "</tbody></table>\n")
    paras = re.findall(r"<p[^>]*>.*?</p>", html, flags=re.S)
    if len(paras) >= 2:
        return html.replace(paras[1], paras[1] + "\n" + table, 1)
    return table + html


def fix_faq(article: dict, html: str) -> str:
    """FAQ section — article['faq'] nunchi (3+ ప్రశ్నలు), v78: <3 aite
    content facts nunchi Q/A build (dates/fee/vacancies — invent kaadu).

    v66 fix: puratana guard `html.count('<h3') >= 3` valla **eppudaina 3 H3
    unte** FAQ skip ayyēdi (FAQ section asalu raadēdi!). Ippudu: FAQ questions
    content lo nijam ga unnaya ani chusi, lekapote add chestundi (invent ledu —
    prashnlu/javabl̄u article['faq'] nunchi).
    """
    faq = article.get("faq") or []
    pairs = []
    for item in faq:
        if isinstance(item, dict):
            q, a = item.get("q") or item.get("question"), item.get("a") or item.get("answer")
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            q, a = item[0], item[1]
        else:
            continue
        if q and a:
            pairs.append((_text(q), _text(a)))
    if len(pairs) < 3:
        # v78 fallback: extract chesina facts nunchi Q/A (invent kaadu —
        # content lo unna dates/fee/vacancies ne prashnalu ga)
        facts = extract_facts(html)
        for key, q, tpl in _FAQ_TPL:
            if len(pairs) >= 6:
                break
            if facts.get(key):
                pairs.append((q, tpl.format(v=facts[key])))
    if len(pairs) < 3:
        return html
    plain = validator.strip_tags(html).lower()
    first_q = re.sub(r"\s+", " ", pairs[0][0].lower())[:40]
    if first_q and first_q in plain:
        return html                     # FAQ already content lo undi
    body = "".join(f"<h3>{_html.escape(q)}</h3><p>{a}</p>" for q, a in pairs[:6])
    return html + ('\n<h2>Frequently Asked Questions (FAQ)</h2>\n'
                   '<div class="su-faq">\n' + body + "</div>\n")

def fix_links(article: dict, html: str) -> str:
    """External (source) + internal (site hub) link — kotha URL invent cheyyadu."""
    out = html
    links = re.findall(r'href="(http[^"]+)"', html)
    host = _host()
    src = _text(article.get("source_url") or "")
    ext = [l for l in links if host and host not in l] if links else []
    if not ext and src.startswith("http"):
        out += ('\n<p class="su-source">అధికారిక మూలం: '
                f'<a href="{_html.escape(src)}" target="_blank" rel="noopener">'
                f'{_html.escape(_host_of(src))}</a> — ee పోస్ట్‌లోని వివరాలు అక్కడినుంచి '
                "పరిశీలించి రాశాము.</p>")
    internal = [l for l in re.findall(r'href="(http[^"]+)"', out) if host and host in l]
    if not internal and config.WP_SITE.startswith("http"):
        out += ('\n<p class="su-internal">ఇది కూడా చూడండి: '
                f'<a href="{_html.escape(config.WP_SITE.rstrip("/"))}">తాజా ఉద్యోగ '
                "నోటిఫికేషన్లు, పరీక్షా అప్‌డేట్లు</a></p>")
    return out



def _transition_ratio(html: str) -> tuple:
    """Checker (validator.rankmath_strict) laage kolichi — (sents, withtr, ratio)."""
    plain = validator.strip_tags(html)
    ss = [x for x in re.split(r"[.!?\u0964]\s", plain) if len(x.split()) >= 4]
    t = sum(1 for x in ss if any(k in x for k in validator.TRANSITION_MARKS))
    return len(ss), t, (t / len(ss) if ss else 0.0)


def fix_transitions(article: dict, html: str) -> str:
    """Preserve the writer's natural sentence flow.

    Prefixing sentences with connectives just to satisfy a readability counter
    produces robotic Telugu. The prompt/refine pass owns style; deterministic
    code must not alter sentence meaning or rhythm.
    """
    return html


def fix_paragraph_len(article: dict, html: str) -> str:
    """Long paragraphs → chunks (~60-75 words) — readability + neat look.

    v78: threshold 120→100, chunk 90→70 — "text cha peddga" complaint ki
    wall-of-text break (sentence boundary lo matrame split — meaning safe).
    """
    def _split(m):
        body = m.group(2)
        if len(body.split()) <= 100:
            return m.group(0)
        sents = re.split(r"(?<=[.!?\u0964])\s+", body)
        if len(sents) < 2:
            return m.group(0)
        chunks, cur = [], []
        for sn in sents:
            cur.append(sn)
            if len(" ".join(cur).split()) >= 70:
                chunks.append(" ".join(cur))
                cur = []
        if cur:
            chunks.append(" ".join(cur))
        if len(chunks) < 2:
            return m.group(0)
        opentag = m.group(1)
        opentag2 = opentag.replace("<p", '<p class="su-cont"', 1)
        out = []
        for i, ch in enumerate(chunks):
            out.append((opentag if i == 0 else opentag2) + ch + "</p>")
        return "\n".join(out)
    return re.sub(r"(<p[^>]*>)(.*?)</p>", _split, html, flags=re.S)

def fix_takeaways(article: dict, html: str) -> str:
    """'ముఖ్యాంశాలు' (Key Takeaways) box — unna content nunchi mattrame.

    Snippet/Discover ki + reader ki top lo summary. Kotha vishayalu **invent
    cheyyadu**: existing list items leda short sentences theesukuntundi.
    """
    if "su-takeaways" in html:
        return html
    items = [validator.strip_tags(x).strip()
             for x in re.findall(r"<li[^>]*>(.*?)</li>", html, flags=re.S)]
    items = [i for i in items if 3 <= len(i.split()) <= 14]
    if len(items) < 3:
        sents = [x.strip() for x in re.split(r"(?<=[.!?\u0964])\s+",
                                             validator.strip_tags(html))
                 if 6 <= len(x.split()) <= 22]
        items = sents[:5]
    if len(items) < 3:
        return html
    box = ('<div class="su-takeaways"><div class="su-takeaways-title">ముఖ్యాంశాలు</div><ul>'
           + "".join(f"<li>{_html.escape(i)}</li>" for i in items[:5])
           + "</ul></div>\n")
    paras = re.findall(r"<p[^>]*>.*?</p>", html, flags=re.S)
    if paras:
        return html.replace(paras[0], paras[0] + "\n" + box, 1)
    return box + html


def fix_entities(article: dict, html: str) -> str:
    """'సంబంధిత అంశాలు' — primary entity ki related entities (universe nunchi).

    Link = site internal search URL (always valid — invent cheyyadu). Idi
    hub-spoke internal linking + semantic coverage (Google topic authority).
    """
    if "su-related-entities" in html:
        return html
    kw = _kw(article)
    if not kw:
        return html
    try:
        from . import top_post
    except Exception:  # noqa: BLE001
        return html
    try:
        ent = top_post.detect_entity(kw)
        universe = top_post.keyword_universe()
    except Exception:  # noqa: BLE001
        return html
    names = []
    if ent:
        names = [e["kw"] for e in universe
                 if e.get("cluster") == ent.get("name") and e["kw"].lower() != kw.lower()][:4]
    if len(names) < 2:
        toks = set(kw.lower().split())
        names = [e["kw"] for e in universe
                 if len(toks & set(e["kw"].split())) >= 2 and e["kw"].lower() != kw.lower()][:4]
    if len(names) < 2:
        return html
    base = config.WP_SITE.rstrip("/")
    links = "".join(
        f'<li><a href="{_html.escape(base)}/?s={_html.escape(urlencode({"q": n})[2:])}">{_html.escape(n.title())}</a></li>'
        for n in names[:4])
    block = ('<div class="su-related-entities"><div class="su-related-title">సంబంధిత అంశాలు</div>'
             f'<ul>{links}</ul></div>\n')
    return html + block


# ------------------------------------------------------------------ pipeline

FIXERS = (
    ("title", None),
    ("meta", None),
    ("slug", None),
    ("lede", "html"),
    ("toc", "html"),
    ("h2_keyword", "html"),
    ("table", "html"),
    ("faq", "html"),
    ("links", "html"),
    ("density", "html"),
    ("paragraphs", "html"),
    ("transitions", "html"),
)


def apply(article: dict, rounds: int = 1) -> Dict:
    """Deterministic Rank Math fixes — idempotent. Returns {"article","before","after",
    "applied","remaining"} (article mutate avutundi + return lo kuda isthamu)."""
    before = analyze(article)["score"]
    applied: List[str] = []
    for _ in range(max(1, rounds)):
        changed = False
        if fix_title(article):
            changed = True
        if fix_meta(article):
            changed = True
        if fix_slug(article):
            changed = True
        html = article.get("content_html") or ""
        # v82: structure (h2/table/faq) MUNDU, toc TARVATA — single pass
        # lone TOC anni headings chustundi (mundu 2nd pass varaku TOC
        # skip ayyedi thin content lo; optimize() cover chesina waste).
        for name, fn in (("lede", fix_lede), ("takeaways", fix_takeaways),
                         ("entities", fix_entities),
                         ("h2_keyword", fix_h2_keyword), ("table", fix_table),
                         ("faq", fix_faq), ("toc", fix_toc),
                         ("links", fix_links),
                         ("density", fix_density), ("transitions", fix_transitions),
                         ("paragraphs", fix_paragraph_len)):
            new = fn(article, html)
            if new != html:
                applied.append(name)
                html = new
                changed = True
        article["content_html"] = html
        if not changed:
            break
    result = analyze(article)
    article["_rm100"] = {"score": result["score"], "issues": result["issues"],
                         "applied": sorted(set(applied)), "before": before}
    return {"article": article, "before": before, "after": result["score"],
            "applied": sorted(set(applied)), "remaining": result["issues"]}


def optimize(article: dict, target: int = 100, max_passes: int = 3) -> Dict:
    """Iterative: score → apply → score... target (100) varaku (max_passes).

    Returns {"article","score","before","passes":[{pass,score,applied}],"reached":bool}
    Deterministic — LLM avasaram ledu. Pipeline idi vadutundi (real-time check).
    """
    before = analyze(article)["score"]
    trace: List[dict] = []
    score = before
    for i in range(1, max(1, max_passes) + 1):
        res = apply(article)
        score = res["after"]
        trace.append({"pass": i, "score": score, "applied": res["applied"]})
        if score >= target or not res["applied"]:
            break
    article["_rm100"] = {"score": score, "before": before,
                         "passes": len(trace), "trace": trace}
    return {"article": article, "before": before, "score": score, "passes": trace,
            "reached": score >= target}


# ------------------------------------------------------------------ proof CLI

def sample_article() -> dict:
    """Deliberately imperfect draft (bot rayagane ela untundo) — proof run kosam."""
    kw = "TSPSC Group 2 Notification"
    body = []
    body.append("<p>తెలంగాణ ప్రభుత్వం గ్రూప్-2 పోస్టులకు నోటిఫికేషన్ విడుదల చేసింది. "
                "దరఖాస్తు ప్రక్రియ ఆన్‌లైన్ లోనే జరుగుతుంది.</p>")
    secs = [
        ("ముఖ్య తేదీలు", ["నోటిఫికేషన్ విడుదల", "ఆన్‌లైన్ దరఖాస్తు ప్రారంభం",
                          "చివరి తేదీ", "పరీక్ష తేదీ"]),
        ("అర్హతలు", ["ఏదైనా గుర్తింపు పొందిన విశ్వవిద్యాలయం నుంచి డిగ్రీ ఉండాలి",
                     "వయోపరిమితి నిబంధనలు ప్రభుత్వ నిబంధనల ప్రకారం",
                     "తెలంగాణ రాష్ట్ర ప్రభుత్వ నిబంధనలు వర్తిస్తాయి"]),
        ("దరఖాస్తు విధానం", ["అధికారిక వెబ్‌సైట్ తెరవండి",
                             "కొత్త registration చేసి OTP నిర్ధారించండి",
                             "వివరాలు నింపి ఫోటో, సంతకం అప్‌లోడ్ చేయండి",
                             "ఫీజు చెల్లించి acknowledgement డౌన్‌లోడ్ చేసుకోండి"]),
        ("పరీక్ష విధానం", ["ప్రిలిమ్స్ మరియు మెయిన్స్ అనే రెండు దశలు",
                           "ప్రతి దశలో ప్రతికూల మార్కింగ్ ఉంటుంది",
                           "అధికారిక నోటిఫికేషన్‌లో సిలబస్ పూర్తిగా ఉంటుంది"]),
        ("సిద్ధతకు చిట్కాలు", ["రోజూ ఒక గంట current affairs చదవండి",
                              "గత ప్రశ్నపత్రాలు నుంచి practice చేయండి",
                              "తెలుగు మరియు ఇంగ్లీషు రెండింటిలోనూ సిద్ధంగా ఉండండి"]),
    ]
    for head, items in secs:
        body.append(f"<h2>{head}</h2>")
        body.append("<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>")
        body.append("<p>ఈ విభాగంలోని వివరాలు అధికారిక నోటిఫికేషన్ ఆధారంగా రాశాము. "
                    "అభ్యర్థులు ఒక్కసారి అధికారిక పత్రం చూడటం మంచిది.</p>")
    # depth: content >= 1500 words
    filler = ("అలాగే గ్రూప్-2 పరీక్షలో తెలుగు, ఇంగ్లీషు, గణితం, రీజనింగ్, సామాన్య "
              "అభ్యసనలు ముఖ్యమైన భాగాలు. అందువల్ల ప్రతి సబ్జెక్టుకు రోజువారీ సమయం "
              "కేటాయించి క్రమం తప్పకుండా సాధన చేస్తే మంచి ఫలితం పొందవచ్చు. ")
    body.append("<p>TSPSC Group 2 Notification కోసం official syllabus ప్రకారం "
                "study plan సిద్ధం చేసుకోవాలి.</p>")
    body.append("<h2>విషయ ప్రణాళిక</h2>")
    body.append("<p>" + filler * 5 + "</p>")
    for h3 in ("సిలబస్ వివరాలు", "సమయ నిర్వహణ", "పుస్తకాల ఎంపిక", "రోజువారీ ప్రణాళిక",
               "మాక్ టెస్ట్‌లు", "పునశ్చరణ చిట్కాలు"):
        body.append(f"<h3>{h3}</h3>")
        body.append("<p>" + filler * 5 + "</p>")
    # depth guarantee (Rank Math content-length 1500+) — deterministic top-up
    while len(validator._normalize_words(validator.strip_tags("\n".join(body)))) < 1750:
        body.append("<h3>అదనపు సూచనలు</h3>")
        body.append("<p>" + filler * 5 + "</p>")
    return {
        "title": "గ్రూప్-2 నోటిఫికేషన్ విడుదల",
        "slug": "group-2",
        "focus_keyword": kw,
        "meta_description": "తెలంగాణ గ్రూప్-2 పోస్టులకు నోటిఫికేషన్ విడుదల. "
                            "దరఖాస్తు, అర్హతలు, పరీక్ష విధానం వివరాలు.",
        "category": "Government Jobs",
        "source_url": "https://www.tspsc.gov.in/",
        "content_html": "\n".join(body),
        "faq": [
            ("TSPSC Group 2 Notification ఎప్పుడు విడుదల అవుతుంది?",
             "అధికారిక వెబ్‌సైట్‌లో నోటిఫికేషన్ ప్రకటన ప్రకారం తేదీలు అప్‌డేట్ అవుతాయి. "
             "ప్రకటన వచ్చిన వెంటనే ఈ పోస్ట్‌లోని ముఖ్య తేదీల పట్టికని మేము అప్‌డేట్ చేస్తాము, "
             "అభ్యర్థులు రోజూ ఒకసారి ఈ పేజీని చూడటం మంచిది."),
            ("దరఖాస్తు ఫీజు ఎంత?",
             "కేటగిరీ ప్రకారం ఫీజు మారుతుంది — అధికారిక నోటిఫికేషన్‌లో పూర్తి వివరాలు ఉంటాయి. "
             "SC/ST/PH మరియు మహిళా అభ్యర్థులకు చాలా పరీక్షల్లో రాయితీ ఉంటుంది, కాబట్టి "
             "ఫీజు చెల్లించే ముందు నోటిఫికేషన్ చదవడం తప్పనిసరి."),
            ("పరీక్ష ఎన్ని దశల్లో ఉంటుంది?",
             "ప్రిలిమ్స్, మెయిన్స్ అనే రెండు దశల్లో పరీక్ష నిర్వహిస్తారు. ప్రిలిమ్స్‌లో "
             "వస్తుగత ప్రశ్నలు, మెయిన్స్‌లో వివరణాత్మక జవాబులు ఉంటాయి, కాబట్టి రెండు "
             "దశలకు వేరుగా ప్రణాళిక వేసుకోవడం ఉపయోగకరం."),
            ("అభ్యర్థులకు ఏమైనా సూచనలు ఉన్నాయా?",
             "సిలబస్ ప్రకారం క్రమం తప్పకుండా సాధన చేయడం ఉత్తమ మార్గం. ప్రతి వారం ఒక "
             "మాక్ టెస్ట్ రాసి, తప్పులను నోట్‌బుక్‌లో రాసుకుంటే చివరి వారాల్లో "
             "పునశ్చరణ సులభం అవుతుంది."),
        ],
    }


def _host_of(url: str) -> str:
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc or url
    except Exception:
        return url


def main() -> int:
    art = sample_article()
    res = apply(art)
    print("=" * 70)
    print("  🎯 RANK MATH 100 ENGINE — proof run (deterministic fixes only)")
    print("=" * 70)
    print(f"  score: {res['before']}/100  →  {res['after']}/100")
    print(f"  applied: {', '.join(res['applied']) or '—'}")
    print(f"  remaining (LLM refine fix cheyyali): {res['remaining'] or 'emi ledu ✔'}")
    print(f"  words: {_words(art['content_html'])} · title: {art['title']} "
          f"({len(art['title'])} ch)")
    print(f"  meta: {len(art['meta_description'])} ch · slug: {art['slug']}")
    print("-" * 70)
    for row in validator.rankmath_strict(art, art["content_html"]).get("checks", []):
        print(f"    {'✅' if row['ok'] else '❌'} {row['item']}")
    print("-" * 70)
    print("=" * 70)
    return 0 if res["after"] == 100 else 1


if __name__ == "__main__":
    raise SystemExit(main())
