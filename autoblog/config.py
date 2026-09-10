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
# Trending listicles ("stories"): roju intha count, auto schedule lo
LISTICLES_PER_DAY = int(_get("LISTICLES_PER_DAY", "2"))
# Daily auto-refresh: prathi roju intha purana posts ni refresh chestundi
AUTO_REFRESH_PER_DAY = int(_get("AUTO_REFRESH_PER_DAY", "1"))
AUTO_REFRESH_MIN_AGE_DAYS = int(_get("AUTO_REFRESH_MIN_AGE_DAYS", "14"))
AUTO_REFRESH_HOUR = int(_get("AUTO_REFRESH_HOUR", "21"))
# In-content ad shortcode (site lo ad plugin active unte; empty = off)
# Example: AD_SHORTCODE=[quads id=1]  or  [advanced_ads_severities]
AD_SHORTCODE = _get("AD_SHORTCODE", "")
# Page ki intha ad slots (3 default; long articles ki 4-5 news standard)
MAX_AD_SLOTS = int(_get("MAX_AD_SLOTS", "3"))
# Ad space min-height tho reserve (CLS/layout-shift radu — CWV + viewability)
AD_CLS_WRAPPER = _get("AD_CLS_WRAPPER", "1") not in ("0", "false", "no")
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
DAILY_MIN = int(_get("DAILY_MIN", "10"))     # min posts per day
DAILY_MAX = int(_get("DAILY_MAX", "15"))     # max posts per day
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
        "Hall Tickets,Results,Internships,Online Education",
    ).split(",")
    if c.strip()
]

# Category priority — ee categories ki extra tickets (revenue strategy:
# Jobs high-CPC ads attract chestundi, Results high search volume).
# Format: "Govt Jobs:4,Results:3,Education News:2" (0 = boost ledu)
CATEGORY_PRIORITY = {}
for _pair in _get("CATEGORY_PRIORITY",
                  "Central Govt Jobs:4,TS Govt Jobs:4,AP Govt Jobs:3,"
                  "Results:3,Software Jobs:2,Private Jobs:2").split(","):
    if ":" in _pair:
        _k, _v = _pair.split(":", 1)
        try:
            CATEGORY_PRIORITY[_k.strip()] = int(_v.strip())
        except ValueError:
            pass

# --- Images --------------------------------------------------------------
IMAGE_ENABLED = _get("IMAGE_ENABLED", "1") not in ("0", "false", "no")
IMAGE_WIDTH = int(_get("IMAGE_WIDTH", "1200"))
IMAGE_HEIGHT = int(_get("IMAGE_HEIGHT", "675"))
SITE_BRAND = _get("SITE_BRAND", "studentup.in")

# --- Paths / network -----------------------------------------------------
STATE_PATH = Path(_get("STATE_PATH", str(BASE_DIR / "state.db")))
LOG_DIR = Path(_get("LOG_DIR", str(BASE_DIR / "log")))
OUTPUT_DIR = Path(_get("OUTPUT_DIR", str(BASE_DIR / "output")))
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
# FAQ + Article JSON-LD schema (Google rich results)
SEO_SCHEMA_ENABLED = _get("SEO_SCHEMA_ENABLED", "1") not in ("0", "false", "no")
