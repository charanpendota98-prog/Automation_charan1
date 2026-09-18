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
PHONE = "+919999999999"
WA_LINK = "https://wa.me/919999999999?text=StudentUp%20Students%20Internet%20Center"
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
    ("about.html", "మా గురించి"),
    ("advertise.html", "Partner with us"),
    ("contact.html", "సంప్రదించండి"),
    ("privacy.html", "గోప్యతా విధానం"),
    ("disclaimer.html", "నిరాకరణ"),
    ("editorial-policy.html", "సంపాదకీయ విధానం"),
]

SHELL = """<!DOCTYPE html>
<html lang="te">
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
<meta property="og:locale" content="te_IN">
<meta property="og:url" content="https://studentup.in/pages/{slug}.html">
<meta property="og:image" content="https://studentup.in/logo.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"WebPage","name":"{title}","inLanguage":"te-IN",
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
  <a class="back" href="../index.html">← హోమ్‌కు తిరిగి వెళ్లండి</a>
</div></header>
<main>
  <h1>{h1}</h1>
  <p class="sub">{sub}</p>
{body}
</main>
{script}
<footer><div class="wrap">
  {nav}
  <p class="fine">© 2026 studentup.in · తెలంగాణ (33 జిల్లాలు) + ఆంధ్రప్రదేశ్ (26 జిల్లాలు) విద్యార్థుల కోసం.
  ప్రకటన ఆదాయం, ర్యాంకింగ్‌లు, ఉద్యోగ ఫలితాలు ఎప్పుడూ హామీ ఇవ్వబడవు — నిజమైన సమాచారం అధికారిక నోటిఫికేషన్‌లలో మాత్రమే నిర్ధారించుకోవాలి.
  సవరణలు: <a href="mailto:{email}">{email}</a> · ఈ పేజీ చివరి నవీకరణ: {updated}</p>
</div></footer>
</body>
</html>
"""


AD_SLOT = """  <aside class="su-ad" aria-label="Sponsored content" data-slot="policy-inline">
    <div class="su-ad-kicker">SPONSORED · భాగస్వామి ప్రకటన స్థలం</div>
    <div class="su-ad-title">మీ కళాశాల / షాప్ / కోచింగ్ ఇక్కడ కనిపించగలదు</div>
    <p class="su-ad-desc">విద్యార్థులు ఎక్కువగా చూసే పేజీలలో శుభ్రమైన, లేబుల్ చేసిన ప్రకటన స్థలం —
      తప్పుడు క్లిక్‌లు లేవు, క్లిక్‌బైట్ లేదు.</p>
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
  <h2>studentup.in అంటే ఏమిటి?</h2>
  <p>తెలంగాణ మరియు ఆంధ్రప్రదేశ్ విద్యార్థుల కోసం ఉద్యోగాలు, స్కాలర్‌షిప్‌లు, ఫలితాలు,
  పరీక్షలు, కెరీర్ మార్గదర్శనం — అన్నీ ఒకే వేదికపై, సులభమైన తెలుగులో ఇచ్చే ప్రయత్నం ఇది.
  మూలం ఎప్పుడూ అధికారిక పోర్టల్‌లు మాత్రమే; వదంతులు, ఊహలు, కాపీ కంటెంట్ ఉండవు.</p>

  <h2>ఎలా పని చేస్తుంది?</h2>
  <div class="grid">
    <div class="tile"><b>1 · మూల పర్యవేక్షణ</b><span>105 అధికారిక మూలాల గ్రిడ్ — TSPSC, APPSC, SSC, NSP,
      రాష్ట్ర బోర్డులు, DSC, DISCOMలు. రోజుకు 4 సార్లు పరిశీలన.</span></div>
    <div class="tile"><b>2 · ధృవీకరణ గేట్లు</b><span>మూల తనిఖీ, లోతైన క్రాస్-వెరిఫికేషన్ (2+ మూలాలు),
      అసలుతనం 72% కనీసం — ఇవి పాస్ అయిన తర్వాతే డ్రాఫ్ట్.</span></div>
    <div class="tile"><b>3 · మానవ సమీక్ష</b><span>ప్రతి పోస్ట్ డ్రాఫ్ట్‌గా వస్తుంది; నాణ్యతా స్కోరు 80/100
      దాటిన తర్వాతే ప్రచురణ. సందేహం ఉంటే ప్రచురణ ఆపేస్తాము.</span></div>
    <div class="tile"><b>4 · నిరంతర నవీకరణ</b><span>తేదీలు మారినప్పుడు, నోటిఫికేషన్ వచ్చినప్పుడు
      పాత వ్యాసాలు సవరించబడతాయి — చివరి నవీకరణ తేదీ ప్రతి వ్యాసంపై ఉంటుంది.</span></div>
  </div>

  <h2>మేము ఏమి చేయము</h2>
  <ul>
    <li>ప్రభుత్వ సంస్థలం కాదు — TSPSC, APPSC, SSC, NSP లాంటి అధికారిక సంస్థలతో మాకు ఎలాంటి సంబంధం లేదు.</li>
    <li>ఉద్యోగం, స్కాలర్‌షిప్, ప్రవేశం, ర్యాంకింగ్ లేదా ఆదాయానికి హామీ ఇవ్వము.</li>
    <li>విద్యార్థుల నుంచి ఎలాంటి రుసుము తీసుకోము; "ఖాతా నంబర్" లేదా OTP ఎప్పుడూ అడగము.</li>
    <li>వ్యక్తిగత డేటా అమ్మకం చేయము — వివరాలకు <a href="privacy.html">గోప్యతా విధానం</a> చూడండి.</li>
  </ul>

  <div class="note">నిజాయితీ గమనిక: తుది తేదీలు, ఖాళీల సంఖ్య, ఫలితాలు — అన్నీ
  అధికారిక నోటిఫికేషన్‌లోనే ఒకసారి నిర్ధారించుకోండి. తప్పు కనిపిస్తే మెయిల్ చేయండి —
  వెంటనే సరిచేస్తాము.</div>

  <p><a class="cta" href="../index.html">ఈరోజు అప్‌డేట్‌లు చూడండి</a>
     <a class="cta alt" href="contact.html">సంప్రదించండి</a></p>
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
  <p class="sub">దరఖాస్తు మొత్తం మేము చేస్తాము — PDF మీకు WhatsApp లో పంపుతాము.</p>
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
    <p class="leadnote">We never sell your number and never pass it to advertisers. You can ask us to
      stop anytime — see <a href="privacy.html">privacy policy</a>.</p>
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
/* v71 — free-updates form (leads) → exam portal API. Homepage nunchi ikkadaki move ayyindi. */
(function(){
  var f=document.getElementById("leadform"); if(!f) return;
  function api(){
    var h=location.hostname;
    if(/^8000-/.test(h)) return location.protocol+"//"+h.replace(/^8000-/,"8080-");
    if(h==="localhost"||h==="127.0.0.1") return "http://localhost:8080";
    return "";
  }
  var msg=document.getElementById("ld-msg"), btn=document.getElementById("ld-submit");
  function say(text,ok){ msg.textContent=text; msg.className="leadmsg "+(ok?"ok":"err"); }
  f.addEventListener("submit",function(e){
    e.preventDefault();
    var name=(document.getElementById("ld-name").value||"").trim();
    var phone=(document.getElementById("ld-phone").value||"").replace(/\D/g,"");
    var interest=document.getElementById("ld-interest").value;
    var city=(document.getElementById("ld-city").value||"").trim();
    var hp=(document.getElementById("ld-website").value||"").trim();
    if(name.length<2){ say("⚠️ Please enter your name.",false); return; }
    if(!/^[6-9]\d{9}$/.test(phone)){ say("⚠️ Enter a valid 10-digit mobile number (e.g. 9876543210).",false); return; }
    if(typeof fetch!=="function"){ say("⚠️ This browser cannot send the form — message us directly.",false); return; }
    btn.disabled=true; say("Sending…",true);
    fetch(api()+"/lead",{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({name:name,phone:phone,interest:interest,city:city,website:hp,source:"site"})})
      .then(function(r){return r.json().then(function(j){return {s:r.status,j:j};});})
      .then(function(o){
        btn.disabled=false;
        if(o.s===200&&o.j&&o.j.ok){ say("✅ "+(o.j.message||"You are on the list!"),true); f.reset(); }
        else { say("⚠️ "+((o.j&&o.j.error)||"Could not send — please try again."),false); }
      })
      .catch(function(){ btn.disabled=false; say("⚠️ Server not reachable — please try again later.",false); });
  });
})();
</script>"""

PRIVACY = """
  <p>ఈ విధానం studentup.in వెబ్‌సైట్, పరీక్షల పోర్టల్ మరియు పోల్‌కు వర్తిస్తుంది.
  సులభంగా చెప్పాలంటే: మేము మీ పేరు, ఫోన్ నంబర్, Aadhaar లాంటివి సేకరించము.</p>

  <h2>మేము ఏమి సేకరించము</h2>
  <ul>
    <li>ఖాతాలు (login) అవసరం లేదు — పేరు, ఇమెయిల్, ఫోన్ నంబర్ అడగము.</li>
    <li>మీ దస్త్రాలు (documents), బ్యాంకు వివరాలు, OTP — ఏవీ తీసుకోము.</li>
    <li>వ్యక్తిగత డేటా ఎవరికీ అమ్మము, అద్దెకు ఇవ్వము.</li>
  </ul>

  <h2>మీ బ్రౌజర్‌లో నిల్వ ఉండేవి</h2>
  <table>
    <tr><th>అంశం</th><th>ఎందుకు</th><th>ఎక్కడ</th></tr>
    <tr><td>థీమ్ ఎంపిక (డార్క్ / లైట్)</td><td>మళ్లీ తెరిచినప్పుడు అదే రూపం రావడానికి</td><td>మీ బ్రౌజర్ మాత్రమే</td></tr>
    <tr><td>క్విజ్ ఉత్తమ స్కోరు</td><td>మీ ప్రగతి మీకే కనిపించడానికి</td><td>మీ బ్రౌజర్ మాత్రమే</td></tr>
    <tr><td>పోల్ ఓటు నిర్ధారణ</td><td>ఒకరు రోజుకు ఒక ఓటు మాత్రమే వేయడానికి</td><td>IP చిరునామా (వ్యక్తిగత గుర్తింపుతో కలపము)</td></tr>
  </table>

  <h2>ప్రకటనలు, కొలతలు</h2>
  <ul>
    <li>ప్రకటనలు మరియు కొలతల కోసం Google AdSense / Analytics వాడవచ్చు — అవి కుకీలను
      ఉపయోగించవచ్చు. అవి <b>యజమాని ఆమోదం తర్వాత మాత్రమే</b> ప్రారంభమవుతాయి.</li>
    <li>AdSense ఆమోదం లేని సమయంలో ప్రదర్శించే ప్రకటనలు మా స్వంత భాగస్వాముల ప్రకటనలు
      (SPONSORED లేబుల్‌తో స్పష్టంగా గుర్తించబడతాయి).</li>
    <li>ప్రకటనదారులకు మేము అందించేది ప్రదర్శన స్థలం మాత్రమే — మీ వ్యక్తిగత డేటా కాదు.</li>
  </ul>

  <h2>ఇమెయిల్ ద్వారా వచ్చే సమాచారం</h2>
  <p>మీరు పంపిన ఇమెయిల్, అందులోని వివరాలు సవరణ చేయడానికి మాత్రమే ఉపయోగించబడతాయి.
  సవరణ పూర్తయిన తర్వాత దానిని శాశ్వతంగా ఉంచాల్సిన అవసరం లేదు.</p>

  <h2>మీ హక్కులు</h2>
  <p>మీ గురించిన ఏదైనా సమాచారం మా దగ్గర ఉందని భావిస్తే తొలగించమని అడగవచ్చు —
  <a href="mailto:{email}">ఇమెయిల్</a> చేయండి. ఈ విధానంలో మార్పులు ఉంటే ఈ పేజీలో
  నవీకరణ తేదీ మారుతుంది.</p>
"""

DISCLAIMER = """
  <div class="note warn"><b>ముఖ్య గమనిక:</b> studentup.in ఒక ప్రైవేట్ సమాచార వేదిక.
  ఇది ప్రభుత్వ వెబ్‌సైట్ కాదు; TSPSC, APPSC, SSC, NSP, రాష్ట్ర బోర్డులు లేదా ఏ ప్రభుత్వ
  సంస్థతోనూ మాకు అధికారిక సంబంధం లేదు.</div>

  <h2>సమాచారం ఎంత నమ్మదగినది?</h2>
  <ul>
    <li>ప్రతి వ్యాసం అధికారిక మూలాల (ప్రధానంగా .gov.in పోర్టల్‌లు) నుండి మాత్రమే తయారవుతుంది
      మరియు 2+ మూలాలతో క్రాస్-వెరిఫికేషన్ చేయబడుతుంది.</li>
    <li>అయినా తేదీలు, ఖాళీల సంఖ్య, ఫీజులు, నియమాలు ప్రభుత్వం మార్చవచ్చు. అందుకే
      <b>తుది నిర్ణయం ఎప్పుడూ అధికారిక నోటిఫికేషన్ మాత్రమే</b> — దరఖాస్తు చేసే ముందు
      అధికారిక పోర్టల్‌లో ఒకసారి నిర్ధారించుకోండి.</li>
    <li>ఏ ఉద్యోగం, స్కాలర్‌షిప్, ప్రవేశం, ఫలితం, ర్యాంకింగ్ లేదా ఆదాయానికి హామీ ఇవ్వబడదు.</li>
  </ul>

  <h2>ఆర్థిక మోసాల గురించి</h2>
  <p>మా పేరు చెప్పి ఎవరైనా "ఉద్యోగం ఖాయం", "సీటు ఖాయం" అని డబ్బు అడిగితే అది మోసం.
  మేము ఎలాంటి రుసుము తీసుకోము, OTP/బ్యాంకు వివరాలు అడగము. అలాంటి ఫోన్ కాల్ లేదా
  సందేశం వస్తే వెంటనే <a href="mailto:{email}">మాకు తెలియజేయండి</a>.</p>

  <h2>ప్రకటనల గురించి</h2>
  <ul>
    <li>ప్రకటనలు <b>SPONSORED</b> లేబుల్‌తో స్పష్టంగా గుర్తించబడతాయి; లింకులపై
      <code>rel="sponsored nofollow"</code> ఉంటుంది.</li>
    <li>ప్రకటనదారుల వెబ్‌సైట్లలోని సమాచారానికి, వారి సేవల నాణ్యతకు మేము బాధ్యులు కాము.
      డబ్బు చెల్లించే ముందు వారి వివరాలు నిర్ధారించుకోండి.</li>
    <li>సంపాదకీయ కంటెంట్ మీద ప్రకటనదారులకు ఎలాంటి నియంత్రణ ఉండదు.</li>
  </ul>

  <h2>బాహ్య లింకులు</h2>
  <p>అధికారిక పోర్టల్‌లకు మేము లింకులు ఇస్తాము. ఆ సైట్ల కంటెంట్, లభ్యత, భద్రత వారి
  బాధ్యత — మా నియంత్రణలో లేదు.</p>
"""

EDITORIAL = """
  <p>ప్రతి పోస్ట్ ప్రచురణకు ముందు ఈ 5 గేట్లు దాటాలి. గేట్ విఫలమైతే పోస్ట్ ఆగిపోతుంది —
  "సరిపోతుంది" అని వదిలేయము.</p>

  <div class="grid">
    <div class="tile"><b>① మూల తనిఖీ (ఫాక్ట్ గార్డ్)</b><span>ప్రతి తేదీ, సంఖ్య మూల పత్రంతో సరిపోలాలి —
      సరిపోలకపోతే ఆటో-ఫ్లాగ్.</span></div>
    <div class="tile"><b>② లోతైన క్రాస్-వెరిఫికేషన్</b><span>2+ మూలాలు; అధికారిక మూలాలకు ప్రాధాన్యం;
      విరుద్ధ తేదీలు లేదా పాత సంవత్సరాల డేటా ఉంటే ప్రచురణ నిరోధం. విశ్వాస స్కోరు 0–100.</span></div>
    <div class="tile"><b>③ అసలుతనం 72% కనీసం</b><span>ఇతర సైట్ల కాపీ కాదు; దగ్గరి నకిలీ (≥62% పోలిక)
      ప్రచురణ కాదు.</span></div>
    <div class="tile"><b>④ మానవ సమీక్ష</b><span>డ్రాఫ్ట్ ముందుగా వస్తుంది; నాణ్యతా స్కోరు 80/100
      దాటిన తర్వాతే ప్రచురణ.</span></div>
    <div class="tile"><b>⑤ ప్రకటనల విధానం</b><span>SPONSORED లేబుల్ తప్పనిసరి; లింకుల పక్కన ప్రకటనలు
      ఉండవు; క్లిక్‌బైట్, నకిలీ క్లిక్కులు పూర్తిగా నిషేధం.</span></div>
  </div>

  <h2>మూల విధానం</h2>
  <ul>
    <li>మూలాలు: ప్రభుత్వ పోర్టల్‌లు (.gov.in), అధికారిక ప్రకటనలు, విశ్వసనీయ వార్తా సంస్థలు —
      సోషల్ మీడియా వదంతులు మూలంగా తీసుకోబడవు.</li>
    <li>ఒక అంశానికి కనీసం రెండు మూలాలు; అధికారిక మూలం లేకపోతే పోస్ట్ ఆగుతుంది.</li>
    <li>ఉల్లేఖనలు (citations) ప్రతి వ్యాసంలో కనిపిస్తాయి; ఏజెన్సీ కాపీ ఉండదు.</li>
  </ul>

  <h2>సవరణల విధానం</h2>
  <ul>
    <li>తప్పు గుర్తిస్తే సాధారణంగా 24 గంటల్లో సవరించి, సవరణ గమనిక చేరుస్తాము.</li>
    <li>సవరణ కోరడానికి: <a href="mailto:{email}?subject=Correction">{email}</a> —
      లింకు, తప్పు, సరైన అధికారిక మూలం పంపండి.</li>
    <li>పెద్ద తప్పు జరిగితే వ్యాసాన్ని తాత్కాలికంగా ఆపేసి, నిర్ధారణ తర్వాత మళ్లీ ప్రచురిస్తాము.</li>
  </ul>

  <h2>ప్రకటనలు మరియు సంపాదకీయ స్వాతంత్ర్యం</h2>
  <p>ప్రకటనలు సంపాదకీయ నిర్ణయాలను ప్రభావితం చేయవు. స్పాన్సర్ చేయబడిన కంటెంట్
  ఎప్పుడూ <b>SPONSORED</b> లేబుల్‌తో వేరుగా కనిపిస్తుంది. ప్రకటన లింకులు
  <code>rel="sponsored nofollow"</code> తో ఉంటాయి. AdSense ఆమోదం తర్వాత ప్రకటనల సంఖ్య
  విధాన పరిమితులకు లోబడి ఉంటుంది.</p>

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
  <p>If a paid slot is empty, StudentUp's own services (daily quiz, exam portal, application help) fill
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
    ("about", "మా గురించి",
     "studentup.in ఎవరు, ఎలా పని చేస్తాము, ఏమి చేయము — తెలంగాణ మరియు ఆంధ్రప్రదేశ్ విద్యార్థుల కోసం అధికారిక మూలాలతో నడిచే నిజాయితీ విద్యా వేదిక.",
     "మా గురించి", "తెలంగాణ &amp; ఆంధ్రప్రదేశ్ విద్యార్థుల కోసం ఒక నిజాయితీ వేదిక", ABOUT),
    ("contact", "సంప్రదించండి",
     "సవరణలు, ప్రకటనలు, విద్యార్థి సహాయం — studentup.in సంప్రదింపు మార్గాలు, స్పందన సమయాలు మరియు మోసాల హెచ్చరిక పూర్తి వివరాలు.",
     "సంప్రదించండి", "సవరణలు · ప్రకటనలు · విద్యార్థి సహాయం", CONTACT),
    ("privacy", "గోప్యతా విధానం",
     "studentup.in ఏ డేటా సేకరిస్తుంది, ఏది సేకరించదు, పోల్ ఓట్లు ఎలా నిల్వ ఉంటాయి, ప్రకటనల కుకీల వివరాలు — సులభమైన తెలుగులో.",
     "గోప్యతా విధానం", "మీ డేటా మీదే హక్కు — మేము ఏమి సేకరిస్తాము, ఏమి సేకరించము", PRIVACY),
    ("disclaimer", "నిరాకరణ",
     "studentup.in ప్రభుత్వ వెబ్‌సైట్ కాదు — సమాచార పరిమితులు, హామీలు లేకపోవడం, ఆర్థిక మోసాల హెచ్చరిక మరియు ప్రకటనల నియమాలు.",
     "నిరాకరణ (గమనిక)", "ముఖ్యమైన పరిమితులు — చదవడం తప్పనిసరి", DISCLAIMER),
    ("editorial-policy", "సంపాదకీయ విధానం",
     "5 ధృవీకరణ గేట్లు, అధికారిక మూల విధానం, సవరణల గడువు, ప్రకటనల నియమాలు — studentup.in ప్రతి పోస్ట్ ఎలా తయారవుతుంది.",
     "సంపాదకీయ విధానం", "ప్రతి పోస్ట్ ఈ 5 గేట్లు దాటిన తర్వాతే ప్రచురణ", EDITORIAL),
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
