"""v39 Exam Portal — college exams, online, easy, mistake-free.

    python run.py --exam-portal            # server start (admin + students)
    python run.py --exam-portal-demo       # sample exam + students seed

Modules:
  store.py   — SQLite schema/queries (WAL, per-student sessions)
  engine.py  — validation, START/CLOSE, scoring, exports, sweeper
  notify.py  — multi-channel notifications (in-app/Telegram/webhook/templates)
  ui.py      — landing, admin console, student exam app (vanilla JS)
  server.py  — stdlib HTTP server + CLI
"""

VERSION = "v39"
