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

# --- Gemini AI -----------------------------------------------------------
GEMINI_API_KEY = _get("GEMINI_API_KEY", "")
GEMINI_MODEL = _get("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_FALLBACK_MODELS = [
    m.strip()
    for m in _get("GEMINI_FALLBACK_MODELS", "gemini-2.0-flash,gemini-1.5-flash").split(",")
    if m.strip()
]
GEMINI_MAX_RETRIES = int(_get("GEMINI_MAX_RETRIES", "3"))

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
        "Scholarships,Govt Jobs,Education News,Exam Updates,"
        "Admissions,Results,Internships,Study Tips",
    ).split(",")
    if c.strip()
]

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
