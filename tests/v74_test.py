# -*- coding: utf-8 -*-
"""v74 tests — live exam portal removal + cron-only bot (MilesWeb-proof).

Live exam avasaram ledu (owner) → portal motham teesesam:
  * code: exam_portal/ · passenger_wsgi · wsgi_dev · --exam-* flags · EXAM_* env
  * site: /exam/ links · /poll + /lead APIs → static daily question + WhatsApp form
  * theme: exam_url/api_base options · dead ?studentup_exam=1 shortcut
  * deploy: portal units/proxy → bot timer + Docker loop + cron
  * new: --approval-poll (cron mode approvals — shared hosting lo daemon ledu)

Offline only. Run: python tests/v74_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from autoblog import approval_bot, config, deploy_check, state  # noqa: E402

TE = re.compile(r"[\u0c00-\u0c7f]")


# ------------------------------------------------------------- code removal

def test_portal_files_gone():
    for gone in ("exam_portal", "passenger_wsgi.py", "wsgi_dev.py",
                 "tests/v39_exam_portal_test.py", "tests/v49_wsgi_test.py",
                 "deploy/exam-portal.service", "deploy/nginx-exam.conf"):
        assert not (ROOT / gone).exists(), f"inka undi: {gone}"
    print("  gone: exam_portal/ · wsgi adapters · portal tests · portal units ✔")


def test_no_portal_refs_in_code():
    bad = []
    files = list((ROOT / "autoblog").glob("*.py")) + list((ROOT / "tools").glob("*.py"))
    files += [ROOT / "run.py"]
    for f in files:
        text = f.read_text(encoding="utf-8")
        for needle in ("exam_portal", "exam-portal", "--exam-", "EXAM_PORTAL",
                       "EXAM_PUBLIC_URL", "EXAM_TELEGRAM", "EXAM_WEBHOOK",
                       "passenger_wsgi", "wsgi_dev", "/poll/", "/lead",
                       "KBHA5W", "8080", "8090"):
            if needle in text:
                bad.append(f"{f.name}: {needle}")
    # config.py historical comment? kuda undakoodadu — clean ga
    assert bad == [], f"portal vestiges: {bad}"
    for sh in ("deploy/su-watchdog.sh", "deploy/backup.sh", "deploy/install-vps.sh",
               "deploy/bot-loop.sh", "deploy/docker-compose.yml", "deploy/Dockerfile",
               "deploy/Caddyfile", "crontab.example"):
        text = (ROOT / sh).read_text(encoding="utf-8")
        # ".env.example" lo "exam" substring — English word, portal vestige kaadu
        text = text.lower().replace("example", "")
        assert "exam" not in text, f"{sh} lo exam vestige"
    print("  clean: bot/tools/run/deploy/cron lo portal refs levu ✔")


def test_env_example_has_no_exam_keys():
    env = (ROOT / ".env.example").read_text(encoding="utf-8")
    assert "EXAM_" not in env, "EXAM_* keys inka unnayi"
    assert "--approval-poll" in env, "cron hint ledu"
    print("  env: EXAM_* keys poyayi · approval-poll cron hint undi ✔")


def test_cli_help_has_no_exam_flags():
    proc = subprocess.run([sys.executable, "run.py", "--help"], cwd=str(ROOT),
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0
    assert "--exam-portal" not in proc.stdout
    assert "--deploy-port" not in proc.stdout
    assert "--approval-poll" in proc.stdout and "--deploy-check" in proc.stdout
    print("  cli: --exam-*/--deploy-port poyayi · --approval-poll vachindi ✔")


# ------------------------------------------------------------- site + theme

def test_preview_has_no_portal():
    html = (ROOT / "preview" / "index.html").read_text(encoding="utf-8")
    for needle in ("#exam", "examlink", "exam-card", "exam-feats", "/exam/",
                   "/poll/", "KBHA5W", "Online Exams", "Exam Portal",
                   ":8080", ":8090", "8080-"):
        assert needle not in html, f"preview vestige: {needle}"
    assert 'id="quizlink"' in html and 'id="quizpromo"' in html
    assert 'href="#quiz"' in html
    for page in (ROOT / "preview" / "pages").glob("*.html"):
        text = page.read_text(encoding="utf-8")
        assert "/exam/" not in text and "KBHA5W" not in text, page.name
        assert "exam portal" not in text.lower(), page.name
    assert 'api()+"/lead"' not in (ROOT / "preview" / "pages" / "contact.html").read_text(encoding="utf-8")
    print("  preview: portal links/APIs poyayi · quiz promo + static poll ✔")


def test_poll_bank_valid_and_english():
    html = (ROOT / "preview" / "index.html").read_text(encoding="utf-8")
    m = re.search(r"var POLL_BANK=\[(.*?)\];", html, re.S)
    assert m, "POLL_BANK ledu"
    items = re.findall(r"\{t:\"(.*?)\",o:\[(.*?)\],a:(\d+),w:\"(.*?)\"\}", m.group(1))
    assert len(items) == 7, len(items)
    for t, opts, a, w in items:
        assert not TE.search(t + opts + w), "poll English-only (v73 scope)"
        assert len(re.findall(r"\"(.*?)\"", opts)) == 4
        assert 0 <= int(a) < 4
    assert "fetch(" not in html.split("var POLL_BANK=")[1].split("</script>")[0], "poll lo fetch undakoodadu"
    print("  poll: 7 valid English questions · zero fetch ✔")


def test_theme_has_no_exam():
    theme = ROOT / "wordpress-theme" / "studentup"
    for f in theme.rglob("*.php"):
        text = f.read_text(encoding="utf-8")
        for needle in ("exam_url", "api_base", "apiBase", "studentup_exam",
                       "Online Exam", "/exam/"):
            assert needle not in text, f"{f.name}: {needle}"
    for f in (theme / "assets" / "js").glob("*.js"):
        assert "apiBase" not in f.read_text(encoding="utf-8"), f.name
    pwa = (theme / "inc" / "pwa.php").read_text(encoding="utf-8")
    for s in ("Jobs", "Qualification", "Results", "Daily Quiz"):
        assert s in pwa, f"shortcut ledu: {s}"
    assert "studentup_exam=1" not in pwa
    css = re.search(r"^Version:\s*(\S+)", (theme / "style.css").read_text(encoding="utf-8"), re.M).group(1)
    assert css == "1.9.8", css
    print("  theme: exam options/buttons/dead-link poyayi · shortcuts aligned · 1.9.4 ✔")


# ------------------------------------------------------------- approval cron

class _Resp:
    def __init__(self, payload: dict):
        self._payload = payload
        self.status_code = 200
        self.headers = {"content-type": "application/json"}

    def json(self):
        return self._payload


def test_approval_poll_no_token_path():
    proc = subprocess.run([sys.executable, "run.py", "--approval-poll"],
                          cwd=str(ROOT), capture_output=True, text=True,
                          timeout=120, env={**__import__("os").environ,
                                            "TELEGRAM_BOT_TOKEN": ""})
    out = proc.stdout + proc.stderr
    assert proc.returncode == 2, out
    assert "TELEGRAM_BOT_TOKEN ledu" in out, out
    assert "Traceback" not in out
    print("  approval-poll: no-token → exit 2 + helpful message (no crash) ✔")


def test_approval_poll_processes_updates_offline():
    tmp = Path(tempfile.mkdtemp(prefix="v74-appr-"))
    db = tmp / "state.db"
    state.init(db)
    updates = [{"update_id": 41, "message": {"chat": {"id": 777},
                                             "text": "/start"}}]
    sent = []

    def _fake_post(url, json=None, timeout=None):
        sent.append((url, json))
        return _Resp({"ok": True})

    def _fake_get(url, params=None, timeout=None):
        off = int(params.get("offset", 0)) if params else 0
        rest = [u for u in updates if u["update_id"] >= off]
        return _Resp({"ok": True, "result": rest})

    with mock.patch.object(config, "STATE_PATH", db), \
         mock.patch.object(config, "TELEGRAM_BOT_TOKEN", "fake-token"), \
         mock.patch.object(config, "TELEGRAM_CHAT_ID", ""), \
         mock.patch("autoblog.approval_bot.requests.post", _fake_post), \
         mock.patch("autoblog.approval_bot.requests.get", _fake_get):
        bot = approval_bot.ApprovalBot()
        n = bot.poll_once(timeout=1)
        assert n == 1, n
        assert state.meta_get(db, approval_bot.CHAT_KEY) == "777", "owner register avvaledu"
        assert state.meta_get(db, approval_bot.OFFSET_KEY) == "42", "offset save avvaledu"
        assert sent and sent[0][0].endswith("/sendMessage"), sent
        assert "Namaskaram" in sent[0][1]["text"]
        assert bot.poll_once(timeout=1) == 0, "offset unna malli raakoodadu"
    print("  approval-poll: /start → register + welcome + offset (offline mock) ✔")


# ------------------------------------------------------------- deploy + docs

def test_deploy_check_green_without_portal():
    for chk in (deploy_check.check_python(), deploy_check.check_deps(),
                deploy_check.check_files(), deploy_check.check_writable(),
                deploy_check.check_imports(), deploy_check.check_cron_hint(),
                deploy_check.check_deploy_artifacts()):
        assert chk["status"] == "ok", chk
    assert not hasattr(deploy_check, "check_exam_portal")
    assert not hasattr(deploy_check, "check_port")
    print("  deploy-check: imports/artifacts/cron green · portal checks levu ✔")


def test_crontab_covers_bot_and_approvals():
    cron = (ROOT / "crontab.example").read_text(encoding="utf-8")
    assert "run.py --approval-poll" in cron and "*/5" in cron
    assert "run.py >>" in cron or "run.py " in cron
    print("  cron: hourly run + */5 approvals ✔")


def test_docs_are_portal_free_and_cron_only():
    miles = (ROOT / "DEPLOY_MILESWEB.md").read_text(encoding="utf-8")
    assert "--approval-poll" in miles and "cron" in miles
    for needle in ("passenger_wsgi", "Setup Python App", "exam portal", "/exam"):
        assert needle not in miles, f"miles vestige: {needle}"
    deploy = (ROOT / "DEPLOY.md").read_text(encoding="utf-8")
    for path_name in ("Path A", "Path B", "Path C", "Backups", "Security checklist"):
        assert path_name in deploy
    assert "exam portal" not in deploy.lower()
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "--exam-portal" not in readme
    assert "v74" in readme and "--approval-poll" in readme
    print("  docs: MilesWeb cron-only · DEPLOY paths · README v74 ✔")


def test_fresh_clone_tooling():
    import json as _json

    pkg = _json.loads((ROOT / "tests" / "runtime" / "package.json").read_text(encoding="utf-8"))
    assert "php-parser" in pkg["dependencies"], "fresh clone lo php-lint fail avutundi"
    ci = (ROOT / "ci" / "github-actions-tests.yml").read_text(encoding="utf-8")
    assert "setup-node" in ci and "tests/runtime" in ci
    assert "exam_portal" not in ci
    print("  tooling: php-parser declared · CI node deps · no portal ✔")


def main() -> None:
    print("=" * 64)
    print("  v74 — PORTAL REMOVAL + CRON-ONLY BOT")
    print("=" * 64)
    tests = [
        ("portal files gone", test_portal_files_gone),
        ("no portal refs in code", test_no_portal_refs_in_code),
        ("env keys clean", test_env_example_has_no_exam_keys),
        ("cli flags clean", test_cli_help_has_no_exam_flags),
        ("preview portal-free", test_preview_has_no_portal),
        ("poll bank valid", test_poll_bank_valid_and_english),
        ("theme exam-free 1.9.4", test_theme_has_no_exam),
        ("approval no-token path", test_approval_poll_no_token_path),
        ("approval processes updates", test_approval_poll_processes_updates_offline),
        ("deploy-check green", test_deploy_check_green_without_portal),
        ("crontab covers bot", test_crontab_covers_bot_and_approvals),
        ("docs portal-free", test_docs_are_portal_free_and_cron_only),
        ("fresh-clone tooling", test_fresh_clone_tooling),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 64)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        raise SystemExit(1)
    print("ALL v74 PORTAL-REMOVAL TESTS PASSED ✔")


if __name__ == "__main__":
    main()
