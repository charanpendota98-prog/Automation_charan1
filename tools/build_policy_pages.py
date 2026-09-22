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

CSS = """
:root{--navy:#0f2e62;--blue:#2463b7;--orange:#ed8a32;--ink:#122036;--muted:#5b6b85;
--line:#dbe4f0;--card:#fff;--soft:#f4f8ff}
*{box-sizing:border-box}
body{margin:0;font-family:system-ui,-apple-system,"Noto Sans Telugu","Segoe UI",Roboto,sans-serif;
background:linear-gradient(180deg,#eef4ff,#f8fbff 320px);color:var(--ink);line-height:1.75}
a{color:var(--blue)}
.top{background:var(--navy);color:#fff}
.wrap{max-width:900px;margin:0 auto;padding:0 18px}
.top .wrap{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:14px 18px;flex-wrap:wrap}
.brand{font-weight:900;font-size:19px;color:#fff;text-decoration:none;letter-spacing:-.02em}
.brand span{color:var(--orange)}
.top a.back{color:#cfe0fb;text-decoration:none;font-size:13.5px;font-weight:700;border:1px solid rgba(255,255,255,.28);
border-radius:99px;padding:7px 14px}
.top a.back:hover{background:rgba(255,255,255,.12)}
main{background:var(--card);border:1px solid var(--line);border-radius:18px;box-shadow:0 14px 34px rgba(15,46,98,.07);
margin:22px auto;padding:30px 32px;max-width:900px}
h1{margin:0 0 6px;font-size:27px;color:var(--navy);letter-spacing:-.02em;line-height:1.35}
.sub{color:var(--muted);font-size:13px;margin:0 0 22px;padding-bottom:16px;border-bottom:1px solid var(--line)}
h2{font-size:18.5px;color:var(--navy);margin:26px 0 8px}
p,li{font-size:15px}
ul{padding-left:22px;margin:8px 0}
li{margin:5px 0}
.note{background:var(--soft);border-left:4px solid var(--blue);border-radius:10px;padding:13px 16px;margin:16px 0;font-size:14px}
.warn{background:#fff6ec;border-left-color:var(--orange)}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));margin:14px 0}
.tile{background:var(--soft);border:1px solid var(--line);border-radius:13px;padding:14px}
.tile b{display:block;color:var(--navy);font-size:15px;margin-bottom:3px}
.tile span{font-size:13px;color:var(--muted)}
.su-ad{background:var(--soft);border:1px dashed #bfd2ee;border-radius:13px;padding:14px 16px;margin:20px 0}
.su-ad-kicker{font-size:10.5px;letter-spacing:.09em;font-weight:800;color:var(--orange);margin-bottom:6px}
.su-ad-title{font-weight:800;color:var(--navy);font-size:15px}
.su-ad-desc{font-size:13px;color:var(--muted);margin:4px 0 10px}
.su-ad a.go{background:var(--blue);color:#fff;text-decoration:none;font-weight:800;border-radius:9px;padding:9px 15px;font-size:13px;display:inline-block}
.cta{display:inline-block;background:var(--orange);color:#fff;text-decoration:none;font-weight:800;
border-radius:11px;padding:12px 20px;margin:6px 8px 6px 0;font-size:14.5px}
.cta.alt{background:var(--navy)}
table{width:100%;border-collapse:collapse;margin:12px 0;font-size:14px}
th,td{text-align:left;padding:9px 10px;border-bottom:1px solid var(--line)}
th{background:var(--soft);color:var(--navy);font-size:13px}
footer{border-top:1px solid var(--line);margin-top:8px;padding:18px 0 30px;font-size:13px;color:var(--muted)}
footer .wrap{display:flex;flex-wrap:wrap;gap:8px 18px;max-width:900px;margin:0 auto}
footer a{color:var(--blue);text-decoration:none}
footer .fine{width:100%;font-size:12px;line-height:1.7;margin-top:6px}
.steps{margin:10px 0 12px;padding-left:20px;line-height:1.7}
.steps li{margin-bottom:5px}
.wa-box{display:inline-block;background:linear-gradient(135deg,#25d366,#128c7e);color:#fff!important;
  border-radius:13px;padding:12px 16px;text-decoration:none;font-weight:800;margin:4px 8px 4px 0;
  box-shadow:0 10px 22px rgba(18,140,126,.22)}
.wa-box small{font-weight:600;opacity:.93}
.leadgrid{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:10px 0 0}
.leadgrid input,.leadgrid select{width:100%;padding:11px 12px;border:1px solid var(--line);
  border-radius:11px;font:inherit;background:var(--card);color:inherit}
.leadgrid input:focus,.leadgrid select:focus{outline:2px solid var(--blue);outline-offset:1px}
.lead-hp{position:absolute;left:-9999px;width:1px;height:1px;opacity:0}
.leadbtn{margin-top:12px;width:100%;padding:13px;border:0;border-radius:12px;background:var(--blue);
  color:#fff;font-weight:700;font-size:14.5px;cursor:pointer}
.leadbtn:disabled{opacity:.6;cursor:default}
.leadnote{font-size:12px;color:var(--muted);margin:10px 0 0;line-height:1.6}
.leadmsg{margin-top:11px;font-size:13px;font-weight:600;display:none}
.leadmsg.ok{display:block;color:#0a7a3d}
.leadmsg.err{display:block;color:#b3261e}
@media(max-width:620px){main{margin:12px;padding:20px 18px;border-radius:14px}h1{font-size:22px}
  .leadgrid{grid-template-columns:1fr}}
""".strip()

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
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} · studentup.in</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="theme-color" content="#0f2e62">
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
<style>
{css}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <a class="brand" href="../index.html">studentup<span>.</span>in</a>
  <a class="back" href="../index.html">← Back to home</a>
</div></header>
<main>
  <h1>{h1}</h1>
  <p class="sub">{sub}</p>
{body}
</main>
{script}
<footer><div class="wrap">
  {nav}
  <p class="fine">© 2026 studentup.in · For Telangana &amp; Andhra Pradesh students.
  Ad revenue, rankings and job results are never guaranteed — always confirm the real information in the official notification.
  Corrections: <a href="mailto:{email}">{email}</a> · This page last updated: {updated}</p>
</div></footer>
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
                        wa=WA_LINK, phone=PHONE, script=script)


ABOUT = """
  <h2>What is studentup.in?</h2>
  <p>studentup.in is an attempt to put jobs, scholarships, results, exams and career guidance for
  Telangana and Andhra Pradesh students in one place, in simple language. Sources are always official
  portals only; there are no rumours, guesses or copied content.</p>

  <h2>How it works</h2>
  <div class="grid">
    <div class="tile"><b>1 · Source monitoring</b><span>A grid of official sources — TSPSC, APPSC, SSC, NSP,
      state boards, DSC, DISCOMs. Checked several times a day.</span></div>
    <div class="tile"><b>2 · Verification gates</b><span>Source check and deep cross-verification
      (2+ sources), minimum originality — a draft is created only after these pass.</span></div>
    <div class="tile"><b>3 · Human review</b><span>Every post arrives as a draft; it goes live only after
      the quality bar is crossed. If anything is doubtful, publishing stops.</span></div>
    <div class="tile"><b>4 · Continuous updates</b><span>When dates change or a notification is
      re-released, older articles are corrected — the last-updated date sits on every article.</span></div>
  </div>

  <h2>What we never do</h2>
  <ul>
    <li>We are not a government body — we have no connection with TSPSC, APPSC, SSC, NSP or any department.</li>
    <li>We never guarantee a job, a scholarship, admission, a ranking or income.</li>
    <li>We never charge students; we never ask for an "account number" or OTP.</li>
    <li>We never sell personal data — see the <a href="privacy.html">privacy policy</a>.</li>
  </ul>

  <div class="note"><b>Honest note:</b> deadlines, vacancy counts and results — always confirm them once
  in the official notification. If you spot a mistake, email us and we correct it fast.</div>

  <p><a class="cta" href="../index.html">See today's updates</a>
     <a class="cta alt" href="contact.html">Contact us</a></p>
"""

CONTACT = """
  <p><b>Students Internet Center (TS &amp; AP)</b> · corrections · partnerships — reach us on WhatsApp
  first; it is the fastest route. We usually reply within one working day.</p>

  <h2>Students Internet Center — apply without travelling</h2>
  <p>You do not need to visit any centre, cyber café or office to apply for a job or scholarship.
  Call us and WhatsApp your documents — we complete the application and send you the PDF. Service
  charge is kept as low as possible.</p>
  <ol class="steps">
    <li><b>Call us</b> with the post or notification you want to apply for.</li>
    <li><b>WhatsApp your documents</b> — photo, signature, certificates, resume (clear photos are enough).</li>
    <li><b>We apply &amp; send the PDF</b> — the filled application PDF reaches you on WhatsApp; corrections free.</li>
  </ol>
  <p class="sub">We fill the whole application — the PDF comes to you on WhatsApp.</p>
  <p><a class="wa-box" href="{wa}" target="_blank" rel="noopener"><b>WhatsApp your documents</b><br>
     <small>Tap to open our WhatsApp chat</small></a>
     <a class="cta alt" href="tel:{phone}">Call {phone}</a>
     <a class="cta alt" href="mailto:{email}?subject=Student%20Help">Email</a>
     <a class="cta alt" href="{tg}" target="_blank" rel="noopener">Telegram</a></p>

  <h2>Get free job &amp; exam updates</h2>
  <p>Daily job notifications, exam dates and results — free, straight to your phone. No spam calls,
  and you can stop anytime.</p>
  <form id="leadform" novalidate>
    <div class="leadgrid">
      <input type="text" id="ld-name" name="name" maxlength="60" autocomplete="name"
             placeholder="Your name" aria-label="Your name" required>
      <input type="tel" id="ld-phone" name="phone" maxlength="15" inputmode="numeric"
             autocomplete="tel" placeholder="Mobile number (10 digits)" aria-label="Mobile number" required>
      <select id="ld-interest" name="interest" aria-label="What are you looking for?">
        <option value="jobs">Jobs</option>
        <option value="scholarships">Scholarships</option>
        <option value="college">College admissions</option>
        <option value="coaching">Coaching</option>
        <option value="exams">Exams</option>
        <option value="other">Other</option>
      </select>
      <input type="text" id="ld-city" name="city" maxlength="40" autocomplete="address-level2"
             placeholder="City (optional)" aria-label="City">
      <input type="text" class="lead-hp" id="ld-website" name="website" tabindex="-1"
             autocomplete="off" aria-hidden="true">
    </div>
    <button type="submit" class="leadbtn" id="ld-submit">Get free updates</button>
    <p class="leadmsg" id="ld-msg" role="status" aria-live="polite"></p>
    <p class="leadnote">Pressing the button opens WhatsApp with your message ready — nothing is stored
      on our site. We never sell your number. You can ask us to stop anytime —
      see <a href="privacy.html">privacy policy</a>.</p>
  </form>

  <h2>Other ways to reach us</h2>
  <table>
    <tr><th>What you need</th><th>Where</th><th>Reply time</th></tr>
    <tr><td><b>Corrections / wrong information</b></td><td><a href="mailto:{email}?subject=Correction">{email}</a></td><td>24–48 hours</td></tr>
    <tr><td><b>Partnership / advertising</b> (colleges, coaching, shops, services)</td>
      <td><a href="{wa}" target="_blank" rel="noopener">WhatsApp</a> ·
      <a href="mailto:{email}?subject=Advertising%20enquiry">{email}</a></td><td>1–2 working days</td></tr>
    <tr><td><b>Student help</b> (applications, documents)</td>
      <td><a href="tel:{phone}">Call</a> · <a href="{wa}" target="_blank" rel="noopener">WhatsApp</a> ·
      <a href="{tg}" target="_blank" rel="noopener">Telegram</a></td><td>same day</td></tr>
  </table>

  <h2>When you email or message us, include</h2>
  <ul>
    <li>Page link, screenshot (if any) and the official source link for the correct information.</li>
    <li>For partnerships: business name, city, target link and the duration you have in mind.</li>
  </ul>

  <div class="note warn"><b>Beware of fraud:</b> nobody from studentup.in will ever call and ask for Aadhaar,
  OTP, bank details or a fee. If that happens, it is a scam — <a href="mailto:{email}">tell us immediately</a>.</div>
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
  <p>This policy covers the studentup.in website, the daily quiz and the daily poll question.
  In one line: we do not collect your name, phone number or Aadhaar details.</p>

  <h2>What we do not collect</h2>
  <ul>
    <li>No accounts or login — we do not ask for name, email or phone number.</li>
    <li>No documents, bank details or OTP — none of it.</li>
    <li>Personal data is never sold or rented to anyone.</li>
  </ul>

  <h2>What stays in your browser</h2>
  <table>
    <tr><th>Item</th><th>Why</th><th>Where</th></tr>
    <tr><td>Theme choice (dark / light)</td><td>So the site opens the way you left it</td><td>Your browser only</td></tr>
    <tr><td>Quiz best score</td><td>So you can see your own progress</td><td>Your browser only</td></tr>
    <tr><td>Daily poll answer</td><td>So you see the correct answer once answered</td><td>Your browser only</td></tr>
  </table>

  <h2>Ads and measurement</h2>
  <ul>
    <li>Google AdSense / Analytics may be used for ads and measurement — they can use cookies.
      They start <b>only after the owner's approval</b>.</li>
    <li>Until AdSense approval, the ads shown are our own partners' creatives, clearly marked with a
      SPONSORED label.</li>
    <li>What we give advertisers is display space only — never your personal data.</li>
  </ul>

  <h2>Third-party vendors and cookies (Google AdSense)</h2>
  <p>This section applies when advertising is active on this site. It is written the way Google's
  AdSense programme requires.</p>
  <ul>
    <li><b>Third-party vendors, including Google</b>, use cookies to serve ads based on your prior
      visits to this website or other websites.</li>
    <li>Google's use of advertising cookies enables it and its partners to serve ads to you based on
      your visit to this site and/or other sites on the internet.</li>
    <li>You may <b>opt out of personalised advertising</b> by visiting
      <a href="https://www.google.com/settings/ads" rel="nofollow noopener" target="_blank">Google Ads
      Settings</a>. You can also opt out of some third-party vendors' use of cookies for personalised
      advertising at
      <a href="https://www.aboutads.info/choices/" rel="nofollow noopener" target="_blank">www.aboutads.info</a>.</li>
    <li>If you are in the EEA, the UK or Switzerland, a Google-certified consent message (CMP) is shown
      before any advertising cookie is set, and advertising is held until you choose.</li>
    <li>You can block or delete cookies at any time in your browser settings. Blocking ad cookies does
      not stop you reading any page on this site.</li>
  </ul>

  <h2>Information you email us</h2>
  <p>Any email you send is used only to make the correction. Once the correction is done there is no need
  to keep it.</p>

  <h2>Your rights</h2>
  <p>If you believe we hold anything about you, ask us to delete it —
  <a href="mailto:{email}">email us</a>. If this policy changes, the updated date on this page changes
  with it.</p>
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

Sitemap: https://studentup.in/sitemap.xml
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


if __name__ == "__main__":
    main()
