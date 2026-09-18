# -*- coding: utf-8 -*-
"""v48 — generate pages/ policy pages, robots.txt, sitemap.xml, favicon.svg.

Why: AdSense review (and basic trust) needs real About / Contact / Privacy /
Disclaimer / Editorial-policy pages. Footer/topbar links must not dead-end on
an anchor. Everything here is pure Telugu for the public reader.

Run:  python tools/build_policy_pages.py
"""
from __future__ import annotations

import io
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "preview"
PAGES = OUT / "pages"
EMAIL = "studentupinformative@gmail.com"
TG = "https://t.me/studentup_in"
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
@media(max-width:620px){main{margin:12px;padding:20px 18px;border-radius:14px}h1{font-size:22px}}
""".strip()

NAV = [
    ("about.html", "మా గురించి"),
    ("advertise.html", "ప్రకటనలు ఇవ్వండి"),
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
    <a class="go" href="../index.html#ads" rel="sponsored">ప్రకటన ఇవ్వండి</a>
  </aside>

"""


def nav_html() -> str:
    return "".join('<a href="%s">%s</a>' % (h, t) for h, t in NAV)


def build(slug: str, title: str, desc: str, h1: str, sub: str, body: str) -> str:
    marker = '<p><a class="cta"'
    if marker in body:
        body = body.replace(marker, AD_SLOT + marker, 1)
    else:
        body = body + "\n" + AD_SLOT
    return SHELL.format(title=title, desc=desc, slug=slug, h1=h1, sub=sub,
                        body=body, css=CSS, nav=nav_html(), email=EMAIL, updated=UPDATED)


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

  <div class="note">నిజాయితీ గమనిక: ఈ వెబ్‌సైట్ ఒక ఆటో-బ్లాగర్ పైప్‌లైన్‌తో నిర్మించబడింది —
  కానీ ప్రతి పోస్ట్ మానవ సమీక్ష దాటిన తర్వాతే ప్రచురణ అవుతుంది.
  గేట్లు తప్పులను తగ్గిస్తాయి, తుది సంఖ్యలు అధికారిక నోటిఫికేషన్‌లోనే ఉంటాయి.</div>

  <p><a class="cta" href="../index.html">ఈరోజు అప్‌డేట్‌లు చూడండి</a>
     <a class="cta alt" href="contact.html">సంప్రదించండి</a></p>
"""

CONTACT = """
  <p>మీ ప్రశ్న, సవరణ, ప్రకటన లేదా సహాయం కోసం క్రింది మార్గాలలో సంప్రదించండి.
  సాధారణంగా 1–2 పని దినాలలో స్పందిస్తాము.</p>

  <h2>మార్గాలు</h2>
  <table>
    <tr><th>అవసరం</th><th>ఎక్కడ</th><th>స్పందన</th></tr>
    <tr><td><b>సవరణలు / తప్పు సమాచారం</b></td><td><a href="mailto:{email}?subject=Correction">{email}</a></td><td>24–48 గంటలు</td></tr>
    <tr><td><b>ప్రకటనలు (కళాశాల బ్యానర్, షాప్, కోచింగ్, సేవలు)</b></td><td><a href="mailto:{email}?subject=Advertising">{email}</a> ·
      <a href="{tg}" target="_blank" rel="noopener">Telegram</a></td><td>1–2 పని దినాలు</td></tr>
    <tr><td><b>విద్యార్థి సహాయం (దరఖాస్తు, పత్రాలు)</b></td><td><a href="mailto:{email}?subject=Student%20Help">{email}</a></td><td>2–3 పని దినాలు</td></tr>
  </table>
  <p><a class="cta" href="mailto:{email}">📧 ఇమెయిల్ చేయండి</a>
     <a class="cta alt" href="{tg}" target="_blank" rel="noopener">💬 Telegram సంప్రదింపు</a></p>

  <h2>ఇమెయిల్ పంపేటప్పుడు ఇవి చేర్చండి</h2>
  <ul>
    <li>పేజీ లింకు, స్క్రీన్‌షాట్ (ఉంటే), మరియు సరైన సమాచారం యొక్క అధికారిక మూల లింకు.</li>
    <li>ప్రకటనల కోసం: వ్యాపారం పేరు, నగరం, బ్యానర్/ఇమేజ్, లక్ష్య లింకు, కాల పరిమితి.</li>
  </ul>

  <div class="note warn"><b>మోసాల నుండి జాగ్రత్త:</b> studentup.in తరఫున ఎవరూ ఫోన్ చేసి
  Aadhaar, OTP, బ్యాంకు ఖాతా వివరాలు లేదా రుసుము అడగరు. అలా అడిగితే అది మోసం —
  వెంటనే <a href="mailto:{email}">మాకు తెలియజేయండి</a>.</div>
"""

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

  <div class="note">నిజాయితీ గమనిక: ఈ గేట్లు తప్పులను గణనీయంగా తగ్గిస్తాయి, కానీ
  గూగుల్ ర్యాంకింగ్, AdSense ఆమోదం, ఆదాయం — వీటిని ఏ కోడ్ కూడా హామీ ఇవ్వదు.</div>
"""

ADVERTISE = '''
  <div class="note"><b>మీ వ్యాపారం / కళాశాల / షాప్ / కోచింగ్ / సేవలు</b> — తెలంగాణ &amp;
  ఆంధ్రప్రదేశ్ విద్యార్థులు, తల్లిదండ్రులు, ఉద్యోగ ఆకాంక్షులు చూసే పేజీల్లో, స్పష్టమైన
  <b>SPONSORED</b> లేబుల్‌తో మీ ప్రకటన కనిపిస్తుంది. నకిలీ క్లిక్‌లు, పాపప్‌లు, క్లిక్‌బైట్ — అసలు ఉండవు.</div>

  <h2>స్లాట్‌లు &amp; ధర (రేట్ కార్డ్)</h2>
  <table>
    <tr><th>స్లాట్</th><th>ఎక్కడ కనిపిస్తుంది</th><th>రూపం</th><th>నెలకు</th></tr>
    <tr><td><b>టాప్ లీడర్‌బోర్డ్</b><br><small>అత్యధిక కనిపించే స్థలం</small></td>
        <td>హోమ్ పేజీ, హెడర్ కింద (అందరు చూస్తారు)</td><td>బ్యానర్</td><td><b>₹4,000</b></td></tr>
    <tr><td><b>ఇన్-ఫీడ్ కార్డ్</b></td>
        <td>న్యూస్ గ్రిడ్ మధ్యలో (స్క్రోల్ చేసేటప్పుడు)</td><td>కార్డ్</td><td><b>₹3,000</b></td></tr>
    <tr><td><b>ఆర్టికల్ మధ్యలో</b></td>
        <td>ప్రతి ఆర్టికల్‌లో క్విక్-ఆన్సర్ తర్వాత (చదివే ఆడియన్స్)</td><td>బ్యానర్ / కార్డ్</td><td><b>₹3,500</b></td></tr>
    <tr><td><b>సైడ్‌బార్ స్టిక్కీ</b></td>
        <td>డెస్క్‌టాప్‌లో పక్కన, స్క్రోల్‌తో పాటు (మళ్లీ మళ్లీ కనిపిస్తుంది)</td><td>కార్డ్</td><td><b>₹2,000</b></td></tr>
    <tr><td><b>విధాన పేజీల స్లాట్</b></td>
        <td>About / Contact / Editorial పేజీలు (నమ్మకమైన పేజీలు)</td><td>కార్డ్</td><td><b>₹1,000</b></td></tr>
    <tr><td><b>ఫుల్ ప్యాకేజీ</b> <small>(ఉత్తమ విలువ)</small></td>
        <td>అన్ని స్లాట్‌లు + రోజూ వచ్చే బాట్ ఆర్టికల్స్‌లో కూడా</td><td>అన్ని రూపాలు</td><td><b>₹8,000</b></td></tr>
  </table>
  <p class="sub" style="margin-top:-4px">GST / పన్నులు వర్తిస్తాయి. చిన్న వ్యాపారం / స్థానిక షాప్‌కు
  సీజన్ ఆధారిత ప్యాకేజీలు కూడా ఉన్నాయి — ఇమెయిల్ చేసి అడగండి.</p>

  <h2>ప్రీమియం సేవలు (అత్యధిక ఫలితం)</h2>
  <table>
    <tr><th>సేవ</th><th>ఏమి ఇస్తాము</th><th>ధర</th></tr>
    <tr><td><b>స్పాన్సర్డ్ ఆర్టికల్</b><br><small>Advertorial</small></td>
        <td>మా బోట్ + ఎడిటర్ రాసిన, 100% SEO ఫీల్డ్స్‌తో కూడిన పూర్తి పాజ్ — మీ కోర్సు / కళాశాల /
        సేవల గురించి, స్పష్టమైన <b>SPONSORED</b> లేబుల్‌తో. Google News / search కోసం సిద్ధం.</td>
        <td><b>₹8,000–₹15,000</b><br><small>ఒక్క పాజ్‌కు</small></td></tr>
    <tr><td><b>లీడ్ జనరేషన్</b><br><small>కళాశాలలు · కోచింగ్ · హాస్టళ్లు</small></td>
        <td>మా పేజీల్లో "ఉచిత సమాచారం" ఫారం నుంచి విద్యార్థి పేరు + నంబర్ + ఆసక్తి — వెరిఫైడ్,
        మీకు మాత్రమే (exclusive). కనీసం 50 లీడ్‌లు.</td>
        <td><b>₹150–₹400</b><br><small>ఒక్క లీడ్‌కు</small></td></tr>
    <tr><td><b>వాట్సాప్/టెలిగ్రామ్ బ్రాడ్‌కాస్ట్</b></td>
        <td>మా ఛానెల్‌లో ఒక స్పాన్సర్డ్ మెసేజ్ + పోస్ట్ లింక్ (స్పష్టమైన ప్రకటన లేబుల్‌తో).</td>
        <td><b>₹1,500</b><br><small>ఒక్క బ్రాడ్‌కాస్ట్</small></td></tr>
  </table>
  <p class="sub">ప్రీమియం సేవలు ముందు చెల్లింపు (advance) తో మాత్రమే బుక్ అవుతాయి. లీడ్‌ల నాణ్యత
  నిర్ధారణ తర్వాత మాత్రమే బిల్లు — నకిలీ/డూప్లికేట్ నంబర్లు లెక్కించము.</p>

  <h2>ఇక్కడ ప్రకటన ఇవ్వడం ఎందుకు మేలు?</h2>
  <ul>
    <li><b>స్థానిక ఆడియన్స్:</b> తెలంగాణ (33 జిల్లాలు) + ఆంధ్రప్రదేశ్ (26 జిల్లాలు) విద్యార్థులు, తల్లిదండ్రులు, ఉద్యోగ ఆకాంక్షులు.</li>
    <li><b>ఉద్దేశం ఉన్న పేజీలు:</b> ఉద్యోగాలు, స్కాలర్‌షిప్‌లు, పరీక్షల క్యాలెండర్, ఫలితాలు — ఇక్కడే నిజమైన శోధనలు జరుగుతాయి.</li>
    <li><b>రోజూ కొత్త కంటెంట్:</b> ప్రతిరోజూ కొత్త నోటిఫికేషన్‌లు + ఆర్టికల్స్ (ఆటో-రిఫ్రెష్‌తో పాత పోస్ట్‌లు కూడా మళ్లీ క్రాల్ అవుతాయి).</li>
    <li><b>కచ్చితమైన లేబుల్:</b> SPONSORED కిక్కర్ + <code>rel="sponsored nofollow"</code> — Google విధానాలకు సురక్షితం.</li>
    <li><b>రిపోర్ట్:</b> మీ ప్రకటన ఎన్నిసార్లు కనిపించింది, ఎన్ని క్లిక్‌లు వచ్చాయి — అడిగితే నెలకు ఒకసారి పంపుతాము.</li>
  </ul>

  <h2>బుకింగ్ ఎలా? (3 అడుగులు)</h2>
  <table>
    <tr><th>అడుగు</th><th>ఏమి చేయాలి</th><th>సమయం</th></tr>
    <tr><td><b>1. వివరాలు పంపండి</b></td>
        <td><a href="mailto:{email}?subject=Ad%20Booking&body=Business%20peru:%0APattanam:%0ASlot:%0AKaalapramanam%20(nelalu):%0ABudget:%0ALink:%0ABanner%20image%20attach%20cheyandi:">ఇమెయిల్</a> లేదా
        <a href="{tg}" target="_blank" rel="noopener">Telegram</a> — వ్యాపారం పేరు, పట్టణం, స్లాట్, నెలలు, లింకు, బ్యానర్ ఇమేజ్.</td>
        <td>2 నిమిషాలు</td></tr>
    <tr><td><b>2. ఆమోదం + చెల్లింపు</b></td>
        <td>స్లాట్ ఖాళీగా ఉందో చెప్పి, ఇన్‌వాయిస్ / చెల్లింపు వివరాలు (UPI / బ్యాంకు) పంపుతాము. చెల్లింపు తర్వాత స్లాట్ లాక్.</td>
        <td>1–2 రోజులు</td></tr>
    <tr><td><b>3. ప్రకటన లైవ్</b></td>
        <td>అడ్మిన్ కన్సోల్‌లో యాడ్ యాడ్ చేస్తాము → వెబ్‌సైట్‌లో + తర్వాత రోజుల్లో వచ్చే ఆర్టికల్స్‌లో కనిపిస్తుంది.
        కాలపరిమితి అయ్యాక ఆటోగా ఆగిపోతుంది (ప్రారంభ / ముగింపు తేదీలతో).</td>
        <td>అదే రోజు</td></tr>
  </table>

  <h2>ఏమి పంపాలి (జాబితా)</h2>
  <ul>
    <li>వ్యాపారం / సంస్థ పేరు, లోగో లేదా బ్యానర్ (1200×360 బ్యానర్, 728×90 లీడర్‌బోర్డ్).</li>
    <li>లక్ష్య లింకు (https:// తో) — ల్యాండింగ్ పేజీ, WhatsApp నంబర్ లేదా దరఖాస్తు పేజీ.</li>
    <li>కాలపరిమితి (ప్రారంభ &amp; ముగింపు తేదీలు), స్లాట్(లు), బడ్జెట్.</li>
    <li>ఏమి చెబుతున్నారో ఒక్క లైన్ (మా బ్యాచ్‌లు · స్కాలర్‌షిప్ సహాయం · హాస్టల్ సౌకర్యం …).</li>
  </ul>

  <h2>ఏవి తీసుకోము (విధానం)</h2>
  <ul>
    <li>క్లిక్‌బైట్, మోసపూరిత ఆఫర్లు, "ఉద్యోగం ఖాయం / ర్యాంకు ఖాయం" అనే వాగ్దానాలు — <b>తీసుకోము</b>.</li>
    <li>నకిలీ క్లిక్‌లు, పాపప్ / ఇంటర్‌స్టిషియల్, ఆటో-రీడైరెక్ట్, పెద్దవాళ్లు / జూదం / అప్పుల యాప్‌లు — <b>బ్లాక్</b>.</li>
    <li>చెల్లింపు తర్వాతే ప్రకటన పెడతాము; రిఫండ్: ప్రకటన మొదలుకాకముందు రద్దు చేస్తే పూర్తి రిఫండ్.</li>
  </ul>

  <h2>StudentUp సొంత ప్రకటనలు (హౌస్ యాడ్స్)</h2>
  <p>స్లాట్ ఖాళీగా ఉంటే, మీ ప్రకటన వచ్చేవరకు <b>StudentUp సొంత సేవలు</b>
  (క్విజ్, పరీక్షల పోర్టల్, దరఖాస్తు సహాయం) కనిపిస్తాయి — అవి SPONSORED కావు,
  "StudentUp · మా సేవ" అని వేరుగా లేబుల్ చేయబడతాయి. అంటే: <b>స్లాట్ ఎప్పుడూ ఖాళీగా కనిపించదు</b>,
  కానీ మీ పెయిడ్ యాడ్ ఉంటే అదే ముందు వస్తుంది (రొటేషన్ + ప్రాధాన్యత).</p>

  <div class="note warn"><b>నిజాయితీగా చెబుతున్నాం:</b> ర్యాంకింగ్, ట్రాఫిక్ లేదా ఆదాయానికి మేము హామీ
  ఇవ్వము. మీకు ఇంప్రెషన్స్, క్లిక్‌లు, ఎలా కనిపిస్తున్నది అన్న నిజమైన సంఖ్యలు మాత్రమే ఇస్తాము. Google
  AdSense ఆమోదం తర్వాత ఈ స్లాట్‌లు AdSense పరిమితులకు అనుగుణంగా ఉంటాయి.</div>

  <p><a class="cta" href="mailto:{email}?subject=Ad%20Booking">📧 స్లాట్ బుక్ చేయండి</a>
     <a class="cta alt" href="{tg}" target="_blank" rel="noopener">💬 Telegram లో మాట్లాడండి</a></p>
'''

PAGE_DEFS = [
    ("advertise", "ప్రకటనలు ఇవ్వండి",
     "studentup.in lo ప్రకటనలు: leaderboard, in-feed, mid-article, sidebar slots — telangana & andhra students audience ki. Rate card, booking process, policy.",
     "ప్రకటనలు ఇవ్వండి (Advertise)", "మీ కళాశాల · షాప్ · కోచింగ్ · సేవలు — విద్యార్థుల దృష్టికి చేరండి", ADVERTISE),
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
Disallow: /legacy-concept.html
Disallow: /ads-preview.html
Disallow: /admin

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


def write_ads_txt() -> str:
    """preview/ads.txt — live publisher line (approval tarvata) leda honest placeholder."""
    pub = _adsense_pub_id()
    if pub:
        text = ADS_TXT_HEADER + f"\ngoogle.com, {pub}, DIRECT, f08c47fec0942fa0\n"
        state = "live"
    else:
        text = ADS_TXT_HEADER + "\n# (placeholder — nothing is served until AdSense approval)\n"
        state = "placeholder"
    (OUT / "ads.txt").write_text(text, encoding="utf-8")
    return state

def main() -> None:
    PAGES.mkdir(parents=True, exist_ok=True)
    for slug, title, desc, h1, sub, body in PAGE_DEFS:
        html = build(slug, title, desc, h1, sub, body.replace("{email}", EMAIL).replace("{tg}", TG))
        (PAGES / ("%s.html" % slug)).write_text(html, encoding="utf-8")
        print("  wrote pages/%s.html (%d bytes)" % (slug, len(html)))
    (OUT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    (OUT / "robots.txt").write_text(ROBOTS, encoding="utf-8")
    (OUT / "sitemap.xml").write_text(SITEMAP.format(d=UPDATED), encoding="utf-8")
    ads_state = write_ads_txt()
    print("  wrote favicon.svg · robots.txt · sitemap.xml · ads.txt (%s)" % ads_state)
    print("ALL POLICY PAGES BUILT ✔")


if __name__ == "__main__":
    main()
