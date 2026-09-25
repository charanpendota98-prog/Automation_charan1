"""Verified Success Stories intake and editorial review helpers.

The public Google Form is only an intake channel. This module turns an
exported row into a *review brief*, never a publish command. It enforces the
StudentUp promise: maximum three selected stories per ISO week, TS/AP scope,
explicit publication/photo consent, attributable evidence, and no sensitive
identity or financial documents.

No form responses, photos, contact details or certificates belong in Git. Keep
exports in a private, access-controlled workspace and delete them according to
the owner's retention policy.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Tuple
from urllib.parse import urlparse

from . import config

ALLOWED_STATES = {"telangana", "andhra pradesh", "telangana state", "ap"}
CONSENT_YES = {"yes", "y", "true", "i agree", "అవును"}
SENSITIVE_WORDS = {
    "aadhaar", "aadhar", "pan card", "bank account", "account number", "ifsc",
    "otp", "password", "debit card", "credit card", "passport number",
}
REQUIRED = (
    "full_name", "state", "achievement", "achievement_date", "official_links",
    "photo_url", "photo_rights", "publish_consent",
)


def _text(value: object) -> str:
    return " ".join(str(value or "").strip().split())


def _yes(value: object) -> bool:
    return _text(value).lower() in CONSENT_YES


def _links(value: object) -> List[str]:
    raw = _text(value)
    return [x.strip() for x in re.split(r"[\n,;]+", raw) if x.strip()]


def _safe_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"} and bool(parsed.netloc)
    except ValueError:
        return False


def _week_key(value: object = "") -> str:
    raw = _text(value)
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date().isocalendar()[:2]
    except (TypeError, ValueError):
        today = date.today().isocalendar()
        return (today.year, today.week)


def submission_id(row: Dict) -> str:
    """Stable internal identifier; never publish the respondent's email."""
    seed = "|".join(_text(row.get(k)).lower() for k in
                     ("full_name", "achievement", "achievement_date", "official_links"))
    return "ss-" + hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


def validate_submission(row: Dict) -> Dict:
    """Validate one private form-export row without storing its raw contents."""
    row = {str(k).strip(): v for k, v in (row or {}).items()}
    errors: List[str] = []
    warnings: List[str] = []
    for field in REQUIRED:
        if not _text(row.get(field)):
            errors.append(f"missing:{field}")

    state = _text(row.get("state")).lower()
    if state not in ALLOWED_STATES:
        errors.append("scope:only Telangana or Andhra Pradesh stories are accepted")

    all_text = " ".join(_text(v).lower() for v in row.values())
    for word in sorted(SENSITIVE_WORDS):
        if word in all_text:
            errors.append("privacy:do not submit Aadhaar/PAN/bank/OTP/password data")
            break

    links = _links(row.get("official_links"))
    bad_links = [link for link in links if not _safe_url(link)]
    if bad_links:
        errors.append("official_links:use complete http(s) URLs")
    if not links:
        errors.append("evidence:at least one attributable result/institution/employer link is required")
    if not _yes(row.get("publish_consent")):
        errors.append("consent:publication consent is required")
    if not _yes(row.get("photo_rights")):
        errors.append("photo:respondent must own or have permission to publish the photo")

    age = _text(row.get("age_group")).lower()
    if any(x in age for x in ("under 18", "below 18", "minor", "18 కంటే తక్కువ")) \
            and not _yes(row.get("guardian_consent")):
        errors.append("consent:guardian consent is required for a minor")

    if not _text(row.get("public_link_consent")):
        warnings.append("confirm separately whether a public profile/portfolio link may be shown")
    if len(links) == 1:
        warnings.append("seek independent corroboration before selecting the story")
    if not _text(row.get("photo_credit")):
        warnings.append("record photographer/credit before publishing the image")

    return {
        "ok": not errors,
        "id": submission_id(row),
        "errors": errors,
        "warnings": warnings,
        "state": state,
        "name": _text(row.get("public_name")) or _text(row.get("full_name")),
        "achievement": _text(row.get("achievement")),
        "achievement_date": _text(row.get("achievement_date")),
        "evidence_links": links,
        "photo_url": _text(row.get("photo_url")),
        "photo_credit": _text(row.get("photo_credit")),
        "week": _week_key(row.get("submitted_at")),
    }


def select_weekly(rows: Iterable[Dict], limit: int | None = None) -> Tuple[List[Dict], List[Dict]]:
    """Select up to three valid rows per ISO week; return selected/rejected."""
    cap = int(limit or getattr(config, "SUCCESS_STORY_WEEKLY_MAX", 3))
    cap = max(1, min(7, cap))
    selected: List[Dict] = []
    rejected: List[Dict] = []
    counts: Dict[Tuple[int, int], int] = {}
    seen = set()
    for raw in rows:
        result = validate_submission(raw)
        key = (result["week"][0], result["week"][1])
        if not result["ok"]:
            result["errors"] = result["errors"] + ["not_selected:fix evidence/consent and resubmit"]
            rejected.append(result)
            continue
        if result["id"] in seen:
            result["errors"] = ["duplicate:the same achievement was already received"]
            rejected.append(result)
            continue
        if counts.get(key, 0) >= cap:
            result["errors"] = [f"weekly_cap:only {cap} stories are selected per ISO week"]
            rejected.append(result)
            continue
        counts[key] = counts.get(key, 0) + 1
        seen.add(result["id"])
        selected.append(result)
    return selected, rejected


def build_editor_brief(item: Dict) -> str:
    """Create a private, evidence-first writing brief for a human editor."""
    links = "\n".join(f"- {link}" for link in item.get("evidence_links", [])) or "- none"
    return f"""SUCCESS STORY REVIEW BRIEF — PRIVATE

Internal ID: {item.get('id', '')}
Category: Success Stories
Region: {item.get('state', '')}
Public name: {item.get('name', '')}
Achievement: {item.get('achievement', '')}
Achievement date: {item.get('achievement_date', '')}

EVIDENCE LINKS — verify independently before drafting:
{links}

EDITORIAL RULES:
- Write a calm, useful, third-person story; never invent first-person quotes,
  marks, rank, salary, timeline, hardship, family details or emotional scenes.
- Separate verified facts from the person's recollection. Attribute every
  achievement and quote. If evidence conflicts, pause the story.
- Add practical reader value: preparation method, decision points, documents,
  mistakes avoided and transferable lessons only when the person supplied them.
- Do not publish phone, email, exact home address, IDs, certificates, private
  Drive links or sensitive family/financial information.
- Publish only after photo rights, name/quote consent, source verification and
  final fact approval are recorded. This brief is not a publication command.
"""


def review_manifest(rows: Iterable[Dict], limit: int | None = None) -> Dict:
    """Return a private review manifest suitable for an internal JSON file."""
    selected, rejected = select_weekly(rows, limit=limit)
    return {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "policy": "draft-only; max three selected per ISO week; human verification required",
        "selected": [dict(item, editor_brief=build_editor_brief(item)) for item in selected],
        "rejected": rejected,
    }


def load_csv(path: Path) -> List[Dict]:
    """Load a private Google Forms CSV export; caller owns deletion/retention."""
    with Path(path).open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_manifest(rows: Iterable[Dict], path: Path, limit: int | None = None) -> Dict:
    """Write a private review manifest; never write to preview/ or public web roots."""
    target = Path(path)
    if str(target).replace("\\", "/").startswith("preview/"):
        raise ValueError("success-story manifests cannot be written under preview/")
    target.parent.mkdir(parents=True, exist_ok=True)
    manifest = review_manifest(rows, limit=limit)
    target.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest
