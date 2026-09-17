#!/usr/bin/env python3
"""studentup.in auto-blogger CLI entry point.

  python run.py               scheduled run (hourly via systemd/cron)
  python run.py --force       create a post immediately
  python run.py --dry-run     generate locally without publishing
  python run.py --mock        offline test without Gemini key
  python run.py --status      show today's plan and stats
  python run.py --check-wp    test WordPress credentials
  python run.py --quiz        v26: today's exam-style Daily Quiz (auto topic)
  python run.py --quiz-kit    v26: update site-wide quiz UI (CSS+JS widget)
  python run.py --plugins      v28: install/activate reviewed WP plugins
  python run.py --theme-audit  v28: read-only active theme audit
  python run.py --adsense-kit  v28: install validated Auto Ads loader widget
  python run.py --production-audit  v30: production safety/revenue gate
  python run.py --service-center    v31: publish Student Internet Center page
  python run.py --content-audit      v32: audit existing posts before refresh
  python run.py --google-audit URL    v33: public HTML + PageSpeed audit
  python run.py --top-post "SSC CGL 2026 apply online"   v38: TOP POST blueprint
  python run.py --top-post "TSPSC Group 2 2026 notification" --publish-top-post
  python run.py --top-post-plan --top-post-days 90      v38: domination calendar
  python run.py --keyword-universe                      v38: ANNI keywords (10k+)
  python run.py --score-post file.html --score-keyword "ssc cgl 2026"
  python run.py --exam-portal              v39: college EXAM PORTAL (students +
                                           admin START/CLOSE, auto-close, results)
  python run.py --exam-portal-demo         v39: sample exam tho portal start
  python run.py --exam-portal-test-channels v39: Telegram/webhook test ping
  python run.py --site-audit               v41: full site audit (junk content,
                                           wrong category, PII, tags, timezone)
  python run.py --site-audit-fix           v41: audit + safe fixes (dry-run)
  python run.py --site-audit-fix --site-audit-apply   v41: fixes ni apply chey
  python run.py --ads                    v43: AD MANAGER — owner ads (college
  python run.py --ads-demo                 banners/shop/services) inventory +
                                           slot plan / visible placement preview
  python run.py --deploy-check            v41: deploy readiness (deps/env/disk/port +
                                           exam portal boot + /healthz) — server SSH lo
  python run.py --test-all                v41: ANNI suites okate command tho
  python run.py --test-all --test-only v41  v41: okka suite matrame
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
