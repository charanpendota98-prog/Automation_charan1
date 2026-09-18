"""Configuration loader for the studentup.in auto-blogger.

Reads settings from a .env file in the project root (see .env.example)
with sensible defaults. Every value can be overridden via environment
variables too.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _load_env_file(path: Path) -> None:
    """Tiny .env parser (no external dependency needed)."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


_load_env_file(BASE_DIR / ".env")


def _get(name: str, default: str = "") -> str:
    return os.environ.get(name, default)


# --- WordPress -----------------------------------------------------------
WP_SITE = _get("WP_SITE", "https://studentup.in").rstrip("/")
WP_USERNAME = _get("WP_USERNAME", "")
WP_APP_PASSWORD = _get("WP_APP_PASSWORD", "")

# "draft" = review flow (Telegram lo approve cheyandi tarvata publish).
# "publish" = posts direct ga live avtavvi.
DEFAULT_POST_STATUS = _get("DEFAULT_POST_STATUS", "draft")

# --- Notifications -------------------------------------------------------
TELEGRAM_BOT_TOKEN = _get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = _get("TELEGRAM_CHAT_ID", "")  # empty = /start tho auto-register
# Publish ayyaka auto-post to mi Telegram CHANNEL (optional — channel chat id,
# example -1001234... ; channel lo bot admin ga add cheyandi)
TELEGRAM_CHANNEL_CHAT_ID = _get("TELEGRAM_CHANNEL_CHAT_ID", "")
TELEGRAM_API_BASE = _get("TELEGRAM_API_BASE", "https://api.telegram.org")
# IndexNow instant indexing (Bing/Yandex) — key file site root lo host cheyandi
INDEXNOW_KEY = _get("INDEXNOW_KEY", "")
# Upload ayyaka local featured image file ni delete (disk full avvakunda)
KEEP_IMAGES = _get("KEEP_IMAGES", "0") not in ("0", "false", "no")
# Scheduler watchdog: itne hours run ledu ante Telegram lo alert
WATCHDOG_HOURS = int(_get("WATCHDOG_HOURS", "26"))
# Quality-first publishing: fewer, source-backed drafts beat scaled thin pages.
# These are draft slots by default; a human still decides what becomes public.
LISTICLES_PER_DAY = int(_get("LISTICLES_PER_DAY", "1"))
# Daily auto-refresh: prathi roju intha purana posts ni refresh chestundi
AUTO_REFRESH_PER_DAY = int(_get("AUTO_REFRESH_PER_DAY", "1"))
AUTO_REFRESH_MIN_AGE_DAYS = int(_get("AUTO_REFRESH_MIN_AGE_DAYS", "30"))
AUTO_REFRESH_HOUR = int(_get("AUTO_REFRESH_HOUR", "21"))
# In-content ad shortcode (site lo ad plugin active unte; empty = off)
# Example: AD_SHORTCODE=[quads id=1]  or  [advanced_ads_severities]
AD_SHORTCODE = _get("AD_SHORTCODE", "")
# Page ki intha ad slots (3 default; long articles ki 4-5 news standard)
MAX_AD_SLOTS = int(_get("MAX_AD_SLOTS", "3"))
# Ad space min-height tho reserve (CLS/layout-shift radu — CWV + viewability)
AD_CLS_WRAPPER = _get("AD_CLS_WRAPPER", "1") not in ("0", "false", "no")
# v43 AD MANAGER — owner ads (college banners, shop, services). Inventory:
# ads/inventory.json (repo lo). Empty/missing inventory = no-op (safe).
# ADSENSE_APPROVED=1 unte personal ad cap auto 1 ki drop avtundi (AdSense safe).
AD_MANAGER_ENABLED = _get("AD_MANAGER_ENABLED", "1") not in ("0", "false", "no")
# Post lo max personal ad slots (AdSense slots ki separate — ee varam matrame)
MAX_PERSONAL_AD_SLOTS = int(_get("MAX_PERSONAL_AD_SLOTS", "2"))
# v48: category match lekapoyina okka ad slot miss avvakunda fallback (round-robin).
# AD_FALLBACK_ALWAYS=0 → peddaga strict: category match unte ne ad vestundi.
AD_FALLBACK_ALWAYS = _get("AD_FALLBACK_ALWAYS", "1") not in ("0", "false", "no")
# Inventory path override (default: repo ads/inventory.json)
ADS_INVENTORY_PATH = _get("ADS_INVENTORY_PATH", "")
# v52: house ads — StudentUp sonta promos. Sponsor ad lekapoyinappudu slot
# khali ga undakunda ivi rotation lo vastayi (SPONSORED label veyyamu).
HOUSE_AD_ENABLED = _get("HOUSE_AD_ENABLED", "1") not in ("0", "false", "no")
HOUSE_ADS_PATH = _get("HOUSE_ADS_PATH", "")
# v44 DEEP POST ENGINE — deep analyse + cross-source verification.
# ≥ DEEP_MIN_SOURCES sources unna posts ki "In-Depth Analysis" section +
# perfect gate (conflicts/stale dates live publish lo block; drafts lo flags).
DEEP_POST_ENABLED = _get("DEEP_POST_ENABLED", "1") not in ("0", "false", "no")
DEEP_MIN_SOURCES = int(_get("DEEP_MIN_SOURCES", "2"))
# 0 = deep gate off (drafts + live rendu lo ledu)
DEEP_GATE_STRICT = _get("DEEP_GATE_STRICT", "1") not in ("0", "false", "no")
# E-E-A-T: Article schema publisher logo (rich results kosam; optional)
SITE_LOGO_URL = _get("SITE_LOGO_URL", "")
# Google Discover: per-post robots lo max-image-preview:large (RM meta)
DISCOVER_META_ENABLED = _get("DISCOVER_META_ENABLED", "1") not in ("0", "false", "no")
# Google Trends daily RSS nunchi trending education topics (India)
USE_TRENDS = _get("USE_TRENDS", "1") not in ("0", "false", "no")
TRENDS_RSS = _get("TRENDS_RSS", "https://trends.google.com/trending/trendingsearches/daily/rss?geo=IN")
# Revenue: prathi post end lo Telegram channel CTA (repeat traffic engine)
TELEGRAM_CHANNEL_URL = _get("TELEGRAM_CHANNEL_URL", "")
# Affiliate links: 'label|url|keywords' okka line okati (empty = off)
# keywords optional — post title/category match aithe matrame vastundi
# Example: Free Resume Builder|https://example.com/?ref=studentup|internship,job
AFFILIATE_LINKS = _get("AFFILIATE_LINKS", "")
# High-CPC content: roju intha posts high-CPC topics meeda (30% default)
HIGH_CPC_SHARE = int(_get("HIGH_CPC_SHARE", "30"))
# CallMeBot free WhatsApp alerts (text only):
# https://api.callmebot.com/whatsapp.php?phone=+91XXXX&apikey=XXXX
WHATSAPP_CALLMEBOT_URL = _get("WHATSAPP_CALLMEBOT_URL", "")

# --- v15: District Breaking-News Radar + Channel Watch -------------------
RADAR_ENABLED = _get("RADAR_ENABLED", "1") not in ("0", "false", "no")
RADAR_HOUR = int(_get("RADAR_HOUR", "7"))               # first radar slot (IST)
RADAR_INTERVAL_HOURS = int(_get("RADAR_INTERVAL_HOURS", "6"))  # 4x/day scan
RADAR_DISTRICTS_PER_RUN = int(_get("RADAR_DISTRICTS_PER_RUN", "10"))
RADAR_SOURCES_PER_RUN = int(_get("RADAR_SOURCES_PER_RUN", "10"))
RADAR_POSTS_PER_DAY = int(_get("RADAR_POSTS_PER_DAY", "2"))
# comma-separated: https://t.me/s/yourchannel,https://site.com/feed
WATCH_SOURCES = _get("WATCH_SOURCES", "")

# --- v16: Viral stories + tips share (%) in listicle rotation -------------
VIRAL_LISTICLE_SHARE = int(_get("VIRAL_LISTICLE_SHARE", "30"))
TIPS_SHARE = int(_get("TIPS_SHARE", "15"))

# --- v17: Keyword Dominance Engine ---------------------------------------
KEYWORD_DAILY_QUEUE = int(_get("KEYWORD_DAILY_QUEUE", "4"))
# custom autocomplete seeds (comma); empty = top exams auto
KEYWORD_SUGGEST_SEEDS = _get("KEYWORD_SUGGEST_SEEDS", "")

# --- Gemini AI -----------------------------------------------------------
GEMINI_API_KEY = _get("GEMINI_API_KEY", "")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in _get("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash,gemini-1.5-flash").split(",")
    if m.strip()
]
GEMINI_MAX_RETRIES = int(_get("GEMINI_MAX_RETRIES", "3"))
# v17.1: Telugu JSON 8192 tokens lo truncate avveti — big cap + env tunable
GEMINI_MAX_OUTPUT_TOKENS = int(_get("GEMINI_MAX_OUTPUT_TOKENS", "32768"))
# v18: Multiple Gemini keys — 429 quota rotation (comma-separated okka line)
GEMINI_API_KEYS = [k.strip() for k in _get("GEMINI_API_KEYS", "").split(",")
                   if k.strip()]
GEMINI_RPD_PER_KEY = int(_get("GEMINI_RPD_PER_KEY", "1400"))
# v18: Rank Math STRICT gate (real panel checks) — target + refine rounds
RM_TARGET = int(_get("RM_TARGET", "90"))
RM_REFINE_ROUNDS = int(_get("RM_REFINE_ROUNDS", "1"))
# v18: AdSense-safe originality floor — ee % kindha post publish cheyyadu
ORIG_HARD_FLOOR = float(_get("ORIG_HARD_FLOOR", "72"))
# Mobile lo headings peddaga unte — responsive clamp CSS add (1=on)
MOBILE_HEADLINE_TUNE = _get("MOBILE_HEADLINE_TUNE", "1") not in ("0", "false", "no")

# v19 (playbook alignment): Google Jobs schema, deadline countdown, dup guard
SUPPORT_EMAIL = _get("SUPPORT_EMAIL", "studentupinformative@gmail.com")

# Real bylines (Google News + E-E-A-T require): "Name:Role;Name:Role"
AUTHOR_TEAM = []
# Never claim a human review that did not happen. Set this only after a named
# editor has actually checked the draft and its official sources.
EDITORIAL_REVIEWER = _get("EDITORIAL_REVIEWER", "").strip()
for _a in _get("AUTHOR_TEAM",
               "Charan Pendota:Founder & Editor;"
               "Anand:Content Manager;"
               "Naga Prathyu:Content Writer").split(";"):
    if ":" in _a:
        _n, _r = _a.split(":", 1)
        AUTHOR_TEAM.append((_n.strip(), _r.strip()))
    elif _a.strip():
        AUTHOR_TEAM.append((_a.strip(), "Editorial Team"))

# Authority hub pages (playbook: exam hubs = session depth + internal links)
HUB_EXAMS = [x.strip() for x in _get(
    "HUB_EXAMS",
    "SSC CGL,SSC CHSL,SSC MTS,RRB Group D,RRB ALP,TET,TS DSC,"
    "TSPSC Group 2,APPSC Group 2,ICET,TS Police Constable,SBI PO,"
    "IBPS Clerk,Scholarships").split(",") if x.strip()]
# Sponsored/featured listing CTA (AdSense disclosure REQUIRED with it)
FEATURED_CTA_HTML = _get("FEATURED_CTA_HTML", "")
JOB_SCHEMA_ENABLED = _get("JOB_SCHEMA_ENABLED", "1") not in ("0", "false", "no")
# Google "scaled content abuse" rule — mana previous post tho ee threshold
# dabbi dup ante source post SKIP avuthundi
DUP_JACCARD_SKIP = float(_get("DUP_JACCARD_SKIP", "0.62"))

# v21 FACT GUARD: article lo unna dates/numbers source lo verify ayyi unali
# (fake deadline = Google News/AdSense ki chamathaga chaduvuna paadu)
FACT_STRICT = _get("FACT_STRICT", "1") not in ("0", "false", "no")

# --- Schedule ------------------------------------------------------------
# Draft-first quality default: do not create a scaled-content firehose.
DAILY_MIN = int(_get("DAILY_MIN", "3"))      # min draft slots per day
DAILY_MAX = int(_get("DAILY_MAX", "5"))      # max draft slots per day
ACTIVE_HOUR_START = int(_get("ACTIVE_HOUR_START", "6"))   # first posting hour (local)
ACTIVE_HOUR_END = int(_get("ACTIVE_HOUR_END", "22"))      # last posting hour (local)
TIMEZONE = _get("TIMEZONE", "Asia/Kolkata")

# --- Content -------------------------------------------------------------
CATEGORIES = [
    c.strip()
    for c in _get(
        "CATEGORIES",
        # LIVE SITE categories (studentup.in wp-json lo unnavi — exact match,
        # bot duplicate categories create cheyadu, existing IDs reuse avtayi)
        "Scholarships,Central Govt Jobs,TS Govt Jobs,AP Govt Jobs,"
        "Private Jobs,Software Jobs,Part Time Jobs,Walkin Jobs,"
        "Outsourcing Jobs,Hall Tickets,Results,Internships,Online Education,"
        "Current Affairs,Exam Tips,Upcoming Exams",
    ).split(",")
    if c.strip()
]

# Category priority — ee categories ki extra tickets (revenue strategy:
# Jobs high-CPC ads attract chestundi, Results high search volume).
# Format: "Govt Jobs:4,Results:3,Education News:2" (0 = boost ledu)
CATEGORY_PRIORITY = {}
for _pair in _get("CATEGORY_PRIORITY",
                  "Central Govt Jobs:4,TS Govt Jobs:4,AP Govt Jobs:3,"
                  "Results:3,Software Jobs:2,Private Jobs:2,"
                  "Upcoming Exams:4,Outsourcing Jobs:3,Current Affairs:3,"
                  "Scholarships:3,Exam Tips:2").split(","):
    if ":" in _pair:
        _k, _v = _pair.split(":", 1)
        try:
            CATEGORY_PRIORITY[_k.strip()] = int(_v.strip())
        except ValueError:
            pass

# --- v28: safe site operations --------------------------------------------
# Only this small, reviewed allow-list can ever be installed by the bot.
# WordPress still decides whether the authenticated user has install_plugins /
# activate_plugins capability; failures are reported, never hidden.
PLUGIN_AUTO_INSTALL = _get("PLUGIN_AUTO_INSTALL", "1") not in ("0", "false", "no")
PLUGIN_AUTO_ACTIVATE = _get("PLUGIN_AUTO_ACTIVATE", "1") not in ("0", "false", "no")
# Comma-separated slugs. Keep this allow-list deliberately boring and small.
AUTO_INSTALL_PLUGINS = [
    p.strip().lower()
    for p in _get(
        "AUTO_INSTALL_PLUGINS",
        "rank-math,redirection,updraftplus,wp-super-cache",
    ).split(",")
    if p.strip()
]
# AdSense Auto Ads loader is never emitted with an empty/invalid id.
ADSENSE_ENABLED = _get("ADSENSE_ENABLED", "1") not in ("0", "false", "no")
ADSENSE_AUTO_ADS = _get("ADSENSE_AUTO_ADS", "1") not in ("0", "false", "no")
# Hard gate: before Google approves the account, neither ad slots nor the
# Auto Ads loader can be emitted even if a client id is accidentally present.
ADSENSE_APPROVED = _get("ADSENSE_APPROVED", "0") not in ("0", "false", "no")
ADSENSE_CLIENT_ID = _get("ADSENSE_CLIENT_ID", "").strip()
# Consent is a deployment responsibility, not something the bot can fake.
# Set a real Google-certified CMP/provider in production and verify its UI.
ADSENSE_CONSENT_PROVIDER = _get("ADSENSE_CONSENT_PROVIDER", "").strip()
# Optional measurement; never emitted unless an explicit GA4 id is supplied.
GA4_ENABLED = _get("GA4_ENABLED", "0") not in ("0", "false", "no")
GA4_MEASUREMENT_ID = _get("GA4_MEASUREMENT_ID", "").strip()

# --- v31: Student Internet Center service workflow ------------------------
SERVICE_CENTER_ENABLED = _get("SERVICE_CENTER_ENABLED", "1") not in ("0", "false", "no")
SERVICE_CENTER_NAME = _get("SERVICE_CENTER_NAME", "StudentUp Internet Center").strip()
SERVICE_CENTER_PHONE = _get("SERVICE_CENTER_PHONE", "").strip()
SERVICE_CENTER_WHATSAPP = _get("SERVICE_CENTER_WHATSAPP", "").strip()
SERVICE_CENTER_EMAIL = _get("SERVICE_CENTER_EMAIL", "").strip()
SERVICE_CENTER_CITY = _get("SERVICE_CENTER_CITY", "Hyderabad").strip()
SERVICE_CENTER_PAGE_SLUG = _get("SERVICE_CENTER_PAGE_SLUG", "student-services")
# Prefer a private upload portal or staff-issued one-time link. Empty means
# the public page tells callers to request a secure link instead of collecting
# raw documents in an open form.
SERVICE_CENTER_UPLOAD_URL = _get("SERVICE_CENTER_UPLOAD_URL", "").strip()
SERVICE_CENTER_DB = Path(_get("SERVICE_CENTER_DB", str(BASE_DIR / "service_center.db")))
SERVICE_RETENTION_DAYS = int(_get("SERVICE_RETENTION_DAYS", "30"))

# --- v33: Google-facing public page audit ---------------------------------
PAGESPEED_API_KEY = _get("PAGESPEED_API_KEY", "").strip()
GOOGLE_AUDIT_TIMEOUT = int(_get("GOOGLE_AUDIT_TIMEOUT", "90"))

# --- v38: Top Post Dominance Engine ---------------------------------------
# Blueprint → write → score → harden → gate. "Top post" = measured, not claimed.
TOP_POST_ENGINE = _get("TOP_POST_ENGINE", "1") not in ("0", "false", "no")
# Live publish ki minimum Top Post Score (drafts eppudu allow).
TOP_POST_MIN_SCORE = int(_get("TOP_POST_MIN_SCORE", "78"))
# Direct live publish lo score < target unte block (draft-first lo enforce kaadu).
TOP_POST_STRICT = _get("TOP_POST_STRICT", "1") not in ("0", "false", "no")
# Word target (score check) + over-optimization ceiling for keyword density.
TOP_POST_WORDS_TARGET = int(_get("TOP_POST_WORDS_TARGET", "1500"))
TOP_POST_MAX_DENSITY = float(_get("TOP_POST_MAX_DENSITY", "0.03"))
# Dominance calendar default length (days) — `--top-post-plan`
TOP_POST_PLAN_DAYS = int(_get("TOP_POST_PLAN_DAYS", "90"))

# --- v26: Daily Quiz Engine (exam-style interactive quizzes) --------------
# Roju okka quiz post automatic ga publish avutundi (QUIZ_HOUR tarvata).
QUIZ_ENABLED = _get("QUIZ_ENABLED", "1") not in ("0", "false", "no")
QUIZ_CATEGORY = _get("QUIZ_CATEGORY", "Daily Quiz")
QUIZ_HOUR = int(_get("QUIZ_HOUR", "8"))          # morning study time
QUIZ_QUESTIONS = int(_get("QUIZ_QUESTIONS", "10"))
QUIZ_SUNDAY_QUESTIONS = int(_get("QUIZ_SUNDAY_QUESTIONS", "20"))  # weekly mega mock
QUIZ_TIME_PER_Q = int(_get("QUIZ_TIME_PER_Q", "60"))   # seconds/question (exam mode)
QUIZ_NEGATIVE_MARK = _get("QUIZ_NEGATIVE_MARK", "1") not in ("0", "false", "no")
# auto = day-of-week difficulty ramp (Mon L1 ... Sun Top-Level); 1-4 = fixed
QUIZ_LEVEL = _get("QUIZ_LEVEL", "auto")
# Quiz JSON cache (server-side analytics kosam; empty = off)
QUIZ_LANGUAGE = _get("QUIZ_LANGUAGE", "te-en")   # bilingual Telugu+English

# --- Images --------------------------------------------------------------
IMAGE_ENABLED = _get("IMAGE_ENABLED", "1") not in ("0", "false", "no")
IMAGE_WIDTH = int(_get("IMAGE_WIDTH", "1200"))
IMAGE_HEIGHT = int(_get("IMAGE_HEIGHT", "675"))
SITE_BRAND = _get("SITE_BRAND", "studentup.in")

# --- Paths / network -----------------------------------------------------
STATE_PATH = Path(_get("STATE_PATH", str(BASE_DIR / "state.db")))
LOG_DIR = Path(_get("LOG_DIR", str(BASE_DIR / "log")))
OUTPUT_DIR = Path(_get("OUTPUT_DIR", str(BASE_DIR / "output")))
RESEARCH_BRIEF_DIR = Path(_get("RESEARCH_BRIEF_DIR", str(OUTPUT_DIR / "research")))
HTTP_TIMEOUT = int(_get("HTTP_TIMEOUT", "90"))

# --- Sources (URL -> original rewrite) ------------------------------------
SOURCES_QUEUE_PATH = Path(_get("SOURCES_QUEUE_PATH", str(BASE_DIR / "sources_queue.txt")))
# Multi-source research: internet lo same topic articles search chesi
# extra facts teesukuni article ni super-complete chestundi (no API key)
RESEARCH_ENABLED = _get("RESEARCH_ENABLED", "1") not in ("0", "false", "no")
RESEARCH_MAX_SOURCES = int(_get("RESEARCH_MAX_SOURCES", "3"))
SEARCH_ENDPOINT = _get("SEARCH_ENDPOINT", "https://html.duckduckgo.com/html/")
SEARCH_FALLBACK_ENDPOINT = _get(
    "SEARCH_FALLBACK_ENDPOINT", "https://lite.duckduckgo.com/lite/"
)
# Rank Math meta REST dwara set cheyadam (plugin active unte automatic)
RANK_MATH_META_ENABLED = _get("RANK_MATH_META_ENABLED", "1") not in ("0", "false", "no")
# A low score may still be saved as a draft for human editing, but direct live
# publishing is blocked. This is a local quality gate, not a Google score.
PUBLISH_QA_MIN_SCORE = int(_get("PUBLISH_QA_MIN_SCORE", "80"))
PUBLISH_ORIGINALITY_MIN = float(_get("PUBLISH_ORIGINALITY_MIN", "72"))
# Article/visible FAQ is useful for readers; FAQPage rich-result markup is not
# emitted because Google retired that search feature in 2026.
SEO_SCHEMA_ENABLED = _get("SEO_SCHEMA_ENABLED", "1") not in ("0", "false", "no")
