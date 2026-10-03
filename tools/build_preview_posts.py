"""v193c — generate the two preview ARTICLE pages in the new design.

Structure mirrors the WP theme's single.php exactly:
  su-layout → su-main (breadcrumbs · article-head · su-hook · article-content ·
  in-article ad · related grid) + su-sidebar (sticky 300×250 + Top-5 + sponsor).
That is the same 2-column, sticky-sidebar layout §19 ships in the theme.
"""
from pathlib import Path
import sys

ROOT = Path("/home/user/Automation_charan1")
sys.path.insert(0, str(ROOT / "tools"))
import build_policy_pages as B  # noqa: E402

OUT = ROOT / "preview" / "posts"
THEME_CSS = "../../wordpress-theme/studentup"
SPRITE = ('<svg style="display:none" aria-hidden="true" focusable="false">'
          '<symbol id="su-i-sun" viewBox="0 0 24 24"><path d="M12 7a5 5 0 1 0 0 10 5 5 0 0 0 0-10Z"/></symbol>'
          '<symbol id="su-i-moon" viewBox="0 0 24 24"><path d="M12 3a9 9 0 1 0 9 9 7.2 7.2 0 0 1-9-9Z"/></symbol>'
          '<symbol id="su-i-home" viewBox="0 0 24 24"><path d="M3 10.5 12 3l9 7.5V21H3z"/></symbol>'
          '<symbol id="su-i-work" viewBox="0 0 24 24"><path d="M3 7h18v13H3zM9 7V5h6v2"/></symbol>'
          '<symbol id="su-i-chart" viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h10"/></symbol>'
          '<symbol id="su-i-bell" viewBox="0 0 24 24"><path d="M12 3a6 6 0 0 0-6 6v3l-2 3h16l-2-3V9a6 6 0 0 0-6-6Zm-2 15a2 2 0 0 0 4 0"/></symbol>'
          '<symbol id="su-i-clock" viewBox="0 0 24 24"><path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm1 11h-2V7h2v6Z"/></symbol>'
          '<symbol id="su-i-check" viewBox="0 0 24 24"><path d="M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4L9 16.2Z"/></symbol>'
          "</svg>")


def cover(label, accent):
    words = label.replace("-", " ").split()
    mono = (words[0][:3] if words and len(words[0]) <= 3 else (words[0][:2] if words else "SU")).upper()
    return (f'<a class="thumb thumb--auto" href="../worldclass/index.html#jobs" aria-hidden="true" tabindex="-1" data-accent="{accent}">'
            f'<span class="su-cov"><b class="su-cov-mono">{mono}</b>'
            f'<span class="su-cov-cat">{label}</span><span class="su-cov-brand">StudentUp</span></span></a>')


def card(title, label, accent, ago, read, last="", href="../worldclass/index.html#jobs"):
    last_html = f'<span class="lastdate">{last}</span>' if last else ""
    return f'''<article class="news" data-accent="{accent}" data-su-card data-cat="{accent}">
  {cover(label, accent)}
  <div class="newsbody">
    <div class="tagrow"><span class="tag">{label}</span><span class="statechip">{ago}</span></div>
    <h3><a href="{href}">{title}</a></h3>
    <div class="newsfoot"><span>{read}</span>{last_html}<a class="su-readmore" href="{href}">Read more →</a></div>
  </div>
</article>'''


def sidebar(top, closing):
    tops = "".join(f'<li><a href="../worldclass/index.html#jobs"><i>{i+1}</i> {t}</a></li>' for i, t in enumerate(top))
    clos = "".join(f'<li><a href="../worldclass/index.html#jobs"><i>⏰</i> {c}</a></li>' for c in closing)
    return f'''<aside class="su-sidebar" aria-label="Sidebar">
  <div class="su-sidebar-ad" aria-label="Advertisement">Advertisement · 300×250</div>
  <div class="sidecard"><h3>Top jobs this week</h3><ul class="su-mini">{tops}</ul></div>
  <div class="sidecard"><h3>Closing this week</h3><ul class="su-mini">{clos}</ul></div>
  <div class="sidecard" style="background:linear-gradient(135deg,#0b2447,#164b8f);border:0;color:#fff">
    <h3 style="color:#fff">Sponsor slot</h3>
    <p style="margin:0 0 10px;font-size:13.5px;color:#d7e6ff">Coaching institutes / books — native card on every article.</p>
    <a class="su-cta" href="../pages/advertise.html" style="width:100%">Advertise here</a>
  </div>
</aside>'''


PAGE = '''<!DOCTYPE html>
<html lang="te" data-su-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>{title} · studentup.in</title>
<meta name="description" content="{desc}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0b2447">
<link rel="canonical" href="https://studentup.in/posts/{slug}.html">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<meta property="og:type" content="article">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:locale" content="te_IN">
<meta property="og:image" content="https://studentup.in/logo.png">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{title}","inLanguage":"te-IN",
"datePublished":"{date}","dateModified":"{updated}","articleSection":"{label}",
"author":{{"@type":"Organization","name":"StudentUp Editorial Team"}},
"publisher":{{"@type":"Organization","name":"studentup.in","url":"https://studentup.in/"}},
"mainEntityOfPage":{{"@type":"WebPage","@id":"https://studentup.in/posts/{slug}.html"}},
"description":"{desc}"}}
</script>
<link rel="stylesheet" href="''' + THEME_CSS + '''/style.css">
<link rel="stylesheet" href="''' + THEME_CSS + '''/assets/css/worldclass.css">
</head>
<body class="single">
''' + SPRITE + '''
{header}
<main id="main">
  <div class="wrap">
    <div class="su-layout">
      <div class="su-main">
        <nav class="crumbs" aria-label="Breadcrumb"><a href="../worldclass/index.html">Home</a> › <a href="../worldclass/index.html#jobs">{label}</a> › {short}</nav>

        <article class="article">
          <div class="article-head">
            <h1>{title}</h1>
            <div class="article-meta">
              <span class="su-am"><svg class="su-uicon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><use href="#su-i-clock"/></svg> {date_te}</span>
              <span class="su-am"><svg class="su-uicon" width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><use href="#su-i-check"/></svg> Official notification నుంచి చెక్ చేశాం</span>
              <span class="su-am">{read} చదువు</span>
            </div>
          </div>

          <p class="su-hook">{hook}</p>

          <div class="su-adleader" aria-label="Advertisement">
            Advertisement · in-article top (highest viewability)
            <small>Height reserved — no layout shift</small>
          </div>

          <div class="article-content" id="su-details">
{body}
          </div>

          <div class="su-adbelow" aria-label="Advertisement">
            Advertisement · end of article
            <small>Readers who finished convert best</small>
          </div>

          <div class="sectionhead"><div><h2>ఇవి కూడా చూడండి</h2><p>Same category · latest updates</p></div>
            <a class="su-viewall" href="../worldclass/index.html#jobs">All updates →</a></div>
          <div class="newsgrid" style="margin-bottom:6px">
{related}
          </div>

          <p class="su-hook" style="margin-top:18px">ముఖ్య గమనిక: తుది నిర్ణయం ఎప్పుడూ <b>అఫీషియల్ నోటిఫికేషన్</b> దే. ఇది విద్యార్థుల కోసం చేసిన సమాచారం మాత్రమే — StudentUp ప్రభుత్వ వెబ్‌సైట్ కాదు.</p>
        </article>
      </div>
{sidebar}
    </div>
  </div>
</main>
{footerbar}
{bottomnav}
{pagejs}
</body>
</html>
'''

POSTS = [
    dict(
        slug="upsc-junior-assistant-2026", label="Central Govt", accent="central",
        title="SSC CHSL 2026 Notification — 3,712 Posts, Apply Online",
        short="SSC CHSL 2026", date="2026-09-28", updated="2026-10-03", date_te="28 Sep 2026",
        read="3 నిమిషాల", desc="SSC CHSL 2026 notification — 3,712 posts, 10th/Inter eligibility, fee, important dates and the official apply link.",
        hook="SSC CHSL 2026 నోటిఫికేషన్ విడుదల అయింది — మొత్తం 3,712 పోస్టులు. 10వ తరగతి / ఇంటర్ పాస్ విద్యార్థులు అప్లై చేసుకోవచ్చు. దరఖాస్తు చివరి తేదీ 28 అక్టోబర్.",
        body='''            <h2>ముఖ్య వివరాలు (ఒక్క చూపులో)</h2>
            <table>
              <tr><th>నోటిఫికేషన్</th><td>SSC CHSL 2026 (Combined Higher Secondary Level)</td></tr>
              <tr><th>మొత్తం పోస్టులు</th><td>3,712</td></tr>
              <tr><th>అర్హత</th><td>10వ తరగతి (LDC/JSA) · ఇంటర్ (DEO)</td></tr>
              <tr><th>వయస్సు</th><td>18 – 27 సంవత్సరాలు (రిజర్వేషన్ ప్రకారం సడలింపు)</td></tr>
              <tr><th>దరఖాస్తు చివరి తేదీ</th><td>28 అక్టోబర్ 2026</td></tr>
              <tr><th>పరీక్ష</th><td>Tier-1: ఆగస్టు 2026 (CBT)</td></tr>
              <tr><th>ఫీసు</th><td>₹100 (SC/ST/PwD/మహిళలకు మినహాయింపు)</td></tr>
            </table>

            <h2>ఎవరు అప్లై చేయవచ్చు?</h2>
            <ul>
              <li><b>LDC / JSA / DEO పోస్టులకు:</b> ఏదైనా గుర్తింపు పొందిన బోర్డు నుంచి 10వ తరగతి లేదా ఇంటర్ పాస్.</li>
              <li><b>DEO పోస్టులకు:</b> ఇంటర్ పాస్ (12th) తప్పనిసరి.</li>
              <li>భారత పౌరులు మాత్రమే — TS / AP విద్యార్థులు అందరూ అర్హులే.</li>
            </ul>

            <h2>అప్లై ఎలా చేయాలి? (దశలు)</h2>
            <ol>
              <li>SSC అధికారిక పోర్టల్ <b>ssc.gov.in</b> తెరవండి → “Apply Online”.</li>
              <li>మొదటి సారి అయితే <b>One-Time Registration (OTR)</b> పూర్తి చేయండి — ఆధార్, ఫోటో, సంతకం అవసరం.</li>
              <li>ఫోటో (20–50 KB) మరియు సంతకం (10–20 KB) JPEG లో ముందే సిద్ధం చేసుకోండి.</li>
              <li>ఫీసు ఆన్‌లైన్‌లో చెల్లించి, దరఖాస్తును <b>submit</b> చేయండి.</li>
              <li>Submit అయిన తర్వాత <b>PDF ప్రింట్ తీసుకోండి</b> — ఇదే మీ రసీదు.</li>
            </ol>

            <h2>తరచుగా అడిగే ప్రశ్నలు</h2>
            <h3>10వ తరగతితో DEO కి అప్లై చేయవచ్చా?</h3>
            <p>లేదు. DEO కోసం ఇంటర్ పాస్ తప్పనిసరి. 10వ తరగతి ఉన్నవారు LDC / JSA కి అప్లై చేయవచ్చు.</p>
            <h3>ఫీసు తిరిగి వస్తుందా?</h3>
            <p>చెల్లించిన ఫీసు సాధారణంగా తిరిగి రాదు. పరీక్షకు హాజరుకాని వారికీ రీఫండ్ ఉండదు.</p>
            <h3>అధికారిక లింక్ ఏది?</h3>
            <p>దరఖాస్తు ఎప్పుడూ అధికారిక పోర్టల్‌లోనే చేయండి. థర్డ్-పార్టీ లింక్‌లకు ఫీసు చెల్లించకండి.</p>

            <h2>జాగ్రత్తగా గమనించాల్సినవి</h2>
            <ul>
              <li>ఇంటర్నెట్ కేఫేలో అప్లై చేస్తే, <b>logout</b> తప్పకుండా చేయండి.</li>
              <li>ఒకే రిజిస్ట్రేషన్‌తో రెండు దరఖాస్తులు వేయకండి — రద్దు అవుతుంది.</li>
              <li>లాస్ట్ డేట్ రోజు సర్వర్ స్లో ఉంటుంది → 2–3 రోజుల ముందే పూర్తి చేయండి.</li>
            </ul>''',
        related=[
            ("RRB NTPC 2026 — 11,558 Posts, 10th / Inter / Degree", "Central", "central", "4 hrs ago", "5 నిమిషాల", "⏳ Last date 18 Nov"),
            ("Post Office GDS 2026 — 21,413 Posts, 10th Pass", "TS Jobs", "ts", "10 hrs ago", "3 నిమిషాల", "⏳ Last date 30 Nov"),
            ("SSC GD Constable 2026 — 39,481 Posts, 10th Pass", "Central", "central", "12 hrs ago", "4 నిమిషాల", "⏳ Last date 12 Dec"),
        ],
        top=["SSC CHSL 2026 — 3,712 posts", "RRB NTPC — 11,558 posts", "AP Police Constable — 6,100 posts",
             "TSPSC Group 2 — 783 posts", "Post Office GDS — 21,413 posts"],
        closing=["SSC CHSL — 28 Oct", "TSPSC Group 2 — 05 Nov", "IBPS Clerk — 05 Nov"],
    ),
    dict(
        slug="engineering-internships-2026", label="TS Jobs", accent="ts",
        title="TSPSC Group 2 Recruitment 2026 — 783 Vacancies, Degree Pass",
        short="TSPSC Group 2", date="2026-09-30", updated="2026-10-03", date_te="30 Sep 2026",
        read="4 నిమిషాల", desc="TSPSC Group 2 2026 — 783 vacancies, degree eligibility, fee ₹200, age 18–44, online application reopened for leftover posts.",
        hook="TSPSC Group 2 నోటిఫికేషన్‌లో మిగిలిన పోస్టులకు ఆన్‌లైన్ దరఖాస్తు మళ్లీ ప్రారంభమైంది — మొత్తం 783 పోస్టులు. ఏదైనా డిగ్రీ పాస్ చాలు, వయస్సు 18–44.",
        body='''            <h2>ముఖ్య వివరాలు</h2>
            <table>
              <tr><th>నోటిఫికేషన్</th><td>TSPSC Group 2 (Services) 2026</td></tr>
              <tr><th>పోస్టులు</th><td>783 (మిగిలిన పోస్టులకు దరఖాస్తు రీఓపెన్)</td></tr>
              <tr><th>అర్హత</th><td>ఏదైనా డిగ్రీ (Recognised University)</td></tr>
              <tr><th>వయస్సు</th><td>18 – 44 సంవత్సరాలు</td></tr>
              <tr><th>ఫీసు</th><td>₹200 (SC/ST/BC/PH &amp; దివ్యాంగులకు ₹120)</td></tr>
              <tr><th>సెలెక్షన్</th><td>Written (Computer Based Test) → Certificate Verification</td></tr>
              <tr><th>దరఖాస్తు చివరి తేదీ</th><td>05 నవంబర్ 2026</td></tr>
            </table>

            <h2>మిగిలిన పోస్టులు ఎక్కడ చూడాలి?</h2>
            <p>ఏ పోస్టులు మిగిలాయో అధికారిక పోర్టల్‌లో <b>“Reopened posts”</b> లిస్ట్‌లో ఉంటుంది. దరఖాస్తు చేసే ముందు మీ qualification ఆ పోస్టుకు సరిపోతుందా చూసుకోండి.</p>

            <h2>అప్లై చేసే ముందు చెక్‌లిస్ట్</h2>
            <ul>
              <li>డిగ్రీ మార్క్‌షీట్ + ప్రొవిజనల్ సర్టిఫికెట్ స్కాన్.</li>
              <li>ఆధార్ / ఓటర్ కార్డ్ / రేషన్ కార్డ్ (గుర్తింపు కోసం).</li>
              <li>Caste certificate (BC/SC/ST అయితే ఫీసు మినహాయింపు కోసం).</li>
              <li>ఫోటో + సంతకం, స్కేన్ చేసినవి, సైజు లిమిట్ లో.</li>
            </ul>

            <h2>సిలబస్ — ఎక్కడ నుంచి మొదలు పెట్టాలి?</h2>
            <h3>Paper-1: General Studies &amp; Mental Ability</h3>
            <p>తెలంగాణ చరిత్ర, ఉద్యమం, జాతీయ ఉద్యమం, భౌగోళికం, ఆర్థిక శాస్త్రం, సైన్స్, రీజనింగ్.</p>
            <h3>Paper-2: ప్రత్యేక అంశాలు (PDF)</h3>
            <p>మీరు ఎంచుకున్న విభాగం ప్రకారం — ప్రతి విభాగానికి అధికారికంగా సిలబస్ ఇస్తారు. Previous papers తో ప్రాక్టీస్ చేయడం అత్యంత ఉపయోగం.</p>

            <h2>తరచుగా అడిగే ప్రశ్నలు</h2>
            <h3>ఫైనల్ ఇయర్ విద్యార్థులు అప్లై చేయవచ్చా?</h3>
            <p>దరఖాస్తు సమయంలో డిగ్రీ పూర్తి అయి ఉండాలి (లేదా అధికారిక నోటిఫికేషన్‌లో చెప్పిన తేదీ నాటికి).</p>
            <h3>ఫీసు ఎలా చెల్లించాలి?</h3>
            <p>TSPSC పోర్టల్‌లో చూపిన ఆన్‌లైన్ పేమెంట్ (Credit/Debit/Net banking/UPI) ద్వారానే.</p>''',
        related=[
            ("AP Police Constable 2026 — 6,100 Posts, Inter Pass", "AP Jobs", "ap", "6 hrs ago", "4 నిమిషాల", "⏳ Last date 22 Nov"),
            ("APPSC Group 1 2026 — 92 Posts, Any Degree", "AP Jobs", "ap", "1 day ago", "5 నిమిషాల", "⏳ Last date 20 Dec"),
            ("SSC CHSL 2026 — 3,712 Posts, Apply Online", "Central Govt", "central", "12 min ago", "3 నిమిషాల", "⏳ Last date 28 Oct"),
        ],
        top=["SSC CHSL 2026 — 3,712 posts", "RRB NTPC — 11,558 posts", "TSPSC Group 2 — 783 posts",
             "AP Police Constable — 6,100 posts", "Post Office GDS — 21,413 posts"],
        closing=["TSPSC Group 2 — 05 Nov", "IBPS Clerk — 05 Nov", "SSC CHSL — 28 Oct"],
    ),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    for p in POSTS:
        html = PAGE.format(
            slug=p["slug"], title=p["title"], desc=p["desc"], label=p["label"],
            short=p["short"], date=p["date"], updated=p["updated"], date_te=p["date_te"],
            read=p["read"], hook=p["hook"], body=p["body"],
            related="\n".join(card(*r) for r in p["related"]),
            sidebar=sidebar(p["top"], p["closing"]),
            header=B.header_html(topbar="\u0c09\u0c26\u0c4d\u0c2f\u0c4b\u0c17 \u00b7 \u0c2a\u0c30\u0c40\u0c15\u0c4d\u0c37\u0c32\u0c41 \u00b7 \u0c38\u0c4d\u0c15\u0c3e\u0c32\u0c30\u0c4d\u200c\u0c37\u0c3f\u0c2a\u0c4d"), footerbar=B.footer_html(pfx="../pages/"),
            bottomnav=B.bottom_html(), pagejs=B.PAGE_JS,
        )
        out = OUT / (p["slug"] + ".html")
        out.write_text(html, encoding="utf-8")
        print(f"  wrote posts/{out.name} ({len(html.encode())} bytes)")
    print("ALL PREVIEW ARTICLES BUILT ✔")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
