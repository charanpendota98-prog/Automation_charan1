# -*- coding: utf-8 -*-
"""v48 — generate pages/ policy pages, robots.txt, sitemap.xml, favicon.svg.

Why: AdSense review (and basic trust) needs real About / Contact / Privacy /
Disclaimer / Editorial-policy pages. Footer/topbar links must not dead-end on
an anchor. Everything here is pure Telugu for the public reader.

Run:  python tools/build_policy_pages.py
"""
from __future__ import annotations

import csv
import io
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# v199.1: preview build stamp — purathana cached preview ni ventane gurtinchadaniki.
PREVIEW_BUILD = "1.9.42"
OUT = ROOT / "preview"
PAGES = OUT / "pages"
EMAIL = "studentupinformative@gmail.com"
TG = "https://t.me/studentup_in"
# v71: Students Internet Center — WhatsApp first contact (placeholder number till owner sets it)
PHONE = "9182739312"
WA_LINK = "https://wa.me/919182739312?text=StudentUp%20Students%20Internet%20Center"
UPDATED = "2026-09-18"

CSS = """/* v193 PIN-TO-PIN: the real theme CSS is linked above (style.css + worldclass.css),
   so these pages ARE the site design. Only legal-page specifics live here. */
.su-legal{max-width:900px;background:var(--card);border:1px solid var(--line);border-radius:var(--r-lg);
  box-shadow:var(--sh-1);margin:20px auto;padding:26px 30px}
.su-legal .crumbs{margin:0 0 10px}
.su-legal h1{margin:0 0 6px;font-size:clamp(22px,4.6vw,30px);color:var(--navy);line-height:1.35;letter-spacing:-.015em}
.su-legal .sub{color:var(--muted);font-size:13px;margin:0 0 20px;padding-bottom:14px;border-bottom:1px solid var(--line)}
.su-legal h2{font-size:19.5px;color:var(--navy);margin:26px 0 8px}
.su-legal h3{font-size:16.5px;color:var(--navy);margin:20px 0 6px}
.su-legal p,.su-legal li{font-size:15.5px;line-height:1.8}
.su-legal ul{padding-left:22px;margin:8px 0}
.su-legal li{margin:5px 0}
.note{background:var(--soft);border-left:4px solid var(--blue);border-radius:0 12px 12px 0;padding:13px 16px;margin:16px 0;font-size:14.5px}
.warn{background:#fff6ec;border-left-color:var(--orange)}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin:14px 0}
.tile{background:var(--soft);border:1px solid var(--line);border-radius:13px;padding:14px}
.tile b{display:block;color:var(--navy);font-size:15px;margin-bottom:3px}
.tile span{font-size:13px;color:var(--muted)}
.su-ad{background:linear-gradient(180deg,#fbfdff,#f2f7fd);border:1px dashed var(--line-2);border-radius:var(--r-lg);padding:14px 16px;margin:20px 0}
.su-ad-kicker{font-size:10.5px;letter-spacing:.09em;font-weight:800;color:var(--orange);margin-bottom:6px}
.su-ad-title{font-weight:800;color:var(--navy);font-size:15px}
.su-ad-desc{font-size:13.5px;color:var(--muted);margin:4px 0 10px}
.su-ad a.go{background:var(--blue);color:#fff;text-decoration:none;font-weight:800;border-radius:10px;padding:10px 16px;font-size:13.5px;display:inline-block}
.su-legal .cta{display:inline-flex;align-items:center;gap:8px;background:linear-gradient(135deg,var(--orange),#e2701a);color:#fff;
  text-decoration:none;font-weight:800;border-radius:13px;padding:0 18px;min-height:var(--tap);margin:6px 8px 6px 0;font-size:15px}
.su-legal .cta.alt{background:linear-gradient(135deg,var(--blue),var(--navy-2))}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14.5px}
th,td{text-align:left;padding:10px;border-bottom:1px solid var(--line)}
th{background:var(--soft);color:var(--navy);font-size:13px}
.steps{margin:10px 0 12px;padding-left:20px;line-height:1.8}
.steps li{margin-bottom:5px}
.wa-box{display:inline-block;background:linear-gradient(135deg,#25d366,#128c7e);color:#fff!important;
  border-radius:13px;padding:12px 16px;text-decoration:none;font-weight:800;margin:4px 8px 4px 0;
  box-shadow:0 10px 22px rgba(18,140,126,.22)}
.wa-box small{font-weight:600;opacity:.93}
.leadgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0 0}
.leadgrid input,.leadgrid select{width:100%;padding:11px 12px;border:1px solid var(--line);
  border-radius:11px;font:inherit;background:var(--card);color:inherit}
@media(max-width:600px){.su-legal{padding:20px 16px;margin:14px auto;border-radius:14px}.leadgrid{grid-template-columns:1fr}}""".strip()

NAV = [
    ("about.html", "About us"),
    ("advertise.html", "Partner with us"),
    ("contact.html", "Contact"),
    ("privacy.html", "Privacy policy"),
    ("disclaimer.html", "Disclaimer"),
    ("terms.html", "Terms"),
    ("editorial-policy.html", "Editorial policy"),
]

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title} · studentup.in</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="theme-color" content="#0b2447">
<link rel="canonical" href="https://studentup.in/pages/{slug}.html">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="{title} · studentup.in">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="en_IN">
<meta property="og:url" content="https://studentup.in/pages/{slug}.html">
<meta property="og:image" content="https://studentup.in/logo.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebPage","name":"{title}","inLanguage":"en-IN",
"url":"https://studentup.in/pages/{slug}.html","isPartOf":{{"@type":"WebSite","name":"studentup.in",
"url":"https://studentup.in/"}},"publisher":{{"@type":"Organization","name":"studentup.in",
"email":"{email}"}},"dateModified":"{updated}"}}
</script>
<link rel="stylesheet" href="../../wordpress-theme/studentup/style.css">
<link rel="stylesheet" href="../../wordpress-theme/studentup/assets/css/worldclass.css">
<script src="../../wordpress-theme/studentup/assets/js/studentup-menu.js" defer></script>
<style>
{css}
</style>
</head>
<body>
{sprite}
{header}
<main id="main">
  <div class="wrap">
    <div class="su-legal">
      <nav class="crumbs" aria-label="Breadcrumb"><a href="../worldclass/index.html">Home</a> › {title}</nav>
      <h1>{h1}</h1>
      <p class="sub">{sub}</p>
{body}
    </div>
  </div>
</main>
{script}
{footerbar}
{bottomnav}
{pagejs}
</body>
</html>
"""


AD_SLOT = """  <aside class="su-ad" aria-label="Sponsored content" data-slot="policy-inline">
    <div class="su-ad-kicker">SPONSORED · PARTNER PLACEMENT</div>
    <div class="su-ad-title">Your college / shop / coaching can appear here</div>
    <p class="su-ad-desc">A clean, clearly labelled placement on the pages students read most —
      no fake clicks, no clickbait.</p>
    <a class="go" href="advertise.html" rel="sponsored">Partner with us</a>
  </aside>

"""


PAGE_JS = """(function(){
  var b=document.body, btn=document.getElementById('su-theme');
  if(btn){
    var MOON='<svg class="su-uicon" width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><use href="#su-i-moon"/></svg>';
    var SUN='<svg class="su-uicon" width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.2 5.2l1.4 1.4M17.4 17.4l1.4 1.4M18.8 5.2l-1.4 1.4M6.6 17.4l-1.4 1.4"/></svg>';
    function paint(){ btn.innerHTML = b.classList.contains('dark') ? SUN : MOON; }
    try{ if(localStorage.getItem('su_theme')==='dark') b.classList.add('dark'); }catch(e){}
    paint();
    btn.addEventListener('click',function(){
      b.classList.toggle('dark');
      try{ localStorage.setItem('su_theme', b.classList.contains('dark')?'dark':'light'); }catch(e){}
      paint();
    });
  }
  var anchor=document.getElementById('su-anchor');
  if(anchor && window.innerWidth<900){
    try{ if(!localStorage.getItem('su_anchor_closed')) setTimeout(function(){ anchor.hidden=false; },6000); }catch(e){}
    var c=anchor.querySelector('button');
    if(c) c.addEventListener('click',function(){ try{ localStorage.setItem('su_anchor_closed','1'); }catch(e){} });
  }

  /* Scroll Progress Bar & Floating Action Bar */
  var pBar = document.getElementById('su-progress-bar');
  var fBar = document.getElementById('su-float-bar');
  var fClosed = false;
  window.addEventListener('scroll', function(){
    var h = document.documentElement.scrollHeight - window.innerHeight;
    var pct = h > 0 ? (window.scrollY / h) * 100 : 0;
    if(pBar) pBar.style.width = Math.min(100, Math.max(0, pct)) + '%';
    if(fBar && !fClosed && window.innerWidth < 800){
      fBar.hidden = window.scrollY < 260 || pct > 94;
    }
  }, { passive: true });
  var fbClose = document.getElementById('su-fb-close');
  if(fbClose){
    fbClose.addEventListener('click', function(){
      fClosed = true;
      if(fBar) fBar.hidden = true;
    });
  }
})();"""


def mega_nav_html(home: str = "../worldclass/index.html", pfx: str = "../") -> str:
    """v197: the SAME mega markup the WP theme renders (inc/megamenu.php).

    Pin-to-pin rule: classes/attrs/id prefixes match the theme exactly, so the
    theme CSS + studentup-menu.js work on the preview without a single change.
    """
    cat = pfx + "pages/"
    groups = [
        ("Jobs", home + "#jobs", "bank", [
            ("Telangana & Andhra Pradesh", [
                ("TS Government Jobs", cat + "ts-jobs-hub.html", "TSPSC · Police · Gurukul", "bank"),
                ("AP Government Jobs", home + "#jobs", "APPSC · Police · DSC · Secretariat", "bank"),
                ("Jobs by qualification", home + "#jobs", "10th · Inter · Degree · PG", "school"),
            ]),
            ("Central & private", [
                ("Central Govt Jobs", home + "#jobs", "SSC · UPSC · Railways · Banks", "flag"),
                ("Private Jobs", home + "#jobs", "Off-campus · fresher drives", "building"),
                ("Software Jobs", home + "#jobs", "IT · developer · support", "laptop"),
                ("Walk-in Interviews", home + "#jobs", "This week drives · venues", "walk"),
                ("Internships", home + "#jobs", "Stipend · remote · college", "work"),
            ]),
        ], ("Latest active jobs", "Only notices with live dates — no expired lists.", home + "#jobs", "Open the board")),
        ("Exams", cat + "results-hub.html", "board", [
            ("Updates", [
                ("Results", cat + "results-hub.html", "Board · competitive · keys", "doc"),
                ("Hall Tickets", cat + "results-hub.html", "Admit card · instructions", "ticket"),
                ("Exam Calendar", cat + "exam-calendar.html", "Confirmed last dates + .ics", "calendar"),
            ]),
            ("Practice", [
                ("Daily Quiz & Polls", cat + "daily-quiz.html", "Fresh questions every day", "chart"),
                ("Current Affairs", home + "#jobs", "Daily GK for exams", "news"),
                ("Free exam tools", pfx + "tools/index.html", "Track subject-wise progress", "book"),
                ("Answer keys", cat + "results-hub.html", "Keys after every exam", "key"),
            ]),
        ], ("Exam calendar 2026", "Add every confirmed last date to your phone in one tap.", cat + "exam-calendar.html", "Open calendar")),
        ("Scholarships", cat + "scholarships-hub.html", "school", [
            ("Find money", [
                ("Scholarships", cat + "scholarships-hub.html", "NSP · ePASS · state schemes", "school"),
                ("Scholarships 2026 hub", cat + "scholarships-hub.html", "Amounts, eligibility, last dates", "doc"),
                ("Success Stories", home + "#jobs", "Verified journeys · lessons", "trophy"),
            ]),
            ("By level", [
                ("Pre-matric (Class 9-10)", cat + "scholarships-hub.html", "School-level schemes", "book"),
                ("Post-matric (Inter · Degree)", cat + "scholarships-hub.html", "The biggest State schemes", "school"),
                ("Minority & overseas", cat + "scholarships-hub.html", "NSP minority + abroad aid", "flag"),
            ]),
        ], ("Free Internet Center", "Form filling at a fixed, published price — what we do and never do.", cat + "internet-center.html", "See the price list")),
        ("Tools", pfx + "tools/index.html", "key", [
            ("Calculators", [
                ("Age Eligibility", pfx + "tools/index.html", "With reservation relaxation", "person"),
                ("Fee Calculator", pfx + "tools/index.html", "Application + exam fee", "card"),
                ("Salary / In-hand", pfx + "tools/index.html", "7th Pay Commission", "wallet"),
            ]),
            ("Career tools", [
                ("Resume Maker", pfx + "tools/index.html", "Govt-format resume, free", "doc"),
                ("Compare Jobs", pfx + "tools/index.html", "Side-by-side up to 3 posts", "swap"),
                ("Saved Posts", pfx + "tools/index.html", "Read later, on this device", "bookmark"),
            ]),
        ], ("All free tools", "No signup, no phone number — works on any phone.", pfx + "tools/index.html", "Open Tools")),
        ("More", cat + "about.html", "help", [
            ("Site", [
                ("About StudentUp", cat + "about.html", "Who writes and verifies", "person"),
                ("Editorial Team", cat + "editorial-team.html", "Standards + sources", "shield"),
                ("Corrections Log", cat + "corrections.html", "Public fixes · 48h SLA", "refresh"),
                ("Contact", cat + "contact.html", "Corrections · suggestions", "phone"),
                ("Advertise", cat + "advertise.html", "Sponsorship slots", "tag"),
            ]),
            ("Policies", [
                ("Privacy Policy", cat + "privacy.html", "What we store (very little)", "shield"),
                ("Terms of Use", cat + "terms.html", "Rules for using the site", "doc"),
                ("Disclaimer", cat + "disclaimer.html", "Not a government website", "alert"),
                ("Editorial Policy", cat + "editorial-policy.html", "How we verify every update", "check"),
            ]),
        ], ("Telegram channel", "Job alerts reach you first — no spam, leave anytime.", "https://t.me/studentup_in", "Join channel")),
    ]

    out = ['<ul id="primary-menu" class="menu-primary su-has-mega">',
           '<li class="menu-item"><a href="%s">Home</a></li>' % home]
    # v202: Breaking News item — theme `studentup_breaking_nav_li()` (inc/nav-breaking.php)
    # laage same markup: li.menu-item-has-children.su-navbrk + ul#su-brkdd panel.
    # Live lo theme ee item ni `wp_nav_menu_items` filter / mega render tho istundi.
    brk_rows = [
        ("UPSC Junior Assistant 2026 — notification out", pfx + "posts/upsc-junior-assistant-2026.html", "yesterday · Central"),
        ("Govt internships for engineering students 2026", pfx + "posts/engineering-internships-2026.html", "yesterday · Internships"),
        ("TSPSC Group 2 last date 28 October", cat + "exam-calendar.html", "2 days ago · Telangana"),
        ("IBPS Clerk online apply — 4,520 posts", pfx + "posts/ibps-clerk-2026.html", "3 days ago · Banking"),
        ("SSC CHSL 2026 notification — 3,712 posts", cat + "results-hub.html", "4 days ago · Central"),
    ]
    brk_url = home + "#jobs"
    out.append('<li class="menu-item menu-item-has-children su-navbrk">'
               '<a href="%s" aria-haspopup="true" aria-expanded="false" aria-controls="su-brkdd">'
               '<span class="su-brkdot" aria-hidden="true"></span>'
               '<span class="su-mega-lb">Breaking News</span></a>' % brk_url)
    out.append('<ul class="sub-menu su-brkdd" id="su-brkdd" aria-label="Breaking News">')
    out.append('<li class="menu-item su-brkdd-head" role="none">'
               '<span>Latest verified updates</span><em>Live</em></li>')
    for btitle, burl, bmeta in brk_rows:
        out.append('<li class="menu-item" role="none"><a role="menuitem" href="%s">'
                   '<span class="su-mega-ic"><svg class="su-uicon su-uicon-bolt" width="16" height="16" '
                   'viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">'
                   '<use href="#su-i-bolt"/></svg></span><span class="su-mega-t">%s<small>%s</small>'
                   '</span></a></li>' % (burl, btitle, bmeta))
    out.append('<li class="menu-item su-brkdd-foot" role="none">'
               '<a class="su-brkdd-cta" href="%s">All updates '
               '<svg class="su-uicon su-uicon-arrow" width="13" height="13" viewBox="0 0 24 24" '
               'fill="currentColor" aria-hidden="true" focusable="false">'
               '<use href="#su-i-arrow"/></svg></a></li>' % brk_url)
    out.append('</ul></li>')
    for label, url, icon, cols, feat in groups:
        key = label.lower()
        out.append('<li class="menu-item menu-item-has-children su-mega-li">')
        out.append('<a href="%s" aria-haspopup="true" aria-expanded="false" aria-controls="su-mega-%s">'
                   '<span class="su-mega-lb">%s</span></a>' % (url, key, label))
        out.append('<ul class="sub-menu" id="su-mega-%s" data-su-mega aria-label="%s">' % (key, label))
        for title, items in cols:
            out.append('<li class="su-mega-col menu-item" role="none">')
            if title:
                out.append('<p class="su-mega-title">%s</p>' % title)
            out.append('<ul class="su-mega-list">')
            for ilabel, iurl, idesc, iicon in items:
                out.append('<li class="menu-item" role="none"><a role="menuitem" href="%s">'
                           '<span class="su-mega-ic"><svg class="su-uicon su-uicon-%s" width="18" height="18" '
                           'viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false">'
                           '<use href="#su-i-%s"/></svg></span><span class="su-mega-t">%s<small>%s</small>'
                           '</span></a></li>' % (iurl, iicon, iicon, ilabel, idesc))
            out.append('</ul></li>')
        ftitle, fdesc, furl, fcta = feat
        out.append('<li class="su-mega-feat menu-item" role="none">'
                   '<span class="su-mega-eyebrow">Recommended</span><b>%s</b><small>%s</small>'
                   '<a class="su-mega-cta" href="%s">%s →</a></li>' % (ftitle, fdesc, furl, fcta))
        out.append('</ul></li>')
    out.append('</ul>')
    return "".join(out)


def header_html(home: str = "../worldclass/index.html", topbar: str = "Government jobs \u00b7 Exams \u00b7 Scholarships") -> str:
    """Shared header — the SAME classes as the WP theme header.php."""
    links = mega_nav_html(home, "../")
    return ('<a class="skip-link screen-reader-text" href="#main">Skip to content</a>\n'
            '<div class="topbar"><div class="wrap">\n'
            '  <span>' + topbar + '</span>\n'
            '  <span><a href="https://wa.me/919182739312">WhatsApp</a> \u00b7 <a href="https://t.me/studentup_in">Telegram</a></span>\n'
            '</div></div>\n'
            '<header class="header"><div class="headrow">\n'
            '  <a class="logo" href="' + home + '"><span class="mark">SU</span><span><span class="brand">StudentUp</span><small>studentup.in</small></span></a>\n'
            '  <nav class="nav" aria-label="Main">' + links + '</nav>\n'
            '  <div class="headactions"><button class="iconbtn" id="su-theme" type="button" aria-label="Dark mode toggle"><svg class="su-uicon su-uicon-moon" width="17" height="17" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-moon"/></svg></button></div>\n'
            '</div></header>')


def footer_html(home: str = "../worldclass/index.html", pfx: str = "") -> str:
    """Shared footer — same 4-column grid as the WP theme footer.php."""
    return ('<footer class="su-foot"><div class="su-foot-grid">\n'
            '  <div><h4>StudentUp</h4><p style="margin:0;color:#a9bfdd">Verified government job, exam and scholarship updates for Telangana &amp; AP students.</p></div>\n'
            '  <div><h4>Jobs</h4><ul><li><a href="' + home + '#jobs">TS Jobs</a></li><li><a href="' + home + '#jobs">AP Jobs</a></li><li><a href="' + home + '#jobs">Central Govt</a></li><li><a href="' + home + '#jobs">Bank Jobs</a></li></ul></div>\n'
            '  <div><h4>Site</h4><ul><li><a href="' + pfx + 'about.html">About us</a></li><li><a href="' + pfx + 'contact.html">Contact</a></li><li><a href="' + pfx + 'advertise.html">Advertise</a></li><li><a href="' + pfx + 'editorial-policy.html">Editorial policy</a></li></ul></div>\n'
            '  <div><h4>Legal</h4><ul><li><a href="' + pfx + 'privacy.html">Privacy</a></li><li><a href="' + pfx + 'disclaimer.html">Disclaimer</a></li><li><a href="' + pfx + 'terms.html">Terms</a></li><li><a href="https://t.me/studentup_in">Telegram</a></li></ul></div>\n'
            '</div>\n'
            '<div class="preview-stamp" style="max-width:1180px;margin:0 auto;padding:0 16px 14px;'
            'font-size:11.5px;color:#7b8aa3">Preview build <b>' + PREVIEW_BUILD + '</b> · theme + bot deploy-ready</div>\n'
            '<div class="su-foot-bottom">\u00a9 2026 studentup.in \u00b7 Sources: official notifications only. '
            'Ad revenue, rankings and job results are never guaranteed \u2014 always confirm the real information in the official notification. '
            'We are not a government website. '
            '\u00b7 <a href="../index.html">Static HTML version</a></div></footer>')


def bottom_html(home: str = "../worldclass/index.html") -> str:
    """Phone bottom nav + dismissible sticky ad — same as the WP theme."""
    return ('<nav class="su-bottomnav" aria-label="Quick nav">\n'
            '  <a href="' + home + '"><span class="su-bi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><use href="#su-i-home"/></svg></span>Home</a>\n'
            '  <a href="' + home + '#jobs"><span class="su-bi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><use href="#su-i-work"/></svg></span>Jobs</a>\n'
            '  <a href="../tools/index.html"><span class="su-bi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><use href="#su-i-chart"/></svg></span>Tools</a>\n'
            '  <a href="' + home + '#alerts"><span class="su-bi"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><use href="#su-i-bell"/></svg></span>Alerts</a>\n'
            '</nav>\n'
            '<div class="su-anchor" id="su-anchor" hidden>\n'
            '  <div class="su-anchor-ad">Advertisement \u00b7 sticky slot</div>\n'
            '  <button type="button" aria-label="Close advertisement" onclick="document.getElementById(\'su-anchor\').hidden=true">\u2715</button>\n'
            '</div>')


def nav_html() -> str:

    return "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV)


def build(slug: str, title: str, desc: str, h1: str, sub: str, body: str,
          script: str = "") -> str:
    marker = '<p><a class="cta"'
    if marker in body:
        body = body.replace(marker, AD_SLOT + marker, 1)
    else:
        body = body + "\n" + AD_SLOT
    try:
        import build_sprite  # noqa: PLC0415 — same tools/ dir, single source of truth
        _paths = build_sprite.icon_paths()
    except Exception:  # pragma: no cover — never break a page build for an icon
        _paths = {}
    _nav = nav_html()
    _hdr = header_html()          # v202: mega + Breaking News nav (bolt icon) kuda scan avvali
    _foot = footer_html(pfx="")
    _keys = set(build_sprite.used_icon_keys((_nav + _hdr + _foot + body + script) if _paths else ""))
    _keys |= {"moon", "sun", "home", "work", "chart", "bell", "close", "search",
              "bank", "flag", "school", "ticket", "doc", "calendar", "news", "key",
              "trophy", "person", "card", "wallet", "swap", "bookmark", "shield",
              "refresh", "phone", "tag", "alert", "check", "arrow", "building",
              "laptop", "walk", "work", "help", "board", "book", "arrow", "external",
              "bolt", "star", "print", "clock", "home"}
    _sprite = build_sprite.sprite_svg(_paths, sorted(_keys)) if _paths else ""
    return SHELL.format(sprite=_sprite, title=title, desc=desc, slug=slug, h1=h1, sub=sub,
                        body=body, css=CSS, nav=_nav, email=EMAIL, updated=UPDATED,
                        wa=WA_LINK, phone=PHONE, script=script, pagejs=PAGE_JS,
                        header=_hdr, footerbar=_foot,
                        bottomnav=bottom_html())


ABOUT = """
  <h2>Welcome to StudentUp</h2>
  <p>StudentUp is an independent education and career-information platform for students,
  freshers and job-seekers. We bring useful TS, AP and central updates into one clear place,
  using simple language and links back to the official notification.</p>

  <h2>What you can find here</h2>
  <div class="grid">
    <div class="tile"><b>Jobs &amp; opportunities</b><span>Government, private, software, walk-in and internship updates with eligibility and official apply links.</span></div>
    <div class="tile"><b>Scholarships &amp; admissions</b><span>Application windows, documents and steps for students — always check the issuing portal before applying.</span></div>
    <div class="tile"><b>Exams, hall tickets &amp; results</b><span>Exam notices, admit cards, results and preparation guidance in a student-friendly format.</span></div>
    <div class="tile"><b>Skills &amp; practice</b><span>Reasoning, simple English aptitude, general knowledge, interview preparation and technology-learning resources.</span></div>
  </div>

  <h2>Our mission</h2>
  <p>Our mission is to make important student information easier to understand and act on,
  while helping readers make their own informed decisions. We do not replace an official
  department, university or employer; we help readers find and read the original source.</p>

  <h2>How it works</h2>
  <div class="grid">
    <div class="tile"><b>1 · Source monitoring</b><span>We track official sources such as TSPSC, APPSC, SSC, NSP, state boards, DSC and DISCOMs.</span></div>
    <div class="tile"><b>2 · Verification gates</b><span>Dates, eligibility and important claims are checked against the available official evidence before a draft is prepared.</span></div>
    <div class="tile"><b>3 · Human review</b><span>Automation can assist research and drafting, but doubtful information stays out of public content until reviewed.</span></div>
    <div class="tile"><b>4 · Corrections</b><span>When a notification changes, older information can be corrected and the last-updated date is shown on the article.</span></div>
  </div>

  <h2>Our vision</h2>
  <p>We want StudentUp to be a dependable starting point for Telangana and Andhra Pradesh
  students as they learn, prepare and explore opportunities — with clarity, useful practice
  and honest limits.</p>

  <h2>What we never do</h2>
  <ul>
    <li>We are not a government body and have no connection with TSPSC, APPSC, SSC, NSP or any department.</li>
    <li>We never guarantee a job, scholarship, admission, rank, income or selection.</li>
    <li>We never ask for an OTP, PIN, password or bank details to show an update.</li>
    <li>We never sell personal data — see the <a href="privacy.html">privacy policy</a>.</li>
  </ul>

  <div class="note"><b>Always verify:</b> deadlines, vacancy counts, fees, eligibility and results can change.
  Confirm them once in the official notification. If you spot a mistake, send us the article link
  through the <a href="contact.html">Contact page</a> so we can review it.</div>

  <p><a class="cta" href="../index.html">See today's updates</a>
     <a class="cta alt" href="contact.html">Contact StudentUp</a></p>
  <p><b>StudentUp — learn, grow and make informed decisions.</b></p>
"""

CONTACT = """
  <p>For corrections, partnerships and student help, contact StudentUp through WhatsApp or email.
  Please include the relevant page link so we can respond quickly.</p>

  <p><a class="wa-box" href="{wa}" target="_blank" rel="noopener"><b>WhatsApp</b><br>
     <small>Open our chat</small></a>
     <a class="cta alt" href="tel:{phone}">Call</a>
     <a class="cta alt" href="mailto:{email}">Email</a>
     <a class="cta alt" href="{tg}" target="_blank" rel="noopener">Telegram</a></p>

  <h2>Corrections</h2>
  <p>Send the article link, the incorrect detail and the official source showing the correction.
  We review it before changing the page.</p>

  <h2>Partnerships</h2>
  <p>For colleges, coaching centres, shops or services, share your organisation name, city, website
  and the page or campaign you are asking about. Paid placements are clearly labelled and never mixed
  with editorial recommendations.</p>

  <h2>Free updates</h2>
  <p>Use the short form below to prepare a WhatsApp message for free job and exam updates. Nothing is
  stored on this website until you choose to send the message.</p>
  <form id="leadform" novalidate>
    <div class="leadgrid">
      <input type="text" id="ld-name" name="name" maxlength="60" autocomplete="name" placeholder="Your name" aria-label="Your name" required>
      <input type="tel" id="ld-phone" name="phone" maxlength="15" inputmode="numeric" autocomplete="tel" placeholder="Mobile number" aria-label="Mobile number" required>
      <select id="ld-interest" name="interest" aria-label="What are you looking for?">
        <option value="jobs">Jobs</option><option value="scholarships">Scholarships</option>
        <option value="exams">Exams</option><option value="other">Other</option>
      </select>
      <input type="text" id="ld-city" name="city" maxlength="40" autocomplete="address-level2" placeholder="City (optional)" aria-label="City">
      <input type="text" class="lead-hp" id="ld-website" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">
    </div>
    <button type="submit" class="leadbtn" id="ld-submit">Open WhatsApp</button>
    <p class="leadmsg" id="ld-msg" role="status" aria-live="polite"></p>
    <p class="leadnote">You control the final send — the form only opens WhatsApp with your text, nothing is stored on our server. We do not sell your number. See the <a href="privacy.html">privacy policy</a>.</p>
  </form>

  <div class="note warn"><b>Fraud warning:</b> StudentUp will never ask for an OTP, Aadhaar number, password, bank details,
  UPI PIN or an upfront fee to show an update. Report suspicious messages to <a href="mailto:{email}">{email}</a>.</div>
"""

CONTACT_SCRIPT = """<script>
/* v74 — free-updates form → WhatsApp compose (no server, no database).
   Details ni WhatsApp message ga ready chesi owner number ki open chestundi —
   press send, ayipoyindi. Server/store ledu kabatti leak avvadaniki emi ledu. */
(function(){
  var f=document.getElementById("leadform"); if(!f) return;
  var WA_NUMBER="919182739312"; /* same owner number as the links on this page */
  var msg=document.getElementById("ld-msg");
  function say(text,ok){ msg.textContent=text; msg.className="leadmsg "+(ok?"ok":"err"); }
  f.addEventListener("submit",function(e){
    e.preventDefault();
    var name=(document.getElementById("ld-name").value||"").trim();
    var phone=(document.getElementById("ld-phone").value||"").replace(/\D/g,"");
    var interest=document.getElementById("ld-interest").value;
    var city=(document.getElementById("ld-city").value||"").trim();
    var hp=(document.getElementById("ld-website").value||"").trim();
    if(hp){ say("✅ You are on the list!",true); f.reset(); return; } /* spam trap */
    if(name.length<2){ say("⚠️ Please enter your name.",false); return; }
    if(!/^[6-9]\d{9}$/.test(phone)){ say("⚠️ Enter a valid 10-digit mobile number (e.g. 9876543210).",false); return; }
    var text="StudentUp free updates: name="+name+", mobile="+phone+", interest="+interest+(city?", city="+city:"");
    var w=window.open("https://wa.me/"+WA_NUMBER+"?text="+encodeURIComponent(text),"_blank");
    if(w){ w.opener=null; }
    say("✅ Opening WhatsApp — press send to join the free updates list.",true); f.reset();
  });
})();
</script>"""

PRIVACY = """
  <p>Welcome to StudentUp. This short policy explains what information may be processed when you
  visit the site, read an article or use the quiz.</p>

  <h2>Information we collect</h2>
  <p>Hosting and security systems may receive technical information such as browser type, device,
  IP address, referring page, pages visited and basic usage or error data. This helps with security
  and performance; exact logs and retention depend on the hosting provider.</p>
  <p>StudentUp does not require an account or ask for Aadhaar, OTPs, passwords, UPI PINs or bank
  details to read an update. If you contact us, we use the information you choose to send for that
  request. We do not sell personal information.</p>

  <h2>Cookies and browser storage</h2>
  <p>Necessary cookies or similar browser features may support security, consent and performance.
  Theme choice, saved posts, quiz scores and daily answers may stay in your browser. Optional saved-post
  account sync works only when enabled and logged in. You can block or delete cookies in your browser;
  some features may then stop working.</p>

  <h2>Polls and quiz answers</h2>
  <p>Poll votes, quiz scores and saved posts are kept in <strong>Your browser only</strong> (localStorage).
  They are never tied to your identity and never counted by IP address, so clearing browser storage
  simply resets them.</p>

  <h2>Google AdSense</h2>
  <p>Google AdSense is used only after approval, publisher configuration and consent setup. Until then,
  house or partner placements are clearly labelled. When AdSense is active, Google and its partners may
  use cookies for personalised or non-personalised advertising based on your choices and visits to this
  or other websites.</p>
  <p>Third-party vendors, including Google, use cookies to serve ads based on a user's prior visits to
  this website or other websites. Google's use of advertising cookies enables it and its partners to
  serve ads to users based on their visit to this and/or other sites on the internet. Users may opt out
  of personalised advertising by visiting Google Ads Settings, or opt out of a third-party vendor's use
  of cookies for personalised advertising at aboutads.info/choices.</p>
  <p>Manage choices at <a href="https://www.google.com/settings/ads" rel="nofollow noopener" target="_blank">Google Ads Settings</a>
  or <a href="https://www.aboutads.info/choices/" rel="nofollow noopener" target="_blank">aboutads.info/choices</a>.
  Where required, a consent message is shown before advertising cookies are used.</p>

  <h2>Third-party links</h2>
  <p>Articles may link to official portals, employers, universities and other websites. We do not
  control their content or privacy practices. Read their policy before submitting personal data and
  confirm jobs, scholarships, exams and results on the official notification.</p>

  <h2>Security, requests and changes</h2>
  <p>We take reasonable measures to protect information under our control, but no internet method is
  completely secure. Do not send passwords, OTPs, financial credentials or sensitive documents through
  ordinary email or chat. For a privacy question, correction or deletion request, contact
  <a href="mailto:{email}">{email}</a>. We may update this page when the website, advertising tools or
  legal requirements change.</p>

  <p><strong>StudentUp Team</strong><br>StudentUp — your education and career information platform.</p>
"""

DISCLAIMER = """
  <div class="note warn"><b>Important note:</b> studentup.in is a private information platform.
  It is not a government website; we have no official connection with TSPSC, APPSC, SSC, NSP,
  state boards or any government body.</div>

  <h2>How reliable is the information?</h2>
  <ul>
    <li>Every article is prepared only from official sources (mainly .gov.in portals) and
      cross-verified with 2+ sources.</li>
    <li>Even so, government can change dates, vacancy counts, fees and rules. That is why the
      <b>final decision is always the official notification</b> — confirm once on the official portal
      before you apply.</li>
    <li>No job, scholarship, admission, result, ranking or income is ever guaranteed.</li>
  </ul>

  <h2>About financial frauds</h2>
  <p>If anyone asks for money in our name saying "job guaranteed" or "seat guaranteed", it is a fraud.
  We never charge a fee and never ask for OTP or bank details. If you get such a call or message,
  <a href="mailto:{email}">tell us immediately</a>.</p>

  <h2>About advertisements</h2>
  <ul>
    <li>Advertisements are clearly marked with a <b>SPONSORED</b> label; links carry
      <code>rel="sponsored nofollow"</code>.</li>
    <li>We are not responsible for the information on advertisers' websites or the quality of their
      services. Verify their details before paying.</li>
    <li>Advertisers have no control over editorial content.</li>
  </ul>

  <h2>External links</h2>
  <p>We link to official portals. Their content, availability and security are their responsibility —
  they are not under our control.</p>
"""

TERMS = """
  <div class="note warn"><b>Short version:</b> studentup.in is a free information site for
  Telangana &amp; Andhra Pradesh students. Use it for information only — always confirm on the
  official portal before you apply or pay anything. We are not a government website and we do not
  guarantee any job, seat, scholarship, result or income.</div>

  <h2>1 · Who can use this site</h2>
  <p>studentup.in is meant for students, parents, teachers and job-seekers. By opening or using
  this website you accept these terms. If you do not agree with them, please do not use the site.
  If you are under 18, use the site with a parent or guardian.</p>

  <h2>2 · What you may do</h2>
  <ul>
    <li>Read, print and share our pages and article links freely — personal, non-commercial use.</li>
    <li>Share a short excerpt with a <b>visible link back</b> to the original page.</li>
    <li>Write to us with a correction, a new notification or a doubt — we act on official information.</li>
  </ul>

  <h2>3 · What you may not do</h2>
  <ul>
    <li>Do not copy full articles and republish them as your own (see section 4).</li>
    <li>Do not scrape, hammer or automate requests in a way that slows the site for other readers.</li>
    <li>Do not upload or post anything unlawful, abusive, casteist, communal, defamatory or misleading
      — including in poll votes, saved lists or messages to us.</li>
    <li>Do not use this site to run a scam, sell "guaranteed jobs or seats", or collect fees from
      students in our name.</li>
  </ul>

  <h2>4 · Our content and copyright</h2>
  <p>All original text, page design, graphics and the studentup name belong to studentup.in. Facts,
  dates, fees and eligibility details belong to the official notification they came from — the credit
  for those always goes to the department or board that published them. Logos and names of government
  departments appear only to identify the notification; they do not mean any partnership or approval.</p>
  <p>If you believe something on this site belongs to you and has been used wrongly, write to
  <a href="mailto:{email}">{email}</a> with the page link and proof. We correct or remove it quickly.</p>

  <h2>5 · Advertisements and sponsored placements</h2>
  <ul>
    <li>Some placements are paid and are always labelled <b>SPONSORED</b>. Sponsored links carry
      <code>rel="sponsored nofollow"</code>.</li>
    <li>Third-party ad networks (including Google and its partners) may use cookies to show ads.
      This is explained in our <a href="privacy.html">privacy policy</a>, along with how to opt out.</li>
    <li>We do not endorse an advertiser's service and are not responsible for what happens on their
      website. Verify everything before you pay anyone.</li>
  </ul>

  <h2>6 · Third-party links</h2>
  <p>We link to official portals (TSPSC, APPSC, SSC, NSP, board and university sites) and sometimes to
  other useful pages. We do not control those sites and cannot promise that their content, links or
  downloads are correct or safe at all times.</p>

  <h2>7 · Information is provided "as is"</h2>
  <p>We work only from official sources and check every post before publishing, but government dates,
  vacancy numbers, fees and rules change without notice. This site is information, not legal, financial,
  medical or career advice, and it is not a government service. The final authority is always the
  official notification. See our <a href="disclaimer.html">disclaimer</a> for details.</p>

  <h2>8 · Limits of our responsibility</h2>
  <p>To the extent allowed by law, studentup.in is not liable for any loss — missed deadlines, rejected
  applications, exam or travel expenses, lost data, or decisions taken after reading this site. Use the
  site at your own risk and keep a copy of anything important.</p>

  <h2>9 · Changes to these terms</h2>
  <p>We may update these terms when the site, the law or our ad partners change. The new version appears
  on this page with an updated date, and continuing to use the site means you accept it.</p>

  <h2>10 · Governing law and contact</h2>
  <p>These terms are governed by the laws of India, with jurisdiction in Telangana, India. Questions,
  corrections or complaints: <a href="mailto:{email}">{email}</a> ·
  <a href="{wa}" rel="noopener">WhatsApp us</a> · or read the
  <a href="editorial-policy.html">editorial policy</a> to see how posts are made.</p>
"""


EDITORIAL = """
  <p>Every post has to clear these 5 gates before publishing. If a gate fails, the post stops —
  we do not let it through saying "good enough".</p>

  <div class="grid">
    <div class="tile"><b>① Source check (fact guard)</b><span>Every date and number must match the source
      document — if it does not match, it is auto-flagged.</span></div>
    <div class="tile"><b>② Deep cross-verification</b><span>2+ sources, official ones preferred;
      conflicting dates or stale-year data block publishing. Confidence score 0–100.</span></div>
    <div class="tile"><b>③ Originality, minimum 72%</b><span>Never a copy of other sites; a close match
      (≥62% similarity) is not published.</span></div>
    <div class="tile"><b>④ Human review</b><span>The draft comes first; publishing happens only after the
      quality score crosses 80/100.</span></div>
    <div class="tile"><b>⑤ Advertising policy</b><span>SPONSORED label is compulsory; no ads beside
      links; clickbait and fake clicks are completely banned.</span></div>
  </div>

  <h2>Source policy</h2>
  <ul>
    <li>Sources: government portals (.gov.in), official notifications, reliable news agencies —
      social media rumours are never accepted as a source.</li>
    <li>At least two sources for a topic; if there is no official source, the post stops.</li>
    <li>Citations appear inside every article; there is no agency copy.</li>
  </ul>

  <h2>Correction policy</h2>
  <ul>
    <li>If a mistake is found, we usually correct it within 24 hours and add a correction note.</li>
    <li>To request a correction: <a href="mailto:{email}?subject=Correction">{email}</a> —
      send the link, the mistake and the correct official source.</li>
    <li>If the mistake is serious, the article is paused temporarily and republished only after
      verification.</li>
  </ul>

  <h2>Advertising and editorial independence</h2>
  <p>Advertisements never influence editorial decisions. Sponsored content always appears separately with
  a <b>SPONSORED</b> label. Ad links carry <code>rel="sponsored nofollow"</code>. After AdSense approval,
  the number of ads follows policy limits.</p>
"""

ADVERTISE = '''
  <div class="note"><b>Partner with StudentUp.</b> We work with a limited number of local colleges,
  coaching centres, hostels, shops and service providers across Telangana &amp; Andhra Pradesh —
  clean, clearly labelled <b>SPONSORED</b> placements on the pages students and parents actually read.</div>

  <h2>What we offer</h2>
  <ul>
    <li><b>Home page placements</b> — top banner and in-feed cards (highest visibility).</li>
    <li><b>In-article placements</b> — inside daily job and exam articles, seen by real readers.</li>
    <li><b>Sidebar &amp; policy-page placements</b> — steady, long-duration visibility.</li>
    <li><b>Sponsored explainer</b> — a full article about your course, college or service, written and
      SEO-checked by our editorial team, labelled SPONSORED.</li>
    <li><b>WhatsApp / Telegram broadcast</b> — one sponsored message to our student channel.</li>
  </ul>

  <h2>Rates &amp; availability</h2>
  <p>We do not publish a public rate card. Availability, packages and pricing are shared personally —
  one WhatsApp message is enough. This keeps the site clean for readers and lets us give you an honest
  number for your budget and duration instead of a fixed table.</p>
  <p><a class="cta" href="{wa}" target="_blank" rel="noopener">WhatsApp us</a>
     <a class="cta alt" href="mailto:{email}?subject=Advertising%20enquiry">Email us</a></p>

  <h2>Why partner with us</h2>
  <ul>
    <li><b>Local, intent-driven audience:</b> students, parents and job-seekers from Telangana
      (33 districts) and Andhra Pradesh (26 districts).</li>
    <li><b>Pages that get searched:</b> jobs, scholarships, exam calendar, results, admissions.</li>
    <li><b>Fresh content every day:</b> new notifications and articles daily; older posts are refreshed
      and re-crawled too.</li>
    <li><b>Clean labelling:</b> SPONSORED kicker + <code>rel="sponsored nofollow"</code> — Google-policy safe.</li>
    <li><b>Simple reporting:</b> on request we share real impression and click numbers — no inflated claims.</li>
  </ul>

  <h2>What we do not accept</h2>
  <ul>
    <li>Clickbait, misleading offers, "job guaranteed / rank guaranteed" promises — <b>not accepted</b>.</li>
    <li>Fake clicks, pop-ups, interstitials, auto-redirects, adult / gambling / instant-loan ads — <b>blocked</b>.</li>
    <li>A placement goes live only after payment is confirmed; full refund if you cancel before it starts.</li>
  </ul>

  <h2>Our own house ads</h2>
  <p>If a paid slot is empty, StudentUp's own services (daily quiz, daily question, application help) fill
  it — never labelled SPONSORED, always marked "StudentUp · our service". A paid placement always takes
  priority, with rotation. <b>A slot never looks empty to a reader.</b></p>

  <div class="note warn"><b>Straight talk:</b> we never guarantee rankings, traffic or revenue. You get real
  numbers (impressions, clicks, how the ad appeared) and nothing more. After AdSense approval, placements
  follow AdSense policies and limits.</div>
'''


# ---------------------------------------------------------------------------
# v195: HUB pages + EDITORIAL TEAM page (theme inc/hubs.php + author-profile.php
# design ne — so preview == real theme). Static list of the same posts the post
# builder writes, so preview lo reader flow (hub → post) కనిపిస్తుంది.
# ---------------------------------------------------------------------------
HUB_CARDS = [
    ("Telangana Government Jobs 2026", "ts-jobs",
     "TSPSC, TS Police, DSC, Gurukulam and every Telangana state notification - latest first, with the official source link.",
     [("TS Police Constable 2026: 8,400 posts notification details",
       "../posts/upsc-junior-assistant-2026.html", "Official notification · apply dates"),
      ("TSPSC Group 2 2026: hall ticket and exam pattern",
       "../posts/upsc-junior-assistant-2026.html", "Hall ticket · preparation guide")]),
    ("Andhra Pradesh Government Jobs 2026", "ap-jobs",
     "APPSC, AP Police, AP DSC and AP state government notifications - apply dates, eligibility, official links.",
     [("APPSC Group 1 2026: notification, vacancies and syllabus",
       "../posts/engineering-internships-2026.html", "Notification · syllabus"),
      ("AP Police SI 2026: physical test and eligibility",
       "../posts/engineering-internships-2026.html", "Eligibility · physical test")]),
    ("Central Government Jobs 2026", "central-jobs",
     "SSC, UPSC, Railway, Bank, Defence and central government job notifications for Telugu students.",
     [("UPSC Junior Assistant 2026: complete notification guide",
       "../posts/upsc-junior-assistant-2026.html", "Notification · apply online"),
      ("Engineering internships 2026: government openings",
       "../posts/engineering-internships-2026.html", "Internship · stipend")]),
    ("Exam Results & Hall Tickets 2026", "results",
     "Every result and hall ticket link - TS, AP and central exams, updated as soon as the official site publishes.",
     [("Hall ticket verification 2026: exam centre guidelines",
       "../posts/upsc-junior-assistant-2026.html", "Hall ticket · centre rules")]),
    ("Scholarships 2026 - Telangana, AP & Central", "scholarships",
     "NSP, ePASS, AICTE and private scholarships with amounts, eligibility and last dates.",
     [("NMMS scholarship 2026: amount, eligibility and last date",
       "../posts/engineering-internships-2026.html", "Scholarship · official portal"),
      ("Post-matric scholarship 2026: how to apply on ePASS",
       "../posts/upsc-junior-assistant-2026.html", "ePASS · documents list")]),
]


def _hub_card(title: str, href: str, meta: str) -> str:
    return (
        '<article class="news su-hub-card"><a class="thumb thumb--auto" href="%s" aria-hidden="true" tabindex="-1">'
        '<span class="su-cov"><span class="su-cov-cat">StudentUp</span><span class="su-cov-brand">StudentUp</span></span></a>'
        '<div class="newsbody"><h3><a href="%s">%s</a></h3>'
        '<div class="newsfoot"><span class="su-date">%s</span>'
        '<a class="su-readmore" href="%s">View details →</a></div></div></article>'
    ) % (href, href, title, meta, href)


def _hub_body(entries) -> str:
    out = ['<p>New notifications are added every day. Every entry links back to the official notification - always confirm the details there before applying.</p>']
    for label, _slug, intro, cards in entries:
        out.append('<h2 class="su-hub-h">%s</h2>' % label)
        out.append('<p>%s</p>' % intro)
        out.append('<div class="newsgrid">%s</div>' % "".join(_hub_card(t, h, m) for t, h, m in cards))
        out.append('<p class="su-hub-more"><a class="su-viewall" href="../posts/upsc-junior-assistant-2026.html">See all %s →</a></p>' % label)
    return "".join(out)


HUBS_BODY = _hub_body(HUB_CARDS[:3])
RESULTS_BODY = _hub_body(HUB_CARDS[3:4])
SCHOLARSHIPS_BODY = _hub_body(HUB_CARDS[4:5])

EDITORIAL_BODY = """
<div class="su-ab su-ab--page" itemscope itemtype="https://schema.org/Person">
  <div class="su-ab-body">
    <h2 itemprop="name">Charan Pendota</h2>
    <p class="su-ab-role" itemprop="jobTitle">Founder &amp; Content Writer</p>
    <p itemprop="description">Charan Pendota writes and verifies government job, scholarship and exam updates for Telangana and Andhra Pradesh students. Every post starts from the official notification, and the source link stays visible so readers can check it themselves.</p>
    <ul class="su-trust su-trust--expertise">
      <li>Telangana &amp; AP government jobs</li><li>Exam patterns</li>
      <li>Scholarships</li><li>Eligibility rules</li>
    </ul>
    <p class="su-ab-links"><a href="mailto:studentupinformative@gmail.com">Email</a> · <a href="https://t.me/studentup_in" rel="me noopener" target="_blank">Telegram channel</a></p>
    <p class="su-ab-since">Publishing since 2026</p>
  </div>
</div>
<h3>How every update is verified</h3>
<ol class="su-ab-steps">
  <li>We start from the official notification or the department website only.</li>
  <li>Dates, fees, vacancies and eligibility go into the post exactly as published - nothing is estimated.</li>
  <li>Every post links the official source so you can check it yourself.</li>
  <li>A reader correction is published publicly with the updated date.</li>
</ol>
<h3>Corrections</h3>
<p>Found a mistake? Write to the email above with the page link. Verified corrections are published with the updated date, and the post keeps a correction note.</p>
"""


# ---------------------------------------------------------------------------
# v196: EXAM CALENDAR · INTERNET CENTER (transparent pricing) · CORRECTIONS
# (theme: page-exam-calendar.php / page-internet-center.php / page-corrections.php)
# ---------------------------------------------------------------------------
CAL_ITEMS = [
    ("2026-10-08", "TS Police Constable 2026 - online application last date",
     "posts/upsc-junior-assistant-2026.html", "Telangana Jobs", 5),
    ("2026-10-14", "NMMS Scholarship 2026 - school submission last date",
     "posts/engineering-internships-2026.html", "Scholarships", 11),
    ("2026-10-21", "UPSC Junior Assistant 2026 - application window closes",
     "posts/upsc-junior-assistant-2026.html", "Central Govt Jobs", 18),
    ("2026-10-30", "Post-matric scholarship 2026 - ePASS last date",
     "posts/upsc-junior-assistant-2026.html", "Scholarships", 27),
    ("2026-11-12", "Engineering internships 2026 - government portal deadline",
     "posts/engineering-internships-2026.html", "Internships", 40),
]


def _cal_month(ymd: str) -> str:
    months = ["January", "February", "March", "April", "May", "June", "July",
              "August", "September", "October", "November", "December"]
    y, m, _d = ymd.split("-")
    return "%s %s" % (months[int(m) - 1], y)


def _cal_body() -> str:
    out = ['<div class="su-cal"><div class="su-cal-head">'
           '<p class="su-cal-count" role="status">%d dated notifications are open right now.</p>'
           '<a class="su-cta" href="?su_ics=1" rel="nofollow">Add all dates to my calendar (.ics)</a>'
           '<p class="su-cal-hint">Opens in Google Calendar, Apple Calendar or any phone calendar. '
           'One alarm one day before each last date.</p></div>' % len(CAL_ITEMS)]
    months = {}
    for ymd, title, href, cat, days in CAL_ITEMS:
        months.setdefault(_cal_month(ymd), []).append((ymd, title, href, cat, days))
    for month, rows in months.items():
        out.append('<section class="su-cal-month"><h2 class="su-hub-h">%s</h2><ul class="su-cal-list">' % month)
        for ymd, title, href, cat, days in rows:
            urgent = " su-cal-urgent" if days <= 3 else ""
            badge = "%d days left" % days
            due = "%s %s %s" % (ymd[8:10], month[:3], ymd[:4])
            out.append(
                '<li class="su-cal-item%s"><span class="su-cal-date" aria-hidden="true">%s</span>'
                '<span class="su-cal-body"><a class="su-cal-title" href="../%s">%s</a>'
                '<span class="su-cal-meta">%s · Last date: %s</span></span>'
                '<span class="su-cal-badge%s">%s</span></li>' % (urgent, due, href, title, cat, due, urgent, badge)
            )
        out.append("</ul></section>")
    out.append("</div>")
    return "".join(out)


CALENDAR_BODY = _cal_body()

IC_BODY = """
<div class="su-ic-note"><strong>This is optional.</strong> Reading this website, getting job alerts and using every tool here is free. You never need this service to use StudentUp.</div>
<h2>Price list (2026)</h2>
<table class="su-ic-price">
  <thead><tr><th scope="col">Service</th><th scope="col">What you get</th><th scope="col">Our service charge</th></tr></thead>
  <tbody>
    <tr><td>Single application form</td><td>One online form filled, checked and returned as a PDF</td><td><b>&#8377;50</b></td></tr>
    <tr><td>Form + photo &amp; signature formatting</td><td>Form filling plus resizing/renaming of your photo and signature to the official size</td><td><b>&#8377;100</b></td></tr>
    <tr><td>Application + document pack</td><td>Form, photo/signature work and a single PDF pack of the documents the notification asks for</td><td><b>&#8377;150</b></td></tr>
  </tbody>
</table>
<p class="su-ic-price-note">Government application fee, exam fee or any official payment is separate and is never collected by us - you pay the department directly on the official portal. Prices are shown here permanently and do not change based on who calls.</p>
<h2>What we never do</h2>
<ul>
  <li>We never promise a job, a rank, a seat or a selection - no one can.</li>
  <li>We never ask for Aadhaar, PAN, bank details, OTPs or passwords.</li>
  <li>We never fill a form with guessed details. If a document is missing, we tell you instead of inventing it.</li>
</ul>
<h2>How it works</h2>
<ol class="su-ab-steps">
  <li>Send the job or scholarship name on WhatsApp, and ask for the price before paying.</li>
  <li>Send only the documents the notification asks for.</li>
  <li>We fill the form, share a draft PDF with you, and submit only after you approve it.</li>
  <li>Turnaround: typically the same day, at most 24 hours on working days.</li>
</ol>
<h2>Cancellation and refund</h2>
<p>If we cannot submit your application, the service charge is returned in full. If you cancel before we start filling, nothing is charged. Government fees paid on the official portal are between you and the department.</p>
<h2>Contact the center</h2>
<p class="su-ic-page-actions">
  <a class="su-cta" href="https://wa.me/919182739312" rel="nofollow noopener" target="_blank">WhatsApp the center</a>
  <a class="su-ic-alt" href="tel:+919182739312">Call +91 91827 39312</a>
</p>
<p class="su-ic-page-legal">This service is a private offline service. It is not connected to any government department, and paying us gives you no advantage in any selection process.</p>
"""

CORRECTIONS_BODY = """
<p>Every correction we make is listed here with what changed and when. If you find a mistake, write to us with the page link and we will publish the fix on this page as well.</p>
<ul class="su-corr-list">
  <li class="su-corr-item">
    <a class="su-corr-title" href="../posts/upsc-junior-assistant-2026.html">UPSC Junior Assistant 2026 - complete notification guide</a>
    <span class="su-corr-meta">Updated: <time datetime="2026-09-24">September 24, 2026</time></span>
    <p class="su-corr-note">Fee for the general category corrected to the figure printed in the official notification (earlier draft said a different amount).</p>
  </li>
  <li class="su-corr-item">
    <a class="su-corr-title" href="../posts/engineering-internships-2026.html">Engineering internships 2026 - government openings</a>
    <span class="su-corr-meta">Updated: <time datetime="2026-09-12">September 12, 2026</time></span>
    <p class="su-corr-note">Stipend range updated after the department released the revised internship circular.</p>
  </li>
</ul>
<h2>How to report a mistake</h2>
<ol class="su-ab-steps">
  <li>Copy the page link (or the headline) that looks wrong.</li>
  <li>Tell us what the official notification says instead - a screenshot or the official link helps most.</li>
  <li>Send it to <a href="mailto:%(email)s">%(email)s</a>. Verified corrections are published within 48 hours.</li>
</ol>
""" % {"email": EMAIL}

QUIZ_BODY = """
  <h2>Daily Exam-Wise Mock Test &amp; Reader Polls</h2>
  <p>Authentic competitive exam practice questions from official notifications — TSPSC, APPSC, SSC, Banking, and Railways. Instant grading, official source verification, and zero login required.</p>

  <!-- Aspirant Mock Test Bar: Timer, Negative Marking, Starred Filter & Print -->
  <div class="su-mock-bar" role="toolbar" aria-label="Mock test tools">
    <div class="su-mock-left">
      <span class="su-mock-timer" id="su-timer" title="Exam Countdown Timer" aria-live="polite">
        <svg class="su-uicon su-uicon-clock" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-clock"/></svg>
        <span id="su-timer-display">15:00</span>
      </span>
      <button type="button" class="su-mock-btn" id="su-timer-btn" aria-label="Pause or resume timer">Pause</button>
      <label class="su-mock-toggle" title="Enable competitive exam negative marking penalty">
        <input type="checkbox" id="su-neg-toggle">
        <span>Negative marking (-0.25)</span>
      </label>
    </div>
    <div class="su-mock-right">
      <button type="button" class="su-mock-btn" id="su-btn-starred" aria-label="Filter bookmarked questions">
        <svg class="su-uicon su-uicon-star" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-star"/></svg>
        <span>Saved (<b id="su-starred-count">0</b>)</span>
      </button>
      <button type="button" class="su-mock-btn" onclick="window.print()" aria-label="Print question paper">
        <svg class="su-uicon su-uicon-print" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-print"/></svg>
        <span>Print Paper</span>
      </button>
    </div>
  </div>

  <div class="su-quiz-head">
    <div>
      <p class="su-quiz-kick">20 DAILY QUESTIONS &middot; TARGET EXAMS</p>
    </div>
    <div class="su-quiz-score" role="status" aria-live="polite"><b data-su-quiz-score>0</b><span id="su-total-label">/ 20</span></div>
  </div>
  <div class="su-quiz-bar"><i data-su-quiz-bar style="width:0%"></i></div>

  <!-- Target Exam Tabs -->
  <div class="su-quiz-exams" role="tablist" aria-label="Select target exam">
    <button type="button" class="su-qtab active" data-exam="all" role="tab" aria-selected="true">All Exams (20 Qs)</button>
    <button type="button" class="su-qtab" data-exam="tspsc" role="tab" aria-selected="false">TSPSC (Group 1-4 / Police)</button>
    <button type="button" class="su-qtab" data-exam="appsc" role="tab" aria-selected="false">APPSC / DSC</button>
    <button type="button" class="su-qtab" data-exam="ssc" role="tab" aria-selected="false">SSC (CGL &middot; CHSL &middot; GD)</button>
    <button type="button" class="su-qtab" data-exam="banking" role="tab" aria-selected="false">Banking (IBPS &middot; SBI)</button>
    <button type="button" class="su-qtab" data-exam="rrb" role="tab" aria-selected="false">Railways (RRB NTPC)</button>
  </div>

  <!-- Question Navigator Palette (1-20) -->
  <div class="su-palette" id="su-q-palette" aria-label="Question Navigator">
    <!-- Pills generated dynamically for visible questions -->
  </div>

  <form method="post" class="su-quiz-form" data-su-quiz-form>
    <!-- Q1 -->
    <fieldset class="su-q" data-c="1" data-i="0" data-exam="all,ssc,banking,rrb,tspsc,appsc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Aptitude &middot; SSC / Banking</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="0" title="Save question for revision" aria-label="Save question 1">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">1</span> A train 240 m long crosses a telegraph pole in 12 seconds. What is the speed of the train in km/h?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q0" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">60 km/h</span></label>
        <label class="su-opt"><input type="radio" name="q0" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">72 km/h</span></label>
        <label class="su-opt"><input type="radio" name="q0" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">54 km/h</span></label>
        <label class="su-opt"><input type="radio" name="q0" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">80 km/h</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Speed = Distance / Time = 240 m / 12 s = 20 m/s. Converting to km/h: 20 &times; (18 / 5) = 72 km/h. <em>&middot; Quantitative Aptitude (SSC &amp; Banking)</em></p>
    </fieldset>

    <!-- Q2 -->
    <fieldset class="su-q" data-c="1" data-i="1" data-exam="all,ssc,rrb,banking,tspsc,appsc" data-diff="easy">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Reasoning &middot; SSC CGL</span>
          <span class="su-q-diff">Easy</span>
        </div>
        <button type="button" class="su-q-star" data-star="1" title="Save question for revision" aria-label="Save question 2">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">2</span> In a certain code language, if 'PAPER' is written as 'QBQFS', how is 'OFFICE' written in that code?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q1" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">PGGIDF</span></label>
        <label class="su-opt"><input type="radio" name="q1" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">PGGJDF</span></label>
        <label class="su-opt"><input type="radio" name="q1" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">NFFHBD</span></label>
        <label class="su-opt"><input type="radio" name="q1" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">QHHJEG</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Each letter is shifted forward by +1: O(+1)=P, F(+1)=G, F(+1)=G, I(+1)=J, C(+1)=D, E(+1)=F. <em>&middot; Logical Reasoning (SSC CGL &amp; RRB)</em></p>
    </fieldset>

    <!-- Q3 -->
    <fieldset class="su-q" data-c="2" data-i="2" data-exam="all,banking,ssc,tspsc,appsc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Banking &middot; RBI Policy</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="2" title="Save question for revision" aria-label="Save question 3">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">3</span> Which key policy rate does the Reserve Bank of India (RBI) adjust to inject short-term liquidity into commercial banks?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q2" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Reverse Repo Rate</span></label>
        <label class="su-opt"><input type="radio" name="q2" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Cash Reserve Ratio (CRR)</span></label>
        <label class="su-opt"><input type="radio" name="q2" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Repo Rate</span></label>
        <label class="su-opt"><input type="radio" name="q2" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Statutory Liquidity Ratio (SLR)</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Repo Rate is the interest rate at which RBI lends short-term funds to commercial banks against government securities to infuse liquidity. <em>&middot; rbi.org.in</em></p>
    </fieldset>

    <!-- Q4 -->
    <fieldset class="su-q" data-c="0" data-i="3" data-exam="all,tspsc,appsc,ssc" data-diff="easy">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Polity &middot; Supreme Court</span>
          <span class="su-q-diff">Easy</span>
        </div>
        <button type="button" class="su-q-star" data-star="3" title="Save question for revision" aria-label="Save question 4">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">4</span> Under which Article of the Constitution can a citizen approach the Supreme Court directly for the enforcement of Fundamental Rights?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q3" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Article 32</span></label>
        <label class="su-opt"><input type="radio" name="q3" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Article 226</span></label>
        <label class="su-opt"><input type="radio" name="q3" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Article 131</span></label>
        <label class="su-opt"><input type="radio" name="q3" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Article 44</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Article 32 gives the right to move the Supreme Court by appropriate proceedings for enforcement of Fundamental Rights (empowering it to issue writs). <em>&middot; Constitution of India</em></p>
    </fieldset>

    <!-- Q5 -->
    <fieldset class="su-q" data-c="1" data-i="4" data-exam="all,ssc,tspsc,appsc,banking,rrb" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Economy &middot; GST</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="4" title="Save question for revision" aria-label="Save question 5">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">5</span> Which Constitutional Amendment Act introduced the nationwide Goods and Services Tax (GST) in India?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q4" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">100th Amendment Act</span></label>
        <label class="su-opt"><input type="radio" name="q4" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">101st Amendment Act</span></label>
        <label class="su-opt"><input type="radio" name="q4" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">102nd Amendment Act</span></label>
        <label class="su-opt"><input type="radio" name="q4" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">103rd Amendment Act</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> The 101st Constitutional Amendment Act, 2016 introduced the unified Goods and Services Tax (GST) nationwide with effect from 1 July 2017. <em>&middot; Ministry of Finance</em></p>
    </fieldset>

    <!-- Q6 (TSPSC) -->
    <fieldset class="su-q" data-c="0" data-i="5" data-exam="tspsc" data-diff="hard">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">TSPSC Group 1/2 &middot; History</span>
          <span class="su-q-diff hard">Advanced</span>
        </div>
        <button type="button" class="su-q-star" data-star="5" title="Save question for revision" aria-label="Save question 6">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">6</span> Who was the founder of the Asaf Jahi dynasty in Hyderabad Deccan?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q5" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Mir Qamar-ud-din Khan (Nizam-ul-Mulk)</span></label>
        <label class="su-opt"><input type="radio" name="q5" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Nasir Jung</span></label>
        <label class="su-opt"><input type="radio" name="q5" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Salabat Jung</span></label>
        <label class="su-opt"><input type="radio" name="q5" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Afzal-ud-Daula</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Nizam-ul-Mulk founded the Asaf Jahi dynasty in 1724 after defeating Mubariz Khan at the Battle of Shakar Kheda. <em>&middot; TSPSC Syllabus / State History</em></p>
    </fieldset>

    <!-- Q7 (TSPSC) -->
    <fieldset class="su-q" data-c="1" data-i="6" data-exam="tspsc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">TSPSC &middot; Polity</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="6" title="Save question for revision" aria-label="Save question 7">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">7</span> Under which Article of the Indian Constitution was the state of Telangana formed in 2014?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q6" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Article 2</span></label>
        <label class="su-opt"><input type="radio" name="q6" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Article 3</span></label>
        <label class="su-opt"><input type="radio" name="q6" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Article 4</span></label>
        <label class="su-opt"><input type="radio" name="q6" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Article 371-D</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Article 3 empowers Parliament to form new States and alter boundaries or names of existing States by law. <em>&middot; Constitution of India</em></p>
    </fieldset>

    <!-- Q8 (TSPSC) -->
    <fieldset class="su-q" data-c="0" data-i="7" data-exam="tspsc" data-diff="hard">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">TSPSC &middot; Culture</span>
          <span class="su-q-diff hard">Advanced</span>
        </div>
        <button type="button" class="su-q-star" data-star="7" title="Save question for revision" aria-label="Save question 8">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">8</span> The iconic Telangana Martyrs Memorial at Gun Park, Hyderabad was sculpted by which renowned artist?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q7" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Aekka Yadagiri Rao</span></label>
        <label class="su-opt"><input type="radio" name="q7" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Kapu Rajaiah</span></label>
        <label class="su-opt"><input type="radio" name="q7" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Thota Vaikuntam</span></label>
        <label class="su-opt"><input type="radio" name="q7" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Laxma Goud</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Prof. Aekka Yadagiri Rao sculpted the historic Gun Park Martyrs Memorial in memory of the 1969 agitation martyrs. <em>&middot; Telangana Sahitya Akademi</em></p>
    </fieldset>

    <!-- Q9 (TSPSC) -->
    <fieldset class="su-q" data-c="2" data-i="8" data-exam="tspsc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">TSPSC &middot; Projects</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="8" title="Save question for revision" aria-label="Save question 9">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">9</span> Which is the first barrage of the Kaleshwaram Lift Irrigation Project located at the Godavari-Pranahita confluence?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q8" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Sundilla Barrage</span></label>
        <label class="su-opt"><input type="radio" name="q8" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Annaram Barrage</span></label>
        <label class="su-opt"><input type="radio" name="q8" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Medigadda (Lakshmi) Barrage</span></label>
        <label class="su-opt"><input type="radio" name="q8" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Yellampalli Barrage</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Medigadda (Lakshmi) Barrage is the headworks where water is lifted from the Pranahita-Godavari confluence. <em>&middot; Irrigation &amp; CAD Dept</em></p>
    </fieldset>

    <!-- Q10 (APPSC) -->
    <fieldset class="su-q" data-c="1" data-i="9" data-exam="appsc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">APPSC Group 1/2 &middot; Geography</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="9" title="Save question for revision" aria-label="Save question 10">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">10</span> The Polavaram Multi-Purpose National Irrigation Project is being constructed across which river in Andhra Pradesh?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q9" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Krishna River</span></label>
        <label class="su-opt"><input type="radio" name="q9" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Godavari River</span></label>
        <label class="su-opt"><input type="radio" name="q9" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Pennar River</span></label>
        <label class="su-opt"><input type="radio" name="q9" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Nagavali River</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Polavaram Project is built across the Godavari River in Eluru and Alluri Sitharama Raju districts of AP. <em>&middot; AP Water Resources Dept</em></p>
    </fieldset>

    <!-- Q11 (APPSC) -->
    <fieldset class="su-q" data-c="1" data-i="10" data-exam="appsc" data-diff="hard">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">APPSC &middot; Reorganisation</span>
          <span class="su-q-diff hard">Advanced</span>
        </div>
        <button type="button" class="su-q-star" data-star="10" title="Save question for revision" aria-label="Save question 11">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">11</span> Under which section of the AP Reorganisation Act, 2014 does the Governor have special responsibilities for Hyderabad as common capital?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q10" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Section 5</span></label>
        <label class="su-opt"><input type="radio" name="q10" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Section 8</span></label>
        <label class="su-opt"><input type="radio" name="q10" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Section 12</span></label>
        <label class="su-opt"><input type="radio" name="q10" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Section 24</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Section 8 of the AP Reorganisation Act, 2014 vests special responsibility in the Governor for law and order in the common capital. <em>&middot; AP Reorganisation Gazette</em></p>
    </fieldset>

    <!-- Q12 (APPSC / DSC) -->
    <fieldset class="su-q" data-c="1" data-i="11" data-exam="appsc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">AP DSC &middot; Education</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="11" title="Save question for revision" aria-label="Save question 12">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">12</span> According to the RTE Act, 2009, what is the pupil-teacher ratio for primary schools (classes 1 to 5)?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q11" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">25:1</span></label>
        <label class="su-opt"><input type="radio" name="q11" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">30:1</span></label>
        <label class="su-opt"><input type="radio" name="q11" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">35:1</span></label>
        <label class="su-opt"><input type="radio" name="q11" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">40:1</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> The RTE Act specifies a Pupil-Teacher Ratio (PTR) of 30:1 for primary schools up to 200 enrolled students. <em>&middot; Ministry of Education</em></p>
    </fieldset>

    <!-- Q13 (SSC) -->
    <fieldset class="su-q" data-c="1" data-i="12" data-exam="ssc" data-diff="hard">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">SSC CGL &middot; Mathematics</span>
          <span class="su-q-diff hard">Advanced</span>
        </div>
        <button type="button" class="su-q-star" data-star="12" title="Save question for revision" aria-label="Save question 13">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">13</span> A sum of money invested at compound interest amounts to Rs. 4,840 in 2 years and Rs. 5,324 in 3 years. Find the rate of interest.</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q12" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">8%</span></label>
        <label class="su-opt"><input type="radio" name="q12" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">10%</span></label>
        <label class="su-opt"><input type="radio" name="q12" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">12%</span></label>
        <label class="su-opt"><input type="radio" name="q12" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">15%</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Interest for 3rd year = Rs. 5324 - 4840 = Rs. 484. Rate = (484 / 4840) * 100 = 10% per annum. <em>&middot; SSC CGL Tier 1</em></p>
    </fieldset>

    <!-- Q14 (SSC) -->
    <fieldset class="su-q" data-c="1" data-i="13" data-exam="ssc" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">SSC &middot; History</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="13" title="Save question for revision" aria-label="Save question 14">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">14</span> Which Indus Valley Civilization site features the world's earliest known tidal dockyard?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q13" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Kalibangan</span></label>
        <label class="su-opt"><input type="radio" name="q13" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Lothal</span></label>
        <label class="su-opt"><input type="radio" name="q13" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Rakhigarhi</span></label>
        <label class="su-opt"><input type="radio" name="q13" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Banawali</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Lothal in Gujarat had a tidal dockyard connected to the ancient Sabarmati river channels for sea trade. <em>&middot; Archaeological Survey of India</em></p>
    </fieldset>

    <!-- Q15 (Banking) -->
    <fieldset class="su-q" data-c="2" data-i="14" data-exam="banking" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Banking &middot; DICGC</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="14" title="Save question for revision" aria-label="Save question 15">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">15</span> What is the maximum deposit insurance coverage provided by DICGC per depositor per insured bank in India?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q14" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Rs. 1,00,000</span></label>
        <label class="su-opt"><input type="radio" name="q14" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Rs. 2,00,000</span></label>
        <label class="su-opt"><input type="radio" name="q14" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Rs. 5,00,000</span></label>
        <label class="su-opt"><input type="radio" name="q14" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Rs. 10,00,000</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> DICGC insures savings, fixed, current and recurring deposits up to Rs. 5 Lakhs (principal + interest). <em>&middot; DICGC / RBI</em></p>
    </fieldset>

    <!-- Q16 (Banking) -->
    <fieldset class="su-q" data-c="0" data-i="15" data-exam="banking" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">Banking &middot; Union Budget</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="15" title="Save question for revision" aria-label="Save question 16">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">16</span> In the Union Budget of India, how is the 'Primary Deficit' calculated?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q15" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Fiscal Deficit - Interest Payments</span></label>
        <label class="su-opt"><input type="radio" name="q15" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Revenue Deficit - Capital Expenditure</span></label>
        <label class="su-opt"><input type="radio" name="q15" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Fiscal Deficit + Borrowings</span></label>
        <label class="su-opt"><input type="radio" name="q15" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Budget Deficit - Subsidies</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Primary Deficit = Fiscal Deficit - Interest Payments. It indicates government borrowing requirements excluding past interest obligations. <em>&middot; Ministry of Finance</em></p>
    </fieldset>

    <!-- Q17 (Railways) -->
    <fieldset class="su-q" data-c="1" data-i="16" data-exam="rrb" data-diff="moderate">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">RRB NTPC &middot; Railways GK</span>
          <span class="su-q-diff moderate">Moderate</span>
        </div>
        <button type="button" class="su-q-star" data-star="16" title="Save question for revision" aria-label="Save question 17">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">17</span> Which is the longest running passenger train route by both distance and time in Indian Railways?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q16" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Himsagar Express (Kanyakumari to Katra)</span></label>
        <label class="su-opt"><input type="radio" name="q16" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Vivek Express (Dibrugarh to Kanyakumari)</span></label>
        <label class="su-opt"><input type="radio" name="q16" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Navyug Express (Mangaluru to Katra)</span></label>
        <label class="su-opt"><input type="radio" name="q16" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Grand Trunk Express (Delhi to Chennai)</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Vivek Express covers 4,189 km from Dibrugarh in Assam to Kanyakumari over approximately 75 hours. <em>&middot; Indian Railways / RRB</em></p>
    </fieldset>

    <!-- Q18 (Railways) -->
    <fieldset class="su-q" data-c="0" data-i="17" data-exam="rrb" data-diff="hard">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">RRB &middot; Space Tech</span>
          <span class="su-q-diff hard">Advanced</span>
        </div>
        <button type="button" class="su-q-star" data-star="17" title="Save question for revision" aria-label="Save question 18">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">18</span> What propellants are utilized in the indigenous CE-20 Cryogenic Upper Stage of ISRO's LVM3 rocket?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q17" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Liquid Hydrogen (LH2) and Liquid Oxygen (LOX)</span></label>
        <label class="su-opt"><input type="radio" name="q17" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Liquid Methane and Liquid Oxygen</span></label>
        <label class="su-opt"><input type="radio" name="q17" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Kerosene and Liquid Oxygen</span></label>
        <label class="su-opt"><input type="radio" name="q17" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Hydrazine and Nitrogen Tetroxide</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> CE-20 operates burning cryogenic Liquid Hydrogen (fuel at -253 deg C) and Liquid Oxygen (oxidizer at -183 deg C). <em>&middot; ISRO Technical Reports</em></p>
    </fieldset>

    <!-- Q19 (Railways / Science) -->
    <fieldset class="su-q" data-c="1" data-i="18" data-exam="rrb" data-diff="easy">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">RRB Group D &middot; Physics</span>
          <span class="su-q-diff">Easy</span>
        </div>
        <button type="button" class="su-q-star" data-star="18" title="Save question for revision" aria-label="Save question 19">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">19</span> What is the SI unit of electrical resistance in the International System of Units?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q18" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Volt</span></label>
        <label class="su-opt"><input type="radio" name="q18" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Ohm</span></label>
        <label class="su-opt"><input type="radio" name="q18" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Ampere</span></label>
        <label class="su-opt"><input type="radio" name="q18" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Watt</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> The SI unit of electrical resistance is the Ohm (Omega), named after German physicist Georg Simon Ohm. <em>&middot; NCERT Class 10 Science</em></p>
    </fieldset>

    <!-- Q20 (General Science) -->
    <fieldset class="su-q" data-c="1" data-i="19" data-exam="all,tspsc,appsc,ssc,rrb" data-diff="easy">
      <div class="su-q-meta">
        <div class="su-q-tags">
          <span class="su-q-badge">General Science &middot; Biology</span>
          <span class="su-q-diff">Easy</span>
        </div>
        <button type="button" class="su-q-star" data-star="19" title="Save question for revision" aria-label="Save question 20">&#9734; Save</button>
      </div>
      <legend class="su-q-title"><span class="su-q-n">20</span> What is the chemical name of Vitamin C, an essential water-soluble antioxidant vitamin?</legend>
      <div class="su-q-opts">
        <label class="su-opt"><input type="radio" name="q19" value="0"><span class="su-opt-key">A</span><span class="su-opt-t">Retinol</span></label>
        <label class="su-opt"><input type="radio" name="q19" value="1"><span class="su-opt-key">B</span><span class="su-opt-t">Ascorbic Acid</span></label>
        <label class="su-opt"><input type="radio" name="q19" value="2"><span class="su-opt-key">C</span><span class="su-opt-t">Calciferol</span></label>
        <label class="su-opt"><input type="radio" name="q19" value="3"><span class="su-opt-key">D</span><span class="su-opt-t">Tocopherol</span></label>
      </div>
      <p class="su-why" data-su-why hidden><strong>Why:</strong> Vitamin C is chemically known as Ascorbic Acid; deficiency causes scurvy characterized by bleeding gums and fatigue. <em>&middot; NCERT Biology</em></p>
    </fieldset>

    <!-- Performance Scorecard Modal Box -->
    <div class="su-scorecard" id="su-scorecard" role="dialog" aria-label="Exam Performance Scorecard">
      <div class="su-scorecard-head">
        <h3 class="su-scorecard-title">Exam Performance Scorecard</h3>
        <span id="su-scorecard-date">Today's Test</span>
      </div>
      <div class="su-scorecard-grid">
        <div class="su-scorecard-stat">
          <b id="su-sc-score">0</b>
          <span>Net Marks</span>
        </div>
        <div class="su-scorecard-stat">
          <b id="su-sc-accuracy">0%</b>
          <span>Accuracy</span>
        </div>
        <div class="su-scorecard-stat">
          <b id="su-sc-time">0m 0s</b>
          <span>Time Taken</span>
        </div>
        <div class="su-scorecard-stat">
          <b id="su-sc-speed">0s</b>
          <span>Avg Pace / Q</span>
        </div>
      </div>
      <div class="su-scorecard-advice" id="su-sc-verdict">
        Great effort! Review the detailed explanations below to improve your target exam score.
      </div>
      <div class="su-scorecard-acts">
        <a class="su-quiz-restart" id="su-sc-share" target="_blank" rel="noopener nofollow" href="https://wa.me/?text=StudentUp%20Daily%20Mock%20Test">Share Score on WhatsApp</a>
        <button type="button" class="su-quiz-restart" id="su-sc-retake">Retake Test</button>
      </div>
    </div>

    <div class="su-quiz-foot">
      <button type="submit" class="su-quiz-restart" data-su-quiz-check><svg class="su-uicon su-uicon-check" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-check"/></svg> Check answers</button>
      <button type="button" class="su-quiz-restart" data-su-quiz-restart hidden><svg class="su-uicon su-uicon-refresh" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-refresh"/></svg> Restart</button>
      <a class="su-quiz-more su-quiz-share" data-su-quiz-share rel="nofollow noopener" target="_blank" href="https://wa.me/?text=StudentUp%20Daily%20Quiz" hidden>Share my score</a>
      <span class="su-quiz-streak" data-su-quiz-streak hidden></span>
      <a class="su-quiz-more" href="ts-jobs-hub.html">More practice questions &rarr;</a>
    </div>
  </form>

  <h2>Reader poll</h2>
  <section class="su-poll" id="su-poll-preview" data-su-poll="preview" aria-label="Reader poll">
    <p class="su-poll-kick">READER POLL</p>
    <h3>Which update do you want first on WhatsApp?</h3>
    <p class="su-poll-sub">Your answer decides what the morning list leads with. Live site: one vote per device, only the count is stored.</p>
    <form method="post" class="su-poll-form" data-su-poll-form>
      <div class="su-poll-opts">
        <label class="su-poll-opt" data-opt="0"><span class="su-poll-bar" data-su-bar style="width:0%"></span><input type="radio" name="su_poll_opt" value="0"><span class="su-poll-radio" aria-hidden="true"></span><span class="su-poll-lbl">New job notifications</span><span class="su-poll-pct" data-su-pct></span></label>
        <label class="su-poll-opt" data-opt="1"><span class="su-poll-bar" data-su-bar style="width:0%"></span><input type="radio" name="su_poll_opt" value="1"><span class="su-poll-radio" aria-hidden="true"></span><span class="su-poll-lbl">Exam date changes</span><span class="su-poll-pct" data-su-pct></span></label>
        <label class="su-poll-opt" data-opt="2"><span class="su-poll-bar" data-su-bar style="width:0%"></span><input type="radio" name="su_poll_opt" value="2"><span class="su-poll-radio" aria-hidden="true"></span><span class="su-poll-lbl">Results &amp; hall tickets</span><span class="su-poll-pct" data-su-pct></span></label>
        <label class="su-poll-opt" data-opt="3"><span class="su-poll-bar" data-su-bar style="width:0%"></span><input type="radio" name="su_poll_opt" value="3"><span class="su-poll-radio" aria-hidden="true"></span><span class="su-poll-lbl">Scholarship deadlines</span><span class="su-poll-pct" data-su-pct></span></label>
      </div>
      <div class="su-poll-foot">
        <button type="submit" class="su-poll-vote" data-su-poll-vote>Vote</button>
        <span>No login. One vote per device.</span>
      </div>
    </form>
    <p class="su-quiz-legend">Open poll, not a scientific survey. In this offline preview the vote is kept on your device; the live site stores only the count &mdash; never who voted.</p>
  </section>

  <h2>How the daily quiz works</h2>
  <ul>
    <li>Questions rotate every day and come from official notifications (SSC, TSPSC, APPSC, IBPS, Railways).</li>
    <li>Every answer carries a one-line explanation and its source &mdash; you learn, not just guess.</li>
    <li>Your score and streak stay in your browser. We never see them and never ask for a phone number.</li>
    <li>The quiz works even with JavaScript off: pick answers, press &ldquo;Check answers&rdquo;, and the server marks them.</li>
  </ul>

  <p><a class="cta" href="ts-jobs-hub.html">Today&rsquo;s Telangana jobs &rarr;</a>
     <a class="cta" href="exam-calendar.html">Exam calendar 2026 &rarr;</a></p>
"""


QUIZ_SCRIPT = """<script>
/* v200 — advanced mock exam + timer + question palette + scorecard behaviour */
(function(){
  var form = document.querySelector('[data-su-quiz-form]');
  if(form){
    var scoreEl = document.querySelector('[data-su-quiz-score]'),
        totalLabel = document.getElementById('su-total-label'),
        barEl = document.querySelector('[data-su-quiz-bar]'),
        checkBtn = document.querySelector('[data-su-quiz-check]'),
        restart = document.querySelector('[data-su-quiz-restart]'),
        share = document.querySelector('[data-su-quiz-share]'),
        streakEl = document.querySelector('[data-su-quiz-streak]'),
        qs = [].slice.call(form.querySelectorAll('fieldset.su-q')),
        allTotal = qs.length,
        score = 0, picked = {}, starred = {};

    /* LocalStorage for Starred/Bookmarked questions */
    try{
      starred = JSON.parse(localStorage.getItem('su_starred_quiz') || '{}');
    }catch(e){ starred = {}; }

    /* Timer state */
    var timeRemaining = 15 * 60; // 15 mins
    var timerRunning = true;
    var timerDisplay = document.getElementById('su-timer-display');
    var timerBtn = document.getElementById('su-timer-btn');
    var timerEl = document.getElementById('su-timer');
    var startTime = Date.now();

    function updateTimer(){
      if(!timerRunning) return;
      if(timeRemaining > 0){
        timeRemaining--;
        var m = Math.floor(timeRemaining / 60);
        var s = timeRemaining % 60;
        if(timerDisplay) timerDisplay.textContent = (m < 10 ? '0' : '') + m + ':' + (s < 10 ? '0' : '') + s;
        if(timeRemaining <= 120 && timerEl) timerEl.classList.add('urgent');
      } else {
        timerRunning = false;
        if(timerDisplay) timerDisplay.textContent = "00:00";
        finish();
      }
    }
    var timerInterval = setInterval(updateTimer, 1000);

    if(timerBtn){
      timerBtn.addEventListener('click', function(){
        timerRunning = !timerRunning;
        timerBtn.textContent = timerRunning ? 'Pause' : 'Resume';
      });
    }

    /* Starred count label update */
    function updateStarredCount(){
      var cnt = Object.keys(starred).filter(function(k){ return starred[k]; }).length;
      var el = document.getElementById('su-starred-count');
      if(el) el.textContent = String(cnt);
    }
    updateStarredCount();

    /* Render Palette */
    var palette = document.getElementById('su-q-palette');
    function renderPalette(){
      if(!palette) return;
      palette.innerHTML = '';
      var visibleQs = qs.filter(function(fs){ return fs.style.display !== 'none'; });
      visibleQs.forEach(function(fs, idx){
        var qIdx = fs.getAttribute('data-i');
        var pill = document.createElement('button');
        pill.type = 'button';
        pill.className = 'su-palette-pill';
        pill.textContent = String(idx + 1);
        pill.setAttribute('aria-label', 'Go to question ' + (idx + 1));
        if(picked[qIdx] !== undefined){
          var right = parseInt(fs.getAttribute('data-c'), 10);
          pill.classList.add(picked[qIdx] === right ? 'correct' : 'wrong');
        }
        if(starred[qIdx]){
          pill.classList.add('starred');
        }
        pill.addEventListener('click', function(){
          fs.scrollIntoView({ behavior: 'smooth', block: 'center' });
          var firstOpt = fs.querySelector('.su-opt');
          if(firstOpt) firstOpt.focus();
        });
        palette.appendChild(pill);
      });
    }

    /* Star bookmark button click listener */
    form.addEventListener('click', function(e){
      var starBtn = e.target.closest ? e.target.closest('.su-q-star') : null;
      if(!starBtn) return;
      e.preventDefault();
      var qIdx = starBtn.getAttribute('data-star');
      starred[qIdx] = !starred[qIdx];
      starBtn.classList.toggle('active', starred[qIdx]);
      starBtn.innerHTML = starred[qIdx] ? '&#9733; Saved' : '&#9734; Save';
      try{ localStorage.setItem('su_starred_quiz', JSON.stringify(starred)); }catch(err){}
      updateStarredCount();
      renderPalette();
    });

    /* Starred filter button */
    var starredFilterBtn = document.getElementById('su-btn-starred');
    var showingOnlyStarred = false;
    if(starredFilterBtn){
      starredFilterBtn.addEventListener('click', function(){
        showingOnlyStarred = !showingOnlyStarred;
        starredFilterBtn.classList.toggle('active', showingOnlyStarred);
        qs.forEach(function(fs){
          var qIdx = fs.getAttribute('data-i');
          if(showingOnlyStarred){
            fs.style.display = starred[qIdx] ? '' : 'none';
          } else {
            fs.style.display = '';
          }
        });
        updateVisibleCounts();
        renderPalette();
      });
    }

    function updateVisibleCounts(){
      var visibleQs = qs.filter(function(fs){ return fs.style.display !== 'none'; });
      if(totalLabel) totalLabel.textContent = '/ ' + visibleQs.length;
    }

    /* Exam Tabs Filter */
    var examTabs = [].slice.call(document.querySelectorAll('.su-qtab'));
    if(examTabs.length){
      examTabs.forEach(function(btn){
        btn.addEventListener('click', function(){
          examTabs.forEach(function(b){ b.classList.remove('active'); b.setAttribute('aria-selected', 'false'); });
          btn.classList.add('active'); btn.setAttribute('aria-selected', 'true');
          var targetExam = (btn.getAttribute('data-exam') || 'all').toLowerCase();
          qs.forEach(function(fs){
            var ex = (fs.getAttribute('data-exam') || 'all').toLowerCase().split(',');
            if(targetExam === 'all' || ex.indexOf(targetExam) !== -1 || ex.indexOf('all') !== -1){
              fs.style.display = '';
            } else {
              fs.style.display = 'none';
            }
          });
          updateVisibleCounts();
          renderPalette();
          paint();
        });
      });
    }

    function paint(){
      var visibleQs = qs.filter(function(fs){ return fs.style.display !== 'none'; });
      var visibleTotal = visibleQs.length || 1;
      var answeredVisible = visibleQs.filter(function(fs){ return picked[fs.getAttribute('data-i')] !== undefined; }).length;
      if(scoreEl) scoreEl.textContent = String(score);
      if(barEl) barEl.style.width = Math.round((answeredVisible / visibleTotal) * 100) + '%';
    }

    function mark(fs, chosen){
      var right = parseInt(fs.getAttribute('data-c'), 10);
      [].forEach.call(fs.querySelectorAll('.su-opt'), function(lab){
        var input = lab.querySelector('input'), val = parseInt(input.value, 10);
        lab.classList.remove('right', 'wrong', 'on');
        input.disabled = true;
        if(val === right) lab.classList.add('right');
        if(val === chosen && chosen !== right) lab.classList.add('wrong');
      });
      var why = fs.querySelector('[data-su-why]');
      if(why) why.hidden = false;
    }

    function finish(){
      timerRunning = false;
      var elapsedSec = Math.max(1, Math.round((Date.now() - startTime) / 1000));
      var visibleQs = qs.filter(function(fs){ return fs.style.display !== 'none'; });
      var visibleTotal = visibleQs.length || 1;
      var correctCount = 0, wrongCount = 0;
      visibleQs.forEach(function(fs){
        var qIdx = fs.getAttribute('data-i');
        var right = parseInt(fs.getAttribute('data-c'), 10);
        if(picked[qIdx] !== undefined){
          if(picked[qIdx] === right) correctCount++;
          else wrongCount++;
        }
      });

      var useNeg = (document.getElementById('su-neg-toggle') || {}).checked;
      var netScore = useNeg ? Math.max(0, correctCount - (wrongCount * 0.25)) : correctCount;
      var accuracy = Math.round((correctCount / Math.max(1, correctCount + wrongCount)) * 100);
      var avgSec = Math.round(elapsedSec / Math.max(1, correctCount + wrongCount));

      var scBox = document.getElementById('su-scorecard');
      if(scBox){
        scBox.classList.add('visible');
        var elSc = document.getElementById('su-sc-score');
        var elAcc = document.getElementById('su-sc-accuracy');
        var elTime = document.getElementById('su-sc-time');
        var elSpd = document.getElementById('su-sc-speed');
        var elVerd = document.getElementById('su-sc-verdict');
        var elShare = document.getElementById('su-sc-share');
        if(elSc) elSc.textContent = netScore + ' / ' + visibleTotal;
        if(elAcc) elAcc.textContent = accuracy + '%';
        if(elTime) elTime.textContent = Math.floor(elapsedSec / 60) + 'm ' + (elapsedSec % 60) + 's';
        if(elSpd) elSpd.textContent = avgSec + 's';
        if(elVerd){
          if(accuracy >= 80) elVerd.textContent = "Outstanding accuracy! You are scoring in the top percentile of competitive aspirants.";
          else if(accuracy >= 50) elVerd.textContent = "Good progress! Focus on reviewing the negative-marked questions below.";
          else elVerd.textContent = "Keep practicing! Review each official explanation to master difficult concepts.";
        }
        if(elShare){
          elShare.href = 'https://wa.me/?text=' + encodeURIComponent("I scored " + netScore + "/" + visibleTotal + " (" + accuracy + "% accuracy) in the StudentUp Mock Exam. Practice free: https://studentup.in/pages/daily-quiz.html");
        }
      }

      if(share){
        share.hidden = false;
        share.href = 'https://wa.me/?text=' + encodeURIComponent("I scored " + netScore + "/" + visibleTotal + " in the StudentUp Daily Mock Test. Practice free: https://studentup.in/pages/daily-quiz.html");
      }
      if(streakEl){
        streakEl.hidden = false;
        streakEl.textContent = visibleTotal + ' questions completed';
      }
    }

    form.addEventListener('click', function(e){
      var lab = e.target.closest ? e.target.closest('.su-opt') : null;
      if(!lab) return;
      var input = lab.querySelector('input'), fs = lab.closest('fieldset.su-q');
      if(!input || !fs || input.disabled) return;
      e.preventDefault();
      input.checked = true;
      var i = fs.getAttribute('data-i');
      if(picked[i] !== undefined) return;
      picked[i] = parseInt(input.value, 10);
      if(picked[i] === parseInt(fs.getAttribute('data-c'), 10)) score++;
      mark(fs, picked[i]);
      paint();
      renderPalette();
      var visibleQs = qs.filter(function(fs){ return fs.style.display !== 'none'; });
      var visibleDone = visibleQs.filter(function(fs){ return picked[fs.getAttribute('data-i')] !== undefined; }).length;
      if(visibleDone === visibleQs.length) finish();
    });

    if(restart){
      restart.hidden = false;
      restart.addEventListener('click', resetQuiz);
    }
    var retakeBtn = document.getElementById('su-sc-retake');
    if(retakeBtn) retakeBtn.addEventListener('click', resetQuiz);

    function resetQuiz(){
      picked = {};
      score = 0;
      timeRemaining = 15 * 60;
      timerRunning = true;
      startTime = Date.now();
      var scBox = document.getElementById('su-scorecard');
      if(scBox) scBox.classList.remove('visible');
      qs.forEach(function(fs){
        [].forEach.call(fs.querySelectorAll('.su-opt'), function(lab){
          lab.classList.remove('right', 'wrong', 'on');
          var input = lab.querySelector('input');
          if(input){ input.disabled = false; input.checked = false; }
        });
        var why = fs.querySelector('[data-su-why]');
        if(why) why.hidden = true;
      });
      if(share) share.hidden = true;
      if(streakEl) streakEl.hidden = true;
      paint();
      renderPalette();
    }

    // Initialize state
    updateVisibleCounts();
    renderPalette();
    paint();
  }

  var box = document.querySelector('[data-su-poll]');
  if(box){
    var pform = box.querySelector('[data-su-poll-form]');
    var labels = [].slice.call(box.querySelectorAll('.su-poll-opt'));
    labels.forEach(function(lab){
      lab.addEventListener('click', function(){
        labels.forEach(function(o){ o.classList.remove('on'); });
        lab.classList.add('on');
      });
    });
    if(pform){
      pform.addEventListener('submit', function(e){
        e.preventDefault();
        var chosen = pform.querySelector('input[name=su_poll_opt]:checked');
        if(!chosen){ if(labels[0]) labels[0].classList.add('on'); return; }
        var counts = [0, 0, 0, 0];
        counts[parseInt(chosen.value, 10)] = 1;
        try{
          var prev = JSON.parse(localStorage.getItem('su_poll_preview') || 'null');
          if(prev){ counts = prev; counts[parseInt(chosen.value, 10)]++; }
          localStorage.setItem('su_poll_preview', JSON.stringify(counts));
        }catch(err){}
        var total = counts.reduce(function(a, b){ return a + b; }, 0) || 1;
        labels.forEach(function(lab, i){
          var pct = Math.round((counts[i] / total) * 100);
          var bar = lab.querySelector('[data-su-bar]'), p = lab.querySelector('[data-su-pct]');
          if(bar) bar.style.width = pct + '%';
          if(p) p.textContent = pct + '%';
          var input = lab.querySelector('input');
          if(input) input.disabled = true;
        });
        var foot = box.querySelector('.su-poll-foot'), btn = box.querySelector('[data-su-poll-vote]');
        if(btn) btn.remove();
        if(foot){ var s = foot.querySelector('span'); if(s) s.textContent = 'Thanks — your vote is counted (on this device in the offline preview).'; }
      });
      try{
        var saved = JSON.parse(localStorage.getItem('su_poll_preview') || 'null');
        if(saved){
          var t = saved.reduce(function(a, b){ return a + b; }, 0) || 1;
          labels.forEach(function(lab, i){
            var pct = Math.round((saved[i] / t) * 100);
            var bar = lab.querySelector('[data-su-bar]'), p = lab.querySelector('[data-su-pct]');
            if(bar) bar.style.width = pct + '%';
            if(p) p.textContent = pct + '%';
            var input = lab.querySelector('input');
            if(input) input.disabled = true;
          });
          var btn = box.querySelector('[data-su-poll-vote]');
          if(btn) btn.remove();
        }
      }catch(err){}
    }
  }
})();
</script>"""


PAGE_DEFS = [
    ("advertise", "Partner with us",
     "Advertise on studentup.in — labelled SPONSORED placements read by Telangana & Andhra Pradesh students. Availability and pricing shared personally on WhatsApp.",
     "Partner with us", "Clean, clearly labelled placements for colleges, coaching, shops and services", ADVERTISE),
    ("about", "About us",
     "Who studentup.in is, how we work and what we never do — an honest student platform for Telangana & Andhra Pradesh, built only on official sources.",
     "About us", "An honest platform for Telangana &amp; Andhra Pradesh students", ABOUT),
    ("contact", "Contact",
     "Reach studentup.in on WhatsApp or email for corrections, partnerships and student application help — reply times, fraud warnings and direct links.",
     "Contact us", "Corrections · advertising · student help", CONTACT),
    ("privacy", "Privacy policy",
     "What data studentup.in collects, what it never collects, how poll votes are stored and how ad cookies work — in simple words.",
     "Privacy policy", "Your data is yours — what we collect and what we never collect", PRIVACY),
    ("disclaimer", "Disclaimer",
     "studentup.in is not a government website — limits of the information, no guarantees, financial fraud warnings and advertising rules.",
     "Disclaimer (note)", "Important limits — a must read", DISCLAIMER),
    ("terms", "Terms of service",
     "The rules for using studentup.in — what you may share, copyright, advertisements, third-party links, limits and the law that applies.",
     "Terms of service", "The simple rules for using studentup.in", TERMS),
    ("editorial-policy", "Editorial policy",
     "The 5 verification gates, official-source policy, correction deadline and advertising rules — how every studentup.in post is made.",
     "Editorial policy", "Every post is published only after clearing these 5 gates", EDITORIAL),
    # v195: hubs (topic clusters) + editorial team (E-E-A-T) — theme inc/hubs.php.
    ("ts-jobs-hub", "Telangana Government Jobs 2026",
     "TSPSC, TS Police, DSC and every Telangana government job notification for 2026 — apply dates, eligibility and official links in one place.",
     "Telangana Government Jobs 2026", "Every Telangana notification, latest first", HUBS_BODY),
    ("results-hub", "Exam Results &amp; Hall Tickets 2026",
     "TS, AP and central exam results plus hall ticket download links 2026 — updated as soon as the official website publishes them.",
     "Exam Results &amp; Hall Tickets 2026", "Result and hall ticket links, latest first", RESULTS_BODY),
    ("scholarships-hub", "Scholarships 2026 — Telangana, AP &amp; Central",
     "NMMS, NSP, ePASS, AICTE and private scholarships 2026 with amounts, eligibility and last dates for Telugu students.",
     "Scholarships 2026", "Amount, eligibility and last date — one page", SCHOLARSHIPS_BODY),
    ("editorial-team", "Editorial team &amp; fact-checking",
     "Who writes and verifies studentup.in — author profile, verification process and the public correction policy readers can hold us to.",
     "Editorial team &amp; fact-checking", "Who writes, who verifies, how to report a mistake", EDITORIAL_BODY),    # v196: calendar (deadline intelligence) · IC price list · corrections log.
    ("exam-calendar", "Exam &amp; application calendar 2026",
     "Every confirmed government job, scholarship and exam last date in one calendar — sorted by month, closing-soon first, with a one-tap .ics export to your phone calendar.",
     "Exam &amp; application calendar 2026",
     "Every last date we have confirmed, in one list — sorted by month", CALENDAR_BODY),
    ("internet-center", "Students Internet Center",
     "The full price list and rules for our offline form-filling service — what is included, what is never included, government fee separation, turnaround and refund policy.",
     "Students Internet Center",
     "Separate offline service &middot; transparent price list &middot; optional", IC_BODY),
    ("corrections", "Corrections &amp; updates",
     "The public correction log — every fixed mistake stays visible with its date, and readers can report errors with the official notification.",
     "Corrections &amp; updates",
     "What changed, when, and how to report a mistake", CORRECTIONS_BODY),
    ("daily-quiz", "Daily quiz &amp; reader polls",
     "Five fresh government-exam practice questions every morning with explained answers, plus one reader poll — free, no login, and nothing about you is stored.",
     "Daily quiz &amp; reader polls", "Five questions every day, explained — plus one poll that decides what we build next", QUIZ_BODY),
]

FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">
  <rect width="64" height="64" rx="14" fill="#0f2e62"/>
  <text x="50%" y="56%" text-anchor="middle" dominant-baseline="middle"
        font-family="system-ui,Segoe UI,Roboto,sans-serif" font-size="30" font-weight="800" fill="#ffffff">S</text>
  <circle cx="50" cy="44" r="4.5" fill="#ed8a32"/>
</svg>
"""

ROBOTS = """# studentup.in — public preview build
User-agent: *
Allow: /
Disallow: /admin
# internal artifacts — strategy/keyword data + (safety-net) purana _dev/ drafts (v58/v70)
Disallow: /_dev/
Disallow: /keyword-universe-top200.csv

# AdSense/verification crawlers
User-agent: Mediapartners-Google
Allow: /

# Public AI/search crawlers may read canonical editorial pages.
# Private evidence, drafts and internal artifacts remain outside public paths.
User-agent: GPTBot
Allow: /
User-agent: OAI-SearchBot
Allow: /
User-agent: Google-Extended
Allow: /
User-agent: ClaudeBot
Allow: /
User-agent: PerplexityBot
Allow: /

Sitemap: https://studentup.in/sitemap.xml
Sitemap: https://studentup.in/news-sitemap.xml
"""

SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://studentup.in/</loc><lastmod>{d}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>
  <url><loc>https://studentup.in/pages/advertise.html</loc><lastmod>{d}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>https://studentup.in/pages/about.html</loc><lastmod>{d}</lastmod><priority>0.6</priority></url>
  <url><loc>https://studentup.in/pages/contact.html</loc><lastmod>{d}</lastmod><priority>0.7</priority></url>
  <url><loc>https://studentup.in/pages/privacy.html</loc><lastmod>{d}</lastmod><priority>0.5</priority></url>
  <url><loc>https://studentup.in/pages/disclaimer.html</loc><lastmod>{d}</lastmod><priority>0.5</priority></url>
  <url><loc>https://studentup.in/pages/terms.html</loc><lastmod>{d}</lastmod><priority>0.5</priority></url>
  <url><loc>https://studentup.in/pages/editorial-policy.html</loc><lastmod>{d}</lastmod><priority>0.6</priority></url>
  <url><loc>https://studentup.in/pages/exam-calendar.html</loc><lastmod>{d}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>
  <url><loc>https://studentup.in/pages/internet-center.html</loc><lastmod>{d}</lastmod><changefreq>monthly</changefreq><priority>0.7</priority></url>
  <url><loc>https://studentup.in/pages/corrections.html</loc><lastmod>{d}</lastmod><changefreq>weekly</changefreq><priority>0.6</priority></url>
  <url><loc>https://studentup.in/pages/ts-jobs-hub.html</loc><lastmod>{d}</lastmod><changefreq>daily</changefreq><priority>0.9</priority></url>
  <url><loc>https://studentup.in/pages/results-hub.html</loc><lastmod>{d}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>
  <url><loc>https://studentup.in/pages/scholarships-hub.html</loc><lastmod>{d}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>
  <url><loc>https://studentup.in/pages/editorial-team.html</loc><lastmod>{d}</lastmod><priority>0.6</priority></url>
  <url><loc>https://studentup.in/pages/daily-quiz.html</loc><lastmod>{d}</lastmod><changefreq>daily</changefreq><priority>0.8</priority></url>
  <url><loc>https://studentup.in/tools/</loc><lastmod>{d}</lastmod><changefreq>weekly</changefreq><priority>0.8</priority></url>
  <url><loc>https://studentup.in/posts/upsc-junior-assistant-2026.html</loc><lastmod>{d}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>
  <url><loc>https://studentup.in/posts/engineering-internships-2026.html</loc><lastmod>{d}</lastmod><changefreq>weekly</changefreq><priority>0.7</priority></url>
</urlset>
"""


ADS_TXT_HEADER = """# ads.txt — studentup.in (IAB ads.txt standard)
# Read by buyers/crawlers to know who may sell this site's ad inventory.
# A missing/invalid ads.txt reduces advertiser demand (lower RPM).
#
# When AdSense is approved: put ADSENSE_CLIENT_ID=ca-pub-XXXXXXXXXXXXXXXX in .env
# and re-run:  python tools/build_policy_pages.py   (this file updates automatically)
"""


def _adsense_pub_id() -> str:
    """ADSENSE_CLIENT_ID (env or .env) → 'pub-################' leda ''."""
    raw = os.environ.get("ADSENSE_CLIENT_ID") or os.environ.get("ADSENSE_CLIENT") or ""
    if not raw:
        env = ROOT.parent / ".env" if (ROOT.parent / ".env").exists() else Path(".env")
        try:
            for line in io.open(env, encoding="utf-8"):
                if line.strip().startswith("ADSENSE_CLIENT_ID"):
                    raw = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
        except OSError:
            raw = ""
    pub = re.sub(r"^ca-", "", raw.strip())
    m = re.fullmatch(r"pub-(\d{10,20})", pub)
    return m.group(0) if m else ""


def _ads_txt_extra_lines() -> list:
    """ads/ads_txt_extra.txt nunchi partner lines (comments skip)."""
    path = ROOT / "ads" / "ads_txt_extra.txt"
    try:
        raw = io.open(path, encoding="utf-8").read()
    except OSError:
        return []
    out = []
    for line in raw.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if len(line.split(",")) < 3:
            continue                      # IAB format minimum: domain, publisher, relationship
        out.append(line)
    return out


def write_ads_txt() -> str:
    """preview/ads.txt — AdSense line (approval tarvata) + partner lines, leda honest placeholder."""
    pub = _adsense_pub_id()
    extra = _ads_txt_extra_lines()
    lines = []
    if pub:
        lines.append(f"google.com, {pub}, DIRECT, f08c47fec0942fa0")
    lines.extend(extra)
    if lines:
        text = ADS_TXT_HEADER + "\n" + "\n".join(lines) + "\n"
        state = "live+partners(%d)" % len(extra) if extra and pub else ("partners(%d)" % len(extra) if extra else "live")
    else:
        text = ADS_TXT_HEADER + "\n# (placeholder — nothing is served until AdSense approval)\n"
        state = "placeholder"
    (OUT / "ads.txt").write_text(text, encoding="utf-8")
    return state

def write_keyword_csv(limit: int = 200) -> str:
    """preview/keyword-universe-top200.csv — engine nunchi top-N keywords (v58).

    Idi INTERNAL artifact (robots.txt lo disallow) — content plan proof ki use avutundi.
    Engine nunchi generate avutundi, so stale avvadu: priority order + category
    + proposed title anni live top_post.keyword_universe() nunchi vasthai.
    autoblog import fail ayithe (standalone builder) skip avutundi — build aagadu.
    """
    try:
        import sys as _sys
        if str(ROOT) not in _sys.path:
            _sys.path.insert(0, str(ROOT))
        from autoblog import top_post
        uni = top_post.keyword_universe()
    except Exception as exc:  # noqa: BLE001
        return "skipped (%s: %s)" % (type(exc).__name__, exc)
    rows = uni[:limit]
    path = OUT / "keyword-universe-top200.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["rank", "keyword", "priority", "cluster", "intent", "funnel",
                    "category", "proposed_title"])
        for i, e in enumerate(rows, 1):
            w.writerow([i, e["kw"], e["priority"], e["cluster"], e["intent"],
                        e["funnel"], e["cat"], e["title"]])
    return "%d rows · universe %d" % (len(rows), len(uni))


def sync_home_nav() -> str:
    """v197: home demo nav ni IDE generator nunchi rasthundi (pin-to-pin).

    Mundu index.html nav ni chey-adi ga copy cheyyadam valla theme builder ki,
    preview ki madhya drift vachedi. Ippudu okkate source: `mega_nav_html()`.
    """
    home_page = OUT / "worldclass" / "index.html"
    if not home_page.exists():
        return "index.html ledu"
    html = home_page.read_text(encoding="utf-8")
    nav = ('<nav class="nav" aria-label="Main menu">'
           + mega_nav_html(home="index.html", pfx="../") + "</nav>")
    new, n = re.subn(r'<nav class="nav" aria-label="Main menu">.*?</nav>',
                     lambda _m: nav, html, count=1, flags=re.S)
    if not n:
        return "nav block dhorakaledu"
    if new != html:
        home_page.write_text(new, encoding="utf-8")
        return "nav updated (%d -> %d bytes)" % (len(html), len(new))
    return "already in sync"


def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    scripts = {"contact": CONTACT_SCRIPT, "daily-quiz": QUIZ_SCRIPT}
    for slug, title, desc, h1, sub, body in PAGE_DEFS:
        filled = (body.replace("{email}", EMAIL).replace("{tg}", TG)
                      .replace("{wa}", WA_LINK).replace("{phone}", PHONE))
        html = build(slug, title, desc, h1, sub, filled, script=scripts.get(slug, ""))
        (PAGES / ("%s.html" % slug)).write_text(html, encoding="utf-8")
        print("  wrote pages/%s.html (%d bytes)" % (slug, len(html)))
    print("  home nav: %s" % sync_home_nav())
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (OUT / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    (OUT / "sitemap.xml").write_text(SITEMAP.format(d=UPDATED), encoding="utf-8")
    ads_state = write_ads_txt()
    print("  wrote favicon.svg · robots.txt · sitemap.xml · ads.txt (%s)" % ads_state)
    kw_state = write_keyword_csv()
    print("  wrote keyword-universe-top200.csv (%s)" % kw_state)
    print("ALL POLICY PAGES BUILT ✔")

    # v193: article pages kuda ide shell nunchi (okate design anta preview lo).
    try:
        import build_preview_posts  # noqa: PLC0415  (circular safe: module already loaded)
        build_preview_posts.main()
        import build_preview_tools  # noqa: PLC0415
        build_preview_tools.main()
        import build_standalone  # noqa: PLC0415
        build_standalone.main()
    except Exception as exc:  # pragma: no cover - build helper
        print(f"  \u26a0\ufe0f  posts build skip: {exc}")


if __name__ == "__main__":
    main()
