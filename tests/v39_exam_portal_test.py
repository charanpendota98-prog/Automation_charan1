"""v39 EXAM PORTAL tests — real HTTP round-trips against a live server.

Sections:
  1. Store: schema, WAL, roll normalization, unique code/session guards
  2. Question parser: blocks / CSV / JSON + all validation errors (no silent skip)
  3. Validation + publish gate (blockers) + unpublish
  4. START: waiting sessions activated, same end time, double-start blocked
  5. Student join: resume same device, duplicate device blocked, roster guard,
     closed/late-join guards, server-authoritative timer
  6. Answers: save/clear/flag, out-of-range rejected, live-only guard
  7. Submit: idempotent, scoring (negative marks), rank, result visibility modes
  8. CLOSE: auto-submit pending, idempotent, results, exports CSV
  9. Question drop → marks recalculate + audit; integrity (tab switch)
 10. Sweeper: auto-close on time over, closing-soon ping, auto-start when all joined
 11. Notifications: in-app log + templates + webhook (fake) — exam never blocks
 12. HTTP end-to-end: admin create → paste questions → roster → publish → start →
     student join → answer → submit → close → export; plus auth/404/validation
"""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from exam_portal import demo, engine, notify, server, ui  # noqa: E402
from exam_portal import store as store_mod  # noqa: E402

BASE = "http://127.0.0.1:{port}"


def http(method: str, url: str, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            raw = resp.read()
            ctype = resp.headers.get("Content-Type", "")
            if "json" in ctype:
                return resp.status, json.loads(raw.decode()), dict(resp.headers)
            return resp.status, raw.decode("utf-8", "ignore"), dict(resp.headers)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw.decode()), dict(exc.headers)
        except ValueError:
            return exc.code, raw.decode("utf-8", "ignore"), dict(exc.headers)


def seed_exam(store, **over):
    exam = store.create_exam(**{
        "college": "Test College", "title": "Unit Test — GK", "subject": "GK",
        "instructions": "Rules: 1) roll type cheyandi 2) time 10 min",
        "duration_min": 10, "per_q_marks": 1, "negative_marks": 0.25,
        "pass_marks": 2, "roster_required": True, **over})
    questions = [
        {"text": "Capital of Telangana?", "options": ["Warangal", "Hyderabad"],
         "correct_index": 1, "explanation": "Hyderabad"},
        {"text": "2 + 2 = ?", "options": ["3", "4", "5", "6"], "correct_index": 1},
        {"text": "TSPSC full form?", "options": ["Telangana State Public Service Commission",
                                                 "Telangana Staff Selection Commission"],
         "correct_index": 0},
        {"text": "NSP portal?", "options": ["scholarships.gov.in", "nsp.in"],
         "correct_index": 0},
        {"text": "National anthem writer?", "options": ["Tagore", "Bankim"],
         "correct_index": 0},
    ]
    store.add_questions(exam["id"], questions)
    store.set_roster(exam["id"], [{"roll": f"R{i:03d}", "name": f"Student {i}"}
                                  for i in range(1, 5)])
    return store.get_exam(exam["id"])


def main():
    tmp = Path(tempfile.mkdtemp(prefix="v39_test_"))
    db = tmp / "exam.db"
    store = store_mod.Store(db)
    print("v39 EXAM PORTAL TESTS:")

    # ---------------------------------------------------------------- 1
    assert db.exists()
    with store.connect() as conn:
        mode = conn.execute("PRAGMA journal_mode").fetchone()[0]
        tables = {r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert mode.lower() == "wal", mode
    assert {"exams", "questions", "roster", "sessions", "answers", "events",
            "notifications"} <= tables, tables
    assert store_mod.normalize_roll(" 21b01a0501 ") == "21B01A0501"
    assert store_mod.normalize_roll("r 001") == "R 001"
    a = store.create_exam(title="A", duration_min=5)
    b = store.create_exam(title="B", duration_min=5)
    assert a["code"] != b["code"] and len(a["code"]) == 6
    assert store.exam_by_code(a["code"].lower())["id"] == a["id"]
    assert store.exam_by_token(a["admin_token"])["id"] == a["id"]
    print(f"  1. store schema + WAL + code/token lookup ✔  ({mode})")

    # ---------------------------------------------------------------- 2
    blocks = """1. Capital of Telangana?
A) Warangal
B) Hyderabad
C) Karimnagar
D) Nizamabad
Answer: B
Explanation: Hyderabad is the capital.

2) 2 + 2 = ?
(a) 3
(b) 4
Answer: b
"""
    qs, errs = engine.parse_questions(blocks)
    assert len(qs) == 2 and not errs, (qs, errs)
    assert qs[0]["options"] == ["Warangal", "Hyderabad", "Karimnagar", "Nizamabad"]
    assert qs[0]["correct_index"] == 1 and "capital" in qs[0]["explanation"]
    assert qs[1]["correct_index"] == 1, qs[1]
    csv_text = ("Question,Opt A,Opt B,Opt C,Opt D,Answer,Explanation\n"
                "2+2=?,3,4,5,6,B,four\n"
                "Capital?,Warangal,Hyderabad,,,B,hyd\n")
    qs2, errs2 = engine.parse_questions(csv_text)
    assert len(qs2) == 2 and not errs2, (qs2, errs2)
    assert qs2[0]["options"] == ["3", "4", "5", "6"] and qs2[0]["correct_index"] == 1
    assert qs2[1]["options"] == ["Warangal", "Hyderabad"], qs2[1]
    json_text = json.dumps([{"text": "Q1?", "options": ["a", "b"], "correct_index": 1},
                            {"text": "Q2?", "options": ["x", "y", "z"], "answer": "C"}])
    qs3, errs3 = engine.parse_questions(json_text)
    assert len(qs3) == 2 and not errs3
    assert qs3[1]["correct_index"] == 2
    bad, bad_errs = engine.parse_questions(
        "1. One option only?\nA) only\nAnswer: A\n\n"
        "2. Duplicate?\nA) same\nB) same\nAnswer: A\n\n"
        "3. No answer set?\nA) x\nB) y\n")
    assert len(bad) == 0 and len(bad_errs) == 3, (bad, bad_errs)
    assert any("minimum 2 options" in e for e in bad_errs)
    assert any("duplicate options" in e for e in bad_errs)
    assert any("correct answer set kaledu" in e for e in bad_errs)
    assert engine.parse_questions("")[1]
    assert engine.parse_questions("{not json")[1][0].startswith("JSON parse error")
    print("  2. parser: blocks/CSV/JSON + 6 error classes (no silent skip) ✔")

    # ---------------------------------------------------------------- 3
    exam = seed_exam(store)
    report = engine.validate_exam(store, exam["id"])
    assert report["ok"] and report["questions"] == 5 and report["total_marks"] == 5
    assert any("Negative marking" in w for w in report["warnings"])
    empty = store.create_exam(title="Empty exam")
    rep2 = engine.validate_exam(store, empty["id"])
    assert not rep2["ok"] and any("Questions 0" in b for b in rep2["blockers"])
    try:
        engine.publish_exam(store, empty["id"])
        raise AssertionError("empty publish should fail")
    except engine.ExamError as exc:
        assert exc.code == "validation"
    bad_pass = store.create_exam(title="Bad pass", pass_marks=99, duration_min=5)
    store.add_questions(bad_pass["id"], [{"text": "q", "options": ["a", "b"],
                                          "correct_index": 0}])
    rep3 = engine.validate_exam(store, bad_pass["id"])
    assert any("Pass marks" in b for b in rep3["blockers"])
    out = engine.publish_exam(store, exam["id"])
    assert out["exam"]["status"] == "published"
    assert engine.unpublish_exam(store, exam["id"])["status"] == "draft"
    engine.publish_exam(store, exam["id"])
    print(f"  3. validation blockers + publish/unpublish ✔  ({len(report['blockers'])} blockers)")

    # ---------------------------------------------------------------- 4
    s1 = engine.join_exam(store, exam["code"], "R001")
    s2 = engine.join_exam(store, exam["code"], "R002", name="Student 2")
    assert s1["status"] == "waiting" and s1["remaining_sec"] == 0
    res = engine.start_exam(store, exam["id"])
    assert res["activated"] == 2 and res["duration_min"] == 10
    live = store.get_exam(exam["id"])
    assert live["status"] == "live" and live["end_at"]
    assert 570 <= store_mod.seconds_left(live["end_at"]) <= 600
    s1b = store.session(s1["session_id"])
    assert s1b["status"] == "active" and s1b["end_at"] == live["end_at"], \
        "all students must share the same end time (fair)"
    try:
        engine.start_exam(store, exam["id"])
        raise AssertionError("double start should fail")
    except engine.ExamError as exc:
        assert exc.code == "already_live"
    late = engine.join_exam(store, exam["code"], "R003")
    assert late["status"] == "active" and late["remaining_sec"] <= 600
    assert late["end_at"] == live["end_at"], "late joiner same end time — fair"
    print("  4. START activates waiting students + fair late-join timer ✔")

    # ---------------------------------------------------------------- 5
    again = engine.join_exam(store, exam["code"], "R001", token=s1["token"])
    assert again["session_id"] == s1["session_id"], "same device must resume"
    try:
        engine.join_exam(store, exam["code"], "R001", device="other phone")
        raise AssertionError("duplicate device should be blocked")
    except engine.ExamError as exc:
        assert exc.code == "duplicate_device" and exc.status == 409
    try:
        engine.join_exam(store, exam["code"], "NOT-IN-LIST")
        raise AssertionError("roster guard should block")
    except engine.ExamError as exc:
        assert exc.code == "not_in_roster"
    try:
        engine.join_exam(store, "WRONGCODE", "R001")
        raise AssertionError("bad code should 404")
    except engine.ExamError as exc:
        assert exc.status == 404
    engine.toggle_late_join(store, exam["id"], False)
    try:
        engine.join_exam(store, exam["code"], "R004")
        raise AssertionError("late join off should block")
    except engine.ExamError as exc:
        assert exc.code == "late_join_off"
    engine.toggle_late_join(store, exam["id"], True)
    draft_exam = seed_exam(store, title="Draft only")
    try:
        engine.join_exam(store, draft_exam["code"], "R001")
        raise AssertionError("draft exam join should block")
    except engine.ExamError as exc:
        assert exc.code == "not_published"
    hb = engine.heartbeat(store, store.session(s1["session_id"]))
    assert hb["status"] == "active" and hb["remaining_sec"] > 0
    server_now = store_mod.parse_iso(hb["server_now"])
    assert server_now is not None
    print("  5. join guards (resume/duplicate/roster/late/draft) + heartbeat ✔")

    # ---------------------------------------------------------------- 6
    sess = store.session(s1["session_id"])
    paper = engine.paper_for(store, sess)
    assert len(paper) == 5
    for p in paper:
        assert "correct_index" not in p and p["options"], "answer key must not leak"
    order_mixed = [p["id"] for p in paper] != sorted(p["id"] for p in paper)
    r = engine.save_answer(store, sess, paper[0]["id"], 1, None)
    assert r["saved"] and r["answered"] == 1
    engine.save_answer(store, sess, paper[1]["id"], None, True)     # flag only
    ans = store.answers(sess["id"])
    assert ans[paper[0]["id"]]["choice"] == 1
    assert ans[paper[1]["id"]]["flagged"] == 1
    engine.save_answer(store, sess, paper[1]["id"], None, False)    # unflag
    assert store.answers(sess["id"])[paper[1]["id"]]["flagged"] == 0
    engine.save_answer(store, sess, paper[0]["id"], -1, None)       # clear (unselect)
    assert store.answers(sess["id"])[paper[0]["id"]]["choice"] is None
    engine.save_answer(store, sess, paper[0]["id"], 0, None)        # re-select
    assert store.answers(sess["id"])[paper[0]["id"]]["choice"] == 0
    engine.save_answer(store, sess, paper[0]["id"], None, None)     # flag-only → answer intact
    assert store.answers(sess["id"])[paper[0]["id"]]["choice"] == 0
    engine.save_answer(store, sess, paper[0]["id"], -1, None)
    assert store.answers(sess["id"])[paper[0]["id"]]["choice"] is None
    try:
        engine.save_answer(store, sess, paper[0]["id"], 9, None)
        raise AssertionError("out of range should fail")
    except engine.ExamError:
        pass
    q_other = store.questions(draft_exam["id"])[0]["id"]
    try:
        engine.save_answer(store, sess, q_other, 0, None)
        raise AssertionError("foreign question should fail")
    except engine.ExamError as exc:
        assert exc.status == 404
    # non-live (draft) exam close is refused — draft ni close cheyyaru
    try:
        engine.close_exam(store, draft_exam["id"], reason="cleanup")
        raise AssertionError("draft exam close should be refused")
    except engine.ExamError as exc:
        assert exc.code == "bad_state"
    print("  6. answers save/clear(‑1)/flag + out-of-range/foreign/draft guards ✔ "
          f"(order shuffled={order_mixed})")

    # ---------------------------------------------------------------- 7
    # R001: 2 correct, 1 wrong, 1 clear → score 2 - 0.25 = 1.75
    q_by_id = {q["id"]: q for q in store.questions(exam["id"])}
    order = json.loads(store.session(s1["session_id"])["question_order"])
    paper_by_id = {x["id"]: x for x in paper}
    topic = [q_by_id[qid] for qid in order[:4]]
    def pos_of(q):
        """Student paper lo correct option e position lo undo (shuffle-safe)."""
        return paper_by_id[q["id"]]["options"].index(q["options"][q["correct_index"]])
    engine.save_answer(store, sess, topic[0]["id"], pos_of(topic[0]), None)
    engine.save_answer(store, sess, topic[1]["id"], pos_of(topic[1]), None)
    wrong_choice = next(p for p, txt in enumerate(paper_by_id[topic[2]["id"]]["options"])
                        if txt != topic[2]["options"][topic[2]["correct_index"]])
    engine.save_answer(store, sess, topic[2]["id"], wrong_choice, None)
    out = engine.submit_session(store, store.session(s1["session_id"]))
    assert not out["already"]
    assert out["result"]["score"] == 1.75, out["result"]
    assert out["result"]["correct"] == 2 and out["result"]["wrong"] == 1
    assert out["result"]["unattempted"] == 2
    assert out["result"]["passed"] is False, "1.75 < pass 2 → FAIL correct ga chupinchali"
    rev = {x["question_id"]: x for x in out["result"]["review"]}
    assert rev[topic[2]["id"]]["your_answer_text"] != \
        rev[topic[2]["id"]]["correct_answer_text"], "wrong answer text same?"
    assert rev[topic[0]["id"]]["your_answer_text"] == \
        rev[topic[0]["id"]]["correct_answer_text"], "correct answer text mismatch"
    assert out["result"]["review"] and len(out["result"]["review"]) == 5
    twice = engine.submit_session(store, store.session(s1["session_id"]))
    assert twice["already"] and twice["result"]["score"] == 1.75, "submit must be idempotent"
    # R002 all correct → rank 1
    sess2 = store.session(s2["session_id"])
    for item in engine.paper_for(store, sess2):
        orig2 = q_by_id[item["id"]]
        engine.save_answer(store, sess2, item["id"],
                           item["options"].index(orig2["options"][orig2["correct_index"]]), None)
    r2 = engine.submit_session(store, store.session(s2["session_id"]))
    assert r2["result"]["score"] == 5 and r2["result"]["rank"] == 1, r2["result"]
    assert store.session(s1["session_id"])["rank"] == 2
    assert r2["result"]["passed"] is True
    summary7 = engine.results_summary(store, exam["id"])
    assert summary7["topper"] == "R002", summary7
    print("  7. scoring + negative marks + rank + topper + idempotent submit ✔ "
          "(1.75 and 5.0, ranks 2/1, topper R002)")

    # --- 7b: OPTION SHUFFLE SAFETY (real-world #1 mistake source) -----------
    exam_sh = seed_exam(store, title="Shuffle safety", shuffle_options=True,
                        shuffle_questions=True, negative_marks=0.5, pass_marks=1)
    engine.publish_exam(store, exam_sh["id"])
    engine.start_exam(store, exam_sh["id"])
    qs_orig = {q["id"]: q for q in store.questions(exam_sh["id"])}
    for roll in ("R001", "R002"):
        sid = engine.join_exam(store, exam_sh["code"], roll)["session_id"]
        sess_sh = store.session(sid)
        paper_sh = engine.paper_for(store, sess_sh)
        shuffled_any = False
        for item in paper_sh:
            orig = qs_orig[item["id"]]
            correct_text = orig["options"][orig["correct_index"]]
            pos = item["options"].index(correct_text)
            if pos != orig["correct_index"]:
                shuffled_any = True
            engine.save_answer(store, sess_sh, item["id"], pos, None)
        res_sh = engine.submit_session(store, store.session(sid))
        score_val = res_sh["result"]["score"]
        assert score_val == 5.0, f"shuffle-safe scoring fail ({roll}): {score_val}"
        assert res_sh["result"]["correct"] == 5 and res_sh["result"]["wrong"] == 0
        review_sh = res_sh["result"]["review"]
        assert all(x["result"] == "correct" for x in review_sh)
        assert all(x["your_answer_text"] == x["correct_answer_text"]
                   for x in review_sh), "review texts mismatch"
    assert shuffled_any, "test needs at least one shuffled option order"
    sid3 = engine.join_exam(store, exam_sh["code"], "R003")["session_id"]
    sess_sh3 = store.session(sid3)
    for item in engine.paper_for(store, sess_sh3):
        orig = qs_orig[item["id"]]
        wrong_pos = next((i for i, t in enumerate(item["options"])
                          if t != orig["options"][orig["correct_index"]]), 0)
        engine.save_answer(store, sess_sh3, item["id"], wrong_pos, None)
    res_wrong = engine.submit_session(store, store.session(sid3))
    assert res_wrong["result"]["score"] == -2.5 and res_wrong["result"]["wrong"] == 5, \
        res_wrong["result"]
    an = engine.question_analysis(store, exam_sh["id"])
    assert all(x["correct"] == 2 and x["wrong"] == 1 for x in an), an
    print("  7b. option-shuffle safety: text-anchored scoring + analysis ✔ "
          "(2×5.0 correct, 1×-2.5 wrong)")

    # ---------------------------------------------------------------- 8
    close_out = engine.close_exam(store, exam["id"], reason="manual")
    assert close_out["exam"]["status"] == "closed"
    assert close_out["auto_submitted"] >= 1, close_out
    summary = close_out["summary"]
    assert summary["submitted"] == 3 and summary["pending"] == 0, summary
    again_close = engine.close_exam(store, exam["id"])
    assert again_close.get("already") and again_close["summary"]["submitted"] == 3
    csv_text = engine.results_csv(store, exam["id"])
    lines = [l for l in csv_text.splitlines() if l.strip()]
    assert len(lines) == 4, f"header + 3 sessions ravali: {lines}"
    assert "Rank" in lines[0] and "R002" in csv_text and "Hyderabad" not in csv_text
    assert "Pass" in csv_text or "Fail" in csv_text
    bundle = engine.export_bundle(store, exam["id"])
    assert set(bundle) == {"results", "questions", "analysis", "audit"}
    # closed exam: no new joins, existing students token tho result chudagalaru
    try:
        engine.join_exam(store, exam["code"], "R004")
        raise AssertionError("closed exam lo join avvakudadu")
    except engine.ExamError as exc:
        assert exc.code == "closed", exc.code
    resumed = engine.join_exam(store, exam["code"], "R001", token=s1["token"])
    assert resumed["status"] == "submitted" and resumed["result"]["score"] == 1.75
    assert store.get_exam(exam["id"])["closed_reason"] == "manual"
    print("  8. CLOSE auto-submit + idempotent + CSV exports ✔ "
          f"(submitted={summary['submitted']}, avg={summary['average']})")

    # ---------------------------------------------------------------- 9
    exam2 = seed_exam(store, title="Analysis exam")
    engine.publish_exam(store, exam2["id"])
    engine.start_exam(store, exam2["id"])
    sess3 = store.session(engine.join_exam(store, exam2["code"], "R001")["session_id"])
    qlist = store.questions(exam2["id"])
    paper3 = {x["id"]: x for x in engine.paper_for(store, sess3)}
    for q in qlist:      # paper position lo correct option (shuffle-safe)
        correct_text = q["options"][q["correct_index"]]
        engine.save_answer(store, sess3, q["id"],
                           paper3[q["id"]]["options"].index(correct_text), None)
    engine.submit_session(store, store.session(sess3["id"]))
    assert store.session(sess3["id"])["score"] == 5
    target = qlist[0]["id"]
    dropped = engine.drop_question(store, exam2["id"], target, dropped=True)
    assert dropped["question"]["dropped"] == 1
    assert store.session(sess3["id"])["score"] == 4, "dropped question must not count"
    assert dropped["summary"]["total_marks"] == 4
    analysis = engine.question_analysis(store, exam2["id"])
    assert analysis[0]["dropped"] and analysis[1]["correct_pct"] == 100.0
    restored = engine.drop_question(store, exam2["id"], target, dropped=False)
    assert store.session(sess3["id"])["score"] == 5
    assert restored["summary"]["total_marks"] == 5
    engine.register_tab_switch(store, store.session(sess3["id"]))
    engine.register_tab_switch(store, store.session(sess3["id"]))
    assert store.session(sess3["id"])["tab_switches"] == 2
    events = [e["kind"] for e in store.events(exam2["id"])]
    assert "question_dropped" in events and "tab_switch" in events
    print("  9. drop/restore recalculation + integrity signals + audit ✔")

    # --------------------------------------------------------------- 10
    exam3 = seed_exam(store, title="Auto everything", duration_min=1,
                      auto_start_all_joined=True)
    engine.publish_exam(store, exam3["id"])
    for roll in ("R001", "R002", "R003", "R004"):
        engine.join_exam(store, exam3["code"], roll)
    out = engine.sweep(store)
    assert any(a.startswith("auto_start") for a in out["actions"]), out
    assert store.get_exam(exam3["id"])["status"] == "live"
    # force time over in the DB then sweep → auto close
    store.update_exam(exam3["id"], end_at=store_mod.now_iso().replace("T", " ")[:19])
    out2 = engine.sweep(store)
    assert any(a.startswith("auto_close") for a in out2["actions"]), out2
    assert store.get_exam(exam3["id"])["status"] == "closed"
    assert all(s["status"] == "submitted" for s in store.sessions(exam3["id"]))
    events = [e["kind"] for e in store.events(exam3["id"])]
    assert "auto_submitted" in events
    # closing-soon ping once
    exam4 = seed_exam(store, title="Soon", duration_min=3)
    engine.publish_exam(store, exam4["id"])
    engine.start_exam(store, exam4["id"])          # ends in 3 min → within 5 min ping
    sw1 = engine.sweep(store)
    sw2 = engine.sweep(store)
    assert any("closing_soon" in a for a in sw1["actions"]), sw1
    assert not any("closing_soon" in a for a in sw2["actions"]), "must ping once only"
    print("  10. sweeper: auto-start + auto-close + once-only ping ✔ "
          f"({out2['actions'][0]})")

    # --------------------------------------------------------------- 11
    exam5 = seed_exam(store, title="Notify exam")
    engine.publish_exam(store, exam5["id"])
    engine.start_exam(store, exam5["id"])
    engine.extend_exam(store, exam5["id"], 5)
    engine.announce(store, exam5["id"], "Q3 lo spelling mistake — ignore cheyandi")
    engine.close_exam(store, exam5["id"])
    engine.publish_results(store, exam5["id"])
    logs = store.notifications(exam5["id"])
    assert len(logs) >= 5 and all(x["status"] in ("ok", "sent", "skipped", "failed")
                                  for x in logs), logs
    assert any(x["channel"] == "in_app" for x in logs)
    tpl = notify.templates(store.get_exam(exam5["id"]))
    assert "whatsapp_group" in tpl and "notice_board" in tpl and "json" in tpl
    assert store.get_exam(exam5["id"])["code"] in tpl["whatsapp_group"]
    # webhook failure must never raise / never block the exam
    old = notify.send_webhook
    notify.send_webhook = lambda payload: {"status": "failed", "detail": "test"}
    try:
        out = notify.broadcast_event(store, store.get_exam(exam5["id"]), "announcement",
                                     extra="hello")
        assert out["results"] and out["message"]
    finally:
        notify.send_webhook = old
    msg = notify.student_message(store.get_exam(exam5["id"]), "started")
    assert "START" in msg and "/exam/" in msg
    print("  11. notifications (in-app + telegram/webhook safe + templates) ✔ "
          f"({len(logs)} logged)")

    # --------------------------------------------------------------- 12
    httpd, api = server.make_server("127.0.0.1", 0, tmp / "http.db", "test-key")
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = BASE.format(port=port)
    try:
        st, body, _ = http("GET", f"{base}/healthz")
        assert st == 200 and body["ok"]
        st, html, hdrs = http("GET", f"{base}/")
        assert st == 200 and "College Exams" in html and "text/html" in hdrs["Content-Type"]
        st, html, _ = http("GET", f"{base}/admin")
        assert st == 200 and "admin login" in html.lower()
        st, body, _ = http("POST", f"{base}/api/admin/verify", {"key": "wrong"})
        assert st == 401 and body["code"] == "unauthorized"
        st, body, _ = http("GET", f"{base}/api/admin/exams?key=bad")
        assert st == 401
        st, out, _ = http("POST", f"{base}/api/admin/exams",
                          {"key": "test-key", "title": "HTTP Exam", "college": "Net College",
                           "duration_min": 5, "per_q_marks": 2, "negative_marks": 0.5,
                           "pass_marks": 2, "roster_required": True})
        assert st == 200 and out["exam"]["code"] and out["links"]["student"]
        code, token = out["exam"]["code"], out["exam"]["admin_token"]
        st, info, _ = http("GET", f"{base}/api/exam-info/{code}")
        assert st == 200 and info["exam"]["title"] == "HTTP Exam"
        assert "admin_token" not in info["exam"], "token leak!"
        raw = ("1. Capital of Telangana?\nA) Warangal\nB) Hyderabad\nAnswer: B\n"
               "2. 2+2?\nA) 3\nB) 4\nAnswer: B\n")
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/questions",
                          {"key": token, "raw": raw, "dry_run": True})
        assert st == 200 and out["added"] == 2 and out["dry_run"]
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/questions",
                          {"key": token, "raw": raw + "3. broken?\nA) same\nB) same\nAnswer: A\n"})
        assert st == 200 and out["added"] == 2 and len(out["errors"]) == 1, out
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/roster",
                          {"key": token, "raw": "R001, Ravi\nR002, Sita\nR002, Dup\n,BAD\n"})
        assert st == 200 and out["added"] == 2 and out["duplicates"] == ["R002"], out
        assert out["invalid"] == [""]
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/publish", {"key": token})
        assert st == 200 and out["exam"]["status"] == "published"
        st, cfg, _ = http("GET", f"{base}/api/admin/exam/{code}?key={token}")
        assert st == 200 and cfg["summary"]["questions"] == 2 and cfg["templates"]
        st, body, _ = http("POST", f"{base}/api/join", {"code": code, "roll": "R009"})
        assert st == 400 and body["code"] == "not_in_roster"
        st, joined, _ = http("POST", f"{base}/api/join", {"code": code, "roll": "r001"})
        assert st == 200 and joined["status"] == "waiting"
        stu_token = joined["token"]
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/start", {"key": token})
        assert st == 200 and out["activated"] == 1
        st, hb, _ = http("POST", f"{base}/api/session/heartbeat", {"token": stu_token})
        assert st == 200 and hb["status"] == "active" and hb["remaining_sec"] > 0
        st, sess, _ = http("GET", f"{base}/api/session?token={stu_token}")
        assert st == 200 and sess["questions"] and "correct_index" not in sess["questions"][0]
        # HTTP level kuda shuffle-safe: paper lo correct TEXT e position lo undo
        http_correct = {1: "Hyderabad", 2: "4"}     # question_id → correct option text
        answers_sent = {}
        for item in sess["questions"]:
            pos = item["options"].index(http_correct[item["id"]])
            answers_sent[item["id"]] = pos
            st, out, _ = http("POST", f"{base}/api/session/answer",
                              {"token": stu_token, "question_id": item["id"],
                               "choice": pos})
            assert st == 200 and out["saved"], out
        qid = sess["questions"][0]["id"]
        st, out, _ = http("POST", f"{base}/api/session/answer",
                          {"token": stu_token, "question_id": qid, "choice": 7})
        assert st == 400
        st, out, _ = http("POST", f"{base}/api/session/answer",
                          {"token": stu_token, "question_id": qid, "choice": -1})
        assert st == 200 and out["answered"] == 1, "clear (-1) work avvali"
        st, out, _ = http("POST", f"{base}/api/session/answer",
                          {"token": stu_token, "question_id": qid,
                           "choice": answers_sent[qid]})
        assert st == 200 and out["answered"] == 2
        st, out, _ = http("POST", f"{base}/api/session/tabswitch", {"token": stu_token})
        assert st == 200 and out["tab_switches"] == 1
        st, out, _ = http("POST", f"{base}/api/session/submit", {"token": stu_token})
        assert st == 200 and out["result"]["score"] == 4.0, out      # 2 Q × 2 marks
        st, out, _ = http("POST", f"{base}/api/session/submit", {"token": stu_token})
        assert st == 200 and out["already"]
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/close", {"key": token})
        assert st == 200 and out["exam"]["status"] == "closed"
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/extend", {"key": token})
        assert st == 400 and out["code"] == "bad_state", out    # closed → extend ledu
        st, csv_text, hdrs = http("GET",
                                  f"{base}/api/admin/exam/{code}/export/results.csv?key={token}")
        assert st == 200 and "R001" in csv_text and "attachment" in hdrs.get("Content-Disposition", "")
        st, body, _ = http("GET", f"{base}/api/admin/exam/{code}/export/results.csv?key=bad")
        assert st == 401
        st, out, _ = http("POST", f"{base}/api/admin/exam/{code}/settings",
                          {"key": token, "title": "Hacked"})
        assert st == 400 and out["code"] == "bad_state", out
        st, html, _ = http("GET", f"{base}/exam/{code}")
        assert st == 200 and "Exam Portal — Student" in html
        st, html, _ = http("GET", f"{base}/manage/{code}")
        assert st == 200 and "Manage" in html
        st, body, _ = http("GET", f"{base}/api/nope")
        assert st == 404
        st, body, _ = http("POST", f"{base}/api/session/answer", {"token": "nope"})
        assert st == 404 and body["code"] == "not_found"
        st, body, _ = http("POST", f"{base}/api/admin/exam/{code}/questions", {"key": token})
        assert st == 400, "empty body must be a clean 400"
    finally:
        httpd.shutdown()
        httpd.server_close()
    print("  12. HTTP end-to-end (auth, join, start, answer, submit, close, export) ✔")

    # --------------------------------------------------------------- 13 (demo)
    demo_db = tmp / "demo.db"
    demo_store = store_mod.Store(demo_db)
    info = demo.seed(demo_store)
    assert info["code"] and info["log"]
    assert demo_store.get_exam(info["exam"]["id"])["status"] == "live"
    qs, errs = engine.parse_questions(demo.DEMO_QUESTIONS)
    assert len(qs) == 5 and not errs
    assert len(demo_store.roster_rolls(info["exam"]["id"])) == 6
    sessions = demo_store.sessions(info["exam"]["id"])
    assert len([s for s in sessions if s["status"] == "submitted"]) == 3
    summary = engine.results_summary(demo_store, info["exam"]["id"])
    assert summary["submitted"] == 3 and summary["average"] == 3.75, summary
    assert summary["topper"] == "21B01A0501" and summary["passed"] == 2, summary
    assert demo_store.get_exam(info["exam"]["id"])["results_published_at"]
    print(f"  13. demo seed (5 Q, 6 students, 3 attempts, avg {summary['average']}) ✔")

    # --------------------------------------------------------------- 14 (UI JS)
    pages = {"landing": ui.landing_html(), "admin": ui.admin_html(),
             "manage": ui.manage_html(), "student": ui.student_html()}
    page_marks = {"landing": ["College Exams", "built-in protections", "/admin"],
                  "admin": ["College admin login", "id=\"f_duration\"", "New exam"],
                  "manage": ["examTitle", "startBtn", "closeBtn"],
                  "student": ["rollInput", "joinBtn", "timer"]}
    js_marks = {"landing": ["function api(", "copyText"],
                "admin": ["function login()", "/api/admin/exams", "createExam", "loadExams"],
                "manage": ["function render()", "doStart", "doClose", "/api/admin/exam/",
                           "renderBulkReport", "renderRosterReport"],
                "student": ["function boot()", "joinNow", "/api/session/heartbeat",
                            "askSubmit", "autoSubmit"]}
    scripts = {}
    for name, html in pages.items():
        assert html.startswith("<!doctype html>") and html.rstrip().endswith("</html>"), name
        found = re.findall(r"<script>(.*?)</script>", html, re.S)
        assert len(found) == 1, f"{name}: 1 script block expect chesam, vachindi {len(found)}"
        scripts[name] = found[0]
        for mark in page_marks[name]:
            assert mark in html, f"{name} page lo '{mark}' ledu"
        for mark in js_marks[name]:
            assert mark in found[0], f"{name} script lo '{mark}' ledu"
    # onclick:fn() (immediate call — page load lo ne fire avutundi) eppudu vadakudadu
    for name, js in scripts.items():
        bad = re.findall(r"onclick:\s*[A-Za-z_$][A-Za-z0-9_$]*\s*\(", js)
        assert not bad, f"{name}: onclick lo immediate call ({bad}) — ()=>fn() vaadandi"
    # f-string escape ({{\n}}) page lo leak avvakudadu — JS lo }} legit, {{ kaadu
    for name, html in pages.items():
        assert "{{" not in html, f"{name}: Python f-string escape leak ({{{{) kanipinchindi"
    # una esc/backslash-ledu (Python 3.11 f-string limits) — node syntax check tho confirm
    node = shutil.which("node")
    if node:
        for name, js in scripts.items():
            js_path = tmp / f"{name}.js"
            js_path.write_text(js, encoding="utf-8")
            proc = subprocess.run([node, "--check", str(js_path)],
                                  capture_output=True, text=True)
            assert proc.returncode == 0, f"{name}.js syntax error:\n{proc.stderr[:400]}"
        print(f"  14. UI pages: markers + onclick-guard + node --check ({len(scripts)} scripts) ✔")
    else:
        print("  14. UI pages: markers + onclick-guard ✔ (node ledu — syntax check skip)")

    print("ALL v39 EXAM PORTAL TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    sys.exit(main())
