"""v39 Exam Portal — demo seed (college ki ippude try cheyyadaniki).

`python run.py --exam-portal-demo` → sample exam + 6 students + 3 submitted
attempts seed avutayi, appudu server start avutundi. Meeru console lo
START/CLOSE, results, exports anni ventane chudachu (fake data — production
ki kotha exam create cheyandi).
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from . import engine, notify
from .store import Store, DEFAULT_DB

DEMO_QUESTIONS = """1. తెలంగాణ రాష్ట్ర రాజధాని ఏది?
A) వరంగల్
B) హైదరాబాద్
C) కరీంనగర్
D) నిజామాబాద్
సరైన జవాబు: B
వివరణ: హైదరాబాద్ తెలంగాణ రాష్ట్ర రాజధాని.

2. భారత రాజ్యాంగంలో ప్రాథమిక హక్కులు ఎన్ని అధికరణాలలో ఉన్నాయి?
A) అధికరణాలు 12-35
B) అధికరణాలు 14-32
C) అధికరణాలు 5-11
D) అధికరణాలు 36-51
సరైన జవాబు: A
వివరణ: పార్ట్ III (అధికరణాలు 12-35)లో ప్రాథమిక హక్కులు ఉన్నాయి.

3. 'జన గణ మన' రచయిత ఎవరు?
A) బంకిం చంద్ర చటర్జీ
B) రవీంద్రనాథ్ టాగూర్
C) సరోజినీ నాయుడు
D) సుభాష్ చంద్ర బోస్
సరైన జవాబు: B
వివరణ: రవీంద్రనాథ్ టాగూర్ రచించారు — జనవరి 24, 1950 నుండి జాతీయ గీతం.

4. TSPSC పూర్తి రూపం ఏమిటి?
A) తెలంగాణ స్టేట్ పబ్లిక్ సర్వీస్ కమిషన్
B) తెలంగాణ స్టేట్ పోలీస్ సర్వీస్ కమిషన్
C) తెలంగాణ స్టాఫ్ సెలక్షన్ కమిషన్
D) తెలంగాణ స్టేట్ ప్రైవేట్ సర్వీస్ కమిషన్
సరైన జవాబు: A
వివరణ: TSPSC = తెలంగాణ స్టేట్ పబ్లిక్ సర్వీస్ కమిషన్.

5. NSP స్కాలర్‌షిప్ పోర్టల్ అధికారిక వెబ్‌సైట్ ఏది?
A) scholarships.gov.in
B) nsp.gov.in
C) scholarshipindia.in
D) education.gov.in
సరైన జవాబు: A
వివరణ: నేషనల్ స్కాలర్‌షిప్ పోర్టల్ = scholarships.gov.in.
"""

DEMO_ROSTER = """21B01A0501, Ravi Kumar
21B01A0502, Sita Devi
21B01A0503, Anand Reddy
21B01A0504, Priya Sharma
21B01A0505, Kiran Yadav
21B01A0506, Meghana Rao
"""


def seed(store: Store, admin_key: str = "") -> Dict:
    """Create (or reuse) the demo exam. Returns {exam, api-ish info, log}."""
    log_lines = []
    existing = store.exam_by_code("DEMO01")
    if existing and existing["status"] in ("live", "closed"):
        log_lines.append("DEMO01 already irukkundi — kotha demo create chestunnam (DEMO02)")
        existing = None

    if existing:
        exam = existing
        log_lines.append("DEMO01 exam reuse (draft/published)")
    else:
        exam = store.create_exam(
            college="Demo Degree College, Hyderabad",
            title="Internal Test 1 — General Knowledge (Demo)",
            subject="GK / Current Affairs",
            exam_date="Today",
            instructions=("1. Roll number correct ga type cheyandi\n"
                          "2. Prathi question ki okka option select cheyandi\n"
                          "3. Time ayyaka automatic submit avutundi\n"
                          "4. Tappu answer ki 1/4 mark minus (negative marking)\n"
                          "5. Ee page ni close cheyyakandi"),
            duration_min=15, per_q_marks=1, negative_marks=0.25,
            pass_marks=3, roster_required=True, allow_late_join=True,
            auto_start_all_joined=False)
        log_lines.append(f"Exam created: {exam['code']}")
        items, errors = engine.parse_questions(DEMO_QUESTIONS)
        if errors:
            log_lines.extend(f"  ⚠️ {e}" for e in errors)
        store.add_questions(exam["id"], items)
        log_lines.append(f"Questions added: {len(items)}")
        store.set_roster(exam["id"], [
            {"roll": line.split(",")[0], "name": line.split(",")[1].strip()}
            for line in DEMO_ROSTER.strip().splitlines()])
        log_lines.append("Roster: 6 students")
        report = engine.validate_exam(store, exam["id"])
        log_lines.append(f"Validation: {'OK ✔' if report['ok'] else report['blockers']}")
        if report["ok"]:
            engine.publish_exam(store, exam["id"])
            exam = store.get_exam(exam["id"])
            log_lines.append("Published ✔ (students join cheyyagalaru)")

    # simulate 3 real attempts so results/analysis have data
    if exam["status"] == "published":
        engine.start_exam(store, exam["id"])
        exam = store.get_exam(exam["id"])
        log_lines.append("Started (demo) — timer 15 min")
        # (roll, correct count, wrong count) — paper position lo text-anchored
        # answers (option shuffle unna kuda 100% correct scoring)
        attempts = [("21B01A0501", 5, 0),      # 5.00
                    ("21B01A0502", 4, 1),      # 3.75 (negative 0.25)
                    ("21B01A0503", 3, 2)]      # 2.50
        for roll, n_ok, n_bad in attempts:
            session = engine.join_exam(store, exam["code"], roll,
                                       name="")["session_id"]
            s = store.session(session)
            paper = engine.paper_for(store, s)
            for i, q in enumerate(paper):
                orig = store.question(q["id"])
                if i < n_ok:
                    pos = q["options"].index(orig["options"][orig["correct_index"]])
                elif i < n_ok + n_bad:
                    pos = next((k for k, t in enumerate(q["options"])
                                if t != orig["options"][orig["correct_index"]]), None)
                    if pos is None:
                        continue
                else:
                    continue
                engine.save_answer(store, store.session(session), q["id"], pos, None)
            engine.submit_session(store, store.session(session))
            log_lines.append(f"  {roll} submitted (demo attempt)")
        engine.publish_results(store, exam["id"], notify_channels=False)
        log_lines.append("Results published (demo)")
        exam = store.get_exam(exam["id"])

    return {
        "exam": exam,
        "code": exam["code"],
        "student_link": notify.exam_link(exam),
        "manage_link": f"/manage/{exam['code']}?key={exam['admin_token']}",
        "log": log_lines,
    }


def run_demo(db_path: Path | str = DEFAULT_DB, admin_key: str = "") -> int:
    store = Store(db_path)
    info = seed(store)
    print("=" * 66)
    print("  🎓 EXAM PORTAL DEMO SEED")
    print("=" * 66)
    for line in info["log"]:
        print(f"  {line}")
    print(f"\n  Exam code     : {info['code']}")
    print(f"  Student link  : {info['student_link']}")
    print(f"  Manage link   : {info['manage_link']}")
    print("=" * 66)
    return 0
