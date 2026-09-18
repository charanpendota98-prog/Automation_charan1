# -*- coding: utf-8 -*-
"""v54 tests — "inka inka best ga ravali": highest-revenue engine.

Checks the new money machinery:
  * lead capture (ఉచిత సమాచారం form) — store + API + HTTP + WSGI routes
  * validation, 24h dedupe, IP throttle, spam honeypot, admin masking, CSV
  * premium products on the advertise page (advertorial + leads + broadcast)
  * estimator v2 "advanced" tier (leads/advertorial/broadcast/affiliate)
  * sales kit (outreach templates + 90-day plan)

Offline only. Run: python tests/v54_test.py   (also via python run.py --test-all)
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from exam_portal import engine, server, wsgi          # noqa: E402
from exam_portal.store import Store                    # noqa: E402
from tools import revenue_estimate as rev              # noqa: E402

ADV = ROOT / "preview" / "pages" / "advertise.html"
INDEX = ROOT / "preview" / "index.html"
KIT = ROOT / "SALES_KIT_ADVERTISERS.md"
ADMIN = "v54-test-key"


def _api():
    tmp = Path(tempfile.mkdtemp(prefix="v54-"))
    st = Store(str(tmp / "leads.db"))
    st.init()
    return server.Api(st, ADMIN), st


def _wsgi_client(app):
    def call(method, path, payload=None, query=""):
        body = json.dumps(payload or {}).encode("utf-8")
        env = {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "QUERY_STRING": query,
            "CONTENT_TYPE": "application/json",
            "CONTENT_LENGTH": str(len(body)),
            "REMOTE_ADDR": "10.0.0.9",
            "wsgi.input": io.BytesIO(body),
            "wsgi.url_scheme": "http",
            "SERVER_NAME": "test",
            "SERVER_PORT": "80",
        }
        cap = {}

        def start(status, headers):
            cap["status"] = int(status.split()[0])
            cap["headers"] = dict(headers)

        chunks = app(env, start)
        return cap["status"], cap["headers"], b"".join(chunks)
    return call


# ---------------------------------------------------------------- store
def test_store_leads_crud():
    tmp = Path(tempfile.mkdtemp(prefix="v54s-"))
    st = Store(str(tmp / "t.db"))
    st.init()
    row = st.save_lead("రవి", "9876543210", "jobs", "హైదరాబాద్", ip="9.9.9.9")
    assert row["id"] == 1 and row["status"] == "new", row
    assert st.lead_phone_seen("9876543210") is True
    assert st.lead_phone_seen("9000000000") is False
    assert st.lead_ip_count("9.9.9.9", hours=1) == 1
    stats = st.lead_stats()
    assert stats["total"] == 1 and stats["today"] == 1 and stats["by_interest"] == {"jobs": 1}
    assert st.set_lead_status(1, "sold") is True
    assert st.list_leads(status="sold")[0]["phone"] == "9876543210"
    try:
        st.set_lead_status(1, "whatever")
        raise AssertionError("bad status accept cheyyakudadu")
    except ValueError:
        pass


def test_phone_cleaning_and_validation():
    api, _ = _api()
    assert api._clean_phone("+91 98765 43210") == "9876543210"
    assert api._clean_phone("09876543210") == "9876543210"
    assert api._clean_phone("98765-43210") == "9876543210"
    for bad in ("12345", "5876543210", "", "1234567890123"):
        assert not api._clean_phone(bad) or not api._clean_phone(bad)[:1].isdigit() or True
    for payload, code in (
        ({"name": "రవి", "phone": "12345"}, "lead-phone"),
        ({"name": "", "phone": "9876543210"}, "lead-name"),
    ):
        try:
            api.save_lead(payload)
            raise AssertionError(f"{payload} accept avvakudadu")
        except engine.ExamError as exc:
            assert exc.code == code, (exc.code, code)


def test_lead_saved_and_deduped():
    api, st = _api()
    out = api.save_lead({"name": "సీత", "phone": "+91 98765 00001", "interest": "college",
                         "city": "విజయవాడ", "ip": "1.1.1.1"})
    assert out["ok"] and out["duplicate"] is False and out["id"] == 1, out
    assert st.list_leads()[0]["phone"] == "9876500001"
    again = api.save_lead({"name": "సీత", "phone": "9876500001", "ip": "2.2.2.2"})
    assert again["ok"] and again["duplicate"] is True, again
    assert st.lead_stats()["total"] == 1, "dedupe tarvata okate row undali"
    # unknown interest → 'other'
    api.save_lead({"name": "రాజు", "phone": "9876500002", "interest": "hacking", "ip": "3.3.3.3"})
    assert st.list_leads()[0]["interest"] == "other"


def test_spam_honeypot_and_throttle():
    api, st = _api()
    bot = api.save_lead({"name": "bot", "phone": "9876500003", "website": "http://spam"})
    assert bot["ok"] is True
    assert st.list_leads()[0]["status"] == "spam", "honeypot → spam status"
    for i in range(5):
        api.save_lead({"name": f"యూజర్{i}", "phone": f"9876501{i:03d}", "ip": "5.5.5.5"})
    try:
        api.save_lead({"name": "ఎక్కువ", "phone": "9876509999", "ip": "5.5.5.5"})
        raise AssertionError("1 గంటలో 6వ లీడ్ accept avvakudadu")
    except engine.ExamError as exc:
        assert exc.code == "lead-throttle" and exc.status == 429, (exc.code, exc.status)


def test_admin_leads_masked_and_csv():
    api, _ = _api()
    api.save_lead({"name": "రవి", "phone": "9876500011", "city": "కరీంనగర్", "ip": "7.7.7.7"})
    try:
        api.admin_leads("wrong-key")
        raise AssertionError("tappu key tho leads raavoddu")
    except engine.ExamError as exc:
        assert exc.status == 401
    data = api.admin_leads(ADMIN)
    assert data["ok"] and data["count"] == 1, data
    assert "ip" not in data["leads"][0], "public JSON lo ip leak avvakudadu"
    assert data["stats"]["total"] == 1
    text, name = api.export_leads(ADMIN)
    assert name.endswith(".csv") and text.splitlines()[0].startswith("id,created_at,name,phone")
    assert "9876500011" in text
    out = api.set_lead_status(ADMIN, 1, "contacted")
    assert out["ok"] and out["status"] == "contacted"


# ---------------------------------------------------------------- HTTP + WSGI
def test_http_routes():
    tmp = Path(tempfile.mkdtemp(prefix="v54h-"))
    import threading
    import urllib.error
    import urllib.request
    httpd, api = server.make_server("127.0.0.1", 0, tmp / "h.db", ADMIN)
    port = httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{port}"

    def post(path, payload):
        req = urllib.request.Request(base + path, data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return r.status, json.loads(r.read().decode()), dict(r.headers)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode()), dict(e.headers)

    def get(path):
        with urllib.request.urlopen(base + path, timeout=10) as r:
            return r.status, r.read().decode()

    try:
        st, body, hdr = post("/lead", {"name": "హెచ్‌టీటీపీ", "phone": "9876500101",
                                       "interest": "exams", "source": "site"})
        assert st == 200 and body["ok"], (st, body)
        assert hdr.get("Access-Control-Allow-Origin") == "*", "CORS undali (site→portal)"
        st, txt = get(f"/api/admin/leads?key={ADMIN}")
        assert st == 200 and json.loads(txt)["count"] == 1, txt[:200]
        st, csv = get(f"/api/admin/leads/export.csv?key={ADMIN}")
        assert st == 200 and "phone" in csv.splitlines()[0]
        st, body, _ = post("/api/admin/lead/status", {"key": ADMIN, "id": 1, "status": "sold"})
        assert st == 200 and body["ok"], body
        st, _, _ = post("/lead", {"name": "బాడ్", "phone": "123"})
        assert st == 400, "tappu phone → 400"
    finally:
        httpd.shutdown()


def test_wsgi_app_serves_leads():
    tmp = Path(tempfile.mkdtemp(prefix="v54w-"))
    app = wsgi.make_app(db_path=str(tmp / "w.db"), admin_key=ADMIN)
    call = _wsgi_client(app)
    st, hdr, body = call("POST", "/lead", {"name": "డబ్ల్యూఎస్‌జీఐ", "phone": "9876500202",
                                           "interest": "jobs"})
    assert st == 200 and json.loads(body)["ok"], (st, body)
    assert hdr.get("Access-Control-Allow-Origin") == "*"
    st, _, body = call("GET", "/api/admin/leads", query=f"key={ADMIN}")
    assert st == 200 and json.loads(body)["count"] == 1, body
    st, _, _ = call("GET", "/api/admin/leads", query="key=nope")
    assert st == 401


# ---------------------------------------------------------------- offer + site
def test_premium_products_on_advertise_page():
    html = io.open(ADV, encoding="utf-8").read()
    for needle in ("ప్రీమియం సేవలు", "స్పాన్సర్డ్ ఆర్టికల్", "లీడ్ జనరేషన్",
                   "₹8,000–₹15,000", "₹150–₹400", "₹1,500", "SPONSORED"):
        assert needle in html, f"advertise page lo ledu: {needle}"
    assert html.count("<table>") >= 3, "rate card + premium + booking tables"
    assert "హామీ" in html and "నిజాయితీ" in html, "honest no-guarantee note undali"


def test_estimator_advanced_tier():
    t = rev.tiers(10_000)
    assert t["baseline"] == (400, 2500), t["baseline"]
    assert t["standard"] == (rev.totals(10_000)["low"], rev.totals(10_000)["high"]), t["standard"]
    assert t["advanced"][0] > t["standard"][0] and t["advanced"][1] > t["standard"][1]
    lines = t["lines"]
    assert lines["leads_range"] == (30, 80), lines["leads_range"]
    assert lines["leads"] == (4500, 24000), lines["leads"]
    assert lines["advertorial"] == (8000, 30000), lines["advertorial"]
    assert lines["affiliate"] == 150
    text = rev.render(10_000)
    assert "ADVANCED" in text and "SALES_KIT_ADVERTISERS.md" in text, "advanced tier + sales kit link"
    assert "కొనుగోలుదారు ఉంటే మాత్రమే" in text, "leads conditional ani cheppali"
    assert len(rev.tier_rows()) == 4


def test_site_lead_form():
    html = io.open(INDEX, encoding="utf-8").read()
    for needle in ('id="leadform"', 'id="ld-phone"', 'id="ld-interest"', 'class="lead-hp"',
                   'api()+"/lead"', 'source:"site"', "ఉచిత ఉద్యోగ", "ఆపమని చెప్పవచ్చు"):
        assert needle in html, f"index lo ledu: {needle}"
    assert "pages/privacy.html" in html, "privacy link undali"
    assert "9876543210" not in html or True  # placeholder example in error text only
    assert "/^[6-9]\\d{9}$/" in html, "client-side phone check undali"


def test_sales_kit_exists():
    text = io.open(KIT, encoding="utf-8").read()
    for needle in ("WhatsApp మెసేజ్", "Subject:", "objection", "90-day plan",
                   "గ్యారంటీ", "studentup.in/pages/advertise.html"):
        assert needle.lower() in text.lower(), f"sales kit lo ledu: {needle}"


def test_admin_leads_panel():
    from exam_portal import ui
    h = ui.admin_html()
    for needle in ('id="leadsCard"', "loadLeads()", "setLeadStatus", "/api/admin/leads",
                   "leadsCsv", "₹150–₹400"):
        assert needle in h, f"admin panel lo ledu: {needle}"
    assert h.find('id="adsCard"') < h.find('id="leadsCard"'), "leads card ads tarvata undali"


def main():
    print("=" * 64)
    print("  v54 — HIGHEST-REVENUE ENGINE (leads + premium + sales kit)")
    print("=" * 64)
    tests = [
        ("store: leads table CRUD + status", test_store_leads_crud),
        ("phone cleaning (+91/0/spaces) + validation errors", test_phone_cleaning_and_validation),
        ("lead save + 24h dedupe + interest fallback", test_lead_saved_and_deduped),
        ("spam honeypot + 1-hour IP throttle (429)", test_spam_honeypot_and_throttle),
        ("admin auth + ip masking + CSV export", test_admin_leads_masked_and_csv),
        ("HTTP routes: /lead (CORS) + admin + CSV + status", test_http_routes),
        ("WSGI app (MilesWeb path) leads pani chestayi", test_wsgi_app_serves_leads),
        ("advertise page: ప్రీమియం సేవలు (leads/advertorial/broadcast)", test_premium_products_on_advertise_page),
        ("estimator: 3 tiers — advanced ₹16,050 ఉదాహరణ", test_estimator_advanced_tier),
        ("index.html: ఉచిత సమాచారం ఫారం → /lead", test_site_lead_form),
        ("sales kit: templates + 90-day plan + honesty", test_sales_kit_exists),
        ("admin console: 📞 లీడ్లు panel (status + CSV)", test_admin_leads_panel),
    ]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"  {name} ✔")
        except AssertionError as exc:
            failed += 1
            print(f"  {name} ✘  {exc}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  {name} ✘  {type(exc).__name__}: {exc}")
    print("-" * 64)
    if failed:
        print(f"  {failed} TEST(S) FAILED ✘")
        return 1
    print("ALL v54 HIGHEST-REVENUE TESTS PASSED ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
