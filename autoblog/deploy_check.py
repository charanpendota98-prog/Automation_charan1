"""Deployment readiness check — "deploy cheyyadaniki ready-a?" (v41 deploy pack).

Ee module production lo deploy cheyyadaniki mundu ANNI avasaralu check chestundi
— server SSH lo okka command tho. Checks nijamga pani cheyyali (claims kaadu):
exam portal ni temp DB tho **boot chesi** HTTP hit chestundi, deps import
chestundi, disk/permissions chustundi.

CLI:  python run.py --deploy-check [--deploy-port 8080]
"""

from __future__ import annotations

import importlib
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import urllib.request
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parent.parent

OK, WARN, FAIL = "ok", "warn", "fail"


def _res(status: str, name: str, detail: str, fix: str = "") -> Dict:
    return {"status": status, "name": name, "detail": detail, "fix": fix}


def check_python() -> Dict:
    v = sys.version_info
    if v >= (3, 10):
        return _res(OK, "Python version", f"{v.major}.{v.minor}.{v.micro}")
    return _res(FAIL, "Python version", f"{v.major}.{v.minor} — 3.10+ kavali",
                "sudo apt install python3.11 (leda 3.12) + venv")


def check_deps() -> Dict:
    missing = []
    for mod in ("requests", "PIL", "bs4", "pypdf"):
        try:
            importlib.import_module(mod)
        except Exception:  # noqa: BLE001
            missing.append(mod)
    if missing:
        return _res(FAIL, "Python deps", f"missing: {', '.join(missing)}",
                    "pip install -r requirements.txt (venv lo)")
    return _res(OK, "Python deps", "requests · pillow · beautifulsoup4 · pypdf")


def check_files() -> Dict:
    need = ["run.py", "requirements.txt", "autoblog/main.py", "exam_portal/server.py"]
    missing = [f for f in need if not (ROOT / f).exists()]
    if missing:
        return _res(FAIL, "Repo files", f"missing: {', '.join(missing)}",
                    "git clone / git pull malli cheyandi")
    return _res(OK, "Repo files", f"{len(need)} core files unnayi")


def check_writable() -> Dict:
    try:
        with tempfile.NamedTemporaryFile(dir=ROOT, delete=True) as fh:
            fh.write(b"ok")
        return _res(OK, "Write permission", f"{ROOT} writable (logs/db/state ki)")
    except OSError as exc:
        return _res(FAIL, "Write permission", str(exc)[:80],
                    "sudo chown -R $USER:$USER " + str(ROOT))


def check_disk() -> Dict:
    total, used, free = shutil.disk_usage(ROOT)
    gb = free / 1e9
    status = OK if gb >= 1 else (WARN if gb >= 0.2 else FAIL)
    return _res(status, "Disk space", f"{gb:.1f} GB free",
                "images/db/logs kosam 1 GB+ ivvandi" if status != OK else "")


def check_env() -> List[Dict]:
    out: List[Dict] = []
    env_file = ROOT / ".env"
    if not env_file.exists():
        out.append(_res(WARN, ".env file", "ledu — defaults tho run avutundi",
                        "cp .env.example .env → WP_USERNAME/WP_APP_PASSWORD pettandi"))
    else:
        out.append(_res(OK, ".env file", f"{env_file.stat().st_size} bytes"))
    has_wp = bool(os.environ.get("WP_USERNAME")) and bool(os.environ.get("WP_APP_PASSWORD"))
    out.append(_res(OK if has_wp else WARN, "WordPress creds",
                    "set" if has_wp else "ledu (audit/publish ki kavali)",
                    "wp-admin → Users → Application Passwords → .env lo pettandi"))
    has_tg = bool(os.environ.get("TELEGRAM_BOT_TOKEN"))
    out.append(_res(OK if has_tg else WARN, "Telegram notify",
                    "set" if has_tg else "ledu (optional — in-app banner pani chestundi)"))
    return out


def check_port(port: int) -> Dict:
    with socket.socket() as s:
        s.settimeout(1.0)
        busy = s.connect_ex(("127.0.0.1", port)) == 0
    if busy:
        return _res(WARN, f"Port {port}", "already in use",
                    f"--exam-port {port + 1} vadandi leda a port vaduthunna service aapeyandi")
    return _res(OK, f"Port {port}", "free (exam portal ki)")


def check_exam_portal(port: int = 0) -> Dict:
    """Exam portal ni temp DB tho boot chesi /healthz hit — nijamga click avutunda."""
    try:
        sys.path.insert(0, str(ROOT))
        from exam_portal.server import make_server, sweeper_loop  # type: ignore

        with tempfile.TemporaryDirectory() as td:
            db = Path(td) / "deploy-check.db"
            httpd, api = make_server("127.0.0.1", port, str(db),
                                     admin_key="deploy-check-key")
            actual_port = httpd.server_address[1]
            stop = threading.Event()
            threading.Thread(target=httpd.serve_forever, daemon=True).start()
            threading.Thread(target=sweeper_loop, args=(api.store, stop),
                             daemon=True).start()
            try:
                with urllib.request.urlopen(
                        f"http://127.0.0.1:{actual_port}/healthz", timeout=5) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                ok = resp.status == 200 and body.get("ok") is True
            finally:
                stop.set()
                httpd.shutdown()
                httpd.server_close()
        if ok:
            return _res(OK, "Exam portal boot", f"booted on :{actual_port} · /healthz ok")
        return _res(FAIL, "Exam portal boot", f"/healthz → {body}")
    except Exception as exc:  # noqa: BLE001
        return _res(FAIL, "Exam portal boot", f"{type(exc).__name__}: {str(exc)[:120]}",
                    "python tests/v39_exam_portal_test.py run chesi error chudandi")


def check_deploy_artifacts() -> Dict:
    arts = ["deploy/exam-portal.service", "deploy/studentup-bot.service",
            "deploy/studentup-bot.timer", "deploy/Caddyfile", "deploy/backup.sh",
            "deploy/Dockerfile", "deploy/docker-compose.yml", "DEPLOY.md"]
    missing = [a for a in arts if not (ROOT / a).exists()]
    if missing:
        return _res(WARN, "Deploy artifacts", f"missing: {', '.join(missing)}",
                    "repo nunchi pull cheyandi (deploy/ + DEPLOY.md)")
    return _res(OK, "Deploy artifacts", f"{len(arts)} files (systemd/Caddy/Docker/backup)")


def check_git() -> Dict:
    if (ROOT / ".git").exists():
        return _res(OK, "Git repo", "clone undi (git pull tho update avutundi)")
    return _res(WARN, "Git repo", ".git ledu", "git clone chesi deploy cheste updates easy")


def run_deploy_check(port: int = 8080) -> int:
    t0 = time.time()
    checks: List[Dict] = [check_python(), check_deps(), check_files(), check_writable(),
                          check_disk(), check_deploy_artifacts(), check_git(),
                          check_port(port), check_exam_portal(0)]
    checks += check_env()
    icon = {OK: "✅", WARN: "⚠️ ", FAIL: "❌"}
    fails = [c for c in checks if c["status"] == FAIL]
    warns = [c for c in checks if c["status"] == WARN]
    print("=" * 74)
    print("  🚀 DEPLOY CHECK — ee server lo deploy cheyyadaniki ready-a?")
    print("=" * 74)
    for c in checks:
        print(f"  {icon[c['status']]} {c['name']:<20} {c['detail']}")
        if c["fix"] and c["status"] != OK:
            print(f"       ↳ fix: {c['fix']}")
    print("-" * 74)
    print(f"  {len(checks) - len(fails) - len(warns)} ok · {len(warns)} warn · "
          f"{len(fails)} fail  ({time.time() - t0:.1f}s)")
    if fails:
        print("  ❌ FAIL items fix chesi malli run cheyandi: python run.py --deploy-check")
        return 1
    print("  ✅ Ready. Next: DEPLOY.md lo mee path (VPS / Docker / PaaS) follow cheyandi.")
    return 0
