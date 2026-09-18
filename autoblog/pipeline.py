"""Shared publish pipeline — run.py & Telegram approval bot okari okaru vadatam.

publish_article(): SEO enhance + internal links + featured image +
Rank Math meta + WP create + state + notification.
create_from_source(url): fetch source -> Gemini 100% original rewrite -> publish.
"""

import hashlib
import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse

from . import (config, gemini_client, image_gen, notifier, post_gate, research,
               rm100, seo, sources, state, validator)
from .notifier import esc, send_telegram
from .wordpress_client import WordPressClient

log = logging.getLogger("autoblog.pipeline")


def _save_provenance(article: Dict) -> None:
    """Store source URLs and hashes, never raw/private source text."""
    urls = list(article.get("_source_urls") or [])
    texts = list(article.get("_source_texts") or [])
    if not urls:
        return
    records = []
    for index, url in enumerate(urls):
        text = texts[index] if index < len(texts) else ""
        records.append({
            "id": f"S{index + 1}",
            "url": url,
            "sha256": hashlib.sha256(text.encode("utf-8", "ignore")).hexdigest(),
            "characters": len(text),
        })
    path = config.OUTPUT_DIR / "provenance"
    path.mkdir(parents=True, exist_ok=True)
    (path / f"{article.get('slug', 'post')}.json").write_text(
        json.dumps({
            "title": article.get("title", ""),
            "created": date.today().isoformat(),
            "notebooklm_claims": article.get("_notebooklm_claims", 0),
            "sources": records,
        }, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------- auto category

CATEGORY_RULES = [
    # live-site categories (v14) — specific rules first (tie-break priority)
    # v58: విదేశీ ఉద్యోగాలు — Gulf/abroad jobs, visa, IELTS/PTE, NRI.
    # List MODATI rule (telugu "ఉద్యోగాలు" generic word Central ki vellakudadu;
    # "గల్ఫ్ ఉద్యోగాలు" → Abroad Jobs). Phrases ki 2x weight, Telugu ki 2x.
    ("Abroad Jobs", ["gulf job", "gulf jobs", "abroad job", "abroad jobs",
                     "overseas job", "overseas jobs", "work visa", "visa slot",
                     "visa appointment", "study abroad", "ielts exam", "ielts test",
                     "pte exam", "toefl", "green card", "h1b", "h-1b", "e-migrate",
                     "గల్ఫ్ ఉద్యోగాలు", "విదేశీ ఉద్యోగాలు", "విదేశీ ఉద్యోగ",
                     "దుబాయ్", "సౌదీ", "కువైట్", "ఖతార్", "ఒమన్", "బహ్రెయిన్",
                     "abroad", "overseas", "gulf", "dubai", "abu dhabi", "saudi",
                     "qatar", "kuwait", "oman", "bahrain", "uae", "sharjah",
                     "singapore", "malaysia", "japan", "south korea", "germany",
                     "canada", "australia", "uk ", "usa ", "ielts", "pte",
                     "emigrate", "nri", "passport", "oci", "visa",
                     "విదేశీ", "గల్ఫ్", "వీసా", "ఐఎల్‌టీఎస్", "ప్రవాస"]),
    ("TS Govt Jobs", ["tspsc", "telangana", "ts police", "ts genco", "transco",
                      "తెలంగాణ", "gurukul", "tgpsc"]),
    ("AP Govt Jobs", ["appsc", "andhra", "ap police", "apsrtc", "ap genco",
                      "ఆంధ్రప్రదేశ్", "ap dsc", "grama sachivalayam"]),
    ("Central Govt Jobs", ["ssc", "upsc", "rrb", "ibps", "sbi po", "sbi clerk",
                           "india post", "agniveer", "job", "vacancy",
                           "recruitment", "bharti", "notification", "posts",
                           "ఉద్యోగ", "నియామక", "ఖాళీల", "si ", "constable"]),
    ("Software Jobs", ["software", "developer", "engineer", "it jobs",
                       "coding", "full stack", "data analyst", "devops",
                       "testing"]),
    ("Private Jobs", ["tcs", "infosys", "wipro", "hcl", "cognizant",
                      "accenture", "fresher", "off campus", "private", "mnc"]),
    ("Part Time Jobs", ["part time", "part-time", "work from home",
                        "freelance", "data entry", "tutor"]),
    ("Walkin Jobs", ["walkin", "walk-in", "walk in", "direct interview"]),
    ("Outsourcing Jobs", ["outsourcing", "contract basis", "contractual",
                          "కాంట్రాక్ట్", "అవుట్‌సోర్సింగ్", "crc", "outsourced",
                          "guest faculty", "honorarium"]),
    ("Current Affairs", ["current affairs", "జాతీయ", "ప్రస్తుతాంశాలు",
                         "pib", "press release", "news today", "daily news",
                         "కరెంట్ అఫైర్స్", "studytoday news"]),
    ("Upcoming Exams", ["upcoming exam", "exam calendar", "notification coming",
                        "రానున్న పరీక్షలు", "exam schedule", "tentative schedule",
                        "recruitment calendar", "పరీక్షల క్యాలెండర్"]),
    ("Exam Tips", ["exam tips", "preparation strategy", "study plan", "revision",
                   "పరీక్షా చిట్కాలు", "సన్నద్ధత", "how to prepare", "time table",
                   "model paper", "previous papers", "mock test"]),
    ("Hall Tickets", ["admit card", "hall ticket", "హాల్ టికెట్", "call letter"]),
    ("Scholarships", ["scholarship", "fellowship", "nsp", "fee reimbursement",
                      "స్కాలర్", "రుసుము", "pragati", "saksham", "yasasvi"]),
    ("Results", ["result", "ఫలిత", "marks list", "manabadi", "grade",
                 "cutoff", "cut-off", "answer key"]),
    ("Internships", ["internship", "ఇంటర్న్"]),
    ("Online Education", ["admission", "counselling", "counseling", "web options",
                          "dost", "eamcet", "eapcet", "icet", "pgecet", "ప్రవేశ",
                          "online mba", "online degree", "course", "syllabus",
                          "preparation", "study plan", "exam date", "పరీక్ష"]),
]


# Generic job words: ivatiki thakkuva weight — "job/vacancy" unna headline ni
# "Outsourcing Jobs" / "Upcoming Exams" lanti specific category lu outrank cheyyali.
_RULE_GENERIC = {"job", "jobs", "vacancy", "posts", "notification", "recruitment",
                 "bharti", "hiring", "apply", "apply online"}


def _rule_weight(word: str) -> float:
    """Keyword specificity: phrase/Telugu 2.0 · normal word 1.0 · generic 0.5."""
    w = word.strip().lower()
    if w in _RULE_GENERIC:
        return 0.5
    if " " in w or "-" in w:
        return 2.0          # "contract basis", "hall ticket", "exam tips"
    if not w.isascii():
        return 2.0          # Telugu keyword (తెలంగాణ, ప్రస్తుతాంశాలు)
    return 1.0


def classify_category(title: str, text: str = "") -> str:
    """URL mode lo category auto-detect (Telugu + English keywords).

    v50: weighted scoring so the *specific* pillar wins over generic job words
    (e.g. "TSSPDCL outsourcing jobs" → Outsourcing Jobs, not Central Govt Jobs).
    """
    blob = f"{title} {title} {text[:600]}".lower()
    best, best_score = "Online Education", 0.0
    for cat, words in CATEGORY_RULES:
        score = sum(_rule_weight(w) for w in words if w in blob)
        if score > best_score:
            best, best_score = cat, score
    return best


# v15 tag hygiene: brand/junk tags create cheyakudadu (SEO value undadu)
JUNK_TAGS = {"studentup", "studentup.in", "studentupin", "news", "latest",
             "update", "updates", "breaking", "breaking news", "viral",
             "trending", "2026", "2025", "students", "telugu news"}


def _hygiene(article: Dict) -> Dict:
    """Chinna chinna quality fixes publish mundhe."""
    # title too long -> seo_title use cheyi (Rank Math 60-75 chars ideal)
    title = article.get("title", "")
    seo_title = article.get("seo_title", "")
    if len(title) > 85 and seo_title and 20 <= len(seo_title) <= 85:
        article["title"] = seo_title
    # tags: junk blocklist + dedupe + max 32 chars + max 8 (v15 hygiene —
    # "Studentup.in"/"News" lanti value-leni tags create avvakudadu)
    seen, tags = set(), []
    for t in article.get("tags", []):
        t = str(t).strip()[:32]
        low = t.lower()
        if not t or low in JUNK_TAGS or low in seen:
            continue
        seen.add(low)
        tags.append(t)
    if not tags:
        tags = [article.get("category", "Students"), str(date.today().year)]
    article["tags"] = tags[:8]
    # meta description fallback: quick_answer or first para nunchi
    md = (article.get("meta_description") or "").strip()
    if len(md) < 120:
        base = article.get("quick_answer") or validator.strip_tags(
            article.get("content_html", ""))
        base = " ".join(base.split())
        article["meta_description"] = (base[:155].rsplit(" ", 1)[0]) if base else md
    return article


_PG_PUBLISH_TIME_CHECKS = {
    "media", "media_size", "media_alt", "img_host", "ad_present", "house_ratio",
    "ad_after_para", "ads_txt", "internal_links", "external_auth", "sponsored_label",
    "schema_article", "schema_breadcrumb", "schema_job", "schema_org_link",
    "no_duplicate", "indexnow", "deadline_valid",
}


def _rankmath_gate(article: dict, category: str) -> dict:
    """v64: Rank Math 100 gate — DETERMINISTIC rm100 fixes + LLM refine rounds.

    Flow: rm100.apply (title/meta/slug/TOC/table/FAQ/links/density/transitions)
       → score check → RM_REFINE_ROUNDS varaku LLM refine (content depth, list items)
       → prathi refine tarvata rm100 malli (rewrite structure break cheyyakunda)
       → final score article["_rm100"] lo (Telegram + WP meta lo chupistamu)

    Mock/no-key flows skip (silently) — score inka compute avutundi.
    """
    if article.get("_mock"):
        article["_rm100"] = rm100.apply(article) if not article.get("_no_rm100") else None
        return article
    # v65: iterative deterministic passes (score → fix → score) — real-time check
    opt = rm100.optimize(article, target=int(getattr(config, "RM_TARGET", 100) or 100),
                         max_passes=2)
    res = {"after": opt["score"], "before": opt["before"],
           "applied": (opt["passes"][-1]["applied"] if opt["passes"] else [])}
    article["_rm100"] = {"score": res["after"], "before": res["before"],
                         "applied": res["applied"], "passes": len(opt["passes"])}
    article["_rm_pre"] = res["before"]
    target = int(getattr(config, "RM_TARGET", 100) or 100)
    rounds = int(getattr(config, "RM_REFINE_ROUNDS", 2) or 0)
    strict = analyze_rm(article)
    if not (config.GEMINI_API_KEY or getattr(config, "GEMINI_API_KEYS", [])):
        # key ledu → LLM refine ledu; deterministic rm100 score mattrame
        article["_rm"] = strict
        return article
    for rnd in range(1, rounds + 1):
        if strict["score"] >= target and not strict["fixes"]:
            break
        facts_before: list = []
        if getattr(config, "FACT_STRICT", True) and article.get("_source_texts"):
            facts_before = validator.fact_guard(
                article.get("content_html", ""), article["_source_texts"])
            if facts_before:
                log.warning("FACT GUARD: %d unverified data item(s): %s",
                            len(facts_before), "; ".join(str(x) for x in facts_before[:3]))
        # SUSPECT (data accuracy) fixes eppudu mundu — v66 gate hints venaka
        fixes = [f"SUSPECT data remove/verify cheyandi — {x}" for x in facts_before] + \
                list(strict["fixes"])
        # v66: pin-gate (67 checks) failures ni kuda refine hint ga ivvadam —
        # "blog rasthunnapudu inka chala check cheyali" → writing loop lo ne fix avvali.
        try:
            from . import post_gate as _pg

            early = _pg.run(article)
            hints: list = []
            for row in early["rows"]:
                if (row["ok"] or not row["fix"] or row["scored"] is False
                        or row["id"] in _PG_PUBLISH_TIME_CHECKS):
                    continue
                if row["group"] in ("CONTENT", "SEMANTIC", "SEO"):
                    hints.append(f"GATE {row['id']}: {row['fix']}")
            fixes = fixes[:10] + hints[:4]
        except Exception as exc:  # noqa: BLE001 — gate hint best-effort (publish aapadu)
            log.debug("post_gate early hints skip: %s", exc)
        if not fixes:
            break
        log.info("RankMath %d/100 (target %d) — refine round %d/%d (%d fixes)",
                 strict["score"], target, rnd, rounds, len(fixes))
        try:
            improved = gemini_client.refine_article(article, fixes[:12])
        except Exception as exc:  # noqa: BLE001 — refine best-effort, publish aapadu
            log.warning("Refine round %d failed (%s)", rnd, exc)
            break
        rm2 = validator.rankmath_strict(improved, improved.get("content_html", ""))
        facts_after = (validator.fact_guard(improved.get("content_html", ""),
                                            article["_source_texts"])
                       if facts_before else [])
        facts_fixed = bool(facts_before) and not facts_after
        if not (rm2["score"] > strict["score"] or facts_fixed):
            log.info("Refine helped ledu (%s/100 vs %s/100) — original draft keep",
                     rm2["score"], strict["score"])
            article["_fact"] = facts_before
            break
        for k in ("title", "banner_text", "meta_description", "content_html",
                  "tags", "focus_keyword", "seo_title"):
            if improved.get(k):
                article[k] = improved[k]
        article["refined"] = True
        article["_fact"] = facts_after
        log.info("Refine helped: %s -> %s/100 (facts fixed: %s)",
                 strict["score"], rm2["score"], facts_fixed)
        # v64: rewrite tarvata structure malli — TOC/title/meta/links intact
        res2 = rm100.optimize(article, target=target, max_passes=2)
        strict = analyze_rm(article)
        article["_rm100"] = {"score": strict["score"], "before": res["before"],
                             "applied": (res2["passes"][-1]["applied"]
                                         if res2.get("passes") else []),
                             "rounds": rnd}
        log.info("Round %d tarvata: %d/100", rnd, strict["score"])
    article["_rm"] = strict
    return article


def analyze_rm(article: dict) -> dict:
    return validator.rankmath_strict(article, article.get("content_html", ""))


def publish_article(article: Dict, day: Optional[date] = None) -> Dict:
    """Full publish flow for a generated article dict. Returns WP result."""
    wp = WordPressClient()
    wp.check_connection()

    is_quiz = article.get("article_type") == "quiz"
    # --- QA step 1: HTML sanitize (Gemini bad tags strip) ---
    if is_quiz:
        # v26: quiz block ni memu build chesam (escaped) — sanitize only around it
        from . import quiz_engine as _qe
        article["content_html"] = _qe.sanitize_quiz_content(article["content_html"])
        article = _hygiene(article)
    else:
        article["content_html"] = validator.sanitize_html(article["content_html"])
        article = _hygiene(article)
        # v38: TOP POST hardening (structural only — kotha facts ledu):
        # keyword meta/slug, snippet answer, FAQ extraction, density cap.
        try:
            from . import top_post as _tp
            article, _tp_report = _tp.harden(article)
        except Exception:  # noqa: BLE001 — hardening never blocks publishing
            log.exception("Top-post hardening skipped (safe)")
        # v18: Rank Math STRICT gate (actual panel checks) — low ante refine round
        article = _rankmath_gate(article, article.get("category") or "")

    category_id = wp.get_or_create_term(article["category"], "categories")
    tag_ids = [wp.get_or_create_term(t, "tags") for t in article["tags"]]

    # --- SEO: quick answer + internal links + TOC + schema ---
    recent = wp.get_recent_published(per_page=8)
    same_cat = [p for p in recent if category_id in p.get("categories", [])]
    internal = (same_cat or recent)[:4]
    # Money-page strategy: traffic posts nunchi high-CPC posts ki link priority
    from . import monetize as _mz

    internal = _mz.prioritize_money_pages(internal)[:4]
    # Internal-link fallback: kotha site lo published posts levu ->
    # category archive links istundi (Rank Math internal-link check pass)
    if len(internal) < 2:
        cat_link = wp.get_term_link(category_id, "categories")
        if cat_link:
            internal.append({"link": cat_link,
                             "title": f"{article['category']} – Latest Articles"})
        if len(internal) < 2:
            internal.append({"link": f"{config.WP_SITE}/", "title": "studentup.in – Home"})
    today_str = (day or date.today()).isoformat()
    if is_quiz:
        from . import quiz_engine as _qe
        article["_link"] = ""   # real link publish tarvata telustundi; share bar
        final_html = _qe.finalize_html(   # fallback = site home
            article, internal_links=[
                {"link": p["link"], "title": p["title"]} for p in internal],
            site_url=config.WP_SITE + "/")
    else:
        final_html = seo.enhance(
            article["content_html"],
            focus_keyword=article.get("focus_keyword", ""),
            internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
            external_links=article.get("external_links", []),
            quick_answer=article.get("quick_answer", ""),
            faq=article.get("faq", []),
            date_str=today_str,
            slug=article["slug"],
            title=article["title"],
            description=article["meta_description"],
            category=article.get("category", ""),
            source_domains=article.get("_source_domains"),
            list_items=article.get("list_items") if article.get("article_type") == "listicle" else None,
            recruitment=article.get("recruitment"),
        )
    # In-content ad hard gate: before AdSense approval no ad spaces are added,
    # even if an old shortcode remains in .env by mistake.
    if config.AD_SHORTCODE and getattr(config, "ADSENSE_APPROVED", False):
        final_html = seo.insert_ad_shortcodes(
            final_html, config.AD_SHORTCODE,
            max_ads=config.MAX_AD_SLOTS, cls_safe=config.AD_CLS_WRAPPER)
    # revenue blocks: affiliate section + channel CTA (schema mundu insert)
    from . import monetize

    if not is_quiz:
        final_html = monetize.append_blocks(final_html, article)
        # v43: AD MANAGER — owner ads (college banners, shop, services).
        # Runs AFTER monetize blocks so the bottom slot + link-adjacency
        # safety check see every real <a> that exists. No-op when inventory
        # empty/missing or AD_MANAGER_ENABLED=0 (publishing never blocked).
        try:
            from . import ad_manager as _admgr
            final_html, _ad_report = _admgr.inject(final_html, article)
            article["_ads"] = _ad_report
        except Exception:  # noqa: BLE001 — owner ads must never block publish
            log.exception("Ad manager inject skipped (safe)")
            article["_ads"] = []

    # v44: DEEP POST ENGINE — cross-source verification + visible
    # "In-Depth Analysis" section + perfect-post flags (drafts).
    if not is_quiz and getattr(config, "DEEP_POST_ENABLED", True):
        try:
            from . import deep_research as _dr

            deep_sources = article.get("_deep_sources") or []
            if len(deep_sources) >= int(getattr(config, "DEEP_MIN_SOURCES", 2)):
                _report = _dr.build_report(
                    article.get("title", ""), deep_sources,
                    notebooklm_brief=article.get("_notebooklm_brief", ""),
                    target_year=article.get("_target_year"))
                final_html = _dr.inject_deep(final_html, _report)
                article["_deep"] = _report
                _hard, _warn = _dr.gate_post(final_html, _report, live=False)
                article["_deep_flags"] = ([f"DEEP: {h}" for h in _hard] +
                                          [f"DEEP?: {w}" for w in _warn])
                log.info("v44 deep: confidence %s/100 · conflicts=%d · gaps=%d",
                         _report.get("confidence"),
                         len(_report.get("conflicts", [])),
                         len(_report.get("gaps", [])))
        except Exception:  # noqa: BLE001 — deep layer must never block publish
            log.exception("Deep post engine skipped (safe)")
            article["_deep"] = None

    # --- QA step 2: validation score + originality proof ---
    qa = validator.validate_article(article, final_html)
    article["_qa"] = qa
    article["_rm"] = validator.rankmath_strict(article, final_html)
    if article.get("_source_texts"):
        article["_orig"] = validator.originality_score(
            final_html, article["_source_texts"])
    # v38: TOP POST SCORE — measurable on-page quality (30+ weighted checks).
    # Quiz posts ki skip (interactive format different rules tho untundi).
    if not is_quiz:
        try:
            from . import top_post as _tp
            article["_top"] = _tp.score_top_post(article, html=final_html)
            log.info("Top Post Score %s/100 %s — failed: %s",
                     article["_top"]["score"], article["_top"]["grade"],
                     ", ".join(article["_top"]["failed"][:4]) or "none")
        except Exception:  # noqa: BLE001
            log.exception("Top-post scoring failed (safe)")
    log.info("QA score %s/100 (words=%d) originality=%s%% issues=%s",
             qa["score"], qa["words"], article.get("_orig", "n/a"),
             qa["issues"][:3] or "none")
    # v35: never let an unreviewed/under-validated article go straight live.
    # Drafts remain available for a human to fix; only direct publish is blocked.
    live_status = getattr(config, "DEFAULT_POST_STATUS", "draft")
    if live_status == "publish":
        reviewer = (getattr(config, "EDITORIAL_REVIEWER", "") or "").strip()
        if not reviewer:
            raise RuntimeError(
                "LIVE-PUBLISH BLOCKED: EDITORIAL_REVIEWER is empty; "
                "a named human must review the draft and official source first")
        min_qa = max(0, min(100, int(getattr(config, "PUBLISH_QA_MIN_SCORE", 80))))
        if qa["score"] < min_qa:
            raise RuntimeError(
                f"LIVE-PUBLISH BLOCKED: local QA {qa['score']}/100 < {min_qa}; "
                "save as draft, fix the listed issues, then review manually")
        if article.get("_orig") is not None:
            min_orig = float(getattr(config, "PUBLISH_ORIGINALITY_MIN", 72))
            if float(article["_orig"]) < min_orig:
                raise RuntimeError(
                    f"LIVE-PUBLISH BLOCKED: originality {article['_orig']}% < "
                    f"{min_orig:g}% — source-backed rewrite needs editorial work")
        # v38: Top Post gate — on-page quality measured, not claimed.
        if article.get("_top") is not None:
            from . import top_post as _tp

            ok_live, detail = _tp.publish_gate(article, live=True)
            if not ok_live:
                raise RuntimeError(
                    f"LIVE-PUBLISH BLOCKED: {detail}. Draft ga save chesi "
                    "fix cheyyandi (run.py --score-post <file>)")
            log.info("Top-post gate ✔ %s", detail)
        # v41: site-audit root-cause gate — junk HTML, unregistered shortcode,
        # duplicate TOC anchors, PII, stale dates, Govt/Private category mismatch,
        # empty title/excerpt, featured image — ivi live publish block chestayi.
        from . import site_audit as _sa

        ok_site, detail_site = _sa.article_gate(
            article, html=final_html, category=article.get("category", ""), live=True)
        if not ok_site:
            raise RuntimeError(
                f"LIVE-PUBLISH BLOCKED: {detail_site}")
        log.info("v41 site gate ✔ %s", detail_site)
        # v44: DEEP GATE — source conflicts / date inconsistency / stale
        # years block live publish (drafts carry the flags for review).
        from . import deep_research as _dr

        ok_deep, detail_deep = _dr.publish_gate(article, html=final_html,
                                                live=True)
        if not ok_deep:
            raise RuntimeError(
                f"LIVE-PUBLISH BLOCKED: {detail_deep}. Draft ga save chesi "
                "official source tho fix cheyyandi (run.py --deep-research)")
        log.info("v44 deep gate ✔ %s", detail_deep)
    try:
        _save_provenance(article)
    except OSError:
        log.warning("Provenance sidecar could not be saved", exc_info=True)
    try:  # v19: dup-guard memory (scaled-content protection for FUTURE posts)
        state.save_fingerprint(config.STATE_PATH, article["slug"],
                               validator.fingerprint_tokens(final_html))
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("publish_article skip: %s", exc)

    # --- featured image (alt text lo focus keyword) ---
    image_path = Path(config.OUTPUT_DIR / "images" / f"{article['slug']}.jpg")
    media_id = None
    if config.IMAGE_ENABLED:
        fk = article.get("focus_keyword") or article["banner_text"]
        year = article.get("year", date.today().year)
        if image_gen.generate_featured_image(article["banner_text"], article["category"], image_path):
            alt_text = f"{fk} – {article['category']} {year} | studentup.in"
            media_id = wp.upload_media(
                image_path,
                title=article["title"],
                alt_text=alt_text,
            )
            # v38: Top Post Score image-alt check ee alt text ni verify chestundi
            if media_id:
                article["_media_alt"] = alt_text
            # disk full avvakunda — upload ayyaka local file delete
            if media_id and not config.KEEP_IMAGES:
                image_path.unlink(missing_ok=True)

    # --- Rank Math meta (plugin active unte) ---
    meta = None
    if config.RANK_MATH_META_ENABLED:
        meta = seo.rankmath_meta(
            focus_keyword=article.get("focus_keyword", article["title"][:60]),
            description=article["meta_description"],
            seo_title=article.get("seo_title") or article["title"],
            secondary_keywords=article.get("secondary_keywords", []),
        )

    if meta and (article.get("_rm100") or {}).get("score") is not None:
        meta["rank_math_seo_score"] = str((article["_rm100"] or {}).get("score"))
    # --- v65 PIN-TO-PIN GATE: certificate + critical block (live publish mattrame) ---
    is_live = (article.get("_live") is True or
               str(getattr(config, "DEFAULT_POST_STATUS", "draft")).lower() == "publish")
    gate = ({"score": 0, "passed": 0, "total": 0, "critical_fails": [], "block": False,
             "cert_id": "mock", "rows": [], "words": 0, "rankmath": 0,
             "title": article.get("title", ""), "slug": article.get("slug", ""),
             "date": date.today().isoformat()}
            if article.get("_mock") else
            post_gate.run(article, final_html, media_id=media_id, image_path=image_path))
    article["_gate"] = gate
    try:
        paths = post_gate.write_certificate(gate) if not article.get("_mock") else {}
        article["_cert"] = paths.get("md", "")
        log.info("PIN GATE %s/100 · %s/%s checks · critical: %s", gate["score"],
                 gate["passed"], gate["total"], gate["critical_fails"] or "none")
    except Exception:  # noqa: BLE001 — certificate fail publish aapadu
        log.exception("certificate write skip (publish safe)")
    try:
        state.meta_set(config.STATE_PATH, "last_cert",
                       f"{gate['cert_id']}:{gate['score']}")
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("publish_article skip: %s", exc)
    if gate["critical_fails"] and gate["block"] and is_live and not article.get("_mock"):
        msg = (f"⛔ PIN GATE BLOCK — {article.get('title', '')[:60]}\n"
               f"critical: {', '.join(gate['critical_fails'])}\n"
               "(fix chesi malli run cheyandi · PIN_GATE_BLOCK=0 tho off)")
        log.error("PIN GATE BLOCK: %s", ", ".join(gate["critical_fails"]))
        try:
            send_telegram(msg)
        except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
            log.debug("publish_article skip: %s", exc)
        return {"error": "pin_gate", "detail": msg, "gate": gate}
    result = wp.create_post(
        title=article["title"],
        content_html=final_html,
        slug=article["slug"],
        category_id=category_id,
        tag_ids=tag_ids,
        excerpt=article["meta_description"],
        media_id=media_id,
        meta=meta,
    )
    # v63: SEO fields nijamainaa land ayyaya? (silent-fail pattadam — "mistake lekunda")
    if meta and result.get("id"):
        try:
            landed = wp.verify_meta(result["id"], ["rank_math_focus_keyword",
                                                   "rank_math_title",
                                                   "rank_math_description"])
            missing = [k for k, ok in landed.items() if not ok]
            if missing:
                log.warning("Rank Math meta land avvaledu: %s (id=%s) — theme seo-bridge "
                            "activate cheyandi (wordpress-theme/studentup/inc/seo-bridge.php)",
                            ", ".join(missing), result["id"])
                result["seo_meta_missing"] = missing
                try:
                    notifier.send_telegram(
                        "⚠️ <b>SEO meta WAR</b> — post %s lo %s land avvaledu.\n"
                        "Fix: WP theme (StudentUp) active undo chudandi (SEO bridge)."
                        % (result["id"], ", ".join(missing)))
                except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
                    log.debug("publish_article skip: %s", exc)
            else:
                log.info("Rank Math meta verified ✔ (id=%s)", result["id"])
        except Exception:
            log.exception("meta verify skip (post safe)")
    state.record_post(config.STATE_PATH, article["title"], article["slug"],
                      article["category"], result["link"], result["status"],
                      qa_score=(article.get("_qa") or {}).get("score"),
                      orig_score=article.get("_orig"), wp_id=result.get("id"))
    state.bump_today_count(config.STATE_PATH, day or date.today())
    if article.get("source_url"):
        state.mark_source_done(config.STATE_PATH, article["source_url"], result.get("id"))
    try:
        state.meta_cleanup(config.STATE_PATH)  # purana rojuvella keys tidy
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("publish_article skip: %s", exc)

    log.info("POST CREATED ✔ id=%s status=%s link=%s",
             result.get("id"), result.get("status"), result.get("link"))
    if result.get("status") == "publish":
        _after_publish_push(article, result)
    try:
        notifier.notify_new_post(article, result)
    except Exception:
        log.exception("Notification failed (post safe ga save ayyindi)")
    return result


def _after_publish_push(article: Dict, result: Dict) -> None:
    """Publish ayyaka instant traffic/indexing push (best-effort)."""
    # 1) Instant indexing: IndexNow (Bing/Yandex) + Google Indexing API (JobPosting)
    try:
        from . import indexing

        idx = indexing.submit_published(article, result.get("link", ""))
        article["_indexing"] = idx
        article["_indexnow"] = bool(idx.get("indexnow"))
        if idx.get("google"):
            log.info("Google Indexing API ✔ (JobPosting) %s", result.get("link", ""))
    except Exception as exc:  # noqa: BLE001 — indexing best-effort (publish aapadu)
        log.warning("Indexing push fail: %s", exc)
    # 2) Telegram channel auto-post (instant traffic + social signal)
    try:
        if config.TELEGRAM_CHANNEL_CHAT_ID:
            qa = article.get("_qa") or {}
            send_telegram(
                f"🆕 <b>{esc(article['title'])}</b>\n\n"
                f"{esc((article.get('meta_description') or '')[:180])}\n\n"
                f"🔗 {esc(result.get('link', ''))}\n"
                f"📊 QA {qa.get('score', '-')}/100 · ~{qa.get('reading_min', '-')} min read",
                chat_id=config.TELEGRAM_CHANNEL_CHAT_ID,
            )
    except Exception:
        log.exception("Channel auto-post failed")


def create_from_source(url: str, mock: bool = False, category: str = "",
                       notebooklm_brief: str = "",
                       target_year: int | None = None) -> Dict:
    """Vere site URL -> 100% original SEO article -> draft post.

    category empty aite auto-classify (Telugu+English keywords tho).
    """
    if not sources.is_valid_source_url(url):
        raise ValueError("URL valid kadu (http/https link ivvandi)")

    if state.source_done(config.STATE_PATH, url):
        raise ValueError("Ee URL already process chesayi — duplicate!")

    log.info("Source fetch chestunnanu: %s", url)
    src = sources.fetch_source(url)
    log.info("Source ready: %s (%d chars)", src.title[:60], len(src.text))
    if target_year is None:
        from .research_brief import target_year_from_text
        target_year = target_year_from_text(f"{src.title} {url} {notebooklm_brief[:4000]}")
    generation_year = target_year or date.today().year
    if target_year:
        log.info("Target-year mode enabled: %d — other-year claims require verification", target_year)

    # --- multi-source research: internet lo same topic articles ---
    extras, competitor_titles = [], []
    if config.RESEARCH_ENABLED and not mock:
        try:
            extras, competitor_titles = research.research_topic(
                src, config.RESEARCH_MAX_SOURCES)
            if extras:
                log.info("Research: +%d extra sources (MERGE & BEAT mode)", len(extras))
            else:
                log.info("Research: extra sources levu — primary source tho rewrite")
        except Exception:
            log.exception("Research step failed — primary source tho continue")

    if mock:
        article = {
            "title": f"{src.title[:80]} – Complete Guide {generation_year} (Original)",
            "slug": "src-" + src.title.lower().replace(" ", "-")[:30],
            "meta_description": f"{src.title[:100]} — Telugu lo complete details.",
            "tags": [str(generation_year), "Students", "Telugu", "Guide", "News"],
            "banner_text": f"Students Guide {generation_year}",
            "content_html": (
                "<p>Ee article source nunchi facts teesi original ga "
                f"rayabadda test article. Source: {src.title}</p>"
                "<h2>Key Details</h2><ul><li>Point one</li><li>Point two</li></ul>"
                "<h2>Process</h2><ol><li>Step one</li><li>Step two</li></ol>"
                "<h2>FAQ</h2><h3>Question?</h3><p>Answer</p>"
            ),
            "category": category or classify_category(src.title, src.text),
            "model": "mock",
            "focus_keyword": f"test guide {generation_year}",
            "seo_title": f"Test Guide {generation_year} – Complete Details",
            "secondary_keywords": ["test guide details", f"{generation_year} guide telugu"],
            "quick_answer": (f"Test guide {generation_year} gurinchi menu thelisi untundi — "
                             "ee quick answer featured snippet test kosam."),
            "faq": [
                {"question": "Ee guide em gurinchi?", "answer": "Test guide gurinchi."},
                {"question": "Ela apply cheyali?", "answer": "Online lo apply cheyali."},
            ],
            "external_links": [{"text": "Official Site", "url": "https://www.gov.in"}],
            "source_url": url,
            "source_title": src.title,
        }
    else:
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_article_from_source(
            src, recent, generation_year, extras=extras,
            competitor_titles=competitor_titles,
            notebooklm_brief=notebooklm_brief,
        )
        if category:
            article["category"] = category
        elif article.get("category", "Education News") == "Education News":
            article["category"] = classify_category(
                f"{src.title} {article['title']}", src.text)
        # --- originality guard: 70% kante takkuva aite OKKO regenerate ---
        source_texts = [src.text] + [e.text for e in extras]
        if notebooklm_brief:
            from . import research_brief as _rb
            source_urls = [src.url] + [e.url for e in extras]
            brief_check = _rb.validate_editor_brief(
                notebooklm_brief, source_urls, target_year=target_year)
            if not brief_check["ok"]:
                raise ValueError(
                    "NotebookLM brief validation failed: "
                    + "; ".join(brief_check["problems"]))
            article["_notebooklm_claims"] = brief_check["claims"]
            article["_notebooklm_sources"] = brief_check["source_ids"]
        article["content_html"] = validator.sanitize_html(article["content_html"])
        orig = validator.originality_score(article["content_html"], source_texts)
        overlaps = validator.verbatim_overlaps(article["content_html"], source_texts)
        if overlaps:
            log.warning("Exact source phrase overlap detected (%d runs) — regenerate", len(overlaps))
        if orig < 70.0 or overlaps:
            log.warning("Source similarity guard triggered (originality %.1f%%) — regenerate", orig)
            try:
                retry_article = gemini_client.generate_article_from_source(
                    src, recent, generation_year, extras=extras,
                    competitor_titles=competitor_titles,
                    notebooklm_brief=notebooklm_brief,
                )
                retry_article["content_html"] = validator.sanitize_html(
                    retry_article["content_html"])
                retry_orig = validator.originality_score(
                    retry_article["content_html"], source_texts)
                retry_overlaps = validator.verbatim_overlaps(
                    retry_article["content_html"], source_texts)
                # Prefer a clean rewrite over a numerically higher similarity
                # score; exact copied runs are never an acceptable tradeoff.
                better = (not retry_overlaps and bool(overlaps)) or (
                    len(retry_overlaps) < len(overlaps)
                    and retry_orig >= orig - 2.0
                ) or (not overlaps and retry_orig > orig)
                if better:
                    log.info("Regenerate better: %.1f%% -> %.1f%%; exact runs %d -> %d",
                             orig, retry_orig, len(overlaps), len(retry_overlaps))
                    article, orig, overlaps = retry_article, retry_orig, retry_overlaps
            except gemini_client.GeminiError:
                log.exception("Regenerate failed — first version e continue")
        if overlaps:
            raise RuntimeError(
                "SKIP-VERBATIM-OVERLAP: rewrite still shares exact long phrases "
                "with a source; source set needs editorial rewriting before use")
        # v18 HARD FLOOR: near-copy anipichte publish EEDU (AdSense rule #1 —
        # copied content unte site approve avakapote runtime lo ban risk)
        floor = getattr(config, "ORIG_HARD_FLOOR", 72)
        if orig < floor:
            raise RuntimeError(
                f"SKIP-NEAR-COPY: best originality {orig:.1f}% < hard floor "
                f"{floor}% — ee source ni skip chestunnam (AdSense risk). "
                f"Inko deep-rewrite source try cheyandi: {src.url}")

    # v19: near-duplicate guard — Google "scaled content abuse" policy:
    # swapped-name/only-date-changed pages site-wide signal ni charchestayi.
    # Mana published posts tho ee level dup ante SKIP (AdSense + ranking both).
    try:
        ratio, match = validator.near_duplicate(
            article["title"], article["content_html"],
            state.load_fingerprints(config.STATE_PATH),
            config.DUP_JACCARD_SKIP)
        if ratio >= config.DUP_JACCARD_SKIP:
            raise RuntimeError(
                f"SKIP-NEAR-DUP: {ratio:.0%} overlap with existing post "
                f"'{match}' — different exam/notification topic pick cheyandi")
        elif ratio >= 0.40:
            log.warning("Near-dup warning: %.0f%% overlap with '%s' (ok, but watch)",
                        ratio, match)
    except RuntimeError:
        raise
    except Exception as exc:  # noqa: BLE001 — guard never blocks on infra error
        log.warning("Dup guard skipped (%s)", exc)

    # --- QA data (notification + trust box kosam) ---
    article["_source_texts"] = [src.text] + [e.text for e in extras]
    article["_deep_sources"] = [src] + extras  # v44: full objects (tiering)
    article["_target_year"] = target_year
    article["_notebooklm_brief"] = notebooklm_brief
    article["_source_urls"] = [src.url] + [e.url for e in extras]
    article["_source_domains"] = [
        d for d in [urlparse(src.url).netloc.replace("www.", "")]
        + [urlparse(e.url).netloc.replace("www.", "") for e in extras]
    ]

    # Preserve provenance in visible official/reference links. The article is
    # still independently written; these links let a student verify a date or
    # fee instead of asking them to trust an AI summary.
    article.setdefault("external_links", [])
    known_links = {str(item.get("url", "")).rstrip("/")
                   for item in article["external_links"] if isinstance(item, dict)}
    for i, source_url in enumerate(article["_source_urls"][:6], 1):
        if source_url.rstrip("/") not in known_links:
            article["external_links"].append({
                "text": f"Source {i} — {urlparse(source_url).netloc}",
                "url": source_url,
            })

    # slug safe ga + Rank Math optimize (keyword tokens + stopwords)
    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]),
        focus_keyword=article.get("focus_keyword", ""))
    article.setdefault("focus_keyword", "")
    article.setdefault("external_links", [])
    article.setdefault("secondary_keywords", [])
    article.setdefault("quick_answer", "")
    article.setdefault("faq", [])
    article.setdefault("seo_title", "")

    return publish_article(article)


# ------------------------------------------------------------------ update flow

def update_post(post_id: int, new_source_urls=None, mock: bool = False) -> Dict:
    """Already-published/draft post ni kotha info tho IMPROVE chesi update.

    Same URL (slug preserve) — Google lo freshness boost + SEO juice safe.
    new_source_urls: user ichina kotha source URLs (optional).
    Levu ante post title meeda auto web research chestundi.
    """
    wp = WordPressClient()
    wp.check_connection()
    post = wp.get_post(post_id)
    title = (post.get("title") or {}).get("raw") or (post.get("title") or {}).get("rendered", "")
    existing_html = (post.get("content") or {}).get("raw", "") or (post.get("content") or {}).get("rendered", "")
    slug = post.get("slug", "")
    link = post.get("link", "")
    existing_text = validator.strip_tags(existing_html)
    log.info("Update mode: post %s '%s' (%d chars)", post_id, title[:50], len(existing_text))

    # --- kotha sources gather ---
    extras = []
    from .sources import SourceArticle as SA

    for u in (new_source_urls or []):
        try:
            extras.append(sources.fetch_source(u))
        except Exception as exc:
            log.warning("New source fetch fail (%s): %s", u[:60], exc)
    if config.RESEARCH_ENABLED and not mock and len(extras) < 2:
        try:
            pseudo = SA(url=link or f"{config.WP_SITE}/?p={post_id}",
                        title=title, site_name="studentup.in", text="")
            more, _unused = research.research_topic(pseudo, config.RESEARCH_MAX_SOURCES)
            extras.extend(more)
        except Exception:
            log.exception("Auto research fail — manual sources tho continue")
    if not extras and not mock:
        raise ValueError("Kotha information dorakaledu — source URL ivvandi "
                         "or konchem rojulu tarvata try cheyandi")

    # --- generate updated version ---
    if mock:
        article = {
            "title": title,
            "slug": slug or "keep",
            "meta_description": f"{title[:100]} — updated version.",
            "tags": ["2026", "Students", "Telugu", "Guide"],
            "banner_text": "Updated Guide",
            "content_html": (
                "<p>Ee updated test article — kotha info merge ayyindi.</p>"
                "<h2>Key Details</h2><ul><li>Old point</li><li>Kotha point add ayyindi</li></ul>"
                "<h2>Process</h2><ol><li>Step one</li><li>Step two</li></ol>"
                "<h2>FAQ</h2><h3>Q?</h3><p>A</p>"
            ),
            "category": "Education News",
            "model": "mock",
            "focus_keyword": "test guide 2026",
            "secondary_keywords": ["update test"],
            "quick_answer": "Updated quick answer for the test.",
            "faq": [{"question": "Q?", "answer": "A"}],
            "update_notes": "• Kotha fee details add chesayi (test)",
        }
    else:
        fk = ""
        try:
            fk = (post.get("meta") or {}).get("rank_math_focus_keyword", "") or ""
            fk = fk.split(",")[0].strip()
        except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
            log.debug("update_post skip: %s", exc)
        article = gemini_client.generate_update(
            title, existing_text, fk, extras, date.today().year,
        )

    # identity preserve — URL marakudadu
    article["title"] = title
    article["slug"] = slug
    article["content_html"] = validator.sanitize_html(article["content_html"])
    article = _hygiene(article)
    article.setdefault("update_notes", "")

    # --- SEO re-enhance (fresh TOC/quick answer/schema) ---
    recent = wp.get_recent_published(per_page=8)
    internal = [p for p in recent if p.get("id") != post_id][:4]
    final_html = seo.enhance(
        article["content_html"],
        focus_keyword=article.get("focus_keyword", ""),
        internal_links=[{"link": p["link"], "title": p["title"]} for p in internal],
        external_links=article.get("external_links", []),
        quick_answer=article.get("quick_answer", ""),
        faq=article.get("faq", []),
        # Google freshness rule: original datePublished preserve, dateModified new
        date_str=(post.get("date") or date.today().isoformat())[:10],
        date_modified=date.today().isoformat(),
        slug=slug,
        title=title,
        description=article["meta_description"],
        category=article.get("category", ""),
        source_domains=[e.site_name for e in extras],
        recruitment=article.get("recruitment"),
    )
    qa = validator.validate_article(article, final_html)
    article["_qa"] = qa
    log.info("Update QA %s/100 words=%d", qa["score"], qa["words"])

    meta = None
    if config.RANK_MATH_META_ENABLED:
        meta = seo.rankmath_meta(
            focus_keyword=article.get("focus_keyword", title[:60]),
            description=article["meta_description"],
            seo_title=article.get("seo_title") or title,
            secondary_keywords=article.get("secondary_keywords", []),
        )

    if meta and (article.get("_rm100") or {}).get("score") is not None:
        meta["rank_math_seo_score"] = str((article["_rm100"] or {}).get("score"))
    try:  # v65: update ki kuda certificate (evidence)
        gate = post_gate.run(article, final_html)
        article["_gate"] = gate
        post_gate.write_certificate(gate)
        log.info("PIN GATE (update) %s/100 · critical: %s", gate["score"],
                 gate["critical_fails"] or "none")
    except Exception:
        log.exception("update gate skip (post safe)")
    result = wp.update_post(
        post_id,
        content_html=final_html,
        title=title,  # same title enforce (URL + identity safe)
        excerpt=article["meta_description"],
        meta=meta,
    )
    log.info("POST UPDATED ✔ id=%s link=%s", post_id, result.get("link"))
    if meta:
        try:
            landed = wp.verify_meta(post_id, ["rank_math_focus_keyword",
                                              "rank_math_title",
                                              "rank_math_description"])
            missing = [k for k, ok in landed.items() if not ok]
            if missing:
                log.warning("UPDATE %s: Rank Math meta missing %s", post_id, missing)
        except Exception:
            log.exception("update meta verify skip (safe)")
    article["source_url"] = None
    try:
        state.record_refresh(config.STATE_PATH, post_id)
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("update_post skip: %s", exc)
    try:
        from . import indexnow

        indexnow.submit(result.get("link", ""))
    except Exception as exc:  # noqa: BLE001 — best-effort (silent kaadu)
        log.debug("update_post skip: %s", exc)
    try:
        notifier.notify_updated_post(article, result)
    except Exception:
        log.exception("Update notification failed (post update safe)")
    return result


# ------------------------------------------------------------------ listicles

def create_listicle(topic: str = "", mock: bool = False) -> Dict:
    """Trending listicle post (Top 10 jobs lanti 'stories')."""
    from . import topic_engine

    idea = topic or topic_engine.pick_listicle_idea(
        state.recent_titles(config.STATE_PATH, limit=30))
    log.info("Listicle idea: %s", idea)

    if mock:
        article = topic_engine.mock_listicle(idea,
                                             state.today_count(config.STATE_PATH, date.today()))
    else:
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY ledu — listicle generate avvaledu")
        recent = state.recent_titles(config.STATE_PATH, limit=30)
        article = gemini_client.generate_listicle(idea, recent, date.today().year)

    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug(article.get("slug", ""), article["title"]),
        focus_keyword=article.get("focus_keyword", "") or idea)
    for k, v in (("focus_keyword", idea), ("external_links", []),
                 ("secondary_keywords", []), ("quick_answer", ""),
                 ("faq", []), ("seo_title", ""), ("list_items", None)):
        article.setdefault(k, v)
    return publish_article(article)


# ------------------------------------------------------------------ daily quiz

def create_quiz(topic: str = "", level: int = 0, questions: int = 0,
                mock: bool = False, dry_run: bool = False) -> Dict:
    """v26: Daily Quiz post — exam-style interactive MCQ quiz.

    topic empty aithe roju automatic rotation (Mon GK ... Sun Mega Mock).
    Telugu lo topic ichhina work avutundi (Gemini bilingual prompt).
    """
    from . import quiz_engine

    now_day = date.today()
    if topic:
        # manual topic (Telugu ok) — level default 2, questions default
        topic_en = topic.strip()
        topic_te = topic.strip()
        lvl = level or 2
        n = questions or config.QUIZ_QUESTIONS
    else:
        topic_en, topic_te, lvl, n = quiz_engine.pick_daily_topic(now_day)
        if questions:
            n = questions
        if level:
            lvl = max(1, min(4, level))

    log.info("Quiz mode: '%s' (%s) — L%d, %d questions%s",
             topic_en, topic_te, lvl, n, " [MOCK]" if mock else "")
    if mock:
        quiz = quiz_engine.mock_quiz(topic_en, topic_te, lvl, n, now_day)
    else:
        if not (config.GEMINI_API_KEY or getattr(config, "GEMINI_API_KEYS", [])):
            raise ValueError("GEMINI_API_KEY ledu — quiz generate avvaledu")
        recent = state.recent_titles(config.STATE_PATH, limit=20)
        quiz = gemini_client.generate_quiz(topic_en, topic_te, lvl, n,
                                           now_day.year)
        _ = recent  # future: question-level dedupe against old quizzes

    content_html, uid = quiz_engine.build_quiz_html(quiz, topic_en, topic_te,
                                                    lvl, n, now_day)
    dstr = now_day.strftime("%d %B %Y")
    title = (f"Daily Quiz – {dstr} | {topic_en} Telugu "
             f"({quiz_engine.LEVEL_NAMES[lvl]})") if not topic else \
            f"Quiz: {topic_en} Telugu ({quiz_engine.LEVEL_NAMES[lvl]})"
    # duplicate guard: same-day/same-topic quiz already unda?
    if state.title_exists(config.STATE_PATH, title):
        raise ValueError(f"Quiz already generated today: {title}")
    focus = "daily quiz telugu" if not topic else topic_en.lower()
    article = {
        "title": title,
        "seo_title": title,
        "slug": "",  # filled below
        "category": config.QUIZ_CATEGORY,
        "tags": ["Daily Quiz", "GK Quiz Telugu", topic_en, "Current Affairs Quiz",
                 str(now_day.year)][:8],
        "meta_description": (
            f"{dstr} Daily Quiz Telugu lo — {topic_en} మీద {n} exam-style "
            f"questions, timer + negative marking + explanations. "
            f"ఆడండి, నేర్చుకోండి! (studentup.in free quiz)"),
        "focus_keyword": focus,
        "secondary_keywords": [topic_en, "quiz telugu", "gk telugu"],
        "quick_answer": (f"ఈరోజు క్విజ్: {topic_en} — {n} questions, "
                         f"Level {lvl}. Start Quiz నొక్కి వెంటనే మొదలుపెట్టండి."),
        "banner_text": f"DAILY QUIZ\n{topic_en}\nLevel {lvl} • {quiz_engine.LEVEL_NAMES[lvl]}",
        "faq": [],
        "external_links": [],
        "article_type": "quiz",
        "content_html": content_html,
        "_quiz": quiz,
        "_quiz_level": lvl,
        "_mock": mock,
    }
    from .main import _safe_slug
    article["slug"] = seo.optimize_slug(
        _safe_slug("", article["title"]), focus_keyword=focus)
    log.info("Quiz ready: %s (uid=%s, %d questions)", title, uid,
             len(quiz["questions"]))
    if dry_run:
        out_dir = config.OUTPUT_DIR / "quiz-dry"
        out_dir.mkdir(parents=True, exist_ok=True)
        final = article["content_html"]
        fp = out_dir / f"{article['slug']}.html"
        fp.write_text(
            "<!doctype html><html><head><meta charset='utf-8'>"
            f"<title>{article['title']}</title></head><body>"
            f"<h1>{article['title']}</h1>{final}</body></html>",
            encoding="utf-8")
        log.info("QUIZ DRY-RUN saved to %s (state lo record cheyaledu)", fp)
        return {"id": 0, "status": "dry-run", "link": str(fp)}
    return publish_article(article)


# ------------------------------------------------------------------ auto refresh

def auto_refresh(limit: int = 1, older_days: int = None) -> list:
    """Purana published posts ni kotha research tho refresh (daily maintenance).

    Google freshness signal — rankings long-term lo stable.
    """
    older = older_days if older_days is not None else config.AUTO_REFRESH_MIN_AGE_DAYS
    targets = state.posts_to_refresh(config.STATE_PATH, older_days=older, limit=limit)
    if not targets:
        log.info("Auto-refresh: eligible posts levu (min %d days old)", older)
        return []
    results = []
    for t in targets:
        try:
            log.info("Auto-refresh: post %s '%s'", t["wp_id"], t["title"][:50])
            results.append(update_post(t["wp_id"]))
        except Exception:
            log.exception("Auto-refresh fail: post %s", t["wp_id"])
    return results
