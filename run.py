#!/usr/bin/env python3
"""studentup.in auto-blogger CLI entry point.

  python run.py               scheduled run (hourly via systemd/cron)
  python run.py --force       create a post immediately
  python run.py --dry-run     generate locally without publishing
  python run.py --mock        offline test without Gemini key
  python run.py --status      show today's plan and stats
  python run.py --check-wp    test WordPress credentials
  python run.py --notify-test test Telegram/WhatsApp notifications
  python run.py --url LINK    source URL -> 100% original SEO rewrite post

Review flow (recommended): DEFAULT_POST_STATUS=draft in .env
  - Posts WordPress lo DRAFT lo vastayi
  - Telegram ki ✅ Publish / 🗑️ Delete buttons tho message vastundi
  - Approval bot: python -m autoblog.approval_bot  (systemd lo 24/7 run avtundi)
"""
from autoblog.main import main

if __name__ == "__main__":
    raise SystemExit(main())
