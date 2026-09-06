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

# "publish" = posts go live instantly. Use "draft" while testing/reviewing.
DEFAULT_POST_STATUS = _get("DEFAULT_POST_STATUS", "publish")

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
