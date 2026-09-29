# -*- coding: utf-8 -*-
"""v163 — Web push sender (VAPID).

Theme subscriptions collect chestundi; ee module vaatiki notification
pampistundi.

    python run.py --push-keys                      # okka sari: VAPID keys
    python run.py --push-send "Title|url"          # andariki pampadam
    python run.py --push-send "Title|url" --dry-run

Design decisions:

  * **Crypto ni nene raayanu.** VAPID signing ES256 — adi sonta ga
    implement cheyyadam security risk. `pywebpush` unte vaadutam, lekapothe
    exact install command cheptam. Half-baked crypto kanna clear error better.
  * **410/404 vachina subscriptions expired** — avi report chestam
    (WordPress lo clean cheyyochu). Vaatiki malli malli pampadam waste.
  * Roju ki oka push default cap. Push spam = unsubscribe + Chrome lo
    site ki permanent "blocked".
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
KEYS_PATH = ROOT / "push_keys.json"   # gitignore lo undali (secret)
TTL = 12 * 3600                        # 12 gantalu — ataruvata notification stale


def keys_available() -> bool:
    return KEYS_PATH.exists()


def load_keys() -> Optional[Dict[str, str]]:
    if not KEYS_PATH.exists():
        return None
    try:
        data = json.loads(KEYS_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not data.get("private_key") or not data.get("public_key"):
        return None
    return data


def generate_keys() -> Tuple[bool, str]:
    """VAPID keypair. Private key repo lo commit cheyyakudadu."""
    try:
        from py_vapid import Vapid01 as Vapid  # type: ignore
    except ImportError:
        try:
            from py_vapid import Vapid  # type: ignore
        except ImportError:
            return False, ("py-vapid ledu. Install: "
                           "pip install pywebpush py-vapid")
    import base64

    v = Vapid()
    v.generate_keys()
    priv = base64.urlsafe_b64encode(
        v.private_key.private_numbers().private_value.to_bytes(32, "big")
    ).decode().rstrip("=")
    pub_nums = v.public_key.public_numbers()
    raw = b"\x04" + pub_nums.x.to_bytes(32, "big") + pub_nums.y.to_bytes(32, "big")
    pub = base64.urlsafe_b64encode(raw).decode().rstrip("=")

    KEYS_PATH.write_text(
        json.dumps({"public_key": pub, "private_key": priv}, indent=2),
        encoding="utf-8")
    return True, pub


def parse_message(raw: str) -> Dict[str, str]:
    """"Title|https://url|body" → payload dict."""
    parts = [p.strip() for p in raw.split("|")]
    return {
        "title": parts[0] if parts else "",
        "url": parts[1] if len(parts) > 1 else "/",
        "body": parts[2] if len(parts) > 2 else "",
    }


def fetch_subscribers() -> Tuple[List[Dict], str]:
    """WordPress REST nunchi subscriptions (application password tho)."""
    from . import config

    base = (getattr(config, "WP_URL", "") or "").rstrip("/")
    user = getattr(config, "WP_USER", "")
    app_pw = getattr(config, "WP_APP_PASSWORD", "")
    if not base or not user or not app_pw:
        return [], ".env lo WP_URL / WP_USER / WP_APP_PASSWORD set cheyandi"

    import requests
    try:
        resp = requests.get(f"{base}/wp-json/studentup/v1/push-subscribers",
                            auth=(user, app_pw), timeout=30)
    except Exception as exc:  # noqa: BLE001 - network call
        return [], f"WordPress ki connect avvaledu: {exc}"
    if resp.status_code != 200:
        return [], f"REST {resp.status_code} — theme activate ayinda, user ki edit_posts unda?"
    try:
        return list(resp.json().get("subs") or []), ""
    except ValueError:
        return [], "REST response JSON kaadu"


def send(payload: Dict[str, str], subs: List[Dict]) -> Dict:
    """Prati subscription ki push. Expired vi separate ga report."""
    keys = load_keys()
    if not keys:
        return {"error": "push_keys.json ledu — mundu `python run.py --push-keys`"}
    try:
        from pywebpush import WebPushException, webpush  # type: ignore
    except ImportError:
        return {"error": "pywebpush ledu. Install: pip install pywebpush py-vapid"}

    sent, expired, failed = 0, [], 0
    for sub in subs:
        endpoint = sub.get("endpoint", "")
        info = {"endpoint": endpoint,
                "keys": {"p256dh": sub.get("p256dh", ""), "auth": sub.get("auth", "")}}
        try:
            webpush(subscription_info=info, data=json.dumps(payload),
                    vapid_private_key=keys["private_key"],
                    vapid_claims={"sub": "mailto:admin@studentup.in"}, ttl=TTL)
            sent += 1
        except WebPushException as exc:  # pragma: no cover - network
            code = getattr(getattr(exc, "response", None), "status_code", 0)
            if code in (404, 410):
                expired.append(endpoint)
            else:
                failed += 1
                log.warning("push fail %s: %s", endpoint[:40], exc)
    return {"sent": sent, "expired": expired, "failed": failed}


def run_cli(message: str = "", dry_run: bool = False, gen_keys: bool = False) -> int:
    print("=" * 70)
    print("  WEB PUSH")
    print("=" * 70)

    if gen_keys:
        ok, out = generate_keys()
        if not ok:
            print(f"  ❌ {out}")
            return 1
        print(f"  ✅ Keys: {KEYS_PATH.name} (private key — evvariki ivvakandi)")
        print("\n  Public key (WP → Appearance → StudentUp → VAPID public key):\n")
        print(f"    {out}\n")
        print("  push_keys.json ni git lo commit cheyyakandi.")
        return 0

    if not message:
        print("  Vaadaka: python run.py --push-send \"Title|https://site/post|body\"")
        print("  Mundu okka sari: python run.py --push-keys")
        return 1

    payload = parse_message(message)
    if not payload["title"]:
        print("  ❌ Title ledu")
        return 1

    print(f"  Title : {payload['title']}")
    print(f"  URL   : {payload['url']}")

    subs, err = fetch_subscribers()
    if err:
        print(f"  ❌ {err}")
        return 1
    print(f"  Subs  : {len(subs)}")

    if dry_run:
        print("-" * 70)
        print("  🧪 DRY RUN — emi pampaledu.")
        return 0
    if not subs:
        print("  ⚠️  Inka subscribers levu.")
        return 0

    res = send(payload, subs)
    if res.get("error"):
        print(f"  ❌ {res['error']}")
        return 1
    print("-" * 70)
    print(f"  ✅ sent {res['sent']} · expired {len(res['expired'])} · failed {res['failed']}")
    if res["expired"]:
        print("  Expired subscriptions WordPress lo clean cheyyochu (reinstall/uninstall chesinavi).")
    return 0
