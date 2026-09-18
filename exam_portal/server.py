"""v39 Exam Portal — HTTP server (stdlib only) + CLI.

Run:
    python run.py --exam-portal                 # http://0.0.0.0:8080
    python run.py --exam-portal --exam-port 9000
    python -m exam_portal.server --port 8080 --db exam_portal.db

No framework, no build step — oka college VM lo `python run.py --exam-portal`
ante chalu. Students same link open chesi roll number tho join avutaru.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import re
import secrets
import threading
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, unquote, urlparse

from . import engine, notify, ui
from .store import DEFAULT_DB, Store, now_iso

log = logging.getLogger("exam_portal")

KEY_FILE = Path(__file__).resolve().parent.parent / "exam_portal_admin_key.txt"
JSON_HEADERS = {"Content-Type": "application/json; charset=utf-8",
                "Cache-Control": "no-store"}


# --------------------------------------------------------------------- helpers

def load_admin_key(explicit: str = "") -> str:
    """Admin key: env/arg > file (auto-create) > random print."""
    key = (explicit or os.environ.get("EXAM_PORTAL_ADMIN_KEY", "")).strip()
    if key:
        return key
    if KEY_FILE.exists():
        saved = KEY_FILE.read_text(encoding="utf-8").strip()
        if saved:
            return saved
    key = secrets.token_urlsafe(12)
    try:
        KEY_FILE.write_text(key + "\n", encoding="utf-8")
        os.chmod(KEY_FILE, 0o600)
    except OSError:
        pass
    return key


class Api:
    """Thin request-router over engine/store (testable without HTTP)."""

    def __init__(self, store: Store, admin_key: str):
        self.store = store
        self.admin_key = admin_key

    # ---------------------------------------------------------- auth
    def require_admin(self, key: str) -> None:
        if not key or key != self.admin_key:
            raise engine.ExamError("Admin key tappu — malli try cheyandi",
                                   "unauthorized", 401)

    def require_exam(self, code: str, key: str) -> Dict:
        exam = self.store.exam_by_code(code)
        if not exam:
            raise engine.ExamError("Exam code dorakaledu", "not_found", 404)
        if not key or key != exam["admin_token"]:
            raise engine.ExamError("Ee exam ki meeke access ledu (admin token tappu)",
                                   "unauthorized", 401)
        return exam

    # ------------------------------------------------------ admin: exams
    def admin_exams(self, key: str) -> Dict:
        self.require_admin(key)
        exams = []
        for e in self.store.list_exams():
            row = dict(e)
            row.pop("admin_token", None)
            row["admin_token"] = e["admin_token"]     # manage link kosam
            row["question_count"] = self.store.count_questions(e["id"], only_live=True)
            row["joined"] = len(self.store.sessions(e["id"]))
            exams.append(row)
        return {"exams": exams, "server_now": now_iso()}

    def create_exam(self, key: str, payload: Dict) -> Dict:
        self.require_admin(key)
        title = (payload.get("title") or "").strip()
        if not title:
            raise engine.ExamError("Exam title ivvandi", "validation")
        duration = int(payload.get("duration_min") or 30)
        if not (1 <= duration <= 480):
            raise engine.ExamError("Duration 1-480 minutes madhya pettandi", "validation")
        exam = self.store.create_exam(
            college=(payload.get("college") or "").strip()[:120],
            title=title[:160],
            subject=(payload.get("subject") or "").strip()[:80],
            exam_date=(payload.get("exam_date") or "").strip()[:40],
            instructions=(payload.get("instructions") or "").strip()[:4000],
            duration_min=duration,
            per_q_marks=float(payload.get("per_q_marks") or 1),
            negative_marks=float(payload.get("negative_marks") or 0),
            shuffle_questions=bool(payload.get("shuffle_questions", True)),
            shuffle_options=bool(payload.get("shuffle_options", True)),
            show_result=(payload.get("show_result") or "immediate"),
            pass_marks=float(payload.get("pass_marks") or 0),
            roster_required=bool(payload.get("roster_required")),
            allow_late_join=bool(payload.get("allow_late_join", True)),
            late_grace_min=int(payload.get("late_grace_min") or 0),
            auto_start_all_joined=bool(payload.get("auto_start_all_joined")),
        )
        return {"exam": exam, "links": self.links(exam)}

    def links(self, exam: Dict) -> Dict:
        base = notify.PUBLIC_URL
        return {"student": f"{base}/exam/{exam['code']}" if base else f"/exam/{exam['code']}",
                "manage": f"/manage/{exam['code']}?key={exam['admin_token']}",
                "code": exam["code"]}

    def admin_exam(self, code: str, key: str) -> Dict:
        exam = self.require_exam(code, key)
        report = engine.validate_exam(self.store, exam["id"])
        sessions = []
        for s in self.store.sessions(exam["id"]):
            sessions.append({k: s[k] for k in
                             ("id", "roll", "name", "status", "joined_at",
                              "started_at", "last_seen", "submitted_at",
                              "auto_submitted", "score", "correct", "wrong",
                              "unattempted", "rank", "tab_switches", "extra_min")})
        questions = [{k: q[k] for k in
                      ("id", "order_no", "text", "options", "correct_index",
                       "explanation", "topic", "difficulty", "marks", "dropped")}
                     for q in self.store.questions(exam["id"])]
        leaderboard = sorted([s for s in sessions if s["status"] == "submitted"],
                             key=lambda s: (s["rank"] or 999, s["roll"]))
        notifications = self.store.notifications(exam["id"], limit=25)
        last = notifications[0] if notifications else None
        return {
            "exam": exam,
            "blockers": report["blockers"],
            "warnings": report["warnings"],
            "summary": engine.results_summary(self.store, exam["id"]),
            "sessions": sessions,
            "questions": questions,
            "leaderboard": leaderboard,
            "analysis": engine.question_analysis(self.store, exam["id"]),
            "events": self.store.events(exam["id"], limit=120),
            "notifications": notifications,
            "notifyLast": (f"{last['channel']}:{last['status']}" if last else ""),
            "announcementLive": exam["announcement"],
            "studentLink": self.links(exam)["student"],
            "manageLink": self.links(exam)["manage"],
            "templates": notify.templates(exam),
            "resultsPublished": exam["results_published_at"],
            "serverNow": now_iso(),
        }

    def update_settings(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        if exam["status"] == "closed":
            raise engine.ExamError("Closed exam settings marchalemu "
                                   "(audit kosam lock chesam)", "bad_state")
        fields: Dict[str, Any] = {}
        for f, cast in (("title", str), ("college", str), ("subject", str),
                        ("exam_date", str), ("instructions", str),
                        ("show_result", str)):
            if f in payload:
                fields[f] = cast(payload[f])[:4000 if f == "instructions" else 160]
        for f in ("duration_min", "late_grace_min"):
            if f in payload:
                fields[f] = max(0, int(payload[f] or 0))
        for f in ("per_q_marks", "negative_marks", "pass_marks"):
            if f in payload:
                fields[f] = max(0.0, float(payload[f] or 0))
        for f in ("allow_late_join", "auto_start_all_joined", "roster_required",
                  "shuffle_questions", "shuffle_options"):
            if f in payload:
                fields[f] = 1 if payload[f] else 0
        if exam["status"] == "live" and fields.get("duration_min", exam["duration_min"]) \
                != exam["duration_min"]:
            raise engine.ExamError("Live exam lo duration marchalemu — "
                                   "'+5 min' button vadandi", "bad_state")
        self.store.update_exam(exam["id"], **fields)
        self.store.log_event(exam["id"], None, "settings_updated",
                             ", ".join(f"{k}={v}" for k, v in fields.items())[:300])
        return {"exam": self.store.get_exam(exam["id"])}

    def add_questions(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        if exam["status"] in ("live", "closed"):
            raise engine.ExamError(
                "Live/closed exam lo questions add cheyyakudadu (fair play + audit "
                "freeze). Kotha paper ki kotha exam create cheyandi.", "bad_state")
        if payload.get("questions"):
            items, errors = payload["questions"], []
            cleaned = []
            for i, item in enumerate(items, 1):
                q = engine._validate_item(item.get("text", ""), item.get("options", []),
                                          item.get("correct_index"), i,
                                          item.get("explanation", ""),
                                          item.get("topic", ""), "", item.get("marks"))
                (errors if q.get("error") else cleaned).append(
                    q["error"] if q.get("error") else q)
            items, errors = cleaned, errors
        else:
            items, errors = engine.parse_questions(payload.get("raw", ""))
        if payload.get("dry_run"):
            return {"added": len(items), "errors": errors, "dry_run": True,
                    "preview": [{"text": q["text"][:90], "options": len(q["options"])}
                                for q in items[:10]]}
        if not items:
            return {"added": 0, "errors": errors or ["Questions parse avvaledu"]}
        total = self.store.add_questions(exam["id"], items)
        self.store.log_event(exam["id"], None, "questions_added",
                             f"+{len(items)} (total {total})")
        return {"added": len(items), "errors": errors, "total": total}

    def delete_question(self, code: str, key: str, qid: int, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        if exam["status"] in ("live", "closed"):
            raise engine.ExamError("Live/closed lo delete ledu — 'Drop' vadandi "
                                   "(unfair marks rakunda recalculate avutundi)",
                                   "bad_state")
        q = self.store.question(qid)
        if not q or q["exam_id"] != exam["id"]:
            raise engine.ExamError("Question dorakaledu", "not_found", 404)
        self.store.delete_question(qid)
        self.store.log_event(exam["id"], None, "question_deleted", q["text"][:80])
        return {"deleted": qid}

    def set_roster(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        rows = []
        for line in (payload.get("raw") or "").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.replace("\t", ",").split(",")]
            rows.append({"roll": parts[0], "name": parts[1] if len(parts) > 1 else ""})
        if not rows and payload.get("rows"):
            rows = payload["rows"]
        result = self.store.set_roster(exam["id"], rows)
        self.store.log_event(exam["id"], None, "roster_saved",
                             f"{result['added']} students")
        return result

    def get_roster(self, code: str, key: str) -> Dict:
        exam = self.require_exam(code, key)
        return {"rolls": self.store.roster(exam["id"])}

    # ------------------------------------------------ admin: lifecycle
    def start(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        return engine.start_exam(self.store, exam["id"],
                                 extend_minutes=int(payload.get("extend_minutes") or 0),
                                 force_allow_late=bool(payload.get("force_allow_late")))

    def close(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        return engine.close_exam(self.store, exam["id"],
                                 reason=payload.get("reason") or "manual")

    def extend(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        return engine.extend_exam(self.store, exam["id"],
                                  minutes=int(payload.get("minutes") or 5))

    def late_join(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        return {"exam": engine.toggle_late_join(self.store, exam["id"],
                                                bool(payload.get("allow")))}

    def announce(self, code: str, key: str, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        return engine.announce(self.store, exam["id"], payload.get("message") or "",
                               channels=bool(payload.get("channels", True)))

    def publish(self, code: str, key: str) -> Dict:
        exam = self.require_exam(code, key)
        return engine.publish_exam(self.store, exam["id"])

    def unpublish(self, code: str, key: str) -> Dict:
        exam = self.require_exam(code, key)
        return {"exam": engine.unpublish_exam(self.store, exam["id"])}

    def publish_results(self, code: str, key: str) -> Dict:
        exam = self.require_exam(code, key)
        return engine.publish_results(self.store, exam["id"])

    def drop_question(self, code: str, key: str, qid: int, payload: Dict) -> Dict:
        exam = self.require_exam(code, key)
        return engine.drop_question(self.store, exam["id"], qid,
                                    dropped=bool(payload.get("dropped", True)))

    def export(self, code: str, key: str, kind: str) -> Tuple[str, str]:
        exam = self.require_exam(code, key)
        funcs = {"results": engine.results_csv, "questions": engine.questions_csv,
                 "analysis": engine.analysis_csv, "audit": engine.audit_csv}
        if kind not in funcs:
            raise engine.ExamError("Export type tappu", "not_found", 404)
        name = f"{exam['code']}-{kind}.csv"
        return funcs[kind](self.store, exam["id"]), name

    # --------------------------------------------------- student: join
    def exam_info(self, code: str) -> Dict:
        exam = self.store.exam_by_code(code)
        if not exam:
            raise engine.ExamError("Exam code tappu — link check cheyandi",
                                   "not_found", 404)
        info = engine.public_exam(exam)
        info["questions"] = self.store.count_questions(exam["id"], only_live=True)
        info["joined"] = len(self.store.sessions(exam["id"]))
        return {"exam": info, "server_now": now_iso()}

    def join(self, payload: Dict) -> Dict:
        return engine.join_exam(
            self.store, payload.get("code", ""), payload.get("roll", ""),
            payload.get("name", ""), payload.get("device", ""),
            payload.get("ip", ""), payload.get("token", ""))

    def session_state(self, token: str) -> Dict:
        session = self.store.session_by_token(token)
        if not session:
            raise engine.ExamError("Session dorakaledu — malli join avvandi",
                                   "not_found", 404)
        return engine._session_payload(self.store, session)

    def heartbeat(self, payload: Dict) -> Dict:
        session = self._require_session(payload)
        return engine.heartbeat(self.store, session)

    def answer(self, payload: Dict) -> Dict:
        session = self._require_session(payload)
        return engine.save_answer(self.store, session,
                                  int(payload.get("question_id") or 0),
                                  payload.get("choice"), payload.get("flagged"))

    def tab_switch(self, payload: Dict) -> Dict:
        session = self._require_session(payload)
        return engine.register_tab_switch(self.store, session)

    def submit(self, payload: Dict) -> Dict:
        session = self._require_session(payload)
        return engine.submit_session(self.store, session,
                                     auto=bool(payload.get("auto")),
                                     reason=payload.get("reason") or "")

    # ------------------------------------------------------ v47: daily poll
    @staticmethod
    def _poll_day() -> str:
        return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")

    def _poll_question(self) -> Dict:
        bank = self.store.bank_questions()
        if not bank:
            raise engine.ExamError(
                "Prashna bank khali — admin console lo questions add cheyandi",
                "no-bank", 404)
        day = self._poll_day()
        idx = datetime.strptime(day, "%Y-%m-%d").toordinal() % len(bank)
        q = bank[idx]
        return {"day": day, "q": q, "bank_size": len(bank)}

    def today_poll(self) -> Dict:
        """Public: roju kotha prashna (question bank rotate avutundi)."""
        pick = self._poll_question()
        q = pick["q"]
        return {"ok": True, "day": pick["day"], "qid": q["id"], "text": q["text"],
                "options": q["options"], "topic": q.get("topic", ""),
                "bank_size": pick["bank_size"]}

    def vote_poll(self, payload: Dict) -> Dict:
        """Public: oka vote (IP ki oka vote per day)."""
        pick = self._poll_question()
        q = pick["q"]
        try:
            qid = int(payload.get("qid") or 0)
            choice = int(payload.get("choice", -1))
        except (TypeError, ValueError):
            raise engine.ExamError("Vote format tappu", "bad-vote", 400)
        if qid != q["id"]:
            raise engine.ExamError("Ee poll marindi — page refresh chesi malli vote cheyandi",
                                   "stale-poll", 409)
        if not (0 <= choice < len(q["options"])):
            raise engine.ExamError("Choice valid kaadu", "bad-choice", 400)
        ip = str(payload.get("_ip") or payload.get("ip") or "")[:64]
        already = self.store.has_poll_vote(pick["day"], qid, ip)
        if not already:
            self.store.record_poll_vote(pick["day"], qid, choice, ip)
        counts = self.store.poll_vote_counts(pick["day"], qid)
        size = len(q["options"])
        counts = (counts + [0] * size)[:size]
        return {"ok": True, "votes": counts, "total": sum(counts),
                "correct_index": q["correct_index"], "already_voted": already,
                "explanation": q.get("explanation", ""), "day": pick["day"]}

    # ------------------------------------------------- v47: admin ad manager
    @staticmethod
    def _ads_path() -> Path:
        p = (os.environ.get("ADS_INVENTORY_PATH") or "").strip()
        if p:
            return Path(p)
        return Path(__file__).resolve().parent.parent / "ads" / "inventory.json"

    @staticmethod
    def _read_inventory(path: Path) -> Dict:
        if not path.exists():
            return {"version": 1, "policy": {}, "ads": []}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise engine.ExamError(f"Ad inventory chadavaleka poyindi: {exc}",
                                   "ads-read", 500)
        if isinstance(raw, list):
            return {"version": 1, "policy": {}, "ads": raw}
        if not isinstance(raw, dict):
            return {"version": 1, "policy": {}, "ads": []}
        raw.setdefault("version", 1)
        raw.setdefault("policy", {})
        raw.setdefault("ads", [])
        if not isinstance(raw["ads"], list):
            raw["ads"] = []
        return raw

    def admin_ads(self, key: str) -> Dict:
        self.require_admin(key)
        path = self._ads_path()
        inv = self._read_inventory(path)
        return {"ok": True, "path": str(path), "version": inv.get("version", 1),
                "policy": inv.get("policy", {}), "ads": inv.get("ads", [])}

    def upsert_ad(self, key: str, payload: Dict) -> Dict:
        """Create/update an ad in ads/inventory.json (bot next post lo vaadutundi)."""
        self.require_admin(key)
        ad = self._validate_ad(payload)
        path = self._ads_path()
        inv = self._read_inventory(path)
        ads = [a for a in inv.get("ads", []) if not (isinstance(a, dict) and a.get("id") == ad["id"])]
        ads.append(ad)
        inv["ads"] = ads
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
            os.replace(tmp, path)
        except OSError as exc:
            raise engine.ExamError(f"Ad save avvaledu: {exc}", "ads-write", 500)
        return {"ok": True, "ad": ad, "count": len(ads)}

    def delete_ad(self, key: str, ad_id: str) -> Dict:
        self.require_admin(key)
        path = self._ads_path()
        inv = self._read_inventory(path)
        before = len(inv.get("ads", []))
        inv["ads"] = [a for a in inv.get("ads", [])
                      if not (isinstance(a, dict) and a.get("id") == ad_id)]
        if len(inv["ads"]) == before:
            raise engine.ExamError("Ee id tho ad ledu", "ads-missing", 404)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".json.tmp")
            tmp.write_text(json.dumps(inv, ensure_ascii=False, indent=2) + "\n",
                           encoding="utf-8")
            os.replace(tmp, path)
        except OSError as exc:
            raise engine.ExamError(f"Ad delete avvaledu: {exc}", "ads-write", 500)
        return {"ok": True, "count": len(inv["ads"])}

    @staticmethod
    def _validate_ad(payload: Dict) -> Dict:
        def s(key: str, default: str = "", limit: int = 300) -> str:
            return str(payload.get(key, default) or default).strip()[:limit]

        ad_id = s("id", limit=52).lower()
        if not re.fullmatch(r"[a-z0-9][a-z0-9\-_]{2,51}", ad_id):
            raise engine.ExamError(
                "Ad id: chinna aksharalu/sankhyalu/hyphen matrame (3-52)",
                "bad-ad-id", 400)
        title = s("title", limit=140)
        if len(title) < 8:
            raise engine.ExamError("Ad title kaneesam 8 aksharalu kavali", "bad-ad-title", 400)
        atype = s("type", "college_banner", limit=30).lower()
        if atype not in ("college_banner", "shop", "service", "coaching", "sponsorship"):
            raise engine.ExamError(
                "type: college_banner | shop | service | coaching | sponsorship",
                "bad-ad-type", 400)
        layout = s("layout", "banner", limit=12).lower()
        if layout not in ("banner", "card", "auto"):
            raise engine.ExamError("layout: banner | card | auto", "bad-ad-layout", 400)
        link = s("link", limit=500)
        if not re.fullmatch(r"https?://[^\s]+", link):
            raise engine.ExamError(
                "link http/https tho start avvali (javascript: vaddu — safety)",
                "bad-ad-link", 400)
        image = s("image", limit=500)
        if image and not re.fullmatch(r"https?://[^\s]+", image):
            raise engine.ExamError("image URL http/https matrame", "bad-ad-image", 400)
        for dkey in ("start", "end"):
            v = s(dkey, limit=10)
            if v and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
                raise engine.ExamError(f"{dkey}: YYYY-MM-DD format lo ivvandi",
                                       f"bad-ad-{dkey}", 400)
        raw_pl = payload.get("placements")
        if isinstance(raw_pl, (list, tuple)):
            placements = [str(x).strip() for x in raw_pl if str(x).strip()]
        elif raw_pl:
            placements = [p.strip() for p in str(raw_pl).split(",") if p.strip()]
        else:
            placements = ["top", "mid", "bottom"]
        placements = placements[:6]

        return {
            "id": ad_id,
            "name": s("name", title, limit=80) or title,
            "type": atype,
            "layout": layout,
            "active": bool(payload.get("active", True)),
            "demo": bool(payload.get("demo", False)),
            "label": s("label", limit=40),
            "name": s("name", limit=140) or title,
            "title": title,
            "description": s("description", limit=300),
            "cta": s("cta", "Know More", limit=40) or "Know More",
            "image": image,
            "link": link,
            "categories": s("categories", "", limit=200),
            "placements": placements,
            "start": s("start", limit=10),
            "end": s("end", limit=10),
        }

    def _require_session(self, payload: Dict) -> Dict:
        session = self.store.session_by_token(payload.get("token", ""))
        if not session:
            raise engine.ExamError("Session expire ayyindi — malli join avvandi",
                                   "not_found", 404)
        return session


    # ------------------------------------------------------- leads (v54 money)
    LEAD_INTERESTS = ("jobs", "scholarships", "college", "coaching", "exams", "other")

    @staticmethod
    def _clean_phone(raw: Any) -> str:
        digits = re.sub(r"\D", "", str(raw or ""))
        if digits.startswith("91") and len(digits) == 12:
            digits = digits[2:]
        elif digits.startswith("0") and len(digits) == 11:
            digits = digits[1:]
        return digits

    def save_lead(self, payload: Dict) -> Dict:
        """Public: ఉచిత సమాచారం అభ్యర్థన (job/college alerts). Ads la revenue line."""
        name = re.sub(r"\s+", " ", str(payload.get("name") or "")).strip()
        phone = self._clean_phone(payload.get("phone"))
        interest = str(payload.get("interest") or "jobs").strip().lower()
        city = re.sub(r"\s+", " ", str(payload.get("city") or "")).strip()
        source = re.sub(r"[^a-z_]", "", str(payload.get("source") or "site").lower())[:20] or "site"
        note = re.sub(r"\s+", " ", str(payload.get("note") or "")).strip()
        ip = str(payload.get("ip") or payload.get("_ip") or "")[:64]
        spammy = bool(str(payload.get("website") or payload.get("url") or "").strip())

        if len(name) < 2:
            raise engine.ExamError("పేరు రాయండి (కనీసం 2 అక్షరాలు)", "lead-name", 400)
        if not re.fullmatch(r"[6-9]\d{9}", phone or ""):
            raise engine.ExamError("10 అంకెల మొబైల్ నంబర్ ఇవ్వండి (ఉదా: 9876543210)",
                                   "lead-phone", 400)
        if interest not in self.LEAD_INTERESTS:
            interest = "other"
        if city and len(city) < 2:
            city = ""
        if not spammy and self.store.lead_ip_count(ip, hours=1) >= 5:
            raise engine.ExamError("కొద్దిసేపటి తర్వాత మళ్లీ ప్రయత్నించండి",
                                   "lead-throttle", 429)

        if spammy:
            row = self.store.save_lead(name, phone, interest, city, source, note, ip)
            self.store.set_lead_status(row["id"], "spam")
            return {"ok": True, "id": row["id"], "duplicate": False,
                    "message": "ధన్యవాదాలు! మేము సంప్రదిస్తాము."}

        if self.store.lead_phone_seen(phone, hours=24):
            return {"ok": True, "duplicate": True,
                    "message": "ఈ నంబర్ ఇప్పటికే నమోదైంది — మేము త్వరలో సంప్రదిస్తాము."}

        row = self.store.save_lead(name, phone, interest, city, source, note, ip)
        log.info("lead #%s (%s) %s", row["id"], interest, phone[-4:].rjust(4, "*"))
        return {"ok": True, "id": row["id"], "duplicate": False,
                "message": "ధన్యవాదాలు! ఉద్యోగ/పరీక్ష సమాచారం మీకు పంపుతాము."}

    def admin_leads(self, key: str, limit: int = 200, status: str = "") -> Dict:
        self.require_admin(key)
        rows = self.store.list_leads(limit=limit, status=status)
        masked = []
        for r in rows:
            d = dict(r)
            d.pop("ip", None)
            d["phone"] = d.get("phone", "")
            masked.append(d)
        return {"ok": True, "count": len(masked), "stats": self.store.lead_stats(),
                "leads": masked}

    def set_lead_status(self, key: str, lead_id: Any, status: str) -> Dict:
        self.require_admin(key)
        try:
            lid = int(lead_id or 0)
        except (TypeError, ValueError):
            raise engine.ExamError("lead id number ga undali", "bad-lead-id", 400)
        try:
            changed = self.store.set_lead_status(lid, str(status or "").strip().lower())
        except ValueError as exc:
            raise engine.ExamError(str(exc), "bad-lead-status", 400)
        if not changed:
            raise engine.ExamError("Ee id tho lead ledu", "lead-missing", 404)
        return {"ok": True, "id": lid, "status": status}

    def export_leads(self, key: str) -> tuple:
        self.require_admin(key)
        rows = self.store.list_leads(limit=5000)
        cols = ["id", "created_at", "name", "phone", "interest", "city", "source",
                "status", "note"]
        lines = [",".join(cols)]
        for r in rows:
            vals = []
            for c in cols:
                v = str(r.get(c, "")).replace('"', '""')
                vals.append(f'"{v}"' if any(ch in v for ch in ',"\n') else v)
            lines.append(",".join(vals))
        return "\n".join(lines) + "\n", "studentup-leads.csv"


# ------------------------------------------------------------------ HTTP layer

class Handler(BaseHTTPRequestHandler):
    server_version = "ExamPortal/1.0"
    api: Api = None            # set by make_server
    store: Store = None

    # ----------------------------------------------------------- responses
    def _send(self, status: int, body: bytes, content_type: str,
              extra: Optional[Dict[str, str]] = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def json_out(self, data: Any, status: int = 200, cors: bool = False) -> None:
        extra = {"Cache-Control": "no-store"}
        if cors:  # v47: public poll endpoints — website (different port/origin) fetch cheyyagaladu
            extra["Access-Control-Allow-Origin"] = "*"
            extra["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            extra["Access-Control-Allow-Headers"] = "Content-Type"
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"),
                   JSON_HEADERS["Content-Type"], extra)

    def html_out(self, html: str, status: int = 200) -> None:
        self._send(status, html.encode("utf-8"), "text/html; charset=utf-8",
                   {"Cache-Control": "no-store"})

    def csv_out(self, text: str, filename: str) -> None:
        self._send(200, text.encode("utf-8-sig"),
                   "text/csv; charset=utf-8",
                   {"Content-Disposition": f'attachment; filename="{filename}"'})

    def redirect(self, location: str) -> None:
        self._send(302, b"", "text/plain", {"Location": location})

    def log_message(self, fmt: str, *args: Any) -> None:  # quieter logs
        log.debug("%s - %s", self.address_string(), fmt % args)

    # -------------------------------------------------------------- helpers
    def body_json(self) -> Dict:
        length = int(self.headers.get("Content-Length") or 0)
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        try:
            return json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            raise engine.ExamError("JSON body tappu", "bad_request", 400)

    def query(self) -> Dict[str, str]:
        qs = parse_qs(urlparse(self.path).query)
        return {k: v[0] for k, v in qs.items() if v}

    def client_ip(self) -> str:
        fwd = self.headers.get("X-Forwarded-For", "")
        if fwd:
            return fwd.split(",")[0].strip()
        return self.client_address[0] if self.client_address else ""

    # ---------------------------------------------------------------- GET
    def do_GET(self) -> None:  # noqa: N802
        try:
            self._route_get()
        except engine.ExamError as exc:
            self.json_out({"error": str(exc), "code": exc.code}, exc.status)
        except Exception:  # noqa: BLE001
            log.exception("GET %s failed", self.path)
            self.json_out({"error": "Server lo internal problem — malli try cheyandi"},
                          500)

    def _route_get(self) -> None:
        path = urlparse(self.path).path
        q = self.query()

        if path == "/healthz":
            self.json_out({"ok": True, "time": now_iso()})
            return
        if path == "/favicon.ico":
            self._send(204, b"", "image/x-icon")
            return
        if path == "/":
            self.html_out(ui.landing_html())
            return
        if path == "/admin":
            self.html_out(ui.admin_html())
            return
        if path.startswith("/manage/"):
            self.html_out(ui.manage_html())
            return
        if path.startswith("/exam/"):
            self.html_out(ui.student_html())
            return

        # --- admin API (GET)
        if path == "/api/admin/exams":
            self.json_out(self.api.admin_exams(q.get("key", "")))
            return
        m = _match(path, "/api/admin/exam/{code}")
        if m:
            self.json_out(self.api.admin_exam(m["code"], q.get("key", "")))
            return
        m = _match(path, "/api/admin/exam/{code}/roster")
        if m:
            self.json_out(self.api.get_roster(m["code"], q.get("key", "")))
            return
        m = _match(path, "/api/admin/exam/{code}/export/{kind}")
        if m:
            kind = m["kind"].replace(".csv", "")
            text, name = self.api.export(m["code"], q.get("key", ""), kind)
            self.csv_out(text, name)
            return

        # --- student API (GET)
        m = _match(path, "/api/exam-info/{code}")
        if m:
            self.json_out(self.api.exam_info(m["code"]))
            return
        if path == "/api/session":
            self.json_out(self.api.session_state(q.get("token", "")))
            return

        if path == "/poll/today":
            self.json_out(self.api.today_poll(), cors=True)
            return
        if path == "/api/admin/leads":
            self.json_out(self.api.admin_leads(q.get("key", ""),
                                               int(q.get("limit", 200) or 200),
                                               q.get("status", "")))
            return
        if path in ("/api/admin/leads/export.csv", "/api/admin/leads.csv"):
            text, name = self.api.export_leads(q.get("key", ""))
            self.csv_out(text, name)
            return
        if path == "/api/admin/ads":
            self.json_out(self.api.admin_ads(self.query().get("key", "")))
            return

        self.json_out({"error": "Page dorakaledu", "path": path}, 404)

    # --------------------------------------------------------------- POST
    def do_OPTIONS(self) -> None:  # noqa: N802 — v47 CORS preflight (public poll)
        self._send(204, b"", "text/plain", {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        })

    def do_POST(self) -> None:  # noqa: N802
        try:
            self._route_post()
        except engine.ExamError as exc:
            self.json_out({"error": str(exc), "code": exc.code}, exc.status)
        except Exception:  # noqa: BLE001
            log.exception("POST %s failed", self.path)
            self.json_out({"error": "Server lo internal problem — malli try cheyandi"},
                          500)

    def _route_post(self) -> None:
        path = urlparse(self.path).path
        body = self.body_json()
        if self.client_ip() and "ip" not in body:
            body["ip"] = self.client_ip()

        if path == "/api/admin/verify":
            self.api.require_admin(body.get("key", ""))
            self.json_out({"ok": True, "server_now": now_iso()})
            return
        if path == "/api/admin/exams":
            self.json_out(self.api.create_exam(body.get("key", ""), body))
            return

        handlers = {
            "/api/admin/exam/{code}/settings": lambda m, b:
                self.api.update_settings(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/questions": lambda m, b:
                self.api.add_questions(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/roster": lambda m, b:
                self.api.set_roster(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/publish": lambda m, b:
                self.api.publish(m["code"], b.get("key", "")),
            "/api/admin/exam/{code}/unpublish": lambda m, b:
                self.api.unpublish(m["code"], b.get("key", "")),
            "/api/admin/exam/{code}/start": lambda m, b:
                self.api.start(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/close": lambda m, b:
                self.api.close(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/extend": lambda m, b:
                self.api.extend(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/late-join": lambda m, b:
                self.api.late_join(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/announce": lambda m, b:
                self.api.announce(m["code"], b.get("key", ""), b),
            "/api/admin/exam/{code}/results/publish": lambda m, b:
                self.api.publish_results(m["code"], b.get("key", "")),
            "/api/admin/exam/{code}/question/{qid}/drop": lambda m, b:
                self.api.drop_question(m["code"], b.get("key", ""), int(m["qid"]), b),
            "/api/admin/exam/{code}/question/{qid}/delete": lambda m, b:
                self.api.delete_question(m["code"], b.get("key", ""), int(m["qid"]), b),
        }
        for pattern, fn in handlers.items():
            m = _match(path, pattern)
            if m:
                self.json_out(fn(m, body))
                return

        if path == "/api/join":
            self.json_out(self.api.join(body))
            return
        student = {
            "/api/session/heartbeat": self.api.heartbeat,
            "/api/session/answer": self.api.answer,
            "/api/session/tabswitch": self.api.tab_switch,
            "/api/session/submit": self.api.submit,
        }
        if path in student:
            self.json_out(student[path](body))
            return

        if path == "/lead":
            self.json_out(self.api.save_lead(body), cors=True)
            return
        if path == "/api/admin/lead/status":
            self.json_out(self.api.set_lead_status(body.get("key", ""),
                                                   body.get("id"),
                                                   body.get("status", "")))
            return
        if path == "/poll/vote":
            body["_ip"] = self.client_ip()
            self.json_out(self.api.vote_poll(body), cors=True)
            return
        if path == "/api/admin/ads":
            self.json_out(self.api.upsert_ad(body.get("key", ""), body))
            return
        if path == "/api/admin/ads/delete":
            self.json_out(self.api.delete_ad(body.get("key", ""), str(body.get("id") or "")))
            return

        self.json_out({"error": "Endpoint dorakaledu", "path": path}, 404)

    do_HEAD = do_GET


def _match(path: str, pattern: str) -> Optional[Dict[str, str]]:
    """Tiny path matcher: '/api/x/{code}/y' → {'code': 'ABC'}."""
    p_parts = [p for p in path.strip("/").split("/") if p]
    t_parts = [p for p in pattern.strip("/").split("/") if p]
    if len(p_parts) != len(t_parts):
        return None
    out: Dict[str, str] = {}
    for got, want in zip(p_parts, t_parts):
        if want.startswith("{") and want.endswith("}"):
            out[want[1:-1]] = unquote(got)
        elif got != want:
            return None
    return out


# ------------------------------------------------------------------- server

class ExamHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def make_server(host: str = "0.0.0.0", port: int = 8080,
                db_path: Path | str = DEFAULT_DB,
                admin_key: str = "") -> Tuple[ExamHTTPServer, Api]:
    store = Store(db_path)
    key = load_admin_key(admin_key)
    api = Api(store, key)

    handler = type("BoundHandler", (Handler,), {"api": api, "store": store})
    httpd = ExamHTTPServer((host, port), handler)
    return httpd, api


def sweeper_loop(store: Store, stop: threading.Event, interval: float = 5.0) -> None:
    """Auto-close / auto-start / closing-soon — admin marchipoyina kuda safe."""
    while not stop.wait(interval):
        try:
            result = engine.sweep(store)
            if result["actions"]:
                log.info("sweeper: %s", ", ".join(result["actions"]))
        except Exception:  # noqa: BLE001
            log.exception("sweeper error (continuing)")


def run_server(host: str = "0.0.0.0", port: int = 8080,
               db_path: Path | str = DEFAULT_DB, admin_key: str = "",
               base_url: str = "") -> int:
    httpd, api = make_server(host, port, db_path, admin_key)
    if base_url:
        notify.PUBLIC_URL = base_url.rstrip("/")
    elif not notify.PUBLIC_URL:
        notify.PUBLIC_URL = os.environ.get("EXAM_PUBLIC_URL", "").rstrip("/")

    stop = threading.Event()
    threading.Thread(target=sweeper_loop, args=(api.store, stop), daemon=True).start()

    banner = f"""
======================================================================
  🎓 EXAM PORTAL running  (v39)
======================================================================
  Admin console : http://{host}:{port}/admin
  Admin key     : {api.admin_key}
                  (file: {KEY_FILE})
  Students      : http://{host}:{port}/exam/<EXAM-CODE>
                  — leda admin console lo share link copy cheyandi
  Database      : {api.store.db_path}
  Notifications : Telegram/webhook env vars set cheste automatic
                  (EXAM_TELEGRAM_BOT_TOKEN, EXAM_TELEGRAM_CHAT_ID,
                   EXAM_WEBHOOK_URL, EXAM_PUBLIC_URL)
  Auto-close    : ON — time ayyina exams automatic close + submit
======================================================================
"""
    print(banner, flush=True)
    log.info("Listening on %s:%s", host, port)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down…")
    finally:
        stop.set()
        httpd.server_close()
    return 0


def main(argv: Optional[list] = None) -> int:
    parser = argparse.ArgumentParser(description="studentup.in Exam Portal")
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--db", default=str(DEFAULT_DB))
    parser.add_argument("--admin-key", default="")
    parser.add_argument("--base-url", default="",
                        help="public URL (share links + notifications kosam)")
    parser.add_argument("--test-channels", action="store_true",
                        help="Telegram/webhook test ping pampi exit")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    if args.test_channels:
        print(json.dumps(notify.test_channels(), indent=2, ensure_ascii=False))
        return 0
    return run_server(args.host, args.port, Path(args.db), args.admin_key,
                      args.base_url)


if __name__ == "__main__":
    raise SystemExit(main())
