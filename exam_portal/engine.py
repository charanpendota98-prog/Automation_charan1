"""v39 Exam Portal — business logic (validation, start/close, scoring, exports).

Ee module HTTP nunchi veru — unit test cheyyadam easy, logic okkate chota.

Mistake-proof rules implemented here:
  * Publish BLOCKED until questions/keys/duration/roster anni clean ga unnayi.
  * START only from 'published'; waiting sessions ki appude timer + paper set.
  * CLOSE idempotent; pending students auto-submit; results ONCE compute.
  * Auto-close sweep (server-side) — admin marchipoyina exam time ki close.
  * Auto-start "andaruu join ayyaka" — roster full aithe automatic start.
  * Server-authoritative clock: end_at server lo; client clock tamper work avvadu.
  * One roll = one session (duplicate device block, resume same device lo).
  * Question drop → marks recalculate; audit event.
"""

from __future__ import annotations

import csv
import io
import json
import random
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from . import notify
from .store import Store, normalize_roll, now_iso, parse_iso, seconds_left

OPT_LETTERS = "ABCDEF"


class ExamError(Exception):
    """User-facing error: code + clear Telugu/English message."""

    def __init__(self, message: str, code: str = "error", status: int = 400):
        super().__init__(message)
        self.code = code
        self.status = status


# ===========================================================================
# Question parsing (Excel paste / JSON / CSV — colleges ki easy)
# ===========================================================================

BLOCK_RE = re.compile(
    r"^\s*(?:Q\s*)?(\d+)\s*[\.\):]\s*(?P<text>.+?)\s*$", re.IGNORECASE)
# Options = LETTERS matrame (A-F). Digits ambiguous — "2) 2 + 2 = ?" lanti
# numbered question ni option ga misinterpret cheyyakunda.
OPT_RE = re.compile(r"^\s*\(?([A-Fa-f])\)?\s*[\.\):\-]\s*(?P<text>.+?)\s*$")
ANS_RE = re.compile(
    r"^\s*(?:Ans(?:wer)?|Correct(?:\s*option)?|సరైన\s*జవాబు)\s*[:=\-]?\s*"
    r"\(?([A-Fa-f1-6])\)?\s*$", re.IGNORECASE)
EXP_RE = re.compile(
    r"^\s*(?:Exp(?:lanation)?|వివరణ)\s*[:=\-]\s*(?P<text>.+?)\s*$", re.IGNORECASE)
TOPIC_RE = re.compile(r"^\s*(?:Topic|Subject)\s*[:=\-]\s*(?P<text>.+?)\s*$", re.I)


def parse_questions(text: str) -> Tuple[List[Dict], List[str]]:
    """Flexible paste parser → (questions, errors).

    Supported:
      1) JSON array: [{"text": "...", "options": ["a","b"], "correct_index": 0}]
      2) CSV lines: question,optA,optB,optC,optD,answer(A-D/1-4),explanation
      3) Block format:
           1. Question text?
           A) option one
           B) option two
           C) option three
           D) option four
           Answer: B
           Explanation: optional
    """
    raw = (text or "").strip()
    if not raw:
        return [], ["Khali text — questions paste cheyandi"]
    if raw.startswith("[") or raw.startswith("{"):
        return _parse_json(raw)
    lines = [ln.rstrip() for ln in raw.splitlines() if ln.strip()]
    if lines and _looks_like_csv(lines[0]):
        return _parse_csv(lines)
    return _parse_blocks(lines)


def _looks_like_csv(line: str) -> bool:
    if line.count(",") < 3:
        return False
    low = line.lower()
    return "option" in low or "question" in low or "answer" in low


def _parse_json(raw: str) -> Tuple[List[Dict], List[str]]:
    try:
        data = json.loads(raw)
    except ValueError as exc:
        return [], [f"JSON parse error: {exc}"]
    items = data if isinstance(data, list) else data.get("questions", [])
    out, errors = [], []
    for i, item in enumerate(items, 1):
        if not isinstance(item, dict):
            errors.append(f"Item {i}: object kaadu")
            continue
        text = str(item.get("text") or item.get("q") or item.get("question") or "").strip()
        options = item.get("options")
        if options is None:
            # alternate keys: opt_a..opt_d
            options = [item.get(k) for k in ("a", "b", "c", "d") if item.get(k)]
        options = [str(o).strip() for o in (options or []) if str(o).strip()]
        correct = item.get("correct_index", item.get("answer", item.get("a", 0)))
        if isinstance(correct, str):
            correct = _letter_to_index(correct)
        q = _validate_item(text, options, correct, i, item.get("explanation", ""),
                           item.get("topic", ""), item.get("difficulty", ""),
                           item.get("marks"))
        if q.get("error"):
            errors.append(q["error"])
        else:
            out.append(q)
    return out, errors


def _parse_csv(lines: List[str]) -> Tuple[List[Dict], List[str]]:
    reader = csv.reader(io.StringIO("\n".join(lines)))
    rows = [r for r in reader if any(str(c).strip() for c in r)]
    out, errors = [], []
    start = 0
    if rows and _looks_like_csv(",".join(rows[0])):
        start = 1
    for i, row in enumerate(rows[start:], 1):
        row = [str(c).strip() for c in row]
        if len(row) < 3:
            errors.append(f"Line {i + start}: columns saripovu (min 3 kavali)")
            continue
        text = row[0]
        answer_cell = row[-1] if len(row) >= 6 else ""
        correct = _letter_to_index(answer_cell)
        if correct is None and len(row) >= 6:
            # last two cells: answer, explanation
            explanation = row[-1]
            correct = _letter_to_index(row[-2])
            options = [o for o in row[1:-2] if o.strip()]
        else:
            explanation = row[-1] if len(row) >= 6 else ""
            raw_opts = row[1:-2] if len(row) >= 6 else row[1:-1]
            options = [o for o in raw_opts if o.strip()]   # empty columns = padding
        q = _validate_item(text, options, correct, i, explanation, "", "", None)
        if q.get("error"):
            errors.append(q["error"])
        else:
            out.append(q)
    return out, errors


def _parse_blocks(lines: List[str]) -> Tuple[List[Dict], List[str]]:
    out, errors = [], []
    cur: Optional[Dict] = None
    stage = "text"

    def flush() -> None:
        nonlocal cur
        if not cur:
            return
        idx = len(out) + len(errors) + 1
        q = _validate_item(cur.get("text", ""), cur.get("options", []),
                           cur.get("correct"), idx, cur.get("explanation", ""),
                           cur.get("topic", ""), "", None)
        if q.get("error"):
            errors.append(q["error"])
        else:
            out.append(q)
        cur = None

    for ln in lines:
        m_ans = ANS_RE.match(ln)
        if m_ans and cur:
            cur["correct"] = _letter_to_index(m_ans.group(1))
            stage = "answer"
            continue
        m_exp = EXP_RE.match(ln)
        if m_exp and cur:
            cur["explanation"] = m_exp.group("text")
            continue
        m_topic = TOPIC_RE.match(ln)
        if m_topic and cur:
            cur["topic"] = m_topic.group("text")
            continue
        m_opt = OPT_RE.match(ln)
        if m_opt and cur is not None and stage in ("options", "text", "answer"):
            opt_idx = _letter_to_index(m_opt.group(1))
            # sanity: letter skip (A then D) allow, kaani option count merisi kaadu
            if opt_idx is not None and opt_idx <= len(cur.get("options", [])):
                cur.setdefault("options", []).append(m_opt.group("text"))
                stage = "options"
                continue
        m_q = BLOCK_RE.match(ln)
        if m_q and (cur is None or cur.get("options") or stage == "answer"):
            flush()
            cur = {"text": m_q.group("text"), "options": []}
            stage = "text"
            continue
        if cur is None:
            cur = {"text": ln.strip(), "options": []}
            stage = "text"
            continue
        # continuation line: option text wrap or question wrap
        if stage == "options" and cur.get("options"):
            cur["options"][-1] = f"{cur['options'][-1]} {ln.strip()}"
        else:
            cur["text"] = f"{cur['text']} {ln.strip()}"
    flush()
    if not out and not errors:
        errors.append("Format ardham kaledu — JSON / CSV / '1. Q ... A) ... Answer: B' "
                      "format lo paste cheyandi")
    return out, errors


def _letter_to_index(value: Any) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, int):
        return value - 1 if value >= 1 else value
    text = str(value).strip().upper()
    if not text:
        return None
    if text in OPT_LETTERS:
        return OPT_LETTERS.index(text)
    if text.isdigit():
        n = int(text)
        return n - 1 if n >= 1 else n
    return None


def _validate_item(text: str, options: List[str], correct: Optional[int], idx: int,
                   explanation: str = "", topic: str = "", difficulty: str = "",
                   marks: Any = None) -> Dict:
    """Okka question validate — mistake unte clear error (skip kaadu)."""
    text = _clean(text)
    options = [_clean(o) for o in options]
    if not text:
        return {"error": f"Q{idx}: question text ledu"}
    if len(options) < 2:
        return {"error": f"Q{idx}: minimum 2 options kavali (unnayi {len(options)})"}
    if len(options) > 6:
        return {"error": f"Q{idx}: options 6 kanna ekkuva unnayi"}
    lowered = [o.lower() for o in options]
    if len(set(lowered)) != len(lowered):
        return {"error": f"Q{idx}: duplicate options unnayi (prathi option veru ga undali)"}
    if correct is None or not (0 <= int(correct) < len(options)):
        return {"error": f"Q{idx}: correct answer set kaledu / out of range "
                         f"(Answer: A-{OPT_LETTERS[len(options) - 1]} ivvandi)"}
    return {"text": text, "options": options, "correct_index": int(correct),
            "explanation": _clean(explanation), "topic": _clean(topic),
            "difficulty": _clean(difficulty),
            "marks": float(marks) if marks not in (None, "") else None}


def _clean(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


# ===========================================================================
# Validation / publish
# ===========================================================================

def validate_exam(store: Store, exam_id: int) -> Dict:
    exam = store.get_exam(exam_id)
    if not exam:
        raise ExamError("Exam dorakaledu", "not_found", 404)
    blockers: List[str] = []
    warnings: List[str] = []
    questions = store.questions(exam_id, include_dropped=False)
    n_q = len(questions)
    if n_q == 0:
        blockers.append("Questions 0 — publish mundu questions add cheyandi")
    bad = [q for q in questions if len(q["options"]) < 2
           or not (0 <= q["correct_index"] < len(q["options"]))]
    if bad:
        blockers.append(f"{len(bad)} questions lo options/answer key problem")
    if int(exam["duration_min"]) <= 0:
        blockers.append("Duration 0 nimishalu — time set cheyandi")
    if not (exam["title"] or "").strip():
        blockers.append("Exam title ledu")
    if float(exam["per_q_marks"]) <= 0:
        blockers.append("Marks per question 0 — 1 lantidi pettandi")
    roster = store.roster_rolls(exam_id)
    if exam["roster_required"] and not roster:
        blockers.append("Roster required ON — kaani roll numbers list ledu")
    if float(exam["negative_marks"]) and n_q:
        warnings.append("Negative marking ON — students ki instructions lo cheppandi")
    if n_q and not exam["instructions"].strip():
        warnings.append("Instructions khali — students ki rules rayandi")
    if n_q and n_q < 5:
        warnings.append(f"Questions {n_q} matrame — chinna exam ki ok, verify cheyandi")
    total = total_marks(exam, questions)
    if exam["pass_marks"] and float(exam["pass_marks"]) > total:
        blockers.append(f"Pass marks ({exam['pass_marks']}) total marks ({total}) "
                        "kanna ekkuva — correct cheyandi")
    return {"ok": not blockers, "blockers": blockers, "warnings": warnings,
            "questions": n_q, "total_marks": total, "roster": len(roster),
            "exam": exam}


def total_marks(exam: Dict, questions: Optional[List[Dict]] = None) -> float:
    questions = questions if questions is not None else []
    return round(sum(float(q["marks"]) if q.get("marks") is not None
                     else float(exam["per_q_marks"]) for q in questions), 2)


def publish_exam(store: Store, exam_id: int) -> Dict:
    report = validate_exam(store, exam_id)
    if not report["ok"]:
        raise ExamError(" | ".join(report["blockers"]), "validation")
    if report["exam"]["status"] not in ("draft", "published"):
        raise ExamError(f"Exam ippudu '{report['exam']['status']}' — publish cheyyaledu",
                        "bad_state")
    store.update_exam(exam_id, status="published", published_at=now_iso())
    store.log_event(exam_id, None, "published",
                    f"{report['questions']} questions, {report['total_marks']} marks")
    exam = store.get_exam(exam_id)
    notify.broadcast_event(store, exam, "published")
    return {"exam": exam, "report": report}


def unpublish_exam(store: Store, exam_id: int) -> Dict:
    exam = store.get_exam(exam_id)
    if not exam or exam["status"] != "published":
        raise ExamError("Publish ayyina exam matrame back teesukovachu", "bad_state")
    store.update_exam(exam_id, status="draft")
    store.log_event(exam_id, None, "unpublished", "")
    return store.get_exam(exam_id)


# ===========================================================================
# START / CLOSE / EXTEND
# ===========================================================================

def start_exam(store: Store, exam_id: int, extend_minutes: int = 0,
               force_allow_late: bool = False) -> Dict:
    """Admin START — waiting students ki timer + paper ippude lock avutundi."""
    exam = store.get_exam(exam_id)
    if not exam:
        raise ExamError("Exam dorakaledu", "not_found", 404)
    if exam["status"] == "live":
        raise ExamError("Exam already START ayyindi", "already_live")
    if exam["status"] == "closed":
        raise ExamError("Exam CLOSE ayyindi — kotha exam create cheyandi", "closed")
    if exam["status"] != "published":
        raise ExamError("Mundu exam PUBLISH cheyandi (draft lo start avvadu)",
                        "not_published")
    report = validate_exam(store, exam_id)
    if not report["ok"]:
        raise ExamError(" | ".join(report["blockers"]), "validation")
    duration = int(exam["duration_min"]) + max(0, int(extend_minutes))
    start_at = datetime.now().astimezone().replace(microsecond=0)
    end_at = (start_at + timedelta(minutes=duration)).isoformat()
    store.update_exam(exam_id, status="live", start_at=start_at.isoformat(),
                      end_at=end_at,
                      allow_late_join=1 if (exam["allow_late_join"] or force_allow_late)
                      else 0)
    activated = store.start_waiting_sessions(exam_id, end_at)
    store.log_event(exam_id, None, "started",
                    f"duration={duration}m waiting={activated}")
    exam = store.get_exam(exam_id)
    notify.broadcast_event(store, exam, "started")
    return {"exam": exam, "activated": activated, "end_at": end_at,
            "duration_min": duration}


def close_exam(store: Store, exam_id: int, reason: str = "manual") -> Dict:
    """Admin CLOSE — pending students auto-submit + results compute (idempotent)."""
    exam = store.get_exam(exam_id)
    if not exam:
        raise ExamError("Exam dorakaledu", "not_found", 404)
    if exam["status"] == "closed":
        return {"exam": exam, "already": True,
                "summary": results_summary(store, exam_id)}
    if exam["status"] not in ("live", "published"):
        raise ExamError("Live/published exam matrame close cheyochu", "bad_state")
    store.update_exam(exam_id, status="closed", closed_at=now_iso(),
                      closed_reason=reason)
    auto = 0
    for s in store.sessions(exam_id):
        if s["status"] in ("waiting", "active"):
            _finalize_session(store, s, auto=True)
            auto += 1
    store.log_event(exam_id, None, "closed", f"reason={reason} auto_submitted={auto}")
    exam = store.get_exam(exam_id)
    notify.broadcast_event(store, exam, "closed")
    if exam["show_result"] == "immediate":
        publish_results(store, exam_id, notify_channels=False)
    return {"exam": store.get_exam(exam_id), "auto_submitted": auto,
            "summary": results_summary(store, exam_id)}


def extend_exam(store: Store, exam_id: int, minutes: int) -> Dict:
    """Live exam ki time add chey (server side — andaru students ki)."""
    exam = store.get_exam(exam_id)
    if not exam or exam["status"] != "live":
        raise ExamError("Live exam matrame extend cheyochu", "bad_state")
    minutes = max(1, min(int(minutes), 120))
    end = parse_iso(exam["end_at"])
    if not end:
        raise ExamError("End time ledu — mundu start cheyandi", "bad_state")
    new_end = end + timedelta(minutes=minutes)
    store.update_exam(exam_id, end_at=new_end.isoformat())
    for s in store.sessions(exam_id):
        if s["status"] == "active":
            s_end = parse_iso(s["end_at"]) or end
            store.update_session(s["id"], end_at=(s_end + timedelta(minutes=minutes)).isoformat(),
                                 extra_min=int(s["extra_min"]) + minutes)
    store.log_event(exam_id, None, "extended", f"+{minutes}m")
    exam = store.get_exam(exam_id)
    notify.broadcast_event(store, exam, "extended", extra=f"+{minutes} nimishalu")
    return {"exam": exam, "end_at": new_end.isoformat()}


def toggle_late_join(store: Store, exam_id: int, allow: bool) -> Dict:
    store.update_exam(exam_id, allow_late_join=1 if allow else 0)
    store.log_event(exam_id, None, "late_join", "on" if allow else "off")
    return store.get_exam(exam_id)


def announce(store: Store, exam_id: int, message: str,
             channels: bool = True) -> Dict:
    msg = _clean(message)[:400]
    if not msg:
        raise ExamError("Message khali", "validation")
    store.update_exam(exam_id, announcement=msg, announcement_at=now_iso())
    store.log_event(exam_id, None, "announcement", msg)
    exam = store.get_exam(exam_id)
    if channels:
        notify.broadcast_event(store, exam, "announcement", extra=msg)
    return {"exam": exam, "message": msg}


# ===========================================================================
# Student join / session
# ===========================================================================

def join_exam(store: Store, code: str, roll: str, name: str = "",
              device: str = "", ip: str = "", token: str = "") -> Dict:
    """Student join (no password — roll number matrame).

    Same device token unte → resume (answers eppudu poyipovu).
    Veru device nunchi same roll → block (duplicate attempt avoid).
    """
    roll = normalize_roll(roll)
    if not roll:
        raise ExamError("Roll number ivvandi", "roll_required")
    exam = store.exam_by_code(code)
    if not exam:
        raise ExamError("Exam code tappu — college ichina link/code check cheyandi",
                        "not_found", 404)
    if exam["status"] == "draft":
        raise ExamError("Exam inka publish kaledu — college intiki wait cheyandi",
                        "not_published")
    if exam["status"] == "closed":
        existing_closed = store.session_by_roll(exam["id"], roll)
        if existing_closed and token and existing_closed["token"] == token:
            return _session_payload(store, existing_closed)
        raise ExamError("Exam CLOSE ayyindi — results kosam college ni adagandi",
                        "closed")
    roster = store.roster_rolls(exam["id"])
    if exam["roster_required"] and roll not in roster:
        raise ExamError("Ee roll number exam list lo ledu — college staff ni "
                        "confirm cheyandi", "not_in_roster")

    existing = store.session_by_roll(exam["id"], roll)
    if existing:
        if token and token == existing["token"]:
            store.touch_session(existing["id"])
            return _session_payload(store, store.session(existing["id"]))
        store.log_event(exam["id"], existing["id"], "duplicate_device_blocked",
                        f"roll={roll} ip={ip}")
        raise ExamError("Ee roll number veru device lo already join ayyindi. "
                        "Mundu join ayyina device/phone ne vadandi — leda college "
                        "staff ni adagandi", "duplicate_device", 409)

    if exam["status"] == "live":
        if not exam["allow_late_join"]:
            raise ExamError("Exam start ayyindi — late join off lo undi. "
                            "College staff ni adagandi", "late_join_off")
        if seconds_left(exam["end_at"]) <= 0:
            raise ExamError("Exam time over — close avutundi", "time_over")

    session = store.create_session(exam["id"], roll, name, device=device, ip=ip)
    store.update_session(session["id"], roll=roll, name=_clean(name)[:80])
    if exam["status"] == "live":
        # Late join — paper ippude lock, kaani timer ANDARIKI same (fair):
        # hard end time = exam end; grace unte dani varaku matrame extra.
        grace = _grace_end(exam)
        session = store.session(session["id"])
        store.update_session(session["id"], status="active",
                             started_at=now_iso(), end_at=grace)
        store.log_event(exam["id"], session["id"], "late_join",
                        f"roll={roll} end={grace}")
    return _session_payload(store, store.session(session["id"]))


def _grace_end(exam: Dict) -> str:
    """Late joiner ki end time — exam end date; grace unte dani varaku max."""
    exam_end = exam["end_at"]
    grace = int(exam["late_grace_min"] or 0)
    if grace > 0:
        candidate = (datetime.now().astimezone() + timedelta(minutes=grace)).isoformat()
        if exam_end and parse_iso(candidate) and parse_iso(exam_end):
            if parse_iso(candidate) < parse_iso(exam_end):
                return exam_end
        return candidate
    return exam_end


def _prepare_paper(store: Store, session: Dict, exam: Dict) -> None:
    """Question order + per-student option shuffle (once — resume lo same)."""
    if session["question_order"]:
        return
    questions = store.questions(exam["id"], include_dropped=False)
    ids = [q["id"] for q in questions]
    if exam["shuffle_questions"]:
        rng = random.Random(f"q{session['id']}{exam['code']}")
        rng.shuffle(ids)
    option_orders: Dict[str, List[int]] = {}
    if exam["shuffle_options"]:
        for q in questions:
            order = list(range(len(q["options"])))
            rng = random.Random(f"o{session['id']}{q['id']}")
            rng.shuffle(order)
            option_orders[str(q["id"])] = order
    store.update_session(session["id"], question_order=json.dumps(ids),
                         option_orders=json.dumps(option_orders))


def _session_payload(store: Store, session: Dict) -> Dict:
    exam = store.get_exam(session["exam_id"])
    _prepare_paper(store, session, exam)
    session = store.session(session["id"])
    payload = {
        "token": session["token"],
        "session_id": session["id"],
        "roll": session["roll"],
        "name": session["name"],
        "status": session["status"],
        "exam": public_exam(exam),
        "server_now": now_iso(),
        "end_at": session["end_at"] or exam["end_at"],
        "remaining_sec": max(0, seconds_left(session["end_at"] or exam["end_at"])),
        "answers": {str(k): v for k, v in store.answers(session["id"]).items()},
    }
    if session["status"] in ("active", "submitted"):
        payload["questions"] = paper_for(store, session)
    payload["result"] = session_result(store, session, exam) \
        if session["status"] == "submitted" else None
    return payload


def paper_for(store: Store, session: Dict) -> List[Dict]:
    """Student ki vellina paper — correct answers PAMPABADAVU (security)."""
    order = json.loads(session["question_order"] or "[]")
    option_orders = json.loads(session["option_orders"] or "{}")
    by_id = {q["id"]: q for q in store.questions(session["exam_id"])}
    paper = []
    for qid in order:
        q = by_id.get(qid)
        if not q or q["dropped"]:
            continue
        order_idx = option_orders.get(str(qid)) or list(range(len(q["options"])))
        options = [q["options"][i] for i in order_idx if 0 <= i < len(q["options"])]
        paper.append({"id": qid, "text": q["text"], "options": options,
                      "topic": q["topic"], "marks": q["marks"]})
    return paper


def public_exam(exam: Dict) -> Dict:
    """Student-safe exam meta (admin token / internal ids ledu)."""
    return {
        "code": exam["code"], "college": exam["college"], "title": exam["title"],
        "subject": exam["subject"], "exam_date": exam["exam_date"],
        "instructions": exam["instructions"], "duration_min": exam["duration_min"],
        "per_q_marks": exam["per_q_marks"], "negative_marks": exam["negative_marks"],
        "pass_marks": exam["pass_marks"], "status": exam["status"],
        "start_at": exam["start_at"], "end_at": exam["end_at"],
        "announcement": exam["announcement"],
        "announcement_at": exam["announcement_at"],
        "questions": store_count_hint(exam),
        "results_published": bool(exam["results_published_at"]),
        "show_result": exam["show_result"],
    }


def store_count_hint(exam: Dict) -> int:
    return int(exam.get("question_count") or 0)


def heartbeat(store: Store, session: Dict) -> Dict:
    """Timer + status sync (server-authoritative; client clock tamper useless)."""
    exam = store.get_exam(session["exam_id"])
    session = store.session(session["id"])
    now = now_iso()
    fields: Dict[str, Any] = {"last_seen": now}
    status = session["status"]
    if status == "waiting" and exam["status"] == "live":
        status = "active"
        fields["status"] = "active"
        fields["started_at"] = session["started_at"] or now
    if status == "active":
        deadline = session["end_at"] or exam["end_at"]
        if deadline and seconds_left(deadline) <= 0:
            _finalize_session(store, store.session(session["id"]), auto=True)
            status = "submitted"
    store.update_session(session["id"], **fields)
    session = store.session(session["id"])
    out = {
        "status": session["status"],
        "exam_status": exam["status"],
        "server_now": now_iso(),
        "end_at": session["end_at"] or exam["end_at"],
        "remaining_sec": max(0, seconds_left(session["end_at"] or exam["end_at"])),
        "announcement": exam["announcement"],
        "announcement_at": exam["announcement_at"],
        "results_published": bool(exam["results_published_at"]),
    }
    if session["status"] == "active" and not session["question_order"]:
        _prepare_paper(store, session, exam)
        out["questions"] = paper_for(store, store.session(session["id"]))
    return out


def save_answer(store: Store, session: Dict, question_id: int,
                choice: Optional[int], flagged: Optional[bool]) -> Dict:
    """Student answer save.

    choice: >=0 select, -1 CLEAR (unselect — mistakes undakudadu),
            None = answer touch cheyyakunda flag matrame update.
    """
    exam = store.get_exam(session["exam_id"])
    if session["status"] != "active" or exam["status"] != "live":
        raise ExamError("Exam active lo ledu — answer save avvaledu", "not_active")
    q = store.question(int(question_id))
    if not q or q["exam_id"] != exam["id"] or q["dropped"]:
        raise ExamError("Question dorakaledu", "not_found", 404)
    if choice is not None and int(choice) >= 0 and not (int(choice) < len(q["options"])):
        raise ExamError("Choice out of range", "validation")
    store.save_answer(session["id"], q["id"],
                      None if choice is None else int(choice), flagged)
    store.touch_session(session["id"])
    return {"saved": True, "updated_at": now_iso(),
            "answered": sum(1 for a in store.answers(session["id"]).values()
                            if a["choice"] is not None)}


def register_tab_switch(store: Store, session: Dict) -> Dict:
    store.update_session(session["id"],
                         tab_switches=int(session["tab_switches"]) + 1,
                         last_seen=now_iso())
    store.log_event(session["exam_id"], session["id"], "tab_switch",
                    f"count={int(session['tab_switches']) + 1}")
    return {"tab_switches": int(session["tab_switches"]) + 1}


def submit_session(store: Store, session: Dict, auto: bool = False,
                   reason: str = "") -> Dict:
    """Idempotent submit — rendu sarlu click chesina okkate result."""
    if session["status"] == "submitted":
        exam = store.get_exam(session["exam_id"])
        return {"already": True, "result": session_result(store, session, exam)}
    _finalize_session(store, session, auto=auto, reason=reason)
    session = store.session(session["id"])
    exam = store.get_exam(session["exam_id"])
    store.log_event(exam["id"], session["id"],
                    "auto_submit" if auto else "submitted",
                    reason or f"score={session['score']}")
    recompute_ranks(store, exam["id"])
    session = store.session(session["id"])
    return {"already": False, "result": session_result(store, session, exam)}


# ===========================================================================
# Scoring
# ===========================================================================

def _finalize_session(store: Store, session: Dict, auto: bool = False,
                      reason: str = "") -> None:
    if session["status"] == "submitted":
        return
    score_session(store, session)
    store.update_session(session["id"], status="submitted",
                         submitted_at=now_iso(),
                         auto_submitted=1 if auto else 0)
    if auto:
        store.log_event(session["exam_id"], session["id"], "auto_submitted", reason)


def _opt_text(question: Dict, index: Optional[int]) -> Optional[str]:
    opts = question.get("options") or []
    if index is None or not (0 <= int(index) < len(opts)):
        return None
    return opts[int(index)]


def _option_orders(session: Dict) -> Dict[str, List[int]]:
    try:
        return json.loads(session["option_orders"] or "{}") or {}
    except (ValueError, TypeError):
        return {}


def _to_original(session: Dict, question: Dict, pos: Optional[int]) -> Optional[int]:
    """Student view position → ORIGINAL option index (option shuffle safe).

    paper_for() options ni shuffle chesi chupistundi; student nokkindi aa shuffled
    position. Store lo position ne pettamu (resume/retry ki same) — kaani scoring
    ki original index kavali, else correct answers MISCOUNT avutayi.
    """
    if pos is None:
        return None
    order = _option_orders(session).get(str(question["id"]))
    if not order:
        return pos
    try:
        if 0 <= int(pos) < len(order):
            return int(order[int(pos)])
    except (TypeError, ValueError):
        return None
    return None


def _pos_of_original(session: Dict, question: Dict, original: Optional[int]) -> Optional[int]:
    """Correct answer ni student view lo e position lo undo chupinchadaniki."""
    if original is None:
        return None
    order = _option_orders(session).get(str(question["id"]))
    if not order:
        return original
    try:
        return order.index(int(original))
    except ValueError:
        return None


def score_session(store: Store, session: Dict) -> Dict:
    exam = store.get_exam(session["exam_id"])
    questions = store.questions(exam["id"])
    answers = store.answers(session["id"])
    per_q = float(exam["per_q_marks"])
    neg = float(exam["negative_marks"])
    correct = wrong = unattempted = dropped_seen = 0
    score = 0.0
    review = []
    for q in questions:
        if q["dropped"]:
            dropped_seen += 1
            continue
        marks = float(q["marks"]) if q["marks"] is not None else per_q
        a = answers.get(q["id"]) or {}
        pos = a.get("choice")                       # student view position
        if pos is None:
            unattempted += 1
            review.append({"question_id": q["id"], "text": q["text"],
                           "your_answer": None, "your_answer_text": None,
                           "correct_answer": None, "correct_answer_text": None,
                           "correct_index": _pos_of_original(session, q, q["correct_index"]),
                           "marks": marks, "result": "unattempted"})
            continue
        choice = _to_original(session, q, pos)       # shuffle-safe compare
        correct_pos = _pos_of_original(session, q, q["correct_index"])
        if choice is not None and choice == q["correct_index"]:
            correct += 1
            score += marks
            verdict = "correct"
        else:
            wrong += 1
            score -= neg
            verdict = "wrong"
        review.append({"question_id": q["id"], "text": q["text"],
                       "your_answer": pos, "correct_answer": correct_pos,
                       "your_answer_text": _opt_text(q, choice),
                       "correct_answer_text": _opt_text(q, q["correct_index"]),
                       "correct_index": correct_pos, "marks": marks,
                       "result": verdict,
                       "explanation": q["explanation"]})
    score = round(score, 3)
    store.update_session(session["id"], score=score, correct=correct,
                         wrong=wrong, unattempted=unattempted,
                         scored_at=now_iso())
    return {"score": score, "correct": correct, "wrong": wrong,
            "unattempted": unattempted, "review": review, "dropped": dropped_seen}


def recompute_ranks(store: Store, exam_id: int) -> None:
    rows = [s for s in store.sessions(exam_id) if s["status"] == "submitted"]
    rows.sort(key=lambda s: (-(s["score"] or 0), s["submitted_at"] or ""))
    for i, s in enumerate(rows, 1):
        store.update_session(s["id"], rank=i)


def session_result(store: Store, session: Dict, exam: Optional[Dict] = None) -> Dict:
    exam = exam or store.get_exam(session["exam_id"])
    questions = store.questions(exam["id"], include_dropped=False)
    total = total_marks(exam, questions)
    published = bool(exam["results_published_at"]) or exam["show_result"] == "immediate"
    passed = None
    if exam["pass_marks"]:
        passed = (session["score"] or 0) >= float(exam["pass_marks"])
    out = {
        "roll": session["roll"], "name": session["name"],
        "status": session["status"],
        "score": session["score"], "total_marks": total,
        "correct": session["correct"], "wrong": session["wrong"],
        "unattempted": session["unattempted"],
        "rank": session["rank"], "passed": passed,
        "submitted_at": session["submitted_at"],
        "auto_submitted": bool(session["auto_submitted"]),
        "show_result": exam["show_result"],
        "results_published": published,
        "review": None,
    }
    if published and exam["show_result"] == "immediate":
        out["review"] = score_session(store, session)["review"]
    return out


def results_summary(store: Store, exam_id: int) -> Dict:
    exam = store.get_exam(exam_id)
    sessions = store.sessions(exam_id)
    submitted = [s for s in sessions if s["status"] == "submitted"]
    scores = [s["score"] or 0 for s in submitted]
    questions = store.questions(exam_id, include_dropped=False)
    total = total_marks(exam, questions)
    pass_marks = float(exam["pass_marks"] or 0)
    passed = sum(1 for s in submitted if (s["score"] or 0) >= pass_marks) if pass_marks else None
    return {
        "joined": len(sessions),
        "submitted": len(submitted),
        "pending": len([s for s in sessions if s["status"] in ("waiting", "active")]),
        "roster": len(store.roster_rolls(exam_id)),
        "questions": len(questions),
        "total_marks": total,
        "pass_marks": pass_marks,
        "passed": passed,
        "average": round(sum(scores) / len(scores), 2) if scores else 0,
        "highest": max(scores) if scores else 0,
        "lowest": min(scores) if scores else 0,
        "topper": (sorted(submitted, key=lambda x: (-(x["score"] or 0),
                                                    x["submitted_at"] or ""))[0]["roll"]
                   if submitted else ""),
    }


def question_analysis(store: Store, exam_id: int) -> List[Dict]:
    """Question-wise correct % — college ki teaching insight (mistake lekunda)."""
    questions = store.questions(exam_id)
    sessions = [s for s in store.sessions(exam_id) if s["status"] == "submitted"]
    out = []
    for q in questions:
        correct = wrong = skipped = 0
        for s in sessions:
            answers = store.answers(s["id"])
            a = answers.get(q["id"]) or {}
            if a.get("choice") is None:
                skipped += 1
            elif _to_original(s, q, a.get("choice")) == q["correct_index"]:
                correct += 1
            else:
                wrong += 1
        attempted = correct + wrong
        out.append({
            "question_id": q["id"], "order_no": q["order_no"],
            "text": q["text"], "topic": q["topic"], "dropped": bool(q["dropped"]),
            "correct": correct, "wrong": wrong, "skipped": skipped,
            "correct_pct": round(100 * correct / attempted, 1) if attempted else 0.0,
            "difficulty_seen": ("easy" if attempted and correct / attempted >= 0.7
                                else "hard" if attempted and correct / attempted < 0.3
                                else "medium"),
        })
    return out


def drop_question(store: Store, exam_id: int, question_id: int,
                  dropped: bool = True) -> Dict:
    """Question mistake unte (wrong key / out of syllabus) → drop + recompute.

    Marks recalculate (aa question evariki count avvadu) — unfair marks ledu.
    """
    q = store.question(question_id)
    if not q or q["exam_id"] != exam_id:
        raise ExamError("Question dorakaledu", "not_found", 404)
    store.update_question(question_id, dropped=1 if dropped else 0)
    store.log_event(exam_id, None, "question_dropped" if dropped else "question_restored",
                    f"Q{q['order_no']}: {q['text'][:80]}")
    for s in store.sessions(exam_id):
        if s["scored_at"] or s["status"] == "submitted":
            score_session(store, s)
    recompute_ranks(store, exam_id)
    return {"question": store.question(question_id),
            "summary": results_summary(store, exam_id)}


def publish_results(store: Store, exam_id: int, notify_channels: bool = True) -> Dict:
    exam = store.get_exam(exam_id)
    if not exam:
        raise ExamError("Exam dorakaledu", "not_found", 404)
    recompute_ranks(store, exam_id)
    store.update_exam(exam_id, results_published_at=now_iso())
    store.log_event(exam_id, None, "results_published", "")
    exam = store.get_exam(exam_id)
    if notify_channels:
        notify.broadcast_event(store, exam, "results")
    return {"exam": exam, "summary": results_summary(store, exam_id)}


# ===========================================================================
# Sweeper — mistakes lekunda automatic (admin marchipoyina kuda)
# ===========================================================================

def sweep(store: Store, closing_soon_min: int = 5) -> Dict:
    """Background thread prathi 5s idi run chestundi.

    1) Time ayyina live exams ni AUTO-CLOSE (admin marchipoyina kuda safe).
    2) 'Andaru join ayyaka start' ON unte roster full aithe AUTO-START.
    3) Close avvadaniki 5 nimishalu mundu okkasari 'closing soon' notify.
    """
    actions: List[str] = []
    # 1) auto-start
    for exam in store.list_exams(limit=200):
        if exam["status"] != "published" or not exam["auto_start_all_joined"]:
            continue
        roster = store.roster_rolls(exam["id"])
        if not roster:
            continue
        joined = {s["roll"] for s in store.sessions(exam["id"])}
        if set(roster) <= joined:
            try:
                start_exam(store, exam["id"])
                actions.append(f"auto_start:{exam['code']}")
            except ExamError as exc:
                store.log_event(exam["id"], None, "auto_start_failed", str(exc))
    # 2) auto-close
    for exam in store.due_exams():
        try:
            res = close_exam(store, exam["id"], reason="auto_time_over")
            actions.append(f"auto_close:{exam['code']}:{res.get('auto_submitted', 0)}")
        except ExamError as exc:
            store.log_event(exam["id"], None, "auto_close_failed", str(exc))
    # 3) closing-soon ping (okkasari)
    for exam in store.list_exams(limit=200):
        if exam["status"] != "live" or not exam["end_at"]:
            continue
        left = seconds_left(exam["end_at"])
        key = f"closing_soon:{exam['id']}"
        already = _meta_seen(store, key, exam["code"])
        if 0 < left <= closing_soon_min * 60 and not already:
            notify.broadcast_event(store, exam, "closing_soon",
                                   extra=f"{max(1, left // 60)} nimishalu migilinayi")
            actions.append(f"closing_soon:{exam['code']}")
    return {"actions": actions}


def _meta_seen(store: Store, key: str, code: str) -> bool:
    """Idempotent notification guard (events table lo mark)."""
    with store.connect() as conn:
        row = conn.execute(
            "SELECT 1 FROM events WHERE kind = ? AND detail = ? LIMIT 1",
            (key, code)).fetchone()
        if row:
            return True
        conn.execute(
            "INSERT INTO events (exam_id, session_id, kind, detail, created_at)"
            " VALUES (NULL, NULL, ?, ?, ?)", (key, code, now_iso()))
    return False


# ===========================================================================
# Exports (college office ki CSV)
# ===========================================================================

def results_csv(store: Store, exam_id: int) -> str:
    exam = store.get_exam(exam_id)
    rows = [["Rank", "Roll", "Name", "Score", "Total", "Correct", "Wrong",
             "Unattempted", "Pass/Fail", "Auto submit", "Submitted at",
             "Tab switches", "Status"]]
    questions = store.questions(exam_id, include_dropped=False)
    total = total_marks(exam, questions)
    for s in store.sessions(exam_id):
        verdict = "Absent" if s["status"] in ("waiting", "active") else (
            "Pass" if float(exam["pass_marks"] or 0) and (s["score"] or 0) >= float(exam["pass_marks"])
            else "Fail" if float(exam["pass_marks"] or 0) else "-")
        rows.append([s["rank"] or "", s["roll"], s["name"], s["score"] if s["score"] is not None else "",
                     total, s["correct"] if s["correct"] is not None else "",
                     s["wrong"] if s["wrong"] is not None else "",
                     s["unattempted"] if s["unattempted"] is not None else "",
                     verdict, "Yes" if s["auto_submitted"] else "No",
                     s["submitted_at"] or "", s["tab_switches"], s["status"]])
    return _to_csv(rows)


def questions_csv(store: Store, exam_id: int) -> str:
    rows = [["No", "Question", "Option A", "Option B", "Option C", "Option D",
             "Option E", "Option F", "Correct", "Topic", "Marks", "Dropped"]]
    for q in store.questions(exam_id):
        opts = list(q["options"]) + [""] * (6 - len(q["options"]))
        rows.append([q["order_no"], q["text"], *opts[:6], OPT_LETTERS[q["correct_index"]],
                     q["topic"], q["marks"] if q["marks"] is not None else "",
                     "Yes" if q["dropped"] else "No"])
    return _to_csv(rows)


def analysis_csv(store: Store, exam_id: int) -> str:
    rows = [["No", "Question", "Topic", "Correct", "Wrong", "Skipped",
             "Correct %", "Difficulty"]]
    for a in question_analysis(store, exam_id):
        rows.append([a["order_no"], a["text"], a["topic"], a["correct"], a["wrong"],
                     a["skipped"], a["correct_pct"], a["difficulty_seen"]])
    return _to_csv(rows)


def audit_csv(store: Store, exam_id: int) -> str:
    rows = [["Time", "Event", "Session", "Detail"]]
    for e in store.events(exam_id, limit=2000):
        rows.append([e["created_at"], e["kind"], e["session_id"] or "", e["detail"]])
    return _to_csv(rows)


def _to_csv(rows: List[List[Any]]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    for r in rows:
        writer.writerow(r)
    return buf.getvalue()


def export_bundle(store: Store, exam_id: int) -> Dict[str, str]:
    """Anni reports okkate chota (college office ki)."""
    return {
        "results": results_csv(store, exam_id),
        "questions": questions_csv(store, exam_id),
        "analysis": analysis_csv(store, exam_id),
        "audit": audit_csv(store, exam_id),
    }
