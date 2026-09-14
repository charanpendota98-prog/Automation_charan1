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

DEMO_QUESTIONS = """1. Capital of Telangana state emiti?
A) Warangal
B) Hyderabad
C) Karimnagar
D) Nizamabad
Answer: B
Explanation: Hyderabad Telangana rajadhani.

2. Indian Constitution lo Fundamental Rights enni Articles lo unnayi?
A) Articles 12-35
B) Articles 14-32
C) Articles 5-11
D) Articles 36-51
Answer: A
Explanation: Part III (Articles 12-35) lo Fundamental Rights unnayi.

3. 'Jana Gana Mana' rachayita evaru?
A) Bankim Chandra Chatterjee
B) Rabindranath Tagore
C) Sarojini Naidu
D) Subhash Chandra Bose
Answer: B
Explanation: Rabindranath Tagore racharu — January 24, 1950 nunchi national anthem.

4. TSPSC full form emiti?
A) Telangana State Public Service Commission
B) Telangana State Police Service Commission
C) Telangana Staff Selection Commission
D) Telangana State Private Service Commission
Answer: A
Explanation: TSPSC = Telangana State Public Service Commission.

5. NSP scholarship portal official website edi?
A) scholarships.gov.in
B) nsp.gov.in
C) scholarshipindia.in
D) education.gov.in
Answer: A
Explanation: National Scholarship Portal = scholarships.gov.in.
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
