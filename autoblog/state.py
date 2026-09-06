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
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
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


def posts_to_refresh(db_path: Path, older_days: int = 14, limit: int = 1) -> list:
    """Auto-refresh selection: purana + publish ayyina + WP id unna posts.

    Priority: never-refreshed first (oldest first), then least-recently refreshed.
    """
    with _connect(db_path) as conn:
        rows = conn.execute(
            """
            SELECT wp_id, title, link FROM posts
            WHERE status = 'publish' AND wp_id IS NOT NULL
              AND created_at <= datetime('now', 'localtime', ?)
            ORDER BY (refreshed_at IS NULL) DESC, refreshed_at ASC, created_at ASC
            LIMIT ?
            """,
            (f"-{older_days} days", limit),
        ).fetchall()
    return [dict(r) for r in rows]


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


def mark_source_done(db_path: Path, url: str, post_id: Optional[int] = None) -> None:
    with _connect(db_path) as conn:
        conn.execute(
            "INSERT INTO sources (url, status, post_id) VALUES (?, 'done', ?) "
            "ON CONFLICT(url) DO UPDATE SET status='done', post_id=excluded.post_id",
            (url, post_id),
        )


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
