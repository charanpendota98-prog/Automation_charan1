"""Tests for autoblog/quiz_intake.py exam-wise quiz intake engine."""
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from autoblog import quiz_intake


def test_normalization():
    # 1. Standard format
    raw1 = {
        "question": "Which Article of the Constitution deals with the Election Commission of India?",
        "options": ["Article 324", "Article 312", "Article 280", "Article 356"],
        "answer": 0,
        "explanation": "Article 324 provides for the Election Commission of India.",
        "exam": "tspsc",
        "category": "Indian Polity"
    }
    norm1 = quiz_intake.normalize_question(raw1)
    assert norm1 is not None
    assert norm1["exam"] == "tspsc"
    assert norm1["c"] == 0
    assert norm1["q"].startswith("Which Article")
    assert len(norm1["a"]) == 4

    # 2. Letter answer ("B"), alt keys ("choices", "target_exam")
    raw2 = {
        "q": "What is the capital of Andhra Pradesh according to recent legislation?",
        "choices": ["Visakhapatnam", "Amaravati", "Kurnool", "Tirupati"],
        "correct": "B",
        "why": "Amaravati is the capital city.",
        "target_exam": "APPSC Group 2",
        "source": "AP Assembly Gazette"
    }
    norm2 = quiz_intake.normalize_question(raw2)
    assert norm2 is not None
    assert norm2["exam"] == "appsc"
    assert norm2["c"] == 1
    assert norm2["src"] == "AP Assembly Gazette"

    # 3. Text answer matching one of choices
    raw3 = {
        "question": "Which organization regulates monetary policy in India?",
        "options": ["SEBI", "IRDAI", "RBI", "NABARD"],
        "answer": "RBI",
        "exam": "Banking IBPS PO"
    }
    norm3 = quiz_intake.normalize_question(raw3)
    assert norm3 is not None
    assert norm3["exam"] == "banking"
    assert norm3["c"] == 2
    print("  1. Question normalization & schema flexibility ✔")


def test_ingestion_and_retrieval(tmp_path=None):
    test_store = Path("/tmp/test_quiz_store.json")
    if test_store.exists():
        test_store.unlink()

    # Create mock 20 questions across various target exams
    questions_batch = []
    exams = ["tspsc", "appsc", "ssc", "banking", "rrb", "general"]
    for i in range(20):
        target = exams[i % len(exams)]
        questions_batch.append({
            "id": i + 1,
            "q": f"Mock Competitive Question {i+1} for {target.upper()}?",
            "choices": ["Choice A", "Choice B", "Choice C", "Choice D"],
            "correct_index": i % 4,
            "explanation": f"Explanation for question {i+1}",
            "exam": target
        })

    # Ingest
    res = quiz_intake.ingest_questions(questions_batch, target_date="2026-10-03", store_path=test_store)
    assert res["status"] == "ok"
    assert res["imported"] == 20
    assert res["total_for_day"] == 20

    # Retrieve all
    all_qs = quiz_intake.get_daily_questions("2026-10-03", exam_filter="all", store_path=test_store)
    assert len(all_qs) == 20

    # Retrieve TSPSC
    tspsc_qs = quiz_intake.get_daily_questions("2026-10-03", exam_filter="tspsc", store_path=test_store)
    assert len(tspsc_qs) >= 3
    assert all(q["exam"] in ("tspsc", "general", "all") for q in tspsc_qs)

    # Retrieve SSC
    ssc_qs = quiz_intake.get_daily_questions("2026-10-03", exam_filter="ssc", store_path=test_store)
    assert len(ssc_qs) >= 3
    assert all(q["exam"] in ("ssc", "general", "all") for q in ssc_qs)

    if test_store.exists():
        test_store.unlink()
    print("  2. Ingestion of 20 questions batch & exam filtering ✔")


def main():
    print("=" * 60)
    print("  EXAM-WISE QUIZ INTAKE ENGINE TESTS")
    print("=" * 60)
    test_normalization()
    test_ingestion_and_retrieval()
    print("-" * 60)
    print("ALL QUIZ INTAKE TESTS PASSED ✔")


if __name__ == "__main__":
    main()
