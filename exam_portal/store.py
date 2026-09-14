"""v39 Exam Portal — SQLite store (schema + queries).

Design rules (mistakes lekunda):
- Every connection: WAL + busy_timeout (multi-threaded HTTP server safe).
- Sessions are resumable: token per device, answers persisted on every change.
- Results are computed ONCE per session (scored_at) — no double counting.
- Audit events for every important action (proof for the college).
"""

from __future__ import annotations

import secrets
import sqlite3
import string
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_DB = Path(__file__).resolve().parent.parent / "exam_portal.db"

EXAM_STATUSES = ("draft", "published", "live", "closed", "archived")


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().replace(microsecond=0).isoformat()


def parse_iso(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=datetime.now().astimezone().tzinfo)
    return dt


def seconds_left(end_at: Optional[str]) -> int:
    end = parse_iso(end_at)
    if not end:
        return 0
    return int((end - datetime.now(end.tzinfo)).total_seconds())


def make_code(length: int = 6) -> str:
    alphabet = string.ascii_uppercase + string.digits
    alphabet = alphabet.replace("O", "").replace("0", "").replace("I", "").replace("1", "")
    return "".join(secrets.choice(alphabet) for _ in range(length))


def make_token(length: int = 22) -> str:
    return secrets.token_urlsafe(length)


class Store:
    def __init__(self, db_path: Path | str = DEFAULT_DB):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init()

    # ------------------------------------------------------------ plumbing
    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path), timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA busy_timeout=8000")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def init(self) -> None:
        with self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS exams (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    code TEXT NOT NULL UNIQUE,
                    admin_token TEXT NOT NULL,
                    college TEXT NOT NULL DEFAULT '',
                    title TEXT NOT NULL,
                    subject TEXT NOT NULL DEFAULT '',
                    exam_date TEXT NOT NULL DEFAULT '',
                    instructions TEXT NOT NULL DEFAULT '',
                    duration_min INTEGER NOT NULL DEFAULT 30,
                    per_q_marks REAL NOT NULL DEFAULT 1,
                    negative_marks REAL NOT NULL DEFAULT 0,
                    shuffle_questions INTEGER NOT NULL DEFAULT 1,
                    shuffle_options INTEGER NOT NULL DEFAULT 1,
                    show_result TEXT NOT NULL DEFAULT 'immediate',
                    pass_marks REAL NOT NULL DEFAULT 0,
                    roster_required INTEGER NOT NULL DEFAULT 0,
                    allow_late_join INTEGER NOT NULL DEFAULT 1,
                    late_grace_min INTEGER NOT NULL DEFAULT 0,
                    auto_start_all_joined INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL DEFAULT 'draft',
                    announcement TEXT NOT NULL DEFAULT '',
                    announcement_at TEXT,
                    created_at TEXT NOT NULL,
                    published_at TEXT,
                    start_at TEXT,
                    end_at TEXT,
                    closed_at TEXT,
                    closed_reason TEXT,
                    results_published_at TEXT
                );

                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
                    order_no INTEGER NOT NULL DEFAULT 0,
                    text TEXT NOT NULL,
                    options TEXT NOT NULL,              -- JSON array (2-6 options)
                    correct_index INTEGER NOT NULL,
                    explanation TEXT NOT NULL DEFAULT '',
                    topic TEXT NOT NULL DEFAULT '',
                    difficulty TEXT NOT NULL DEFAULT '',
                    marks REAL,                         -- NULL = exam default
                    dropped INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS roster (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
                    roll TEXT NOT NULL,
                    name TEXT NOT NULL DEFAULT '',
                    UNIQUE (exam_id, roll)
                );

                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER NOT NULL REFERENCES exams(id) ON DELETE CASCADE,
                    roll TEXT NOT NULL,
                    name TEXT NOT NULL DEFAULT '',
                    token TEXT NOT NULL UNIQUE,
                    device TEXT NOT NULL DEFAULT '',
                    ip TEXT NOT NULL DEFAULT '',
                    status TEXT NOT NULL DEFAULT 'waiting',   -- waiting|active|submitted|blocked
                    joined_at TEXT NOT NULL,
                    started_at TEXT,
                    last_seen TEXT,
                    end_at TEXT,                              -- per-student deadline
                    extra_min INTEGER NOT NULL DEFAULT 0,
                    submitted_at TEXT,
                    auto_submitted INTEGER NOT NULL DEFAULT 0,
                    tab_switches INTEGER NOT NULL DEFAULT 0,
                    score REAL,
                    correct INTEGER,
                    wrong INTEGER,
                    unattempted INTEGER,
                    scored_at TEXT,
                    rank INTEGER,
                    passed INTEGER,
                    question_order TEXT NOT NULL DEFAULT '',  -- JSON array of question ids
                    option_orders TEXT NOT NULL DEFAULT '{}'   -- JSON {qid: [opt indexes]}
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_session_exam_roll
                    ON sessions(exam_id, roll);

                CREATE TABLE IF NOT EXISTS answers (
                    session_id INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
                    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
                    choice INTEGER,                          -- NULL = cleared
                    flagged INTEGER NOT NULL DEFAULT 0,
                    updated_at TEXT NOT NULL,
                    PRIMARY KEY (session_id, question_id)
                );

                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    session_id INTEGER,
                    kind TEXT NOT NULL,
                    detail TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS notifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    exam_id INTEGER,
                    channel TEXT NOT NULL,
                    message TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'queued',
                    detail TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_exam ON events(exam_id, id DESC);
                CREATE INDEX IF NOT EXISTS idx_answers_session ON answers(session_id);
                """
            )

    # ------------------------------------------------------------- exams
    def create_exam(self, **kw: Any) -> Dict:
        with self.connect() as conn:
            for _ in range(12):                       # unique short code
                code = make_code()
                if not conn.execute("SELECT 1 FROM exams WHERE code = ?",
                                    (code,)).fetchone():
                    break
            else:
                code = make_code(8)
            token = make_token()
            cur = conn.execute(
                """INSERT INTO exams (code, admin_token, college, title, subject,
                   exam_date, instructions, duration_min, per_q_marks, negative_marks,
                   shuffle_questions, shuffle_options, show_result, pass_marks,
                   roster_required, allow_late_join, late_grace_min,
                   auto_start_all_joined, status, created_at)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?, 'draft', ?)""",
                (code, token, kw.get("college", ""), kw["title"],
                 kw.get("subject", ""), kw.get("exam_date", ""),
                 kw.get("instructions", ""), int(kw.get("duration_min", 30)),
                 float(kw.get("per_q_marks", 1)), float(kw.get("negative_marks", 0)),
                 1 if kw.get("shuffle_questions", True) else 0,
                 1 if kw.get("shuffle_options", True) else 0,
                 kw.get("show_result", "immediate"), float(kw.get("pass_marks", 0)),
                 1 if kw.get("roster_required") else 0,
                 1 if kw.get("allow_late_join", True) else 0,
                 int(kw.get("late_grace_min", 0)),
                 1 if kw.get("auto_start_all_joined") else 0, now_iso()))
            exam_id = cur.lastrowid
        self.log_event(exam_id, None, "exam_created", kw.get("title", ""))
        return self.get_exam(exam_id)

    def get_exam(self, exam_id: int) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM exams WHERE id = ?", (exam_id,)).fetchone()
        return dict(row) if row else None

    def exam_by_code(self, code: str) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM exams WHERE code = ?",
                               ((code or "").strip().upper(),)).fetchone()
        return dict(row) if row else None

    def exam_by_token(self, admin_token: str) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM exams WHERE admin_token = ?",
                               (admin_token,)).fetchone()
        return dict(row) if row else None

    def list_exams(self, limit: int = 100) -> List[Dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM exams ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [dict(r) for r in rows]

    def update_exam(self, exam_id: int, **fields: Any) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self.connect() as conn:
            conn.execute(f"UPDATE exams SET {cols} WHERE id = ?",
                         (*fields.values(), exam_id))

    def due_exams(self) -> List[Dict]:
        """Live exams whose end time has passed (auto-close sweeper)."""
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM exams WHERE status = 'live' AND end_at IS NOT NULL"
            ).fetchall()
        out = []
        for r in rows:
            if seconds_left(r["end_at"]) <= 0:
                out.append(dict(r))
        return out

    # --------------------------------------------------------- questions
    def add_questions(self, exam_id: int, items: List[Dict]) -> int:
        with self.connect() as conn:
            base = conn.execute(
                "SELECT COALESCE(MAX(order_no), 0) n FROM questions WHERE exam_id = ?",
                (exam_id,)).fetchone()["n"]
            for i, q in enumerate(items, 1):
                conn.execute(
                    """INSERT INTO questions (exam_id, order_no, text, options,
                       correct_index, explanation, topic, difficulty, marks, created_at)
                       VALUES (?,?,?,?,?,?,?,?,?,?)""",
                    (exam_id, base + i, q["text"], _json(q["options"]),
                     int(q["correct_index"]), q.get("explanation", ""),
                     q.get("topic", ""), q.get("difficulty", ""),
                     q.get("marks"), now_iso()))
        return self.count_questions(exam_id)

    def questions(self, exam_id: int, include_dropped: bool = True) -> List[Dict]:
        sql = "SELECT * FROM questions WHERE exam_id = ?"
        if not include_dropped:
            sql += " AND dropped = 0"
        sql += " ORDER BY order_no, id"
        with self.connect() as conn:
            rows = conn.execute(sql, (exam_id,)).fetchall()
        out = []
        for r in rows:
            d = dict(r)
            d["options"] = _unjson(d.get("options"), [])
            out.append(d)
        return out

    def question(self, qid: int) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM questions WHERE id = ?", (qid,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["options"] = _unjson(d.get("options"), [])
        return d

    def count_questions(self, exam_id: int, only_live: bool = False) -> int:
        sql = "SELECT COUNT(*) c FROM questions WHERE exam_id = ?"
        if only_live:
            sql += " AND dropped = 0"
        with self.connect() as conn:
            return conn.execute(sql, (exam_id,)).fetchone()["c"]

    def update_question(self, qid: int, **fields: Any) -> None:
        if not fields:
            return
        if "options" in fields:
            fields["options"] = _json(fields["options"])
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self.connect() as conn:
            conn.execute(f"UPDATE questions SET {cols} WHERE id = ?",
                         (*fields.values(), qid))

    def delete_question(self, qid: int) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM questions WHERE id = ?", (qid,))

    # ------------------------------------------------------------ roster
    def set_roster(self, exam_id: int, rows: List[Dict]) -> Dict:
        """Roster replace. Returns {added, skipped_duplicates, invalid}."""
        added, dupes, invalid = 0, [], []
        seen = set()
        with self.connect() as conn:
            conn.execute("DELETE FROM roster WHERE exam_id = ?", (exam_id,))
            for r in rows:
                roll = normalize_roll(r.get("roll", ""))
                if not roll or len(roll) > 24:
                    invalid.append(r.get("roll", ""))
                    continue
                if roll in seen:
                    dupes.append(roll)
                    continue
                seen.add(roll)
                conn.execute(
                    "INSERT INTO roster (exam_id, roll, name) VALUES (?,?,?)",
                    (exam_id, roll, (r.get("name") or "").strip()[:80]))
                added += 1
        return {"added": added, "duplicates": dupes, "invalid": invalid,
                "total": added}

    def roster(self, exam_id: int) -> List[Dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT roll, name FROM roster WHERE exam_id = ? ORDER BY roll",
                (exam_id,)).fetchall()
        return [dict(r) for r in rows]

    def roster_rolls(self, exam_id: int) -> List[str]:
        return [r["roll"] for r in self.roster(exam_id)]

    # ---------------------------------------------------------- sessions
    def create_session(self, exam_id: int, roll: str, name: str = "",
                       device: str = "", ip: str = "") -> Dict:
        with self.connect() as conn:
            cur = conn.execute(
                """INSERT INTO sessions (exam_id, roll, name, token, device, ip,
                   status, joined_at, last_seen)
                   VALUES (?,?,?,?,?,?, 'waiting', ?, ?)""",
                (exam_id, roll, name, make_token(), device[:120], ip[:60],
                 now_iso(), now_iso()))
            sid = cur.lastrowid
        self.log_event(exam_id, sid, "joined", f"roll={roll}")
        return self.session(sid)

    def session(self, sid: int) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (sid,)).fetchone()
        return dict(row) if row else None

    def session_by_token(self, token: str) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE token = ?",
                               ((token or "").strip(),)).fetchone()
        return dict(row) if row else None

    def session_by_roll(self, exam_id: int, roll: str) -> Optional[Dict]:
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM sessions WHERE exam_id = ? AND roll = ?",
                               (exam_id, roll)).fetchone()
        return dict(row) if row else None

    def sessions(self, exam_id: int) -> List[Dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM sessions WHERE exam_id = ? ORDER BY roll",
                (exam_id,)).fetchall()
        return [dict(r) for r in rows]

    def update_session(self, sid: int, **fields: Any) -> None:
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self.connect() as conn:
            conn.execute(f"UPDATE sessions SET {cols} WHERE id = ?",
                         (*fields.values(), sid))

    def touch_session(self, sid: int, status: Optional[str] = None) -> None:
        fields = {"last_seen": now_iso()}
        if status:
            fields["status"] = status
        self.update_session(sid, **fields)

    def start_waiting_sessions(self, exam_id: int, end_at: str) -> int:
        """START press: waiting students ki timer + question paper ippude set."""
        with self.connect() as conn:
            cur = conn.execute(
                """UPDATE sessions SET status = 'active', started_at = ?,
                   end_at = ?, last_seen = ?
                   WHERE exam_id = ? AND status = 'waiting'""",
                (now_iso(), end_at, now_iso(), exam_id))
            return cur.rowcount

    # ----------------------------------------------------------- answers
    def save_answer(self, session_id: int, question_id: int,
                    choice: Optional[int] = None,
                    flagged: Optional[bool] = None) -> None:
        """choice=None → keep, -1 → CLEAR (unselect), >=0 → set."""
        with self.connect() as conn:
            row = conn.execute(
                "SELECT choice, flagged FROM answers WHERE session_id = ? AND question_id = ?",
                (session_id, question_id)).fetchone()
            cur_choice = row["choice"] if row else None
            cur_flag = row["flagged"] if row else 0
            # choice: None = keep, -1 = clear (unselect), >=0 = set
            if choice is None:
                new_choice = cur_choice
            elif int(choice) < 0:
                new_choice = None
            else:
                new_choice = int(choice)
            new_flag = cur_flag if flagged is None else (1 if flagged else 0)
            conn.execute(
                """INSERT INTO answers (session_id, question_id, choice, flagged,
                   updated_at) VALUES (?,?,?,?,?)
                   ON CONFLICT(session_id, question_id) DO UPDATE SET
                   choice = excluded.choice, flagged = excluded.flagged,
                   updated_at = excluded.updated_at""",
                (session_id, question_id, new_choice, new_flag, now_iso()))

    def answers(self, session_id: int) -> Dict[int, Dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT question_id, choice, flagged FROM answers WHERE session_id = ?",
                (session_id,)).fetchall()
        return {r["question_id"]: {"choice": r["choice"], "flagged": r["flagged"]}
                for r in rows}

    # ------------------------------------------------------------ events
    def log_event(self, exam_id: Optional[int], session_id: Optional[int],
                  kind: str, detail: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO events (exam_id, session_id, kind, detail, created_at)"
                " VALUES (?,?,?,?,?)",
                (exam_id, session_id, kind, detail[:500], now_iso()))

    def events(self, exam_id: int, limit: int = 200) -> List[Dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM events WHERE exam_id = ? ORDER BY id DESC LIMIT ?",
                (exam_id, limit)).fetchall()
        return [dict(r) for r in rows]

    # ----------------------------------------------------- notifications
    def log_notification(self, exam_id: Optional[int], channel: str, message: str,
                         status: str = "queued", detail: str = "") -> None:
        with self.connect() as conn:
            conn.execute(
                """INSERT INTO notifications (exam_id, channel, message, status,
                   detail, created_at) VALUES (?,?,?,?,?,?)""",
                (exam_id, channel, message[:2000], status, detail[:500], now_iso()))

    def notifications(self, exam_id: int, limit: int = 50) -> List[Dict]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT * FROM notifications WHERE exam_id = ? ORDER BY id DESC LIMIT ?",
                (exam_id, limit)).fetchall()
        return [dict(r) for r in rows]


# ---------------------------------------------------------------- helpers

def normalize_roll(roll: str) -> str:
    """Roll number normalize — '  21b01a0501 ' → '21B01A0501' (mismatch lekunda)."""
    return " ".join(str(roll or "").strip().upper().split())


def _json(value: Any) -> str:
    import json

    return json.dumps(value, ensure_ascii=False)


def _unjson(value: Any, default: Any) -> Any:
    import json

    if value in (None, ""):
        return default
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return default
