"""v31 Student Internet Center service and case workflow.

The public-facing side is a WordPress service page. The private case store
keeps only intake metadata and references to documents in an external private
storage system; it never stores uploaded document bytes in this repository.

This is an application-assistance service, not a government office. The page
must never promise selection/approval and explicitly tells clients not to share
OTP, UPI PIN, passwords, or bank credentials.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
import re
import secrets
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import quote, urlencode, urlparse

from . import config

log = __import__("logging").getLogger("autoblog.service_center")

STATUSES = (
    "new", "documents_pending", "reviewing", "fee_pending",
    "approved_by_client", "submitted", "materials_sent", "completed", "cancelled",
)
SERVICE_CATALOG = (
    ("applications", "Online Applications", "Government, private-job and exam application assistance."),
    ("jobs", "Jobs & Recruitment Help", "Notification reading, eligibility check, apply guidance and job materials."),
    ("schemes", "Scholarships & Schemes", "Scholarship, fee-reimbursement and welfare-scheme guidance."),
    ("resume", "Resume / CV Service", "ATS-friendly resume, cover letter and profile improvement."),
    ("admissions", "Admissions & Exam Registrations", "Course, entrance-exam and counselling form guidance."),
    ("documents", "Print, Scan & Digital Help", "Safe scan, PDF merge, resize, print and email assistance."),
)
SERVICE_SLUGS = {item[0] for item in SERVICE_CATALOG}
SERVICE_PAGE_MARKER = "su-service-center-v31"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _clean_phone(value: str) -> str:
    value = re.sub(r"[^0-9+]", "", (value or "").strip())
    return value[:20]


def _phone_href(value: str) -> Optional[str]:
    phone = _clean_phone(value)
    if not re.fullmatch(r"\+?[0-9]{10,15}", phone):
        return None
    return "tel:" + phone


def _whatsapp_href(value: str) -> Optional[str]:
    phone = re.sub(r"\D", "", (value or ""))
    if len(phone) == 10:
        phone = "91" + phone
    if not 10 <= len(phone) <= 15:
        return None
    text = "Hello, I need StudentUp Internet Center service assistance."
    return "https://wa.me/" + phone + "?" + urlencode({"text": text})


def _external_url(value: str) -> Optional[str]:
    parsed = urlparse((value or "").strip())
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        return None
    return html.escape(value.strip(), quote=True)


def _e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)


def _service_cards() -> str:
    return "".join(
        f'<article class="su-service-card"><h3>{_e(title)}</h3>'
        f'<p>{_e(description)}</p><a href="#service-process">How it works →</a></article>'
        for _slug, title, description in SERVICE_CATALOG
    )


def build_page_html() -> str:
    """Build a transparent service landing page from environment settings."""
    phone = _phone_href(config.SERVICE_CENTER_PHONE)
    whatsapp = _whatsapp_href(config.SERVICE_CENTER_WHATSAPP or config.SERVICE_CENTER_PHONE)
    upload = _external_url(config.SERVICE_CENTER_UPLOAD_URL)
    contact_links = []
    if phone:
        contact_links.append(f'<a class="su-service-cta primary" href="{phone}">📞 Call now</a>')
    if whatsapp:
        contact_links.append(f'<a class="su-service-cta" target="_blank" rel="noopener" href="{whatsapp}">💬 WhatsApp enquiry</a>')
    if upload:
        contact_links.append(f'<a class="su-service-cta" target="_blank" rel="noopener" href="{upload}">🔒 Secure document upload</a>')
    if not contact_links:
        contact_links.append('<p class="su-service-config-note">Contact number/configure secure upload link soon. Call details will appear here.</p>')
    else:
        contact_links.append('<p class="su-service-config-note">Documents పంపే ముందు secure upload link అడగండి. Open chat lo sensitive files పంపకండి.</p>')
    cards = _service_cards()
    return f"""<!--{SERVICE_PAGE_MARKER}-->
<section class="su-service-hero" aria-labelledby="service-center-title">
  <p class="su-service-kicker">STUDENT ASSISTANCE · { _e(config.SERVICE_CENTER_CITY).upper() }</p>
  <h1 id="service-center-title">{_e(config.SERVICE_CENTER_NAME)}</h1>
  <p class="su-service-lead">Applications, resumes, jobs, scholarships and online forms — call us, send the required documents through a secure channel, and get step-by-step guidance without unnecessary travel.</p>
  <div class="su-service-actions">{"".join(contact_links)}</div>
</section>

<section aria-labelledby="service-list-title"><h2 id="service-list-title">మా Services</h2><div class="su-service-grid">{cards}</div></section>

<section class="su-service-process" id="service-process" aria-labelledby="process-title">
  <h2 id="process-title">How it works — simple and transparent</h2>
  <ol>
    <li><strong>Call / enquiry:</strong> మీకు కావాల్సిన service, deadline and location చెప్పండి.</li>
    <li><strong>Eligibility check:</strong> Official notification ఆధారంగా required documents మాత్రమే confirm చేస్తాము.</li>
    <li><strong>Secure documents:</strong> Private upload link ద్వారా పంపండి; WhatsApp/open email lo sensitive files avoid చేయండి.</li>
    <li><strong>Fee confirmation:</strong> Work start చేసే ముందు service fee clearly చెప్పి మీ approval తీసుకుంటాము.</li>
    <li><strong>Application:</strong> Form fill చేసి, final details మీతో verify చేసి మాత్రమే submit చేస్తాము.</li>
    <li><strong>Receipt + materials:</strong> Application number, acknowledgement, print/PDF and preparation material పంపిస్తాము.</li>
  </ol>
</section>

<section class="su-service-safety" aria-labelledby="safety-title">
  <h2 id="safety-title">Security & privacy — very important</h2>
  <ul>
    <li><strong>OTP, UPI PIN, ATM PIN, passwords, net-banking login</strong> ఎప్పుడూ share చేయకండి. OTP applicant device లో మీరే enter చేయాలి.</li>
    <li>Application submit చేసే ముందు name, date of birth, category, mobile number and uploaded details మీరే check చేయాలి.</li>
    <li>We are an independent assistance center; government job, scholarship or selection guarantee చేయము.</li>
    <li>Documents purpose complete అయిన తర్వాత private storage policy ప్రకారం delete/return చేస్తాము. Retention period ముందే అడగండి.</li>
    <li>Fee, refund policy and correction responsibility submit చేసే ముందు written confirmation గా తీసుకోండి.</li>
  </ul>
</section>

<section class="su-service-faq" aria-labelledby="service-faq-title">
  <h2 id="service-faq-title">Frequently asked questions</h2>
  <h3>Center కి రావాల్సిందేనా?</h3><p>ప్రతి service కి కాదు. Call చేసి eligibility and secure document process తెలుసుకుని remote ga complete చేయవచ్చు. Original biometric/verification అవసరమైతే మాత్రం official center rules follow చేయాలి.</p>
  <h3>Fee ఎంత?</h3><p>Service, pages, urgency and correction work ఆధారంగా fee మారుతుంది. Work ప్రారంభించే ముందు exact fee confirm చేస్తాము; hidden charges ఉండకూడదు.</p>
  <h3>Application status ఎలా తెలుస్తుంది?</h3><p>మీకు case reference number ఇస్తాము. Receipt, acknowledgement and next step WhatsApp/email/call ద్వారా share చేస్తాము.</p>
</section>

<section class="su-service-final-cta"><h2>Need help today?</h2><p>Call చేసి service పేరు చెప్పండి. Official notification link ఉంటే పంపండి; మేము required documents and fee ముందే explain చేస్తాము.</p><div class="su-service-actions">{"".join(contact_links)}</div></section>
""".strip()


def init_db(path: Optional[Path] = None) -> Path:
    path = Path(path or config.SERVICE_CENTER_DB)
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS cases (
            case_id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            service_slug TEXT NOT NULL,
            status TEXT NOT NULL,
            consent_at TEXT NOT NULL,
            notes TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
            file_name TEXT NOT NULL,
            storage_ref TEXT NOT NULL,
            sha256 TEXT NOT NULL,
            received_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS case_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT NOT NULL REFERENCES cases(case_id) ON DELETE CASCADE,
            status TEXT NOT NULL,
            note TEXT NOT NULL DEFAULT '',
            actor TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        PRAGMA foreign_keys=ON;
        """)
    try:
        os.chmod(path, 0o600)
    except OSError:
        pass
    return path


def _case_exists(db: sqlite3.Connection, case_id: str) -> bool:
    return db.execute("SELECT 1 FROM cases WHERE case_id=?", (case_id,)).fetchone() is not None


def create_case(client_name: str, phone: str, service_slug: str,
                consent: bool, notes: str = "", path: Optional[Path] = None) -> str:
    """Create a consented case; document bytes are intentionally not accepted."""
    name = " ".join((client_name or "").split())[:120]
    phone = _clean_phone(phone)
    service_slug = (service_slug or "").strip().lower()
    if not name or not re.fullmatch(r"\+?[0-9]{10,15}", phone):
        raise ValueError("valid client name and phone required")
    if service_slug not in SERVICE_SLUGS:
        raise ValueError("unknown service")
    if not consent:
        raise ValueError("client consent is required before storing a case")
    path = init_db(path)
    now = _now()
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        for _ in range(5):
            case_id = "SU-" + datetime.now().strftime("%Y%m%d") + "-" + secrets.token_hex(3).upper()
            if not _case_exists(db, case_id):
                break
        db.execute("INSERT INTO cases VALUES (?,?,?,?,?,?,?,?,?)",
                   (case_id, name, phone, service_slug, "new", now,
                    (notes or "")[:1000], now, now))
        db.execute("INSERT INTO case_events(case_id,status,note,actor,created_at) VALUES(?,?,?,?,?)",
                   (case_id, "new", "Case created with client consent", "system", now))
    return case_id


def add_document(case_id: str, file_name: str, storage_ref: str, sha256: str,
                 path: Optional[Path] = None) -> int:
    """Store metadata for a privately stored document, never its content/path."""
    if not re.fullmatch(r"[a-fA-F0-9]{64}", (sha256 or "")):
        raise ValueError("sha256 must be a 64-character hex digest")
    ref = (storage_ref or "").strip()
    parsed = urlparse(ref)
    if parsed.scheme not in ("https", "s3") or not parsed.netloc:
        raise ValueError("storage_ref must be a private https:// or s3:// reference")
    safe_name = Path(file_name or "document").name[:160]
    path = init_db(path)
    with sqlite3.connect(path) as db:
        if not _case_exists(db, case_id):
            raise ValueError("case not found")
        cur = db.execute("INSERT INTO documents(case_id,file_name,storage_ref,sha256,received_at) VALUES(?,?,?,?,?)",
                         (case_id, safe_name, ref, sha256.lower(), _now()))
        return int(cur.lastrowid)


def update_status(case_id: str, new_status: str, actor: str = "staff",
                  note: str = "", path: Optional[Path] = None) -> None:
    new_status = (new_status or "").strip().lower()
    if new_status not in STATUSES:
        raise ValueError("unknown status")
    path = init_db(path)
    with sqlite3.connect(path) as db:
        row = db.execute("SELECT status FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if not row:
            raise ValueError("case not found")
        old = row[0]
        if old in ("completed", "cancelled") and new_status != old:
            raise ValueError("terminal case cannot be reopened")
        now = _now()
        db.execute("UPDATE cases SET status=?,updated_at=? WHERE case_id=?", (new_status, now, case_id))
        db.execute("INSERT INTO case_events(case_id,status,note,actor,created_at) VALUES(?,?,?,?,?)",
                   (case_id, new_status, (note or "")[:1000], (actor or "staff")[:80], now))


def get_case(case_id: str, path: Optional[Path] = None) -> Optional[Dict]:
    path = init_db(path)
    with sqlite3.connect(path) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM cases WHERE case_id=?", (case_id,)).fetchone()
        if not row:
            return None
        out = dict(row)
        out["documents"] = [dict(x) for x in db.execute(
            "SELECT id,file_name,storage_ref,sha256,received_at FROM documents WHERE case_id=? ORDER BY id",
            (case_id,)).fetchall()]
        out["events"] = [dict(x) for x in db.execute(
            "SELECT status,note,actor,created_at FROM case_events WHERE case_id=? ORDER BY id",
            (case_id,)).fetchall()]
        return out


def purge_expired(path: Optional[Path] = None, retention_days: Optional[int] = None) -> int:
    """Delete terminal cases older than the configured retention period."""
    days = max(1, int(retention_days if retention_days is not None else config.SERVICE_RETENTION_DAYS))
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()
    path = init_db(path)
    with sqlite3.connect(path) as db:
        db.execute("PRAGMA foreign_keys=ON")
        cur = db.execute("DELETE FROM cases WHERE status IN ('completed','cancelled') AND updated_at < ?", (cutoff,))
        return int(cur.rowcount)


def _page_sidecar() -> Path:
    return Path(config.STATE_PATH).with_name("service_center.json")


def _stored_page_hash() -> str:
    try:
        return json.loads(_page_sidecar().read_text(encoding="utf-8")).get("content_sha256", "")
    except Exception:
        return ""


def _save_page_hash(content: str) -> None:
    try:
        f = _page_sidecar()
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({"content_sha256": hashlib.sha256(content.encode()).hexdigest()}),
                     encoding="utf-8")
    except Exception:
        log.debug("service page sidecar write failed", exc_info=True)


def publish_page(wp, dry: bool = True, force: bool = False) -> Dict:
    """Create/update service page without silently overwriting WP manual edits.

    ``force=True`` is an explicit operator decision for refreshing a managed
    page after its copy/config has intentionally changed.
    """
    title = f"{config.SERVICE_CENTER_NAME} — Applications, Jobs & Schemes Help"
    body = build_page_html()
    if dry:
        return {"status": "dry-run", "title": title, "slug": config.SERVICE_CENTER_PAGE_SLUG,
                "html": body}

    existing = None
    getter = getattr(wp, "get_page_for_edit", None)
    if callable(getter):
        existing = getter(config.SERVICE_CENTER_PAGE_SLUG)
    else:
        existing = wp.get_page_by_slug(config.SERVICE_CENTER_PAGE_SLUG)
    if existing and not force:
        current = existing.get("content", "") if isinstance(existing, dict) else ""
        if not current:
            return {"status": "manual-preserved", "title": title,
                    "slug": config.SERVICE_CENTER_PAGE_SLUG,
                    "detail": "existing page body could not be inspected; use --force to replace"}
        if SERVICE_PAGE_MARKER not in current:
            return {"status": "manual-preserved", "title": title,
                    "slug": config.SERVICE_CENTER_PAGE_SLUG,
                    "detail": "existing page is manual/non-managed; no overwrite"}
        saved = _stored_page_hash()
        if not saved or saved != hashlib.sha256(current.encode()).hexdigest():
            return {"status": "manual-preserved", "title": title,
                    "slug": config.SERVICE_CENTER_PAGE_SLUG,
                    "detail": "manual changes detected; use --force only after backup"}
    result = wp.upsert_page(title, body, config.SERVICE_CENTER_PAGE_SLUG)
    _save_page_hash(body)
    return {"status": "published", "title": title, "slug": config.SERVICE_CENTER_PAGE_SLUG,
            **result}
