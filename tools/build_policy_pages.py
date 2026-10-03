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
<style>
{css}
</style>
</head>
<body>
<svg style="display:none" aria-hidden="true" focusable="false"><symbol id="su-i-sun" viewBox="0 0 24 24"><path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z"/></symbol><symbol id="su-i-moon" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9 7.2 7.2 0 0 1-9-9Z"/></symbol><symbol id="su-i-home" viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5V21H3z"/></symbol><symbol id="su-i-work" viewBox="0 0 24 24"><path d="M3 7h18v13H3zM9 7V5h6v2"/></symbol><symbol id="su-i-chart" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></symbol><symbol id="su-i-bell" viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0-6 6v3l-2 3h16l-2-3V9a6 6 0 0 0-6-6Zm-2 15a2 2 0 0 0 4 0"/></symbol><symbol id="su-i-close" viewBox="0 0 24 24"><path d="M19 6.4 17.6 5 12 10.6 6.4 5 5 6.4l5.6 5.6L5 17.6 6.4 19l5.6-5.6 5.6 5.6 1.4-1.4-5.6-5.6Z"/></symbol></svg>
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
})();"""


def header_html(home: str = "../worldclass/index.html", topbar: str = "Government jobs \u00b7 Exams \u00b7 Scholarships") -> str:
    """Shared header — the SAME classes as the WP theme header.php."""
    nav = [("Home", home), ("Jobs", home + "#jobs"), ("Tools", "../tools/index.html"), ("Alerts", home + "#alerts")]
    links = "".join('<a href="%s">%s</a>' % (h, t) for t, h in nav)
    return ('<a class="skip-link screen-reader-text" href="#main">Skip to content</a>\n'
            '<div class="topbar"><div class="wrap">\n'
            '  <span>' + topbar + '</span>\n'
            '  <span><a href="https://wa.me/919182739312">WhatsApp</a> \u00b7 <a href="https://t.me/studentup_in">Telegram</a></span>\n'
            '</div></div>\n'
            '<header class="header"><div class="headrow">\n'
            '  <a class="logo" href="' + home + '"><span class="mark">SU</span><span><span class="brand">StudentUp</span><small>studentup.in</small></span></a>\n'
            '  <nav class="nav" aria-label="Main">' + links + '</nav>\n'
            '  <div class="headactions"><button class="iconbtn" id="su-theme" type="button" aria-label="Dark mode toggle"></button></div>\n'
            '</div></header>')


def footer_html(home: str = "../worldclass/index.html", pfx: str = "") -> str:
    """Shared footer — same 4-column grid as the WP theme footer.php."""
    return ('<footer class="su-foot"><div class="su-foot-grid">\n'
            '  <div><h4>StudentUp</h4><p style="margin:0;color:#a9bfdd">Verified government job, exam and scholarship updates for Telangana &amp; AP students.</p></div>\n'
            '  <div><h4>Jobs</h4><ul><li><a href="' + home + '#jobs">TS Jobs</a></li><li><a href="' + home + '#jobs">AP Jobs</a></li><li><a href="' + home + '#jobs">Central Govt</a></li><li><a href="' + home + '#jobs">Bank Jobs</a></li></ul></div>\n'
            '  <div><h4>Site</h4><ul><li><a href="' + pfx + 'about.html">About us</a></li><li><a href="' + pfx + 'contact.html">Contact</a></li><li><a href="' + pfx + 'advertise.html">Advertise</a></li><li><a href="' + pfx + 'editorial-policy.html">Editorial policy</a></li></ul></div>\n'
            '  <div><h4>Legal</h4><ul><li><a href="' + pfx + 'privacy.html">Privacy</a></li><li><a href="' + pfx + 'disclaimer.html">Disclaimer</a></li><li><a href="' + pfx + 'terms.html">Terms</a></li><li><a href="https://t.me/studentup_in">Telegram</a></li></ul></div>\n'
            '</div>\n'
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
    return SHELL.format(title=title, desc=desc, slug=slug, h1=h1, sub=sub,
                        body=body, css=CSS, nav=nav_html(), email=EMAIL, updated=UPDATED,
                        wa=WA_LINK, phone=PHONE, script=script, pagejs=PAGE_JS,
                        header=header_html(), footerbar=footer_html(pfx=""),
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


def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    scripts = {"contact": CONTACT_SCRIPT}
    for slug, title, desc, h1, sub, body in PAGE_DEFS:
        filled = (body.replace("{email}", EMAIL).replace("{tg}", TG)
                      .replace("{wa}", WA_LINK).replace("{phone}", PHONE))
        html = build(slug, title, desc, h1, sub, filled, script=scripts.get(slug, ""))
        (PAGES / ("%s.html" % slug)).write_text(html, encoding="utf-8")
        print("  wrote pages/%s.html (%d bytes)" % (slug, len(html)))
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
