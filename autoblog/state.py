"""SQLite-backed state: posted articles, daily plan, WordPress term ids.

Everything lives in state.db next to the project so the bot survives
restarts and never duplicates posts.
"""

import json
import sqlite3
from datetime import date
from pathlib import Path
from typing import List, Optional


def _connect(db_path: Path) -> sqlite3.Connection:
    # v84: timeout 30 + WAL — hourly run + */5 approval-poll overlap
    # writes ("database is locked" raakudadu; readers writers ni block cheyaru).
    conn = sqlite3.connect(str(db_path), timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("PRAGMA journal_mode=WAL")
    except Exception:  # noqa: BLE001 — read-only fs etc: rollback mode tho run
        pass
    return conn


def init(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connect(db_path) as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                title_norm TEXT NOT NULL,
                slug TEXT,
                category TEXT,
                link TEXT,
                status TEXT,
                qa_score REAL,
                orig_score REAL,
                wp_id INTEGER,
                refreshed_at TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );
            CREATE UNIQUE INDEX IF NOT EXISTS idx_posts_title_norm
                ON posts(title_norm);

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS wp_terms (
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                wp_id INTEGER NOT NULL,
                PRIMARY KEY (name, type)
            );

            CREATE TABLE IF NOT EXISTS sources (
                url TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'done',
                post_id INTEGER,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );

            CREATE TABLE IF NOT EXISTS radar_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                url TEXT,
                title TEXT,
                details TEXT,
                created_at TEXT DEFAULT (datetime('now', 'localtime'))
            );
            CREATE INDEX IF NOT EXISTS idx_radar_events_created
                ON radar_events(created_at);
            """
        )
        # old DBs kosam column upgrade (idempotent)
        for col, coltype in (("qa_score", "REAL"), ("orig_score", "REAL"),
                             ("wp_id", "INTEGER"), ("refreshed_at", "TEXT")):
            try:
                conn.execute(f"ALTER TABLE posts ADD COLUMN {col} {coltype}")
            except sqlite3.OperationalError:
                pass  # already exists


def normalize_title(title: str) -> str:
    """Lowercase + keep only unicode letters/digits -> Telugu safe."""
    import re

    return re.sub(r"\s+", " ", re.sub(r"[^\w\d\u0c00-\u0c7f]+", " ", title.lower())).strip()


def title_exists(db_path: Path, title: str) -> bool:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM posts WHERE title_norm = ?", (normalize_title(title),)
        ).fetchone()
    return row is not None


def recent_titles(db_path: Path, limit: int = 60) -> List[str]:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT title FROM posts ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [r["title"] for r in rows]


def record_post(
    db_path: Path,
    title: str,
    slug: str,
    category: str,
    link: str,
    status: str,
    qa_score: float = None,
    orig_score: float = None,
    wp_id: int = None,
) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO posts (title, title_norm, slug, category, link, "
            "status, qa_score, orig_score, wp_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (title, normalize_title(title), slug, category, link, status,
             qa_score, orig_score, wp_id),
        )


def record_refresh(db_path: Path, wp_id: int) -> None:
    """Post refresh ayyaka mark (next refresh selection kosam)."""
    with _connect(db_path) as conn:
        conn.execute(
            "UPDATE posts SET refreshed_at = datetime('now', 'localtime') "
            "WHERE wp_id = ?",
            (wp_id,),
        )


def _refresh_url(url: str) -> str:
    """GSC + WP URL match: ignore query/fragment/trailing slash/case host."""
    from urllib.parse import urlsplit

    try:
        p = urlsplit((url or "").strip())
        if not p.netloc:
            return (p.path or "").rstrip("/").lower()
        return (p.netloc.lower() + (p.path.rstrip("/") or "/")).lower()
    except ValueError:
        return (url or "").strip().rstrip("/").lower()


def posts_to_refresh(db_path: Path, older_days: int = 14, limit: int = 1) -> list:
    """Auto-refresh selection with GSC opportunity priority.

    GSC Pages export ingest ayithe, matching URLs first — high impressions,
    page-1/2 edge, low CTR. GSC data lekapothe safe legacy order (never
    refreshed/oldest) continue avutundi. Never blindly selects a URL absent
    from the local publication state.
    """
    import json

    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT wp_id, title, link, refreshed_at, created_at FROM posts
            WHERE status = 'publish' AND wp_id IS NOT NULL
              AND created_at <= datetime('now', 'localtime', ?)
            """,
            (f"-{older_days} days",),
        ).fetchall()
        meta = conn.execute(
            "SELECT value FROM meta WHERE key = 'gsc:refresh-priority:v1'"
        ).fetchone()
    candidates = [dict(r) for r in rows]
    ranks = {}
    try:
        data = json.loads(meta["value"]) if meta else {}
        ranks = {str(x.get("url")): float(x.get("score", 0))
                 for x in data.get("rows", []) if x.get("url")}
        ranks = {_refresh_url(k): v for k, v in ranks.items()}
    except (ValueError, TypeError, KeyError):
        ranks = {}

    # First establish the safe legacy order: never-refreshed first, then
    # least-recently refreshed (ASC). Do not reverse this tuple — reversing
    # would pick the most recently refreshed post after every run.
    candidates.sort(key=lambda row: (
        0 if row.get("refreshed_at") is None else 1,
        row.get("refreshed_at") or row.get("created_at") or ""))
    # Stable second sort moves only URL-matched GSC opportunities to the front;
    # among equal evidence, the legacy order above remains intact.
    candidates.sort(key=lambda row: ranks.get(_refresh_url(row.get("link", "")), 0.0),
                    reverse=True)
    return [{k: row[k] for k in ("wp_id", "title", "link")} for row in candidates[:limit]]


def avg_scores(db_path: Path) -> dict:
    """Avg QA + originality (quality trend tracking)."""
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT AVG(qa_score) qa, AVG(orig_score) orig, COUNT(qa_score) n "
            "FROM posts WHERE qa_score IS NOT NULL"
        ).fetchone()
    return {"qa": round(row["qa"], 1) if row["qa"] else None,
            "orig": round(row["orig"], 1) if row["orig"] else None,
            "n": row["n"] or 0}


# --- daily plan -----------------------------------------------------------

def _meta_get(db_path: Path, key: str) -> Optional[str]:
    with _connect(db_path) as conn:
        row = conn.execute("SELECT value FROM meta WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else None


def _meta_set(db_path: Path, key: str, value: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO meta (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def meta_get(db_path: Path, key: str) -> Optional[str]:
    return _meta_get(db_path, key)


def meta_set(db_path: Path, key: str, value: str) -> None:
    _meta_set(db_path, key, value)


def meta_delete(db_path: Path, key: str) -> None:
    """Delete a transient queue/lock marker without touching publication state."""
    with _connect(db_path) as conn:
        conn.execute("DELETE FROM meta WHERE key = ?", (key,))


def meta_cleanup(db_path: Path, keep_days: int = 7) -> None:
    """Purana rojuvella keys (slots:/count:/digest:) clean — DB tidy."""
    import re as _re
    from datetime import date as _date, timedelta as _td

    cutoff = (_date.today() - _td(days=keep_days)).isoformat()
    with _connect(db_path) as conn:
        rows = conn.execute("SELECT key FROM meta").fetchall()
        stale = []
        for r in rows:
            m = _re.match(r"^(slots|count|digest):(\d{4}-\d{2}-\d{2})$", r["key"])
            if m and m.group(2) < cutoff:
                stale.append(r["key"])
        if stale:
            conn.executemany("DELETE FROM meta WHERE key = ?", [(k,) for k in stale])


def today_plan(db_path: Path, day: date, hour_start: int, hour_end: int,
               daily_min: int, daily_max: int) -> List[int]:
    """Return today's planned posting hours, generating them once per day."""
    key = f"slots:{day.isoformat()}"
    raw = _meta_get(db_path, key)
    if raw:
        return json.loads(raw)

    import random

    window = list(range(max(0, hour_start), min(23, hour_end) + 1))
    if not window:
        window = list(range(6, 23))
    n = max(1, min(len(window), random.randint(min(daily_min, daily_max), daily_max)))
    slots = sorted(random.sample(window, n))
    _meta_set(db_path, key, json.dumps(slots))
    return slots


def today_count(db_path: Path, day: date) -> int:
    raw = _meta_get(db_path, f"count:{day.isoformat()}")
    return json.loads(raw) if raw else 0


def bump_today_count(db_path: Path, day: date) -> None:
    count = today_count(db_path, day) + 1
    _meta_set(db_path, f"count:{day.isoformat()}", json.dumps(count))


# --- WordPress term id cache ----------------------------------------------

def get_term_id(db_path: Path, name: str, term_type: str) -> Optional[int]:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT wp_id FROM wp_terms WHERE name = ? AND type = ?",
            (name, term_type),
        ).fetchone()
    return row["wp_id"] if row else None


def save_term_id(db_path: Path, name: str, term_type: str, wp_id: int) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO wp_terms (name, type, wp_id) VALUES (?, ?, ?)",
            (name, term_type, wp_id),
        )


# --- sources ---------------------------------------------------------------

def source_done(db_path: Path, url: str) -> bool:
    with _connect(db_path) as conn:
        row = conn.execute(
            "SELECT 1 FROM sources WHERE url = ? AND status = 'done'", (url,)
        ).fetchone()
    return row is not None


def mark_source_queued(db_path: Path, url: str) -> None:
    """Keep a durable pending/retryable source status for radar reporting."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sources (url, status) VALUES (?, 'queued') "
            "ON CONFLICT(url) DO UPDATE SET status='queued'",
            (url,),
        )


def mark_source_retry(db_path: Path, url: str) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sources (url, status) VALUES (?, 'retry') "
            "ON CONFLICT(url) DO UPDATE SET status='retry'",
            (url,),
        )


def mark_source_done(db_path: Path, url: str, post_id: Optional[int] = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sources (url, status, post_id) VALUES (?, 'done', ?) "
            "ON CONFLICT(url) DO UPDATE SET status='done', post_id=excluded.post_id",
            (url, post_id),
        )


def record_radar_event(
    db_path: Path,
    event_type: str,
    url: str = "",
    title: str = "",
    details: str = "",
) -> None:
    """Persist an auditable discovery/pipeline outcome, not just a log line."""
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO radar_events (event_type, url, title, details) VALUES (?, ?, ?, ?)",
            (event_type, (url or "")[:2000], (title or "")[:500], (details or "")[:2000]),
        )


def recent_radar_events(db_path: Path, limit: int = 100) -> list:
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT event_type, url, title, details, created_at "
            "FROM radar_events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def source_status_counts(db_path: Path) -> dict:
    """Current queued/retry/done source inventory for operator reporting."""
    with _connect(db_path) as conn:
        rows = conn.execute(
            "SELECT status, COUNT(*) AS count FROM sources GROUP BY status"
        ).fetchall()
    return {row["status"]: int(row["count"]) for row in rows}


# --- stats ----------------------------------------------------------------

def status_summary(db_path: Path, limit: int = 10) -> dict:
    with _connect(db_path) as conn:
        last = conn.execute(
            "SELECT title, category, link, status, created_at FROM posts "
            "ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
        total = conn.execute("SELECT COUNT(*) c FROM posts").fetchone()["c"]
    return {"total": total, "last": [dict(r) for r in last]}


# ---------------- v19: published-article fingerprints (dup guard) ----------------
_FP_KEY = "***"
_FP_CAP = 120


def load_fingerprints(db_path) -> list:
    import json as _json

    raw = meta_get(db_path, _FP_KEY)
    if not raw:
        return []
    try:
        return _json.loads(raw)
    except ValueError:
        return []


def save_fingerprint(db_path, slug: str, tokens: list) -> None:
    import json as _json

    rows = load_fingerprints(db_path)
    rows = [r for r in rows if r.get("slug") != slug]
    rows.insert(0, {"slug": slug, "t": list(tokens)[:250]})
    meta_set(db_path, _FP_KEY, _json.dumps(rows[:_FP_CAP], ensure_ascii=False))
