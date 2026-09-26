"""v41 — Site-wide Deep Audit + Safe Autofix (studentup.in jaise top sites).

Problem: live site lo thin pages, wrong categories, junk HTML, PII, unprocessed
shortcodes, demo pages, tag bloat, duplicate anchors — ivi human ga pattukovadam
kastam, malli malli vasthayi. Ee module **okka scan lo anni** pattukuni, safe
fixes ni (dry-run default) apply chestundi + malli raakunda gates istundi.

Design (mistakes lekunda):
  * READ-ONLY audit — credentials lekunda kuda pani chestundi (public REST).
  * Prathi finding ki: id, severity, evidence, fix, fixable, fix_action.
  * WRITES eppudu explicit — `--site-audit-fix` + `--site-audit-apply` (dry-run
    default). Junk/off-topic pages delete kaadu — **draft/trash** matrame.
  * Prathi fixer deterministic + audit log (.json) — reversible (WP revision).

Checks (v41): empty title · junk HTML fragment · missing featured image ·
wrong category (private MNC in Govt category, walk-in in Internships) ·
Uncategorized · PII phone numbers · stale event dates · unprocessed ad
shortcodes · duplicate TOC anchors · mixed image formats · off-topic entities ·
truncated tag names · duplicate tags (EN/TE variants) · zero-count tag bloat ·
empty categories · theme-demo pages live · slug/title mismatch (About us in
privacy-policy) · duplicate contact pages · UTC timezone · Local-SEO KML without
business location.

Fixers (safe set): draft junk post · set/remove categories · strip shortcode ·
mask PII · dedupe anchors · purge zero-count tags · trash demo page · update
page slug · set timezone · remove duplicate contact page (draft).
"""

from __future__ import annotations

import html as html_mod
import json
import logging
import re
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import requests

from . import config

log = logging.getLogger(__name__)


class SiteAuditError(RuntimeError):
    """Audit ki kavalsina data fetch avvakapoyinappudu (network/auth)."""


SITE = config.WP_SITE
TIMEOUT = getattr(config, "HTTP_TIMEOUT", 30)
OUT_DIR = Path(__file__).resolve().parent.parent / "output" / "audit"

# --------------------------------------------------------------------- lists

PRIVATE_EMPLOYERS = [
    "optum", "unitedhealth", "electronics mart", "amazon", "google", "microsoft",
    "infosys", "tcs", "tata consultancy", "wipro", "accenture", "cognizant",
    "flipkart", "zoho", "deloitte", "hcl", "tech mahindra", "capgemini", "ibm",
    "oracle", "sap", "adobe", "meta", "netflix", "swiggy", "zomato", "paytm",
    "phonepe", "freshworks", "mphasis", "ltimindtree", "cgi", "virtusa",
    "genpact", "concentrix", "teleperformance",
]
GOVT_HINTS = ("govt", "government", "central", "state", "psu", "railway", "bank")
WALKIN_HINTS = ("walk-in", "walkin", "walk in", "walk\u2011in", "job fair", "mega drive")
OFFTOPIC_ENTITIES = [
    "bellingham", "football", "cricket", "ipl", "box office", "movie", "actor",
    "actress", "song", "serial", "bigg boss",
]
DEMO_PAGE_SIGNATURES = [
    "button & separator", "button and separator", "image & gallery block",
    "image and gallery block", "table block", "quote block", "columns block",
    "left sidebar", "right sidebar", "default width", "narrow width",
]
SHORTCODE_RE = re.compile(r"\[([a-zA-Z_][\w-]*)(?:\s[^\]\n]{0,60})?\]")
SHORTCODE_SAFE = {"embed", "caption", "gallery", "contact-form-7", "wpforms"}
PHONE_RE = re.compile(r"(?:(?:\+|00)91[\s-]?)?\b([6-9]\d{9})\b")
ANCHOR_RE = re.compile(r"href=[\"']#([^\"']+)[\"']")
HEADING_ID_RE = re.compile(r"<h([2-4])[^>]*\sid=[\"']([^\"']+)[\"']", re.I)
JUNK_HTML = ["<title>", "<header>", "<footer>", "<meta ", "100/100 seo",
             "<!doctype", "</figure>"]
DATE_RANGE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2}\s*[\u2013\u2014-]\s*"
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+\d{1,2},?\s*(\d{4})", re.I)
DATE_SINGLE_RE = re.compile(
    r"(January|February|March|April|May|June|July|August|September|October|"
    r"November|December)\s+(\d{1,2}),?\s*(\d{4})", re.I)
MIXED_IMG_RE = re.compile(r"\.(?:jpe?g|png|gif|webp)\.webp(?:$|[?#])", re.I)
TRUNCATED_TAG_RE = re.compile(r"^(.{28,}?)[a-z]$")


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_date(value: str) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


# ------------------------------------------------------------------- finding

def finding(fid: str, severity: str, kind: str, title: str, evidence: str,
            fix: str, fixable: bool = False, fix_action: str = "",
            fix_params: Optional[Dict[str, Any]] = None,
            target_id: int = 0, target_title: str = "", slug: str = "",
            link: str = "") -> Dict[str, Any]:
    return {
        "id": fid, "severity": severity, "kind": kind, "title": title,
        "evidence": evidence[:400], "fix": fix, "fixable": bool(fixable),
        "fix_action": fix_action, "fix_params": fix_params or {},
        "target_id": target_id, "target_title": target_title[:120],
        "slug": slug, "link": link,
    }


SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "info": 3}


# ----------------------------------------------------------------------- API

class SiteAPI:
    """Thin REST wrapper — reads public ga, writes ki credentials kavali."""

    def __init__(self, site: str = "", username: str = "", password: str = "",
                 session: Optional[requests.Session] = None):
        self.site = (site or SITE).rstrip("/")
        self.username = username or config.WP_USERNAME
        self.password = password or config.WP_APP_PASSWORD
        self.session = session or requests.Session()
        self.session.headers.setdefault("User-Agent", "studentup-site-audit/1.0")
        if self.username and self.password:
            self.session.auth = (self.username, self.password)

    # -- reads (retry + friendly errors: egress block / DNS / TLS / 5xx)
    def _fetch(self, url: str, params: Optional[Dict] = None,
               tries: int = 3) -> Any:
        last: Optional[Exception] = None
        for attempt in range(1, tries + 1):
            try:
                resp = self.session.get(url, params=params, timeout=TIMEOUT)
                if resp.status_code >= 500:
                    raise requests.HTTPError(f"HTTP {resp.status_code}")
                resp.raise_for_status()
                return resp.json()
            except (requests.RequestException, ValueError) as exc:
                last = exc
                if attempt < tries:
                    time.sleep(1.5 * attempt)
        raise SiteAuditError(
            f"{url} reach avvatledu ({type(last).__name__}: {str(last)[:120]}). "
            "Check: (1) WP_SITE correct-a? (2) mee network/proxy studentup.in ki "
            "allow chestunda? (3) leda --site-audit-snapshot FILE tho offline run "
            "cheyandi (mee machine lo --site-audit-save FILE tho export).")

    def get(self, path: str, **params) -> Any:
        return self._fetch(f"{self.site}/wp-json/wp/v2/{path.lstrip('/')}", params)

    def get_root(self) -> Dict:
        try:
            data = self._fetch(f"{self.site}/wp-json/", tries=2)
            return data if isinstance(data, dict) else {}
        except SiteAuditError:
            log.warning("wp-json root read fail — settings checks skip avutayi")
            return {}

    def paginate(self, path: str, **params) -> List[Dict]:
        out: List[Dict] = []
        page = 1
        per_page = int(params.pop("per_page", 100))
        while page <= 20:
            try:
                chunk = self.get(path, per_page=per_page, page=page, **params)
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 400:
                    break          # page beyond range
                raise
            if not isinstance(chunk, list) or not chunk:
                break
            out.extend(chunk)
            if len(chunk) < per_page:
                break
            page += 1
        return out

    def kexml_exists(self) -> bool:
        try:
            resp = self.session.get(f"{self.site}/locations.kml", timeout=TIMEOUT)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    # -- writes (auth required)
    def can_write(self) -> bool:
        return bool(self.username and self.password)

    def update(self, kind: str, item_id: int, payload: Dict) -> Dict:
        if not self.can_write():
            raise PermissionError("Write ki WP_USERNAME/WP_APP_PASSWORD kavali (.env)")
        url = f"{self.site}/wp-json/wp/v2/{kind}/{item_id}"
        resp = self.session.post(url, json=payload, timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()

    def delete(self, kind: str, item_id: int, force: bool = False) -> Dict:
        if not self.can_write():
            raise PermissionError("Delete ki WP creds kavali (.env)")
        url = f"{self.site}/wp-json/wp/v2/{kind}/{item_id}"
        resp = self.session.delete(url, params={"force": "true" if force else "false"},
                                   timeout=TIMEOUT)
        resp.raise_for_status()
        return resp.json()


# ------------------------------------------------------------------ collect

def collect(api: SiteAPI) -> Dict[str, Any]:
    """Site data okka sari fetch (posts/pages/categories/tags/media/settings)."""
    data: Dict[str, Any] = {}
    data["posts"] = api.paginate("posts", _fields=(
        "id,title,slug,link,date,modified,status,categories,featured_media,"
        "excerpt,content"))
    data["pages"] = api.paginate("pages", _fields=(
        "id,title,slug,link,date,status,content,parent,template"))
    data["categories"] = api.paginate("categories", _fields="id,name,slug,count")
    data["tags"] = api.paginate("tags", _fields="id,name,slug,count")
    try:
        data["media"] = api.paginate("media", _fields="id,source_url,alt_text,title")
    except (requests.HTTPError, SiteAuditError):
        data["media"] = []
    data["settings"] = api.get_root()
    data["kml"] = api.kexml_exists()
    return data


def load_snapshot(path: Any) -> Dict[str, Any]:
    """Offline audit kosam snapshot JSON load (str 'demo' → demo_snapshot())."""
    if path == "demo":
        return demo_snapshot()
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    # Snapshot ki {'data': {...}} leda nerugaa data dict rendu accept cheyyali.
    return raw.get("data", raw) if isinstance(raw, dict) else raw


def save_snapshot(data: Dict[str, Any], path: Any) -> str:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2, default=str),
                   encoding="utf-8")
    return str(out)


def demo_snapshot() -> Dict[str, Any]:
    """Offline demo — studentup.in lo nijamga pattukunna 21 problem classes
    ke synthetic fixture (tests + preview ki; real audit mee machine lo run chey).
    """
    def p(pid, title, slug, cats, media, content, link=""):
        return {"id": pid, "title": {"rendered": title}, "slug": slug,
                "link": link or f"{SITE}/{slug}/", "categories": cats,
                "featured_media": media, "content": {"rendered": content},
                "date": "2026-08-01T00:00:00", "modified": "2026-08-01T00:00:00",
                "status": "publish"}

    filler = "<p>" + ("Ee article lo exam notification details, eligibility, "
                      "application process, important dates mariyu official link "
                      "vivaralu untayi. " * 40) + "</p>"
    return {
        "posts": [
            p(3452, "", "3452-2", [1], 0,
              "<title>Post 3452</title><header>menu</header><footer>end</footer>"
              "<p>score 100/100 SEO</p>"),
            p(3476, "Optum Software Engineer Jobs 2026 Freshers", "optum-software-engineer-jobs-2026-freshers",
              [35], 101, filler + "<p>Optum hiring freshers, apply online "
              "[adinsert block=1] check official site.</p>"),
            p(3443, "TS Police Constable 2026" + NONBREAKING_HYPHEN + "today", "telangana-police-2026",
              [44], 102, '</figure></h2><h2 id="amp">Vacancy details</h2><a href="#amp">jump</a>'
              '<h2 id="amp">How to apply</h2><a href="#amp">jump</a><p>Walk-in drive '
              'July 30 - August 7, 2026. Contact 8977614045 for details.</p>'),
            p(3469, "Jobe Bellingham inspiration: online education", "jobe-bellingham-education",
              [1], 0, "<p>football career and online learning motivation. </p>" + filler),
            p(3454, "NIC STA Recruitment 2026", "nic-sta-recruitment-2026", [1], 0,
              filler + "<p>NIC STA apply online last date.</p>"),
        ],
        "pages": [
            {"id": 3029, "title": {"rendered": "Button & Separator"}, "slug": "3029-2",
             "link": f"{SITE}/3029-2/", "content": {"rendered": "theme demo"}, "status": "publish"},
            {"id": 3028, "title": {"rendered": "Image & Gallery Block"}, "slug": "image-gallery-block",
             "link": f"{SITE}/image-gallery-block/", "content": {"rendered": "theme demo"}, "status": "publish"},
            {"id": 3, "title": {"rendered": "About us"}, "slug": "privacy-policy",
             "link": f"{SITE}/privacy-policy/", "content": {"rendered": "about"}, "status": "publish"},
            {"id": 20, "title": {"rendered": "Privacy Policy"}, "slug": "privacy-policy-2",
             "link": f"{SITE}/privacy-policy-2/", "content": {"rendered": "privacy"}, "status": "publish"},
            {"id": 17, "title": {"rendered": "Contact Us"}, "slug": "contact-us",
             "link": f"{SITE}/contact-us/", "content": {"rendered": "contact form"}, "status": "publish"},
            {"id": 3162, "title": {"rendered": "Contact"}, "slug": "contact",
             "link": f"{SITE}/contact/", "content": {"rendered": "old contact"}, "status": "publish"},
        ],
        "categories": [
            {"id": 1, "name": "Uncategorized", "slug": "uncategorized", "count": 3},
            {"id": 35, "name": "Central Govt Jobs", "slug": "central-govt-jobs", "count": 6},
            {"id": 36, "name": "Private Jobs", "slug": "private-jobs", "count": 5},
            {"id": 44, "name": "Internships", "slug": "internships", "count": 2},
            {"id": 45, "name": "Walkin Jobs", "slug": "walkin-jobs", "count": 3},
            {"id": 50, "name": "Scholarships", "slug": "scholarships", "count": 4},
            {"id": 61, "name": "Degree Admissions", "slug": "degree-admissions", "count": 0},
            {"id": 62, "name": "Polytechnic", "slug": "polytechnic", "count": 0},
        ],
        "tags": [
            {"id": 1, "name": "Fresher", "slug": "fresher", "count": 12},
            {"id": 2, "name": "Freshers Jobs", "slug": "freshers-jobs", "count": 8},
            {"id": 3, "name": "Part Time", "slug": "part-time", "count": 6},
            {"id": 4, "name": "Part-time Jobs", "slug": "part-time-jobs", "count": 4},
            {"id": 279, "name": "TS Police SI Constable Preparati", "slug": "ts-police-si-constable-preparati", "count": 0},
            {"id": 300, "name": "Testbook", "slug": "testbook", "count": 0},
            {"id": 301, "name": "Unacademy", "slug": "unacademy", "count": 0},
            {"id": 302, "name": "Adda247", "slug": "adda247", "count": 0},
            {"id": 303, "name": "StudentUp Telugu", "slug": "studentup-telugu", "count": 0},
        ],
        "media": [{"id": 101, "source_url": f"{SITE}/wp-content/uploads/2026/08/optum-jobs.jpg.webp",
                   "alt_text": "Optum jobs", "title": {"rendered": "Optum"}},
                  {"id": 102, "source_url": f"{SITE}/wp-content/uploads/2026/08/ts-police-768x432.jpg.webp",
                   "alt_text": "TS police", "title": {"rendered": "TS Police"}}],
        "settings": {"name": "StudentUp", "timezone_string": "", "gmt_offset": "0",
                     "description": "Education updates"},
        "kml": True,
        "_demo": True,
        "_note": "Synthetic fixture — studentup.in lo pattukunna 21 problem classes; "
                 "real audit: python run.py --site-audit (mee network lo)",
    }


def _text(value: Any) -> str:
    if isinstance(value, dict):
        return html_mod.unescape(re.sub(r"<[^>]+>", "", value.get("rendered", ""))).strip()
    return html_mod.unescape(str(value or "")).strip()


def _raw(value: Any) -> str:
    return value.get("rendered", "") if isinstance(value, dict) else str(value or "")


# -------------------------------------------------------------------- checks

def check_posts(data: Dict, today: Optional[datetime] = None) -> List[Dict]:
    today = today or _now()
    media = {m["id"]: m for m in data.get("media", [])}
    cats = {c["id"]: c for c in data.get("categories", [])}
    out: List[Dict] = []
    for post in data.get("posts", []):
        pid = post.get("id", 0)
        title = _text(post.get("title"))
        content = _raw(post.get("content"))
        plain = re.sub(r"\s+", " ", _text(post.get("content")))
        slug = post.get("slug", "")
        link = post.get("link", "")
        cat_ids = post.get("categories") or []
        cat_names = [cats.get(c, {}).get("name", "") for c in cat_ids]
        low = f"{title} {plain[:4000]}".lower()

        if not title.strip():
            out.append(finding("empty_title", "high", "post", "Post ki title ledu",
                               f"id={pid} slug={slug}", "Draft chesi title ivvandi leda delete",
                               True, "draft_post", {"id": pid}, pid, title, slug, link))
        if not plain.strip():
            out.append(finding("empty_content", "high", "post", "Post content khali",
                               f"id={pid}", "Draft/trash cheyandi",
                               True, "draft_post", {"id": pid}, pid, title, slug, link))

        junk_hits = [j for j in JUNK_HTML if j in content.lower()]
        if junk_hits or content.lstrip().startswith("</"):
            out.append(finding(
                "junk_html_fragment", "high", "post",
                "Content lo raw HTML dump (theme/bot fragments)",
                f"hits={junk_hits or ['leading closing tag']} slug={slug}",
                "Bot rebuild chesi clean HTML publish cheyandi (junk draft)",
                True, "draft_post", {"id": pid}, pid, title, slug, link))

        closers = len(re.findall(r"</h[2-4]>", content))
        openers = len(re.findall(r"<h[2-4][^>]*>", content, re.I))
        if closers > openers:
            out.append(finding(
                "broken_heading_tags", "high", "post",
                f"Heading tags broken (closing {closers} > opening {openers}) — "
                "sanitizer lo opening tags poyayi",
                f"slug={slug}", "Content rebuild cheyandi (bot rewrite)",
                True, "draft_post", {"id": pid}, pid, title, slug, link))

        if not post.get("featured_media"):
            out.append(finding(
                "missing_featured_image", "medium", "post", "Featured image ledu",
                f"slug={slug}", "Bot tho featured image generate chesi set cheyandi",
                False, "", {}, pid, title, slug, link))
        else:
            m = media.get(post["featured_media"])
            src = (m or {}).get("source_url", "")
            if src and MIXED_IMG_RE.search(src):
                out.append(finding(
                    "mixed_image_format", "low", "post",
                    "Image URL double-extension (.jpg.webp)",
                    f"{src.rsplit('/', 1)[-1]}", "Image pipeline normalize (okate format)",
                    False, "", {}, pid, title, slug, link))

        cat_govt = [c for c in cat_names if any(h in c.lower() for h in GOVT_HINTS)]
        private_hit = next((e for e in PRIVATE_EMPLOYERS if e in low), "")
        if private_hit and cat_govt:
            # Use the same classifier as publishing: a TCS developer belongs
            # in Software Jobs, while a TCS sales/operations opening belongs in
            # Private Jobs. Never repair both to a generic private bucket.
            suggested = guess_category(title, data["categories"])
            private_cat = suggested if suggested and suggested.get("name") in (
                "Private Jobs", "Software Jobs") else next(
                    (c for c in data["categories"] if c["name"] == "Private Jobs"), None)
            out.append(finding(
                "wrong_category_govt_private", "high", "post",
                f"Private employer ('{private_hit}') ni '{cat_govt[0]}' category lo pettaru",
                f"slug={slug} categories={cat_names}",
                f"Category '{private_cat['name'] if private_cat else 'Private Jobs'}' ki marchandi (search intent tappu avutundi)",
                bool(private_cat), "set_categories",
                {"id": pid, "add": [private_cat["id"]] if private_cat else [],
                 "remove": cat_ids}, pid, title, slug, link))

        if any(h in low for h in WALKIN_HINTS) and any("intern" in c.lower() for c in cat_names):
            walkin_cat = next((c for c in data["categories"]
                               if "walk" in c["name"].lower()), None)
            out.append(finding(
                "wrong_category_walkin", "medium", "post",
                "Walk-in job ni 'Internships' category lo pettaru",
                f"slug={slug} categories={cat_names}",
                "Category 'Walkin Jobs' ki marchandi",
                bool(walkin_cat), "set_categories",
                {"id": pid, "add": [walkin_cat["id"]] if walkin_cat else [],
                 "remove": cat_ids}, pid, title, slug, link))

        if any(c.get("slug") == "uncategorized" for c in
               [cats.get(i, {}) for i in cat_ids]):
            guess = guess_category(title, data["categories"])
            out.append(finding(
                "uncategorized_post", "high", "post", "Post 'Uncategorized' lo undi",
                f"slug={slug} title={title[:60]}",
                "Correct category pettandi" + (f" (suggest: {guess['name']})" if guess else ""),
                bool(guess), "set_categories",
                {"id": pid, "add": [guess["id"]] if guess else [],
                 "remove": cat_ids}, pid, title, slug, link))

        phones = PHONE_RE.findall(plain)
        if phones:
            shown = ", ".join(p[:2] + "X" * 6 + p[-2:] for p in phones[:3])
            out.append(finding(
                "pii_phone", "high", "post", "Content lo personal phone number",
                f"slug={slug} numbers={shown}", "Phone number remove cheyandi (privacy)",
                True, "strip_pii", {"id": pid}, pid, title, slug, link))

        codes = {(m.group(1) or "").lower() for m in SHORTCODE_RE.finditer(content)}
        bad_codes = sorted(c for c in codes if c and c not in SHORTCODE_SAFE)
        if bad_codes:
            out.append(finding(
                "unprocessed_shortcode", "high", "post",
                f"Body lo raw shortcode: {', '.join(bad_codes[:4])}",
                f"slug={slug}", "Ad block ni plugin tho process cheyyandi leda remove cheyandi",
                True, "strip_shortcode", {"id": pid, "codes": bad_codes}, pid, title, slug, link))

        anchors = ANCHOR_RE.findall(content)
        dupes = sorted({a for a in anchors if anchors.count(a) > 1})
        heading_ids = [m.group(2) for m in HEADING_ID_RE.finditer(content)]
        dup_ids = sorted({i for i in heading_ids if heading_ids.count(i) > 1})
        if dupes or dup_ids:
            out.append(finding(
                "duplicate_toc_anchor", "medium", "post",
                "TOC lo same anchor multiple sections ki (click tappu place ki veltundi)",
                f"dupes={dupes or dup_ids}", "Anchors unique cheyandi (amp, amp-2, amp-3…)",
                True, "dedupe_anchors", {"id": pid}, pid, title, slug, link))

        off = next((e for e in OFFTOPIC_ENTITIES if e in low), "")
        if off:
            out.append(finding(
                "off_topic_entity", "medium", "post",
                f"Education site lo off-topic entity: '{off}'",
                f"slug={slug} title={title[:60]}",
                "Topic shift chesi relevant education angle tho rewrite cheyandi",
                False, "", {}, pid, title, slug, link))

        stale_note = stale_dates_note(plain, today)
        if stale_note:
            out.append(finding(
                "stale_dates", "low", "post",
                "Post lo unna anni dates puranavi (session over/stale info)",
                f"slug={slug} {stale_note}",
                "Dates verify chesi update cheyandi leda post refresh cheyandi "
                "(dateModified = current session)",
                False, "", {}, pid, title, slug, link))
    return out


STALE_DAYS = 30


def stale_dates_note(plain: str, today: Optional[datetime] = None,
                     days: int = STALE_DAYS) -> str:
    """Post lo unna **newest** date kuda `days` rojula kanna puranadi aithe note.

    Anni dates parse chesi (range leda single) max date tisukuntam — future/current
    date unte post stale kaadu (false positive ledu). Returns "" if not stale.
    """
    today = today or _now()
    seen: List[Tuple[datetime, str]] = []
    for m in DATE_RANGE_RE.finditer(plain):
        # range lo second end = newest (month + year chalu)
        try:
            end = datetime.strptime(f"{m.group(2)} {m.group(3)}", "%B %Y")
        except ValueError:
            continue
        seen.append((end, m.group(0)[:60]))
    for m in DATE_SINGLE_RE.finditer(plain):
        try:
            dt = datetime.strptime(f"{m.group(1)} {m.group(2)} {m.group(3)}",
                                   "%B %d %Y")
        except ValueError:
            continue
        seen.append((dt, m.group(0)[:60]))
    if not seen:
        return ""
    newest, note = max(seen, key=lambda x: x[0])
    newest = newest.replace(tzinfo=timezone.utc)
    if newest < today - timedelta(days=days):
        age = (today - newest).days
        return f"newest date {newest.strftime('%B %d, %Y')} ({age} days old) | {note}"
    return ""


def guess_category(title: str, categories: Iterable[Dict]) -> Optional[Dict]:
    """Use the same canonical classifier as the publishing pipeline.

    The audit must not have a second, older keyword map: that is how a
    Software Jobs post can be proposed for Central Govt Jobs during repair.
    """
    from .pipeline import classify_category

    cat_name = classify_category(title or "")
    available = list(categories)
    for c in available:
        name = str(c.get("name") or "")
        if name.lower() == cat_name.lower():
            return c
    # Existing sites sometimes have a harmless slug/name variation. Resolve
    # that only after an exact canonical-name attempt.
    wanted = re.sub(r"[^a-z0-9]+", "-", cat_name.lower()).strip("-")
    for c in available:
        slug = str(c.get("slug") or "").lower().strip()
        if slug == wanted or slug.replace("-", " ") == cat_name.lower():
            return c
    return None


def check_pages(data: Dict) -> List[Dict]:
    out: List[Dict] = []
    contacts: List[Dict] = []
    for page in data.get("pages", []):
        pid = page.get("id", 0)
        title = _text(page.get("title"))
        slug = page.get("slug", "")
        link = page.get("link", "")
        low = f"{title} {slug}".lower()
        if any(sig in low for sig in DEMO_PAGE_SIGNATURES) or re.match(r"^\d{3,4}-\d+$", slug):
            out.append(finding(
                "demo_page_live", "high", "page",
                f"Theme/demo page live+sitemap lo: '{title or slug}'",
                f"slug={slug} link={link}", "Trash chesi 301 redirect pettandi",
                True, "trash_page", {"id": pid}, pid, title, slug, link))
        if "contact" in low:
            contacts.append(page)
        if "privacy" in slug and "about" in title.lower():
            out.append(finding(
                "slug_title_mismatch", "medium", "page",
                "URL privacy-policy kaani content/title 'About us'",
                f"slug={slug} title={title}", "About page ni about-us slug ki marchandi",
                True, "update_slug", {"id": pid, "slug": "about-us"}, pid, title, slug, link))
        if "about" in slug and "privacy" in title.lower():
            out.append(finding(
                "slug_title_mismatch", "medium", "page",
                "URL about-us kaani title 'Privacy Policy'",
                f"slug={slug} title={title}", "Privacy page ni privacy-policy slug ki marchandi",
                True, "update_slug", {"id": pid, "slug": "privacy-policy"}, pid,
                title, slug, link))
        if re.match(r"^privacy-policy-\d+$", slug) and "privacy" in title.lower():
            out.append(finding(
                "ugly_legal_slug", "low", "page",
                f"Legal page slug '-\" suffix tho undi ({slug})",
                f"slug={slug}", "privacy-policy slug ki marchandi (order: About first)",
                True, "update_slug", {"id": pid, "slug": "privacy-policy"}, pid,
                title, slug, link))
    if len(contacts) > 1:
        for page in contacts[1:]:
            out.append(finding(
                "duplicate_contact_page", "medium", "page",
                f"Duplicate contact page ({page.get('slug')})",
                f"link={page.get('link')}", "Draft cheyandi (okate contact page undali)",
                True, "draft_page", {"id": page.get("id")}, page.get("id", 0),
                _text(page.get("title")), page.get("slug", ""), page.get("link", "")))
    return out


def normalize_tag_key(name: str) -> str:
    """Tag name ni merge-key ga marchu.

    'Freshers Jobs' / 'Fresher' → fresher · 'Part-time Jobs' / 'Part Time' →
    parttime · 'Scholarships' / 'Scholarship' → scholarship. Deterministic —
    prune sugestions ki matrame, guesses ki kaadu.
    """
    key = re.sub(r"[^a-z0-9]+", "", (name or "").lower())
    key = re.sub(r"jobs?$", "", key) or key          # 'freshersjobs' → 'freshers'
    key = re.sub(r"(?<=[a-z])s$", "", key) or key     # 'freshers' → 'fresher'
    return key


COMMON_LONG_WORDS = (
    "preparation", "notification", "recruitment", "scholarship", "examination",
    "admission", "application", "university", "government", "department",
    "commission", "counselling", "certificate", "engineering", "technology",
    "management", "interview", "eligibility", "verification", "appointment",
    "qualification", "announcement", "registration", "examination",
)


def looks_truncated_tag(name: str) -> bool:
    """Tag name last word mid-way lo cut ayyinda? (SEO platforms 40-char cut)

    Heuristic (deterministic): last word, 6+ chars, common education word ki
    prefix ga undi kaani aa word kanna chinna ga undi → truncated.
    """
    name = (name or "").strip()
    if len(name) < 20:
        return False
    last = name.split()[-1].lower()
    if len(last) < 6:
        return False
    return any(w.startswith(last) and len(last) < len(w) - 1
               for w in COMMON_LONG_WORDS)


def complete_truncated_tag(name: str) -> str:
    """Truncated word ni dictionary nunchi complete chesi full name return."""
    name = (name or "").strip()
    parts = name.split()
    if not parts:
        return name
    last = parts[-1].lower()
    for w in COMMON_LONG_WORDS:
        if w.startswith(last) and len(last) < len(w):
            parts[-1] = w.capitalize() if parts[-1].islower() else w.capitalize()
            return " ".join(parts)
    return name


def check_taxonomy(data: Dict) -> List[Dict]:
    out: List[Dict] = []
    zero_tags = [t for t in data.get("tags", []) if not t.get("count")]
    if zero_tags:
        out.append(finding(
            "zero_count_tags", "medium", "tag",
            f"{len(zero_tags)} tags ki e post ledu (tag bloat)",
            "examples: " + ", ".join(f"'{t['name']}'" for t in zero_tags[:6]),
            "Zero-count tags ni delete cheyandi (thin archives + crawl budget)",
            True, "purge_zero_tags", {"ids": [t["id"] for t in zero_tags]}))

    for t in data.get("tags", []):
        if not looks_truncated_tag(t["name"]):
            continue
        fixed = complete_truncated_tag(t["name"])
        out.append(finding(
            "truncated_tag_name", "low", "tag",
            f"Tag name mid-word lo cut ayyindi: '{t['name']}'",
            f"id={t['id']} last-word='{t['name'].split()[-1]}'",
            f"Rename: '{fixed}' (leda tag delete chesi malli pettandi)",
            True, "rename_tag", {"id": t["id"], "name": fixed}, t["id"], t["name"]))

    groups: Dict[str, List[Dict]] = {}
    for t in data.get("tags", []):
        groups.setdefault(normalize_tag_key(t["name"]), []).append(t)
    for key, items in sorted(groups.items()):
        names = {i["name"].lower().strip() for i in items}
        if len(items) > 1 and len(names) > 1:
            counts = sum(i.get("count", 0) for i in items)
            keep = max(items, key=lambda i: (i.get("count", 0), -i["id"]))
            drop = [i for i in items if i is not keep]
            out.append(finding(
                "duplicate_tags", "medium", "tag",
                "Duplicate tags: " + ", ".join(f"'{i['name']}'" for i in items[:4]),
                f"total posts={counts} → okate tag ki merge cheyandi "
                f"(key='{key}')",
                f"'{keep['name']}' ki posts reassign chesi migilina tags delete",
                True, "merge_tags",
                {"keep": keep["id"], "keep_name": keep["name"],
                 "drop": [i["id"] for i in drop],
                 "drop_names": [i["name"] for i in drop]}))

    empty_cats = [c for c in data.get("categories", []) if not c.get("count")]
    if empty_cats:
        out.append(finding(
            "empty_categories", "low", "category",
            f"{len(empty_cats)} categories ki posts levu (kaani sitemap lo unnayi)",
            "examples: " + ", ".join(f"'{c['name']}'" for c in empty_cats[:6]),
            "Posts assign cheyandi leda category ni hide/noindex cheyandi",
            False, "", {}))
    return out


def check_site(data: Dict) -> List[Dict]:
    out: List[Dict] = []
    settings = data.get("settings", {}) or {}
    tz = settings.get("timezone_string") or ""
    offset = settings.get("gmt_offset", "")
    if not tz and str(offset) in ("0", 0, "0.0"):
        out.append(finding(
            "timezone_utc", "low", "site",
            "WordPress timezone UTC lo undi (Indian audience ki tappu timestamps)",
            f"gmt_offset={offset} timezone_string='{tz}'",
            "Settings → General → Asia/Kolkata (+5:30)",
            True, "set_timezone", {"timezone": "Asia/Kolkata"}))
    if data.get("kml"):
        out.append(finding(
            "local_seo_without_location", "low", "site",
            "Rank Math Local SEO active (locations.kml live) kaani business location ledu",
            f"{SITE}/locations.kml → 200",
            "Rank Math → Local SEO module OFF cheyandi",
            False, "", {}))
    return out


def audit_site(api: Optional[SiteAPI] = None, data: Optional[Dict] = None,
               today: Optional[datetime] = None,
               snapshot: Any = "") -> Dict[str, Any]:
    """Full audit — findings + summary (writes emi ledu).

    snapshot: JSON path leda "demo" → offline audit (network avasaram ledu).
    """
    api = api or SiteAPI()
    data = data or (load_snapshot(snapshot) if snapshot else collect(api))
    findings: List[Dict] = []
    findings += check_posts(data, today=today)
    findings += check_pages(data)
    findings += check_taxonomy(data)
    findings += check_site(data)
    findings.sort(key=lambda f: (SEVERITY_ORDER.get(f["severity"], 9),
                                 f["kind"], f["id"]))
    summary = {
        "posts": len(data.get("posts", [])),
        "pages": len(data.get("pages", [])),
        "categories": len(data.get("categories", [])),
        "tags": len(data.get("tags", [])),
        "findings": len(findings),
        "by_severity": {sev: sum(1 for f in findings if f["severity"] == sev)
                        for sev in ("high", "medium", "low", "info")},
        "fixable": sum(1 for f in findings if f["fixable"]),
        "site": api.site,
        "checked_at": _now().isoformat(timespec="seconds"),
    }
    return {"summary": summary, "findings": findings, "data": data}


# -------------------------------------------------------------------- fixers

def strip_shortcodes(text: str, codes: Iterable[str]) -> str:
    codes = {c.lower() for c in codes}
    def repl(m: re.Match) -> str:
        return "" if (m.group(1) or "").lower() in codes else m.group(0)
    out = SHORTCODE_RE.sub(repl, text)
    return re.sub(r"\n{3,}", "\n\n", out)


def mask_phones(text: str) -> str:
    def repl(m: re.Match) -> str:
        num = m.group(1)
        return f"{num[:2]}XXXXX{num[-2:]}"
    return PHONE_RE.sub(repl, text)


def dedupe_anchors(content: str) -> str:
    """Same anchor/id ni unique chey — TOC hrefs + heading ids rendu sync lo.

    ReN: heading ids and TOC hrefs document order lo nundi ne map avutayi
    (first occurrence as-is, tarvata -2, -3 …). Prathi match ki counter **okka
    sari** increment (double-increment bug fix).
    """
    heading_counts: Dict[str, int] = {}
    for m in HEADING_ID_RE.finditer(content):
        heading_counts[m.group(2)] = heading_counts.get(m.group(2), 0) + 1

    head_seen: Dict[str, int] = {}

    def head_repl(m: re.Match) -> str:
        old = m.group(2)
        head_seen[old] = head_seen.get(old, 0) + 1
        new = old if head_seen[old] == 1 else f"{old}-{head_seen[old]}"
        return m.group(0).replace(f'id="{old}"', f'id="{new}"').replace(
            f"id='{old}'", f"id='{new}'")

    content = HEADING_ID_RE.sub(head_repl, content)

    href_seen: Dict[str, int] = {}

    def href_repl(m: re.Match) -> str:
        old = m.group(1)
        if heading_counts.get(old, 0) <= 1:
            return m.group(0)
        href_seen[old] = href_seen.get(old, 0) + 1
        new = old if href_seen[old] == 1 else f"{old}-{href_seen[old]}"
        return f'href="#{new}"'

    return ANCHOR_RE.sub(href_repl, content)


def apply_fixes(api: SiteAPI, findings: List[Dict], dry_run: bool = True,
                actions: Optional[Iterable[str]] = None,
                allow_trash: bool = False) -> Dict[str, Any]:
    """Safe fixes apply — default dry-run; prathi action log avutundi."""
    allow = set(actions) if actions else None
    result: Dict[str, Any] = {"dry_run": dry_run, "applied": [], "skipped": [],
                              "errors": []}
    for f in findings:
        if not f["fixable"] or not f["fix_action"]:
            result["skipped"].append({"id": f["id"], "why": "manual fix"})
            continue
        if allow and f["fix_action"] not in allow:
            result["skipped"].append({"id": f["id"], "why": "action filter"})
            continue
        if f["fix_action"] in ("trash_page", "draft_post", "draft_page") and not allow_trash:
            if not dry_run:
                result["skipped"].append({"id": f["id"],
                                          "why": "allow_trash ledu (safety)"})
                continue
        entry = {"id": f["id"], "action": f["fix_action"],
                 "target": f"{f['kind']}#{f['target_id']}"}
        if dry_run:
            result["applied"].append({**entry, "dry_run": True})
            continue
        try:
            _run_fixer(api, f)
            entry["ok"] = True
            result["applied"].append(entry)
        except Exception as exc:      # noqa: BLE001
            entry["error"] = str(exc)[:200]
            result["errors"].append(entry)
    return result


def _run_fixer(api: SiteAPI, f: Dict) -> None:
    action = f["fix_action"]
    params = f["fix_params"]
    kind = "pages" if f["kind"] == "page" else "posts"

    if action in ("draft_post", "draft_page"):
        api.update(kind, params["id"], {"status": "draft"})
    elif action == "trash_page":
        api.delete("pages", params["id"], force=False)      # trash (reversible)
    elif action == "set_categories":
        api.update("posts", params["id"],
                   {"categories": sorted(set(params.get("add", [])))})
    elif action == "strip_pii" or action == "strip_shortcode" or action == "dedupe_anchors":
        post = api.get(f"posts/{params['id']}", context="edit")
        content = _raw(post.get("content"))
        if action == "strip_pii":
            content = mask_phones(content)
        elif action == "strip_shortcode":
            content = strip_shortcodes(content, params.get("codes", []))
        else:
            content = dedupe_anchors(content)
        api.update("posts", params["id"], {"content": content})
    elif action == "purge_zero_tags":
        for tag_id in params.get("ids", []):
            api.delete("tags", tag_id, force=True)
    elif action == "merge_tags":
        for drop_id in params.get("drop", []):
            merge_tag(api, params["keep"], drop_id)
    elif action == "rename_tag":
        api.update("tags", params["id"], {"name": params["name"]})
    elif action == "update_slug":
        api.update("pages", params["id"], {"slug": params["slug"]})
    elif action == "set_timezone":
        api.update("settings", 0, {"timezone_string": params["timezone"]}) \
            if hasattr(api, "update_settings") else _set_timezone(api, params["timezone"])
    else:
        raise ValueError(f"unknown fixer: {action}")


def merge_tag(api: SiteAPI, keep_id: int, drop_id: int, per_page: int = 50) -> int:
    """Drop tag lo unna posts ni keep tag ki reassign chesi, drop tag delete.

    Idi **lossless** merge — posts ki tag association povadu (plain delete
    chesthe povali). Returns: reassign ayyina posts count.
    """
    moved = 0
    page = 1
    while True:
        posts = api.get("posts", tags=[drop_id], per_page=per_page, page=page,
                        _fields="id,categories,tags")
        if not isinstance(posts, list) or not posts:
            break
        for post in posts:
            tags = [t for t in (post.get("tags") or []) if t != drop_id]
            if keep_id not in tags:
                tags.append(keep_id)
            api.update("posts", post["id"], {"tags": tags})
            moved += 1
        if len(posts) < per_page:
            break
        page += 1
    api.delete("tags", drop_id, force=True)
    return moved


def _set_timezone(api: SiteAPI, tz: str) -> None:
    if not api.can_write():
        raise PermissionError("Timezone fix ki WP creds kavali")
    url = f"{api.site}/wp-json/wp/v2/settings"
    resp = api.session.post(url, json={"timezone_string": tz}, timeout=TIMEOUT)
    resp.raise_for_status()


# ------------------------------------------------------------------- report

def report_markdown(res: Dict[str, Any]) -> str:
    s = res["summary"]
    lines = [
        f"# Site Audit — {s['site']}", "",
        f"_Checked: {s['checked_at']} · Posts: {s['posts']} · Pages: {s['pages']} · "
        f"Categories: {s['categories']} · Tags: {s['tags']}_", "",
        f"**Findings: {s['findings']}** "
        f"(high {s['by_severity']['high']} · medium {s['by_severity']['medium']} · "
        f"low {s['by_severity']['low']} · info {s['by_severity']['info']}) · "
        f"auto-fixable: {s['fixable']}", "",
    ]
    for f in res["findings"]:
        tag = {"high": "🔴", "medium": "🟠", "low": "🟡", "info": "ℹ️"}[f["severity"]]
        where = f"{f['kind']}#{f['target_id']}" + (f" ({f['slug']})" if f["slug"] else "")
        lines += [f"## {tag} {f['title']}", f"- where: `{where}`",
                  f"- evidence: {f['evidence']}", f"- fix: {f['fix']}",
                  f"- auto: {'yes → ' + f['fix_action'] if f['fixable'] else 'manual'}", ""]
    return "\n".join(lines)


def write_report(res: Dict[str, Any], out_dir: Optional[Path] = None) -> Dict[str, str]:
    out_dir = Path(out_dir or OUT_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _now().strftime("%Y%m%d-%H%M")
    json_path = out_dir / f"site-audit-{stamp}.json"
    md_path = out_dir / f"site-audit-{stamp}.md"
    json_path.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str),
                         encoding="utf-8")
    md_path.write_text(report_markdown(res), encoding="utf-8")
    latest = out_dir / "site-audit-latest.json"
    latest.write_text(json.dumps(res, ensure_ascii=False, indent=2, default=str),
                      encoding="utf-8")
    return {"json": str(json_path), "md": str(md_path), "latest": str(latest)}


def run_audit(fix: bool = False, dry_run: bool = True, allow_trash: bool = False,
              actions: Optional[Iterable[str]] = None, snapshot: Any = "",
              save: str = "") -> int:
    """CLI entry: audit → print summary → optional fixes → report files.

    snapshot: JSON path leda "demo" (offline audit) · save: fetched data ni JSON
    ga export (tarvata offline audit ki / CI ki).
    """
    api = SiteAPI()
    try:
        res = audit_site(api, snapshot=snapshot)
    except SiteAuditError as exc:
        print("=" * 70)
        print("  ⚠️  SITE AUDIT — data fetch avvaledu")
        print("=" * 70)
        print(f"  {exc}")
        print("\n  Options:")
        print("   1) Mee own machine/network nunchi run cheyandi:")
        print("        python run.py --site-audit")
        print("   2) Offline demo (engine proof):")
        print("        python run.py --site-audit --site-audit-snapshot demo")
        print("   3) Sibling machine lo snapshot teesi ikkada run cheyandi:")
        print("        python run.py --site-audit --site-audit-save output/audit/"
              "site-audit-snapshot.json   # WP unna machine lo")
        print("        python run.py --site-audit --site-audit-snapshot "
              "output/audit/site-audit-snapshot.json")
        return 2
    if save:
        path = save_snapshot(res["data"], save)
        print(f"  💾 Snapshot saved: {path}")
    s = res["summary"]
    print("=" * 70)
    print(f"  🔎 SITE AUDIT — {s['site']}")
    print("=" * 70)
    print(f"  Posts {s['posts']} · Pages {s['pages']} · Categories {s['categories']}"
          f" · Tags {s['tags']}")
    print(f"  Findings: {s['findings']}  (high {s['by_severity']['high']}, "
          f"medium {s['by_severity']['medium']}, low {s['by_severity']['low']})"
          f"  · auto-fixable {s['fixable']}")
    for f in res["findings"]:
        mark = {"high": "🔴", "medium": "🟠", "low": "🟡", "info": "ℹ️"}[f["severity"]]
        auto = f" → {f['fix_action']}" if f["fixable"] else ""
        print(f"   {mark} [{f['kind']}#{f['target_id']}] {f['title']}{auto}")
    paths = write_report(res)
    print(f"\n  📄 Report: {paths['md']}")

    if fix:
        if not api.can_write():
            print("\n  ⚠️  Fixes ki WP_USERNAME/WP_APP_PASSWORD kavali (.env) — "
                  "audit matrame chesam.")
            return 1
        out = apply_fixes(api, res["findings"], dry_run=dry_run,
                          actions=actions, allow_trash=allow_trash)
        print(f"\n  🛠️  Fixes ({'DRY-RUN' if dry_run else 'APPLIED'}): "
              f"{len(out['applied'])} · skipped {len(out['skipped'])} · "
              f"errors {len(out['errors'])}")
        for a in out["applied"][:25]:
            print(f"   ✔ {a['id']} → {a['action']} ({a['target']})")
        for e in out["errors"]:
            print(f"   ✘ {e['id']} → {e['action']}: {e.get('error')}")
        log_path = OUT_DIR / f"site-fix-{_now().strftime('%Y%m%d-%H%M')}.json"
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps(out, ensure_ascii=False, indent=2, default=str),
                            encoding="utf-8")
        print(f"  📄 Fix log: {log_path}")
    return 0


# ------------------------------------------------- v41 root-cause PUBLISH GATE

# Live publish ki mundu ee tappalu block avutayi (audit lo pattukunna class of
# bugs malli raakunda). Draft lu eppudu allow — human review ki pani cheyyali.

NONBREAKING_HYPHEN = "\u2011"
EMPTY_EXCERPT_MIN = 60
TITLE_MIN, TITLE_MAX = 40, 62


def article_gate(article: Dict[str, Any], html: str = "", category: str = "",
                 live: Optional[bool] = None) -> Tuple[bool, str]:
    """v41 gate — publish ki mundu site-audit class tappalu block.

    live=None → article status / DEFAULT_POST_STATUS nunchi decide (draft allow).
    Returns (ok, detail). Ee gate **content quality** chuustundi (v35 QA /
    originality / top-post scores ki additional, vati ni replace cheyyadu).
    """
    if live is None:
        live = (article.get("status") or config.DEFAULT_POST_STATUS) == "publish"
    if not live:
        return True, "draft — v41 gate not enforced"

    problems: List[str] = []
    title = (article.get("title") or "").strip()
    body = html or _raw(article.get("content")) or article.get("html") or ""
    plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", body)).strip()
    excerpt = (article.get("meta_description") or article.get("excerpt") or "").strip()

    if not title:
        problems.append("title khali")
    elif not (TITLE_MIN <= len(title) <= TITLE_MAX):
        problems.append(f"title {len(title)} chars (kavali {TITLE_MIN}-{TITLE_MAX})")
    if len(excerpt) < EMPTY_EXCERPT_MIN:
        problems.append(f"meta/excerpt {len(excerpt)} chars (<{EMPTY_EXCERPT_MIN})")
    if not body.strip() or len(plain) < 300:
        problems.append("content khali/chala chinnadi (<300 chars)")

    if not article.get("featured_media") and not article.get("image_path") \
            and not article.get("has_image"):
        problems.append("featured image ledu")

    low = body.lower()
    junk = [j for j in JUNK_HTML if j in low]
    if junk:
        problems.append("junk HTML/theme fragment: " + ", ".join(junk[:3]))
    if body.lstrip().startswith("</") or re.search(r"</(figure|div|p)>", body[:1]):
        problems.append("content leading closing tag (sanitizer damage)")

    codes = {(m.group(1) or "").lower() for m in SHORTCODE_RE.finditer(body)}
    bad = sorted(c for c in codes if c and c not in SHORTCODE_SAFE)
    if bad:
        problems.append("unregistered shortcode: " + ", ".join(bad[:3]))

    anchors = ANCHOR_RE.findall(body)
    dups = sorted({a for a in anchors if anchors.count(a) > 1})
    hids = [m.group(2) for m in HEADING_ID_RE.finditer(body)]
    dup_ids = sorted({i for i in hids if hids.count(i) > 1})
    if dups or dup_ids:
        problems.append("duplicate anchor/id: " + ", ".join((dups or dup_ids)[:3]))

    if NONBREAKING_HYPHEN in title:
        problems.append("title lo non-breaking hyphen (U+2011) — search/snippet tappu")
    if re.search(r"\btoday\b", title, re.I) and not re.search(r"as on", title, re.I):
        problems.append("title lo template 'today' — date-stale avutundi")

    dates = [int(m.groups()[-1]) for m in DATE_RANGE_RE.finditer(plain)]
    dates += [int(m.groups()[-1]) for m in DATE_SINGLE_RE.finditer(plain)]
    if dates and min(dates) < _now().year - 1:
        problems.append(f"stale date ({min(dates)}) content lo")

    phones = PHONE_RE.findall(plain)
    if phones:
        problems.append(f"PII phone number ({len(phones)}) content lo")

    cat = (category or article.get("category") or "").lower()
    if any(h in cat for h in GOVT_HINTS):
        hit = next((e for e in PRIVATE_EMPLOYERS
                    if e in f"{title} {plain[:3000]}".lower()), "")
        if hit:
            problems.append(f"private employer '{hit}' ni Govt category lo publish")

    haystack = f"{title} {plain[:4000]}".lower()
    off = next((e for e in OFFTOPIC_ENTITIES if e in haystack), "")
    if off:
        problems.append(f"off-topic entity '{off}' (education angle ledu)")

    if problems:
        return False, ("V41 SITE GATE: " + "; ".join(problems[:6]) +
                       " — draft ga save chesi fix cheyyandi "
                       "(run.py --site-audit-fix tho existing posts kuda scan)")
    return True, "v41 gate ✔ (no junk/shortcode/PII/stale-date/category issues)"
