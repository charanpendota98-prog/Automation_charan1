"""v41 SITE AUDIT + SAFE AUTOFIX + PUBLISH GATE tests.

Sections:
  1. Tag key normalization + category guessing (deterministic)
  2. Post checks — junk HTML, empty title, missing image, wrong category,
     uncategorized, PII, stale dates, unprocessed shortcode, duplicate anchors,
     off-topic entity, mixed image format
  3. Page checks — demo pages, slug/title mismatch, ugly legal slug, duplicate
     contact page
  4. Taxonomy checks — zero-count tags, truncated tag, duplicate tags, empty cats
  5. Site checks — timezone UTC, Local-SEO KML without business location
  6. Fixers — strip_shortcodes / mask_phones / dedupe_anchors (idempotent)
  7. apply_fixes — dry-run default, allow_trash safety, action filter, fake API
  8. merge_tag — lossless (posts reassign before delete)
  9. article_gate — junk blocked live, drafts allowed, good post passes
 10. Demo snapshot audit + report files (markdown/json) + CLI options
 11. Network failure — friendly SiteAuditError (no traceback), retries
 12. Pipeline root-cause gate wiring (source-level proof)
 13. CLI flags exist (--site-audit / -fix / -apply / -trash / -action / -snapshot)
 14. Idempotency — audit twice = same findings; fixers safe on clean input
"""

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from autoblog import site_audit as sa  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


def section(n: int, title: str) -> None:
    print(f"\n── §{n}. {title} " + "─" * max(0, 50 - len(title)))


def ids(findings) -> set:
    return {f["id"] for f in findings}


class FakeAPI:
    """In-memory WP API — writes ni record chestundi (live site touch ledu)."""

    def __init__(self, data=None):
        self.data = data or sa.demo_snapshot()
        self.calls = []
        self.username = "tester"
        self.password = "app-pass"
        self.site = "https://example.test"
        self.session = self          # _set_timezone uses api.session.post

    def can_write(self):
        return True

    # -- reads
    def get(self, path, **params):
        base, *rest = path.split("/", 1)
        if rest and rest[0].isdigit():
            item_id = int(rest[0])
            for item in self.data.get(base, []):
                if item.get("id") == item_id:
                    return item
            raise KeyError(f"{base}/{item_id} not found")
        items = self.data.get(base, [])
        if base == "posts" and params.get("tags"):
            want = params["tags"][0]
            items = [p for p in items if want in (p.get("tags") or [])]
        return items

    # -- writes
    def update(self, kind, item_id, payload):
        self.calls.append(("update", kind, item_id, payload))
        for item in self.data.get(kind, []):
            if item.get("id") == item_id:
                item.update(payload)
        return {"id": item_id}

    def delete(self, kind, item_id, force=False):
        self.calls.append(("delete", kind, item_id, {"force": force}))
        self.data[kind] = [i for i in self.data.get(kind, [])
                           if i.get("id") != item_id]
        return {"deleted": True, "id": item_id}

    def post(self, url, **kwargs):
        self.calls.append(("post", url, kwargs.get("json")))
        return type("R", (), {"status_code": 200, "raise_for_status": lambda s: None})()


# ------------------------------------------------------------------ §1

section(1, "Tag key normalization + category guessing")
assert sa.normalize_tag_key("Fresher") == "fresher"
assert sa.normalize_tag_key("Freshers Jobs") == "fresher"
assert sa.normalize_tag_key("Part Time") == "parttime"
assert sa.normalize_tag_key("Part-time Jobs") == "parttime"
assert sa.normalize_tag_key("Scholarship") == sa.normalize_tag_key("Scholarships")
assert sa.normalize_tag_key("Internship") == sa.normalize_tag_key("Internships")
assert sa.normalize_tag_key("Testbook") == "testbook"
assert sa.normalize_tag_key("") == ""

cats = sa.demo_snapshot()["categories"]
assert sa.guess_category("NSP Scholarship 2026 last date", cats)["name"] == "Scholarships"
assert sa.guess_category("SSC CGL 2026 notification", cats)["name"] == "Central Govt Jobs"
assert sa.guess_category("Walk-in drive for freshers", cats)["name"] == "Walkin Jobs"
# category site lo lekapote None (crash kaadu) — fixable=False avutundi
assert sa.guess_category("Software developer jobs 2026", cats) is None
assert sa.guess_category("Random unrelated headline 12345", cats) is None
print("   ✔ tag keys + deterministic category guessing")


# ------------------------------------------------------------------ §2

section(2, "Post checks (13 classes)")
posts = sa.demo_snapshot()
f = sa.check_posts(posts)
got = ids(f)
for want in ("empty_title", "junk_html_fragment", "missing_featured_image",
             "wrong_category_govt_private", "uncategorized_post", "pii_phone",
             "stale_dates", "unprocessed_shortcode", "duplicate_toc_anchor",
             "off_topic_entity", "mixed_image_format", "wrong_category_walkin",
             "broken_heading_tags"):
    assert want in got, f"{want} missing → {sorted(got)}"
pii = next(x for x in f if x["id"] == "pii_phone")
assert "8977614045" not in pii["evidence"], "raw PII evidence lo undakoodadu"
assert pii["fixable"] and pii["fix_action"] == "strip_pii"
govt = next(x for x in f if x["id"] == "wrong_category_govt_private")
assert govt["severity"] == "high" and govt["fix_params"]["add"], "Private Jobs id kavali"
# private employer in a Govt category is NOT flagged when category is private
clean = {"posts": [{"id": 9, "title": {"rendered": "Optum hiring 2026"},
                    "slug": "optum", "categories": [36], "featured_media": 1,
                    "content": {"rendered": "<p>apply online</p>"}}],
         "categories": cats, "media": [], "tags": [], "pages": []}
assert "wrong_category_govt_private" not in ids(sa.check_posts(clean))
print(f"   ✔ {len(f)} findings, {len(got)} distinct classes (no raw PII in report)")


# ------------------------------------------------------------------ §3

section(3, "Page checks")
pf = sa.check_pages(posts)
pid = ids(pf)
assert "demo_page_live" in pid and "slug_title_mismatch" in pid
assert "ugly_legal_slug" in pid and "duplicate_contact_page" in pid
demo = [x for x in pf if x["id"] == "demo_page_live"]
assert all(x["fixable"] and x["fix_action"] == "trash_page" for x in demo)
single = {"pages": [{"id": 17, "title": {"rendered": "Contact Us"},
                     "slug": "contact-us", "link": "x", "content": {"rendered": "c"}}]}
assert "duplicate_contact_page" not in ids(sa.check_pages(single)), \
    "okate contact page unte flag avvakoodadu"
print(f"   ✔ {len(pf)} page findings (demo pages + slug/title + duplicate contact)")


# ------------------------------------------------------------------ §4

section(4, "Taxonomy checks")
tf = sa.check_taxonomy(posts)
tid = ids(tf)
assert "zero_count_tags" in tid and "duplicate_tags" in tid and "empty_categories" in tid
assert "truncated_tag_name" in tid, "truncated tag name pattukovali"
dup = [x for x in tf if x["id"] == "duplicate_tags"]
assert len(dup) == 2, f"Fresher + Part-time merge suggestions raavali: {len(dup)}"
for d in dup:
    p = d["fix_params"]
    assert p["keep"] and p["drop"] and p["keep"] not in p["drop"]
    assert d["fix_action"] == "merge_tags"
zero = next(x for x in tf if x["id"] == "zero_count_tags")
assert len(zero["fix_params"]["ids"]) == 5
print(f"   ✔ {len(tf)} taxonomy findings, {len(dup)} duplicate-tag merges, "
      f"{len(zero['fix_params']['ids'])} zero-count tags")


# ------------------------------------------------------------------ §5

section(5, "Site checks")
sf = sa.check_site(posts)
sid = ids(sf)
assert "timezone_utc" in sid and "local_seo_without_location" in sid
tz = next(x for x in sf if x["id"] == "timezone_utc")
assert tz["fix_params"]["timezone"] == "Asia/Kolkata"
ok_settings = {"settings": {"timezone_string": "Asia/Kolkata", "gmt_offset": "5.5"},
               "kml": False, "posts": [], "pages": [], "categories": [], "tags": []}
assert sa.check_site(ok_settings) == [], "clean site lo findings undakoodadu"
print("   ✔ timezone + local-SEO findings (clean site = zero findings)")


# ------------------------------------------------------------------ §6

section(6, "Fixers (pure functions)")
st = sa.strip_shortcodes
assert st("<p>a [adinsert block=1] b</p>", ["adinsert"]) == "<p>a  b</p>"
kept = st("<p>[embed]x[/embed]</p>", ["adinsert"])
assert "[embed]x[/embed]" in kept, "safe shortcodes ni touch cheyyakoodadu"
_stripped = st("<p>[adinsert]\n\n\n</p>", ["adinsert"])
assert "[adinsert]" not in _stripped and _stripped.strip().startswith("<p>")
assert sa.mask_phones("call 9876543210") == "call 98XXXXX10"
assert sa.mask_phones("+91 8977614045 and 12345") == "89XXXXX45 and 12345"
assert sa.mask_phones(sa.mask_phones("9876543210")) == "98XXXXX10", "idempotent"
d = sa.dedupe_anchors
assert d('<h2 id="a">x</h2>') == '<h2 id="a">x</h2>'
two = '<h2 id="amp">A</h2><a href="#amp">t</a><h2 id="amp">B</h2><a href="#amp">u</a>'
out = d(two)
assert 'id="amp"' in out and 'id="amp-2"' in out
assert 'href="#amp"' in out and 'href="#amp-2"' in out
assert d(out) == out, "idempotent avvali"
assert d('<h2 id="amp">A</h2>' * 3).count('id="amp-3"') == 1
print("   ✔ shortcode/PII/anchor fixers (idempotent)")


# ------------------------------------------------------------------ §7

section(7, "apply_fixes (dry-run default + safety gates)")
data = sa.demo_snapshot()
api = FakeAPI(json.loads(json.dumps(data)))
res = sa.audit_site(data=data)
dry = sa.apply_fixes(api, res["findings"], dry_run=True)
assert api.calls == [], "dry-run lo e write call undakoodadu"
assert len(dry["applied"]) == res["summary"]["fixable"] and not dry["errors"]
assert all(a.get("dry_run") for a in dry["applied"])
# real apply without trash permission → destructive ops skipped
live = sa.apply_fixes(api, res["findings"], dry_run=False)
kinds = {(c[0], c[1]) for c in api.calls}
assert ("delete", "pages") not in kinds, "allow_trash ledu → page delete undakoodadu"
assert any(k == "update" for k, _ in [(c[0], c[1]) for c in api.calls]), "updates jaragali"
skipped_why = {s["why"] for s in live["skipped"]}
assert any("allow_trash" in w for w in skipped_why), sorted(skipped_why)
# action filter
api2 = FakeAPI(json.loads(json.dumps(data)))
only = sa.apply_fixes(api2, res["findings"], dry_run=False, actions=["strip_pii"])
assert all(a["action"] == "strip_pii" for a in only["applied"])
assert len([c for c in api2.calls if c[0] == "update"]) == 1, api2.calls
assert len(only["applied"]) == 1, only
# trash permission on → page drafts/trash jaragali
api3 = FakeAPI(json.loads(json.dumps(data)))
with_trash = sa.apply_fixes(api3, res["findings"], dry_run=False, allow_trash=True)
assert any(c[0] == "delete" and c[1] == "pages" for c in api3.calls), \
    "allow_trash tho demo page trash avvali"
assert not with_trash["errors"], with_trash["errors"]
print(f"   ✔ dry-run {len(dry['applied'])} planned · live {len(live['applied'])} applied "
      f"· {len(live['skipped'])} skipped (safe)")


# ------------------------------------------------------------------ §8

section(8, "merge_tag — lossless")
api4 = FakeAPI()
api4.data["posts"] = [
    {"id": 501, "tags": [2], "categories": [1], "title": {"rendered": "A"}},
    {"id": 502, "tags": [2, 9], "categories": [1], "title": {"rendered": "B"}},
]
moved = sa.merge_tag(api4, keep_id=1, drop_id=2)
assert moved == 2, moved
assert api4.data["posts"][0]["tags"] == [1], api4.data["posts"][0]["tags"]
assert sorted(api4.data["posts"][1]["tags"]) == [1, 9], api4.data["posts"][1]["tags"]
assert 2 not in [t["id"] for t in api4.data["tags"]], "drop tag delete avvali"
print("   ✔ merge_tag posts reassign chesi drop tag delete (association loss ledu)")


# ------------------------------------------------------------------ §9

section(9, "article_gate (root-cause publish gate)")
good = {
    "title": "SSC CGL 2026 Notification: Apply Online Last Date Details",
    "meta_description": ("SSC CGL 2026 notification apply online process, eligibility "
                         "criteria, important dates and official website link details "
                         "for Telugu students."),
    "status": "publish", "has_image": True, "category": "Central Govt Jobs",
    "content": "<h2 id=\"a\">Overview</h2>" + "<p>" + ("word " * 400) + "</p>",
}
ok, msg = sa.article_gate(good)
assert ok is True, msg
bad = dict(good, title="Optum Jobs 2026\u2011today", meta_description="x",
           has_image=False,
           content="<title>junk</title>[adinsert block=1]"
                   "<h2 id=\"amp\">a</h2><h2 id=\"amp\">b</h2>"
                   "<p>Call 9876543210 " + ("word " * 200) + "</p>")
ok, msg = sa.article_gate(bad)
assert ok is False and "V41 SITE GATE" in msg
for frag in ("title", "featured image", "shortcode", "duplicate anchor"):
    assert frag in msg, f"'{frag}' msg lo undali: {msg}"
assert sa.article_gate(dict(bad, status="draft"))[0] is True, "draft lu allow"
assert sa.article_gate(bad, live=False)[0] is True
off = dict(good, title="Jobe Bellingham football inspiration for students")
assert sa.article_gate(off)[0] is False, "off-topic entity block avvali"
telugu = dict(good, title="SSC CGL 2026 \u0c28\u0c4b\u0c1f\u0c3f\u0c2b\u0c3f\u0c15\u0c47\u0c37\u0c28\u0c4d \u0c35\u0c3f\u0c35\u0c30\u0c3e\u0c32\u0c41 \u0c2e\u0c30\u0c3f\u0c2f\u0c41 \u0c26\u0c30\u0c16\u0c3e\u0c38\u0c41")
assert sa.article_gate(telugu)[0] is True, "Telugu title length valid (chars count)"
print(f"   ✔ live block + draft allow + gap-list proof: {msg[:90]}…")


# ------------------------------------------------------------------ §10

section(10, "Demo snapshot audit + report files + CLI")
demo = sa.audit_site(snapshot="demo")
assert demo["summary"]["findings"] >= 20
assert demo["summary"]["by_severity"]["high"] >= 8
with tempfile.TemporaryDirectory() as td:
    paths = sa.write_report(demo, td)
    md = Path(paths["md"]).read_text(encoding="utf-8")
    js = json.loads(Path(paths["json"]).read_text(encoding="utf-8"))
    assert "Site Audit" in md and "🔴" in md
    assert js["summary"]["findings"] == demo["summary"]["findings"]
    assert Path(paths["latest"]).exists()
    snap = sa.save_snapshot(demo["data"], Path(td) / "snap.json")
    back = sa.audit_site(snapshot=snap)
    assert back["summary"]["findings"] == demo["summary"]["findings"], \
        "snapshot round-trip same findings ivvali"
print(f"   ✔ demo audit {demo['summary']['findings']} findings · report md/json + "
      f"snapshot round-trip")


# ------------------------------------------------------------------ §11

section(11, "Network failure → friendly error (no traceback)")
class Boom:
    def __init__(self):
        self.headers = {}
        self.auth = None

    def get(self, *a, **k):
        raise sa.requests.exceptions.SSLError("connection closed")

    def request(self, *a, **k):
        raise sa.requests.exceptions.SSLError("connection closed")


api_boom = sa.SiteAPI(site="https://blocked.test", session=Boom())
import time as _time  # noqa: E402
t0 = _time.time()
try:
    sa.collect(api_boom)
    raise AssertionError("SiteAuditError raise avvali")
except sa.SiteAuditError as exc:
    took = _time.time() - t0
    assert "reach avvatledu" in str(exc)
    assert "snapshot" in str(exc), "guidance lo snapshot option undali"
assert took >= 3.0, f"retries jaragali (took {took:.1f}s)"
assert sa.SiteAPI(session=Boom()).can_write() is False or True  # no crash
print("   ✔ retry + friendly SiteAuditError (traceback ledu, guidance tho)")


# ------------------------------------------------------------------ §12

section(12, "Pipeline root-cause gate wiring")
src = (ROOT / "autoblog" / "pipeline.py").read_text(encoding="utf-8")
assert "site_audit as _sa" in src and "article_gate(" in src
assert "LIVE-PUBLISH BLOCKED" in src
assert re.search(r"ok_site, detail_site = _sa\.article_gate\(\s*\n?\s*article, html=final_html",
                 src), "final_html tho gate call avvali"
main_src = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
assert "def site_audit_run(" in main_src and "site_audit.run_audit(" in main_src
print("   ✔ pipeline + main.py wiring confirmed")


# ------------------------------------------------------------------ §13

section(13, "CLI flags")
help_out = subprocess.run([sys.executable, str(ROOT / "run.py"), "--help"],
                          capture_output=True, text=True, timeout=120).stdout
for flag in ("--site-audit", "--site-audit-fix", "--site-audit-apply",
             "--site-audit-trash", "--site-audit-action", "--site-audit-snapshot",
             "--site-audit-save"):
    assert flag in help_out, f"{flag} help lo ledu"
demo_cli = subprocess.run(
    [sys.executable, str(ROOT / "run.py"), "--site-audit",
     "--site-audit-snapshot", "demo"],
    capture_output=True, text=True, timeout=180)
assert demo_cli.returncode == 0, demo_cli.stderr[-500:]
assert "SITE AUDIT" in demo_cli.stdout and "Findings:" in demo_cli.stdout
assert "Report:" in demo_cli.stdout
print("   ✔ all 7 flags + demo CLI run (exit 0, report written)")


# ------------------------------------------------------------------ §14

section(14, "Determinism / idempotency")
a = sa.audit_site(snapshot="demo")["findings"]
b = sa.audit_site(snapshot="demo")["findings"]
key = lambda fl: [(x["id"], x["target_id"], x["evidence"]) for x in fl]  # noqa: E731
assert key(a) == key(b), "audit deterministic ga undali"
clean_post = {"posts": [{"id": 1, "title": {"rendered": "Clean Post Title 2026"},
                         "slug": "clean", "categories": [36], "featured_media": 1,
                         "content": {"rendered": "<h2 id=\"a\">H</h2><p>text</p>"}}],
              "categories": cats, "media": [], "tags": [], "pages": []}
assert sa.check_posts(clean_post) == [], "clean post lo findings undakoodadu"
assert sa.strip_shortcodes("no shortcode here", ["adinsert"]) == "no shortcode here"
print("   ✔ audit twice = same findings · clean input = zero findings")

print("\n" + "=" * 62)
print("  ALL v41 SITE AUDIT TESTS PASSED ✔")
print("=" * 62)
