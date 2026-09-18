# -*- coding: utf-8 -*-
"""v49 — exam portal on WSGI (cPanel "Setup Python App" / gunicorn / uWSGI).

Proves the *exact same* portal works when only a WSGI app can be served
(MilesWeb shared hosting), so nothing is lost versus the long-running server.

Offline only: in-process WSGI calls, temp DB, no sockets.
"""
from __future__ import annotations

import io
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam_portal import wsgi                              # noqa: E402

ADMIN = "wsgi-admin-key"


def _client(app):
    """Tiny WSGI test client."""

    def call(method: str, path: str, body: bytes = b"", query: str = "",
             headers=None):
        env = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "SCRIPT_NAME": os.environ.get("WSGI_SCRIPT_NAME", ""),
            "REQUEST_URI": (os.environ.get("WSGI_SCRIPT_NAME", "") + path
                            + (("?" + query) if query else "")),
            "REMOTE_ADDR": "203.0.113.9",
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(body)),
            "wsgi.input": io.BytesIO(body),
            "SERVER_PORT": "443",
            "wsgi.url_scheme": "https",
        }
        for k, v in (headers or {}).items():
            env["HTTP_" + k.upper().replace("-", "_")] = v
        captured = {}

        def start_response(status, headers):
            captured["status"] = status
            captured["headers"] = dict(headers)

        out = b"".join(app(env, start_response))
        return int(str(captured["status"]).split()[0]), captured["headers"], out

    return call


def _app():
    tmp = Path(tempfile.mkdtemp(prefix="v49-"))
    return wsgi.make_app(db_path=str(tmp / "exam.db"), admin_key=ADMIN), tmp


def test_health_and_home():
    app, _ = _app()
    call = _client(app)
    st, hdr, body = call("GET", "/healthz")
    assert st == 200 and json.loads(body)["ok"] is True, (st, body[:120])
    assert hdr["Content-Type"].startswith("application/json")
    st2, hdr2, body2 = call("GET", "/")
    assert st2 == 200 and b"<html" in body2.lower(), st2
    assert "text/html" in hdr2["Content-Type"]
    print("  wsgi: /healthz + landing page served (same routes) ✔")


def test_admin_and_student_pages():
    app, _ = _app()
    call = _client(app)
    for path in ("/admin", "/exam/ABC123", "/manage/ABC123"):
        st, hdr, body = call("GET", path)
        assert st == 200, (path, st)
        assert b"<html" in body.lower(), path
    print("  wsgi: /admin · /exam/<code> · /manage/<code> pages ✔")


def test_poll_endpoints_with_cors():
    app, _ = _app()
    store = app.store
    eid = store.create_exam(code="WSGIT1", admin_token="t", title="wsgi",
                            duration_min=15)["id"]
    store.add_questions(eid, [{"text": "తెలంగాణ రాజధాని?", "options": ["వరంగల్", "హైదరాబాద్"],
                               "correct_index": 1, "explanation": "హైదరాబాద్.", "topic": "GK"}])
    call = _client(app)
    st, hdr, body = call("GET", "/poll/today")
    assert st == 200 and hdr.get("Access-Control-Allow-Origin") == "*", (st, hdr)
    qid = json.loads(body)["qid"]

    payload = json.dumps({"qid": qid, "choice": 1}).encode()
    st2, _, body2 = call("POST", "/poll/vote", body=payload)
    assert st2 == 200 and json.loads(body2)["total"] == 1, (st2, body2[:150])

    st3, hdr3, _ = call("OPTIONS", "/poll/vote")
    assert st3 == 204 and hdr3.get("Access-Control-Allow-Origin") == "*", (st3, hdr3)
    print("  wsgi: /poll/today · /poll/vote · OPTIONS preflight + CORS ✔")


def test_vote_dedup_uses_forwarded_ip():
    app, _ = _app()
    store = app.store
    eid = store.create_exam(code="WSGIT2", admin_token="t", title="wsgi2",
                            duration_min=15)["id"]
    store.add_questions(eid, [{"text": "Q?", "options": ["a", "b"], "correct_index": 0,
                               "explanation": "a.", "topic": "GK"}])
    call = _client(app)
    qid = json.loads(call("GET", "/poll/today")[2])["qid"]
    body = json.dumps({"qid": qid, "choice": 0}).encode()
    first = json.loads(call("POST", "/poll/vote", body=body, headers={"X-Forwarded-For": "5.5.5.5"})[2])
    second = json.loads(call("POST", "/poll/vote", body=body, headers={"X-Forwarded-For": "5.5.5.5"})[2])
    other = json.loads(call("POST", "/poll/vote", body=body, headers={"X-Forwarded-For": "6.6.6.6"})[2])
    assert first["already_voted"] is False and second["already_voted"] is True
    assert other["already_voted"] is False and other["total"] == 2, (first, second, other)
    print("  wsgi: behind a proxy X-Forwarded-For used for 1-vote-per-IP ✔")


def test_admin_ads_api_over_wsgi():
    app, tmp = _app()
    inv = tmp / "inventory.json"
    inv.write_text(json.dumps({"version": 2, "policy": {"label": "SPONSORED"}, "ads": []}),
                   encoding="utf-8")
    os.environ["ADS_INVENTORY_PATH"] = str(inv)
    import importlib
    from autoblog import config as cfg
    importlib.reload(cfg)
    call = _client(app)
    st, _, body = call("GET", "/api/admin/ads", query="key=" + ADMIN)
    assert st == 200 and json.loads(body)["ads"] == [], (st, body[:120])
    payload = json.dumps({"key": ADMIN, "id": "wsgi-ad", "title": "WSGI ప్రకటన ఇక్కడ",
                          "link": "https://example.com/wsgi"}).encode()
    st2, _, body2 = call("POST", "/api/admin/ads", body=payload)
    assert st2 == 200 and json.loads(body2)["ok"] is True, (st2, body2[:150])
    saved = json.loads(inv.read_text(encoding="utf-8"))
    assert [a["id"] for a in saved["ads"]] == ["wsgi-ad"] and saved["version"] == 2
    print("  wsgi: admin ads API (read + save, version/policy preserved) ✔")


def test_errors_stay_clean_json():
    app, _ = _app()
    call = _client(app)
    st, hdr, body = call("GET", "/nope/nothing")
    assert st == 404 and json.loads(body)["error"], (st, body[:120])
    st2, _, body2 = call("POST", "/api/admin/ads", body=b"{not json")
    assert st2 == 400 and json.loads(body2)["code"] == "bad_request", (st2, body2[:150])
    st3, _, body3 = call("PUT", "/healthz")
    assert st3 == 405, (st3, body3[:120])
    print("  wsgi: 404 / bad JSON 400 / unsupported method 405 (all JSON) ✔")


def test_head_and_script_name_subdirectory():
    app, _ = _app()
    eid = app.store.create_exam(code="WSGIT3", admin_token="t", title="wsgi3",
                                duration_min=15)["id"]
    app.store.add_questions(eid, [{"text": "Q?", "options": ["a", "b"], "correct_index": 0,
                                   "explanation": "a.", "topic": "GK"}])
    call = _client(app)
    st, hdr, body = call("HEAD", "/healthz")
    assert st == 200 and body == b"" and hdr["Content-Length"] != "0", (st, hdr, body)
    os.environ["WSGI_SCRIPT_NAME"] = "/exam"
    try:
        call2 = _client(app)
        st2, _, body2 = call2("GET", "/healthz")
        assert st2 == 200 and json.loads(body2)["ok"] is True, (st2, body2[:120])
        st3, _, _ = call2("GET", "/poll/today")
        assert st3 == 200, st3
    finally:
        os.environ.pop("WSGI_SCRIPT_NAME", None)
    print("  wsgi: HEAD support + SCRIPT_NAME subdirectory (/exam) routing ✔")


def test_passenger_entry_file_and_import():
    p = ROOT / "passenger_wsgi.py"
    assert p.exists(), "passenger_wsgi.py missing"
    src = p.read_text(encoding="utf-8")
    assert "from exam_portal.wsgi import application" in src
    assert hasattr(wsgi, "application") and callable(wsgi.application)
    assert hasattr(wsgi.application, "store") and hasattr(wsgi.application, "api")
    print("  wsgi: passenger_wsgi.py entry + module-level application object ✔")


def main() -> None:
    test_health_and_home()
    test_admin_and_student_pages()
    test_poll_endpoints_with_cors()
    test_vote_dedup_uses_forwarded_ip()
    test_admin_ads_api_over_wsgi()
    test_errors_stay_clean_json()
    test_head_and_script_name_subdirectory()
    test_passenger_entry_file_and_import()
    print("ALL v49 WSGI (cPanel/MilesWeb) TESTS PASSED ✔")


if __name__ == "__main__":
    main()
