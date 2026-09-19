# -*- coding: utf-8 -*-
"""v68: GOOGLE INDEXING API + IndexNow — publish ayyaka **instant indexing**.

Enduku (trending ki idi mukhyam):
  · IndexNow (Bing/Yandex) — `autoblog/indexnow.py` lo undi (free, key-based)
  · **Google Indexing API** — Google ee API ni **JobPosting** + BroadcastEvent pages ki
    officially support chestundi. Mana site lo **job posts** (recruitment schema) unnayi →
    avi publish ayyina ventane Google ki notify cheyochu (sitemap wait cheyyakunda).
    Idi Google ni "deceive" cheyyadam kaadu — Google docs lo unna **allowed** use case,
    kaani mana page lo nijamaina JobPosting structured data undali (gate adi verify chestundi).

Auth (2 methods — okkati unte chalu):
  1. `GOOGLE_INDEXING_SA_JSON=/path/service-account.json` (recommended, Oracle VM lo)
  2. `GOOGLE_INDEXING_SA='{"client_email":...,"private_key":...}'` (inline, .env lo)
  Signature: `cryptography` unte adi vaadutundi, lekapote **openssl CLI** (Linux servers lo
  default ga untundi) — Python dependency ledu.

Set cheyyakapote: module silent ga skip avutundi (publish aapadu) + reason log avutundi.
Run:  python run.py --index-now https://studentup.in/<slug>/   (manual)
"""
from __future__ import annotations

import base64
import json
import logging
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

import requests

from . import config

log = logging.getLogger("autoblog.indexing")

TOKEN_URL = "https://oauth2.googleapis.com/token"
PUBLISH_URL = "https://indexing.googleapis.com/v3/urlNotifications:publish"
SCOPE = "https://www.googleapis.com/auth/indexing"


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def service_account() -> dict:
    """SA credentials (env nunchi) — lekapote {}."""
    inline = os.getenv("GOOGLE_INDEXING_SA", "").strip()
    if inline:
        try:
            return json.loads(inline)
        except Exception as exc:  # noqa: BLE001
            log.warning("GOOGLE_INDEXING_SA JSON parse fail: %s", exc)
            return {}
    path = os.getenv("GOOGLE_INDEXING_SA_JSON", "").strip()
    if path:
        root = Path(__file__).resolve().parent.parent
        p = path if os.path.isabs(path) else str(root / path)
        try:
            return json.loads(Path(p).read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            log.warning("GOOGLE_INDEXING_SA_JSON read fail (%s): %s", path, exc)
    return {}


def configured() -> bool:
    sa = service_account()
    return bool(sa.get("client_email") and sa.get("private_key"))


def _sign_rs256(signing_input: bytes, private_key_pem: str) -> bytes:
    """RS256 sign — cryptography unte adi, lekapote openssl CLI (dependency-free)."""
    try:
        from cryptography.hazmat.primitives import hashes, serialization  # type: ignore
        from cryptography.hazmat.primitives.asymmetric import padding  # type: ignore

        key = serialization.load_pem_private_key(private_key_pem.encode("utf-8"), password=None)
        return key.sign(signing_input, padding.PKCS1v15(), hashes.SHA256())
    except ImportError:
        pass
    openssl = shutil.which("openssl")
    if not openssl:
        raise RuntimeError("RS256 signing ki 'cryptography' package leda openssl CLI kaavali")
    with tempfile.NamedTemporaryFile("w", suffix=".pem", delete=False) as fh:
        fh.write(private_key_pem)
        key_path = fh.name
    try:
        os.chmod(key_path, 0o600)
        proc = subprocess.run([openssl, "dgst", "-sha256", "-sign", key_path],
                              input=signing_input, capture_output=True, timeout=30)
        if proc.returncode != 0:
            raise RuntimeError(f"openssl sign fail: {proc.stderr.decode()[:200]}")
        return proc.stdout
    finally:
        try:
            os.unlink(key_path)
        except OSError:
            pass


def access_token() -> str:
    """Service account → OAuth access token (cached ~50 min)."""
    cached = getattr(access_token, "_cache", None)
    if cached and cached[1] > time.time():
        return cached[0]
    sa = service_account()
    if not sa.get("client_email") or not sa.get("private_key"):
        return ""
    now = int(time.time())
    header = _b64(json.dumps({"alg": "RS256", "typ": "JWT"}).encode())
    claims = _b64(json.dumps({
        "iss": sa["client_email"],
        "scope": SCOPE,
        "aud": TOKEN_URL,
        "iat": now,
        "exp": now + 3600,
    }).encode())
    signing_input = f"{header}.{claims}".encode("ascii")
    try:
        signature = _sign_rs256(signing_input, sa["private_key"])
    except Exception as exc:  # noqa: BLE001 — sign fail → skip (publish aapadu)
        log.warning("Google Indexing sign fail: %s", exc)
        return ""
    assertion = f"{header}.{claims}.{_b64(signature)}"
    try:
        resp = requests.post(TOKEN_URL, data={
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }, timeout=config.HTTP_TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        log.warning("Google Indexing token request fail: %s", exc)
        return ""
    if resp.status_code != 200:
        log.warning("Google Indexing token %s: %s", resp.status_code, resp.text[:160])
        return ""
    token = (resp.json() or {}).get("access_token", "")
    if token:
        access_token._cache = (token, time.time() + 3000)  # noqa: SLF001
    return token


def publish_url(url: str, kind: str = "URL_UPDATED") -> bool:
    """Google Indexing API ki okka URL publish notify (JobPosting/BroadcastEvent pages)."""
    if not url or not configured():
        return False
    token = access_token()
    if not token:
        return False
    try:
        resp = requests.post(PUBLISH_URL, json={"url": url, "type": kind},
                             headers={"Authorization": f"Bearer {token}",
                                      "Content-Type": "application/json"},
                             timeout=config.HTTP_TIMEOUT)
    except Exception as exc:  # noqa: BLE001
        log.warning("Google Indexing publish fail: %s", exc)
        return False
    if resp.status_code == 200:
        log.info("Google Indexing ✔ %s (%s)", url, kind)
        return True
    log.warning("Google Indexing %s: %s", resp.status_code, resp.text[:200])
    return False


def submit_published(article: dict, link: str) -> dict:
    """Publish ayyaka: IndexNow + (JobPosting unte) Google Indexing API.

    Returns {"indexnow": bool, "google": bool, "job": bool} — state/Telegram lo chupinchadam ki.
    """
    out = {"indexnow": False, "google": False, "job": False}
    if not link:
        return out
    try:
        from . import indexnow

        out["indexnow"] = bool(indexnow.submit(link))
    except Exception as exc:  # noqa: BLE001 — best-effort
        log.debug("indexnow skip: %s", exc)
    is_job = bool(article.get("recruitment"))
    out["job"] = is_job
    if is_job and configured():
        out["google"] = publish_url(link, "URL_UPDATED")
    return out


def status() -> dict:
    """Configuration status (CLI/readiness lo chupinchadam ki)."""
    sa = service_account()
    return {
        "configured": configured(),
        "client_email": (sa.get("client_email") or "")[:40],
        "openssl": bool(shutil.which("openssl")),
        "signing": "cryptography" if _has_crypto() else ("openssl" if shutil.which("openssl") else "none"),
        "indexnow_key": bool(getattr(config, "INDEXNOW_KEY", "")),
    }


def _has_crypto() -> bool:
    try:
        import cryptography  # noqa: F401

        return True
    except ImportError:
        return False
