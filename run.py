#!/usr/bin/env python3
"""studentup.in auto-blogger CLI entry point.

  python run.py               scheduled run (hourly via systemd/cron)
  python run.py --force       publish immediately
  python run.py --dry-run     generate locally without publishing
  python run.py --mock        offline test without Gemini key
  python run.py --status      show today's plan and stats
  python run.py --check-wp    test WordPress credentials
"""
from autoblog.main import main

if __name__ == "__main__":
    raise SystemExit(main())
