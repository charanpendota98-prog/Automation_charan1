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
  python run.py --readiness                v62: TOP WEBSITE READINESS score (content ·
                                            SEO · ads · automation · real site)
  python run.py --push-theme-data         v61: bot data → WP theme (breaking · proof ·
                                            house ads) — REST push
                                          v73: countdown data push ledu (hero card poyindi)
  python run.py --guardian                v60: SITE GUARDIAN — site/UI/SEO/ads/
                                          feed/storage check (roju auto @ GUARDIAN_HOUR)
  python run.py --guardian-notify         v60: guardian report → Telegram
  python run.py --breaking-feed             v59: బ్రేకింగ్ న్యూస్ feed build (radar →
                                                   preview/data/breaking.json → site)
  python run.py --breaking-from F.json       v59: feed ni JSON nunchi (offline/test)
  python run.py --score-post file.html --score-keyword "ssc cgl 2026"
  python run.py --approval-poll            v74: Telegram approvals — okka poll
                                           pass (cron mode; shared hosting lo
                                           */5 min ki; daemon avasaram ledu)
  python run.py --site-audit               v41: full site audit (junk content,
                                           wrong category, PII, tags, timezone)
  python run.py --site-audit-fix           v41: audit + safe fixes (dry-run)
  python run.py --site-audit-fix --site-audit-apply   v41: fixes ni apply chey
  python run.py --ads                    v43: AD MANAGER — owner ads (college
  python run.py --ads-demo                 banners/shop/services) inventory +
                                           slot plan / visible placement preview
  python run.py --deep-research "TOPIC"  v44: DEEP POST ENGINE — source tiering
  python run.py --research-brief             + fact extraction + cross-verification
    "TOPIC" --research-year 2027          + confidence report (--deep = NotebookLM
  python run.py --deep ... --notebooklm-          passes 6-8; --notebooklm-brief FILE
    brief FILE                              merges cited NotebookLM output)
  python run.py --deploy-check            v41: deploy readiness (python/deps/files/
                                           disk/env + artifacts) — server SSH lo
                                           (v74: cron-only bot; portal boot ledu)
  python run.py --test-all                v41: ANNI suites okate command tho
  python run.py --test-all --test-only v41  v41: okka suite matrame
  python run.py --notify-test test Telegram/WhatsApp notifications
  python run.py --url LINK    source URL -> 100% original SEO rewrite post

Review flow (recommended): DEFAULT_POST_STATUS=draft in .env
  - Posts WordPress lo DRAFT lo vastayi
  - Telegram ki ✅ Publish / 🗑️ Delete buttons tho message vastundi
  - Approval bot VPS lo: python -m autoblog.approval_bot  (systemd lo 24/7 run avtundi)
  - Approval shared hosting lo: cron → */5 * * * * .../python run.py --approval-poll
"""
from autoblog.main import main

if __name__ == "__main__":
    raise SystemExit(main())
