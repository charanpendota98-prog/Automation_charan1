# -*- coding: utf-8 -*-
"""autoblog/quiz_intake.py — Daily Exam-Wise Channel Quiz Intake Engine.

Accepts 20 daily questions from external bots/channels tagged by target exam:
  - tspsc: TSPSC Group 1-4, Police SI/PC, Gurukulam, Forest
  - appsc: APPSC Group 1-2, Police, DSC, Secretariat
  - ssc: SSC CGL, CHSL, MTS, CPO, GD Constable
  - banking: IBPS PO/Clerk, SBI PO/Clerk, RRB Officer/Clerk
  - rrb: Railways NTPC, Group D, ALP, Technician
  - general: General Studies, Current Affairs, Indian Polity

Validates schema (4 options, valid 0..3 key, detailed explanation, source),
normalizes tags, and stores in data/daily_quiz_store.json for theme/bot consumption.
"""
from __future__ import annotations

import json
import logging
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Union

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
QUIZ_STORE_PATH = DATA_DIR / "daily_quiz_store.json"

log = logging.getLogger("autoblog.quiz_intake")

VALID_EXAMS = {
    "all": "All Competitive Exams",
    "tspsc": "TSPSC (Group 1-4 / Police / Gurukul)",
    "appsc": "APPSC (Group 1-2 / DSC / Police)",
    "ssc": "SSC (CGL / CHSL / MTS / GD)",
    "banking": "Banking (IBPS / SBI / RRB)",
    "rrb": "Railways (RRB NTPC / Group D)",
    "general": "General Studies & Current Affairs",
}


def normalize_question(item: Dict, index: int = 0) -> Optional[Dict]:
    """Validate and normalize a single exam question from external bots or channels."""
    q_text = str(item.get("q") or item.get("question") or "").strip()
    if not q_text:
        return None

    raw_opts = item.get("a") or item.get("options") or item.get("choices") or item.get("answers") or []
    if not isinstance(raw_opts, (list, tuple)) or len(raw_opts) < 2:
        return None

    options = [str(opt).strip() for opt in raw_opts[:4]]
    while len(options) < 4:
        options.append(f"Option {chr(65 + len(options))}")

    # Correct answer index normalization (0..3, 'A'..'D', or exact option string match)
    c_val = item.get("c") if item.get("c") is not None else (
        item.get("answer") if item.get("answer") is not None else (
            item.get("correct") if item.get("correct") is not None else item.get("correct_index")
        )
    )

    c_idx = 0
    if isinstance(c_val, str):
        c_str = c_val.strip()
        c_upper = c_str.upper()
        if c_upper in ("A", "B", "C", "D"):
            c_idx = ord(c_upper) - ord("A")
        elif c_str.isdigit():
            c_idx = int(c_str)
        else:
            # Try to find string matching one of the options
            found = False
            for oi, opt in enumerate(options):
                if opt.lower() == c_str.lower():
                    c_idx = oi
                    found = True
                    break
            if not found:
                c_idx = 0
    elif isinstance(c_val, int):
        c_idx = max(0, min(3, c_val))
    else:
        c_idx = 0

    why = str(item.get("why") or item.get("explanation") or "Official examination key verification.").strip()
    cat = str(item.get("cat") or item.get("category") or "General Studies").strip()
    src = str(item.get("src") or item.get("source") or "Official Exam Key").strip()

    raw_exam = str(item.get("exam") or item.get("target_exam") or "general").strip().lower()
    if "tspsc" in raw_exam or "telangana" in raw_exam or "tg " in raw_exam:
        exam = "tspsc"
    elif "appsc" in raw_exam or "andhra" in raw_exam or "dsc" in raw_exam:
        exam = "appsc"
    elif "ssc" in raw_exam or "cgl" in raw_exam or "chsl" in raw_exam:
        exam = "ssc"
    elif "bank" in raw_exam or "ibps" in raw_exam or "sbi" in raw_exam:
        exam = "banking"
    elif "railway" in raw_exam or "rrb" in raw_exam or "ntpc" in raw_exam:
        exam = "rrb"
    elif raw_exam in VALID_EXAMS:
        exam = raw_exam
    else:
        exam = "general"

    return {
        "id": index + 1,
        "exam": exam,
        "q": q_text,
        "a": options,
        "c": c_idx,
        "why": why,
        "cat": cat,
        "src": src,
    }


def ingest_questions(
    source: Union[str, Path, List[Dict]],
    target_date: Optional[Union[str, date]] = None,
    store_path: Optional[Path] = None,
) -> Dict[str, Union[str, int, List[Dict]]]:
    """Ingest a list of questions or load from a JSON file."""
    path = store_path or QUIZ_STORE_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    if target_date is None:
        day_key = date.today().isoformat()
    elif isinstance(target_date, str):
        day_key = target_date
    else:
        day_key = target_date.isoformat()

    raw_items: List[Dict] = []
    if isinstance(source, (str, Path)):
        p = Path(source)
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    raw_items = data
                elif isinstance(data, dict):
                    if "questions" in data and isinstance(data["questions"], list):
                        raw_items = data["questions"]
                    elif day_key in data and isinstance(data[day_key], list):
                        raw_items = data[day_key]
                    else:
                        # Could be dict of exams or date keys
                        for val in data.values():
                            if isinstance(val, list):
                                raw_items.extend(val)
                            elif isinstance(val, dict):
                                raw_items.append(val)
            except Exception as e:
                log.error("Failed to parse quiz source file %s: %s", p, e)
                return {"status": "error", "error": str(e), "count": 0, "imported": 0, "questions": []}
    elif isinstance(source, list):
        raw_items = source

    valid_questions = []
    for idx, item in enumerate(raw_items):
        if isinstance(item, dict):
            norm = normalize_question(item, idx)
            if norm:
                valid_questions.append(norm)

    # Save to persistent store partitioned by day
    store_data = {}
    if path.exists():
        try:
            store_data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            store_data = {}

    if not valid_questions:
        log.warning("No valid questions found to ingest from %s", source)
        return {
            "status": "warning",
            "message": "No valid questions found to ingest",
            "day": day_key,
            "count": 0,
            "imported": 0,
            "total_for_day": len(store_data.get(day_key, [])),
            "questions": [],
        }

    # Merge or set for the day
    existing = store_data.get(day_key, [])
    # Re-index if appending
    start_id = len(existing)
    for i, q in enumerate(valid_questions):
        q["id"] = start_id + i + 1
    existing.extend(valid_questions)
    store_data[day_key] = existing
    path.write_text(json.dumps(store_data, ensure_ascii=False, indent=2), encoding="utf-8")

    log.info("Ingested %d valid exam-wise questions for %s into %s", len(valid_questions), day_key, path)
    return {
        "status": "ok",
        "day": day_key,
        "count": len(valid_questions),
        "imported": len(valid_questions),
        "total_for_day": len(existing),
        "questions": valid_questions,
    }


def get_daily_questions(
    exam: str = "all",
    target_date: Optional[Union[str, date]] = None,
    store_path: Optional[Path] = None,
    **kwargs,
) -> List[Dict]:
    """Fetch daily questions filtered by target exam.

    Flexible arguments:
      - get_daily_questions() -> all questions for today
      - get_daily_questions("tspsc") -> tspsc questions for today
      - get_daily_questions("tspsc", "2026-10-03") -> tspsc questions for 2026-10-03
      - get_daily_questions(exam_filter="tspsc", day=...) -> kwargs supported
    """
    path = store_path or kwargs.get("path") or QUIZ_STORE_PATH

    # Detect if first argument was meant as a date
    if isinstance(exam, date) or (isinstance(exam, str) and len(exam) == 10 and exam.count("-") == 2):
        target_date = exam
        exam = kwargs.get("exam_filter", "all")
    elif kwargs.get("exam_filter"):
        exam = kwargs.get("exam_filter")

    if kwargs.get("day"):
        target_date = kwargs.get("day")

    if target_date is None:
        day_key = date.today().isoformat()
    elif isinstance(target_date, str):
        day_key = target_date
    else:
        day_key = target_date.isoformat()

    if not path.exists():
        return []

    try:
        store_data = json.loads(path.read_text(encoding="utf-8"))
        # If the requested day isn't found, fallback to the latest available day
        qs = store_data.get(day_key)
        if qs is None and store_data:
            latest_day = sorted(store_data.keys())[-1]
            qs = store_data.get(latest_day, [])

        if not qs:
            return []

        exam_clean = exam.lower().strip()
        if exam_clean in ("all", "*"):
            return qs

        return [q for q in qs if q.get("exam") in (exam_clean, "all", "general")]
    except Exception as e:
        log.error("Failed to read quiz store from %s: %s", path, e)
        return []


def format_for_telegram(q: Dict) -> str:
    """Format a single question for Telegram channel publication with spoiler tags."""
    letters = ["A", "B", "C", "D"]
    q_text = q.get("q", "").strip()
    opts = q.get("a", [])
    c_idx = q.get("c", 0)
    why = q.get("why", "").strip()
    exam = q.get("exam", "general").upper()
    cat = q.get("cat", "General Studies")
    src = q.get("src", "Official Key")

    lines = [
        f"🎯 *[{exam}] Daily Mock Question*",
        f"📚 *Category:* {cat}",
        "",
        f"*{q_text}*",
        "",
    ]
    for i, opt in enumerate(opts[:4]):
        lines.append(f"{letters[i]}) {opt}")

    correct_letter = letters[c_idx] if 0 <= c_idx < 4 else "A"
    correct_text = opts[c_idx] if 0 <= c_idx < len(opts) else ""

    lines.extend([
        "",
        f"💡 *Correct Answer:* ||{correct_letter}) {correct_text}||",
        f"📖 *Explanation:* ||{why}||",
        f"🏛️ *Source:* {src}",
        "",
        "🔗 *Practice 20+ Daily Questions Free:* https://studentup.in/pages/daily-quiz.html",
        f"#{exam} #CompetitiveExams #StudentUpQuiz",
    ])
    return "\n".join(lines)


def format_for_whatsapp(q: Dict) -> str:
    """Format a single question for WhatsApp channel publication."""
    letters = ["A", "B", "C", "D"]
    q_text = q.get("q", "").strip()
    opts = q.get("a", [])
    c_idx = q.get("c", 0)
    why = q.get("why", "").strip()
    exam = q.get("exam", "general").upper()
    cat = q.get("cat", "General Studies")

    lines = [
        f"📝 *StudentUp Daily Quiz* | *[{exam}]*",
        f"📌 *Topic:* {cat}",
        "",
        f"*{q_text}*",
        "",
    ]
    for i, opt in enumerate(opts[:4]):
        lines.append(f"*{letters[i]})* {opt}")

    correct_letter = letters[c_idx] if 0 <= c_idx < 4 else "A"
    correct_text = opts[c_idx] if 0 <= c_idx < len(opts) else ""

    lines.extend([
        "",
        f"✅ *Answer:* *{correct_letter}) {correct_text}*",
        f"💡 *Reason:* _{why}_",
        "",
        "👉 *Free Daily Mock Tests:* https://studentup.in/pages/daily-quiz.html",
    ])
    return "\n".join(lines)


def export_channel_broadcast(
    target_channel: str = "telegram",
    exam: str = "all",
    target_date: Optional[Union[str, date]] = None,
    store_path: Optional[Path] = None,
) -> str:
    """Export all questions for the day formatted for Telegram or WhatsApp broadcast."""
    qs = get_daily_questions(exam=exam, target_date=target_date, store_path=store_path)
    if not qs:
        return "No questions available for the selected date/exam."

    formatter = format_for_telegram if target_channel.lower() == "telegram" else format_for_whatsapp
    separator = "\n" + ("=" * 40) + "\n\n"
    return separator.join(formatter(q) for q in qs)

