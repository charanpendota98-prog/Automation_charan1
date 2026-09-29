# -*- coding: utf-8 -*-
"""v163 — real web push (VAPID)."""
from __future__ import annotations

import json
from pathlib import Path

from autoblog import webpush

ROOT = Path(__file__).resolve().parents[1]
THEME = ROOT / "wordpress-theme" / "studentup"


def test_message_parsing():
    p = webpush.parse_message("TSPSC Group 2|https://x.in/a|783 posts")
    assert p == {"title": "TSPSC Group 2", "url": "https://x.in/a", "body": "783 posts"}
    assert webpush.parse_message("Only title")["url"] == "/"
    print("      title|url|body message format parses ✔")


def test_send_refuses_without_keys(monkeypatch, tmp_path):
    monkeypatch.setattr(webpush, "KEYS_PATH", tmp_path / "none.json")
    res = webpush.send({"title": "x"}, [{"endpoint": "e", "p256dh": "p", "auth": "a"}])
    assert "error" in res and "push-keys" in res["error"]
    print("      sending without VAPID keys fails loudly, not silently ✔")


def test_keys_file_is_gitignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "push_keys.json" in ignore, "VAPID private key commit ayye risk"
    assert not (ROOT / "push_keys.json").exists(), "private key repo lo undi!"
    print("      the VAPID private key can never be committed ✔")


def test_subscribe_endpoint_validates_push_hosts():
    php = (THEME / "inc" / "webpush.php").read_text(encoding="utf-8")
    # Regex lo dots escape ayyayi, andhuke escaped form ne chustam.
    for host in (r"\.googleapis\.com", r"\.mozilla\.com", r"\.windows\.com", r"\.apple\.com"):
        assert host in php, f"push host allowlist lo ledu: {host}"
    assert "esc_url_raw" in php and "sanitize_text_field" in php
    assert "$wpdb->prepare" in php, "SQL prepare lekunda insert"
    assert "current_user_can( 'edit_posts' )" in php, "subscriber list public ga undi"
    print("      subscribe endpoint is host-checked, escaped and prepared ✔")


def test_subscriptions_are_not_stored_in_options():
    php = (THEME / "inc" / "webpush.php").read_text(encoding="utf-8")
    assert "CREATE TABLE" in php and "dbDelta" in php, \
        "vela subscriptions ni options lo pedithe prati page load slow"
    assert "UNIQUE KEY endpoint" in php, "duplicate subscriptions penchutayi"
    print("      subscriptions live in their own table with a unique endpoint ✔")


def test_prompt_waits_for_engagement():
    php = (THEME / "inc" / "webpush.php").read_text(encoding="utf-8")
    assert "store.views >= 2" in php, "modati pageview lo ne permission adugutundi"
    assert "snoozeUntil" in php and "30 * 24" in php, "No thanks gurthu pettukovadam ledu"
    assert "Notification.permission === 'denied'" in php, "denied ayina malli adugutundi"
    print("      permission is asked after engagement, and 'no' is remembered ✔")


def test_service_worker_handles_push_and_click():
    sw = (THEME / "inc" / "pwa.php").read_text(encoding="utf-8")
    assert 'addEventListener("push"' in sw, "SW lo push handler ledu"
    assert 'addEventListener("notificationclick"' in sw
    assert "showNotification" in sw and "clients.matchAll" in sw, \
        "click chesthe already open tab focus avvali"
    print("      service worker shows the push and focuses an open tab ✔")


def test_feature_off_without_a_public_key():
    php = (THEME / "inc" / "webpush.php").read_text(encoding="utf-8")
    assert "'' !== studentup_push_public_key()" in php, \
        "key lekunda prompt chupinchi permission waste chestundi"
    print("      no VAPID key => the whole feature stays off ✔")


def test_flags_documented():
    main = (ROOT / "autoblog" / "main.py").read_text(encoding="utf-8")
    assert '"--push-keys"' in main and '"--push-send"' in main
    for name in ("README.md", "MANUAL_ADVANCED_CHECKLIST.md", "GO_LIVE_CHECKLIST.md"):
        txt = (ROOT / name).read_text(encoding="utf-8")
        assert "--push-keys" in txt and "--push-send" in txt, name
    print("      --push-keys / --push-send documented in all 3 docs ✔")
