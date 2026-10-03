"""v198 — preview TOOLS page (theme-parity, English UI, phone-first).

Owner rule (standing): tools live ONLY here, never on the home page
("e tools em avasaram ledu" on home). v198 ask: "tools and UI advanced ga vundali,
neat ga, phone lo easy ga click vachelaga".

Ee builder theme tho **pin-to-pin** — same classes, same data attributes, same
engine: `wordpress-theme/studentup/assets/js/studentup-tools.js` inline avutundi
(copy kaadu — single source of truth). Anduke preview lo test chesinadi live lo
kuda ade pani chestundi.

8 tools (theme lo unna functions ki mirror):
  salary · age · fee · score · calendar · admit · resume · syllabus
"""
from pathlib import Path
import sys

ROOT = Path("/home/user/Automation_charan1")
sys.path.insert(0, str(ROOT / "tools"))
import build_policy_pages as B  # noqa: E402

OUT = ROOT / "preview" / "tools"
THEME_CSS = "../../wordpress-theme/studentup"
THEME_JS = ROOT / "wordpress-theme" / "studentup" / "assets" / "js" / "studentup-tools.js"

SPRITE = B.SPRITE if hasattr(B, "SPRITE") else ""

# (id, label, icon, cat, keywords, formula, source, body)
TABS = [
    ("salary", "In-hand salary", "wallet", "money",
     "salary in hand pay gross net da hra pay slip 7th cpc",
     "Gross = Basic × (1 + DA% + HRA%); In-hand = Gross − deductions (NPS, tax).",
     "7th CPC fitment table + your department pay slip",
     '''      <div class="su-fields">
        <label>Basic pay (₹)
          <input id="t-basic" type="number" inputmode="numeric" min="0" step="100" value="18000">
        </label>
        <label>DA % (current rate)
          <input id="t-da" type="number" inputmode="numeric" min="0" max="120" step="1" value="55">
        </label>
        <label>HRA % (X / Y / Z city)
          <input id="t-hra" type="number" inputmode="numeric" min="0" max="30" step="1" value="18">
        </label>
        <label>Deductions — NPS + tax (₹)
          <input id="t-ded" type="number" inputmode="numeric" min="0" step="50" value="2200">
        </label>
      </div>
      <p class="su-tout" id="t-salary-out" data-su-result role="status">—</p>
      <p class="su-note">Estimate only — every department pay slip and the 7th CPC fitment change the exact figure.</p>'''),

    ("age", "Age checker", "person", "eligibility",
     "age eligibility dob relaxation obc sc st pwd ex servicemen cutoff",
     "Age is counted on the cutoff date; category relaxation is added to the upper limit.",
     "the notification’s age table (TSPSC/APPSC/SSC)",
     '''      <div class="su-fields">
        <label>Date of birth
          <input id="t-dob" type="date" value="2002-06-15">
        </label>
        <label>As on (cutoff date)
          <input id="t-as" type="date">
        </label>
        <label>Upper limit (years)
          <input id="t-max" type="number" inputmode="numeric" min="18" max="60" value="27">
        </label>
        <label>Relaxation (years)
          <input id="t-relax" type="number" inputmode="numeric" min="0" max="15" value="0">
        </label>
      </div>
      <p class="su-tout" id="t-age-out" data-su-result role="status">—</p>
      <p class="su-note">Age is calculated on the “crucial date” printed in the notification — that is exactly what this does.</p>'''),

    ("fee", "Fee &amp; concession", "tag", "money",
     "fee application fee concession sc st obc ews payment challan",
     "Payable = base fee × category share; exemptions are shown as ₹0.",
     "the official notification fee table",
     '''      <div class="su-fields">
        <label>Application fee (₹)
          <input id="t-fee" type="number" inputmode="numeric" min="0" step="50" value="200">
        </label>
        <label>Your category
          <select id="t-cat">
            <option value="100">General / OBC (full fee)</option>
            <option value="0">SC / ST (exempt)</option>
            <option value="60">BC / PH (usually reduced)</option>
            <option value="0">Women (exempt in many notifications)</option>
          </select>
        </label>
      </div>
      <p class="su-tout" id="t-fee-out" data-su-result role="status">—</p>
      <p class="su-note">The concession percentage changes per exam — confirm it in the notification.</p>'''),

    ("score", "Score &amp; negative", "chart", "exams",
     "score marks negative marking answer key expected cutoff",
     "Marks = correct − (wrong × negative mark per question).",
     "the exam’s marking scheme",
     '''      <div class="su-fields">
        <label>Total questions
          <input id="t-total" type="number" inputmode="numeric" min="1" max="250" value="100">
        </label>
        <label>Correct answers
          <input id="t-right" type="number" inputmode="numeric" min="0" value="72">
        </label>
        <label>Wrong answers
          <input id="t-wrong" type="number" inputmode="numeric" min="0" value="14">
        </label>
        <label>Negative mark (per wrong)
          <input id="t-neg" type="number" inputmode="decimal" min="0" max="1" step="0.05" value="0.25">
        </label>
      </div>
      <p class="su-tout" id="t-score-out" data-su-result role="status">—</p>
      <p class="su-note">TSPSC / SSC negative-marking pattern is printed in the notification — use that value.</p>'''),

    ("calendar", "Last-date calendar", "calendar", "deadlines",
     "last date deadline calendar reminder exam date",
     "Only confirmed dates from published posts are listed; nothing is estimated.",
     "every post’s verified last-date field",
     '''      <ul class="su-mini" id="t-cal-list">
        <li><i>·</i> <span><b>28 Oct</b> — UPSC Junior Assistant 2026 (last date)</span></li>
        <li><i>·</i> <span><b>05 Nov</b> — Engineering internships 2026</span></li>
        <li><i>·</i> <span><b>18 Nov</b> — TSPSC Group-2 application window</span></li>
        <li><i>·</i> <span><b>22 Nov</b> — SSC CHSL tier-1 exam date</span></li>
      </ul>
      <p class="su-tout" id="t-cal-out" data-su-result role="status">Next confirmed last date: 28 Oct (12 days)</p>
      <p class="su-note">Live site: every date comes from the post itself, and one tap adds all of them to your phone calendar (.ics).</p>
      <p><a class="su-cta" href="../pages/exam-calendar.html">Open the full calendar + .ics export</a></p>'''),

    ("admit", "Admit card helper", "ticket", "exams",
     "admit card hall ticket download centre instructions",
     "Checklist follows the standard hall-ticket instructions.",
     "the exam authority’s instruction sheet",
     '''      <div class="su-fields">
        <label>Exam
          <select id="t-admit-exam">
            <option>SSC CGL 2026 Tier-1</option>
            <option>TSPSC Group-2</option>
            <option>RRB NTPC CBT-1</option>
          </select>
        </label>
      </div>
      <ul class="su-mini" id="t-admit-list">
        <li><label><input type="checkbox" id="t-ad-1"> Printed hall ticket (2 copies)</label></li>
        <li><label><input type="checkbox" id="t-ad-2"> Photo ID original + photocopy</label></li>
        <li><label><input type="checkbox" id="t-ad-3"> Passport photo (same as uploaded)</label></li>
        <li><label><input type="checkbox" id="t-ad-4"> Ballpoint pen + transparent water bottle</label></li>
        <li><label><input type="checkbox" id="t-ad-5"> Report 90 minutes before gate closes</label></li>
      </ul>
      <p class="su-tout" id="t-admit-out" data-su-result role="status">0 of 5 ready</p>
      <p class="su-note">Tick boxes as you pack — the progress line updates instantly and stays on this device only.</p>'''),

    ("resume", "Resume maker", "doc", "career",
     "resume cv bio data government format application",
     "Fields fill a plain government-format summary — no account, nothing stored.",
     "standard government application format",
     '''      <div class="su-fields">
        <label>Name
          <input id="t-res-name" type="text" value="Ravi Kumar" autocomplete="name">
        </label>
        <label>Phone
          <input id="t-res-phone" type="tel" inputmode="tel" value="9xxxxxxxxx" autocomplete="tel">
        </label>
        <label>Qualification
          <select id="t-res-qual">
            <option>B.Com (2024)</option>
            <option>B.Tech CSE (2024)</option>
            <option>Intermediate (2023)</option>
            <option>Any degree</option>
          </select>
        </label>
        <label>Applying for
          <input id="t-res-post" type="text" value="Junior Assistant">
        </label>
      </div>
      <button type="button" class="su-tact su-tact-copy" id="t-res-go">Generate summary</button>
      <p class="su-tout" id="t-res-out" data-su-result role="status">—</p>
      <p class="su-note">Copy the summary into any government application form. Nothing leaves your phone.</p>'''),

    ("syllabus", "Syllabus tracker", "book", "career",
     "syllabus tracker preparation progress subjects revision",
     "Progress = ticked subjects ÷ total subjects.",
     "the exam’s official syllabus",
     '''      <ul class="su-mini" id="t-syl-list">
        <li><label><input type="checkbox" id="t-sy-1"> Current affairs &amp; GK</label></li>
        <li><label><input type="checkbox" id="t-sy-2"> Arithmetic &amp; reasoning</label></li>
        <li><label><input type="checkbox" id="t-sy-3"> Telangana movement &amp; history</label></li>
        <li><label><input type="checkbox" id="t-sy-4"> Polity &amp; constitution</label></li>
        <li><label><input type="checkbox" id="t-sy-5"> English language</label></li>
        <li><label><input type="checkbox" id="t-sy-6"> Telugu language</label></li>
      </ul>
      <p class="su-tout" id="t-syl-out" data-su-result role="status">0 of 6 subjects done (0%)</p>
      <p class="su-note">Your ticks stay in this browser (localStorage) — no account, no upload.</p>'''),
]

PAGE = '''<!DOCTYPE html>
<html lang="en" data-su-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Free student tools — salary · age · fee · score · studentup.in</title>
<meta name="description" content="Free government-job tools for TS &amp; AP students: in-hand salary estimate, age eligibility, fee concession, score with negative marking, admit-card checklist, resume summary and syllabus tracker.">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<meta name="theme-color" content="#0b2447">
<link rel="canonical" href="https://studentup.in/tools/">
<link rel="icon" href="../favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:title" content="Free student tools · studentup.in">
<meta property="og:locale" content="te_IN">
<meta property="og:image" content="https://studentup.in/logo.png">
<meta property="og:url" content="https://studentup.in/tools/">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{"@context":"https://schema.org","@type":"WebPage","name":"Free student tools","inLanguage":"en-IN",
"url":"https://studentup.in/tools/","isPartOf":{"@type":"WebSite","name":"studentup.in","url":"https://studentup.in/"}}
</script>
<link rel="stylesheet" href="''' + THEME_CSS + '''/style.css">
<link rel="stylesheet" href="''' + THEME_CSS + '''/assets/css/worldclass.css">
</head>
<body>
''' + SPRITE + '''
<!--HEADER-->
<main id="main">
  <div class="wrap">
    <nav class="crumbs" aria-label="Breadcrumb"><a href="../worldclass/index.html">Home</a> › Tools</nav>
    <div class="sectionhead">
      <div><h1>Free tools for students</h1><p>Salary, age, fee, score, deadlines, admit card, resume and syllabus — one tool at a time, everything works on the phone.</p></div>
      <a class="su-viewall" href="../worldclass/index.html#jobs">Go to job board →</a>
    </div>

    <section class="su-tools" id="tools" data-su-tools aria-label="Free tools for students">
      <noscript><style>.su-toolpanel[hidden]{display:block!important}.su-tooltabs,.su-toolcats,.su-toolfind,.su-tools-top{display:none!important}</style></noscript>
      <div class="su-tools-head">
        <div class="sectionhead" style="margin:0 0 6px">
          <div><h2>8 tools, one clean card</h2><p>Search or tap a tab — one tool at a time keeps the screen readable.</p></div>
        </div>

        <div class="su-toolfind">
          <label class="screen-reader-text" for="su-tool-search">Search tools</label>
          <span class="su-toolfind-ic" aria-hidden="true"><!--SEARCHICON--></span>
          <input id="su-tool-search" type="search" data-su-tool-find autocomplete="off" enterkeyhint="search"
            placeholder="Search a tool — salary, age, fee, resume…">
          <button type="button" class="su-toolfind-clear" data-su-tool-clear hidden aria-label="Clear search">✕</button>
        </div>

        <div class="su-toolcats" role="group" aria-label="Filter tools by category">
<!--CHIPS-->
        </div>
        <p class="su-toolfind-none" data-su-tool-none hidden>No tool matches “<span data-su-tool-q></span>”. Try “salary”, “age” or “resume”.</p>
      </div>

      <div class="su-tooltabs" role="tablist" aria-label="Student tools" data-su-tool-strip>
<!--TABBUTTONS-->
      </div>

      <div class="su-toolpanels" data-su-tool-swipe>
<!--PANELS-->
      </div>

      <button type="button" class="su-tools-top" data-su-tool-top hidden>↑ Back to tools</button>
    </section>

    <div class="su-adbelow" aria-label="Advertisement" style="margin-top:22px">
      Advertisement · below tools
      <small>Tools page = high-intent students (highest RPM pages)</small>
    </div>
  </div>
</main>
<!--FOOTERBAR-->
<!--BOTTOMNAV-->
<!--PAGEJS-->
<script>
/* v198 preview calculators — same maths as the theme's tool modules. */
(function(){
  var S = function(id){ return document.getElementById(id); };
  var num = function(id){ var v = parseFloat((S(id)||{}).value || 0); return isNaN(v) ? 0 : v; };
  var set = function(id, txt){ var el = S(id); if(el) el.textContent = txt; };
  var inr = function(v){ return '\\u20b9' + Math.round(v).toLocaleString('en-IN'); };

  function salary(){
    if(!S('t-basic')) return;
    var basic = num('t-basic'), gross = basic * (1 + num('t-da')/100 + num('t-hra')/100);
    set('t-salary-out', 'Gross ' + inr(gross) + ' / month  ·  In-hand approx ' + inr(gross - num('t-ded')) + ' / month');
  }
  function age(){
    if(!S('t-dob')) return;
    var dob = new Date(S('t-dob').value);
    var asOn = S('t-as').value ? new Date(S('t-as').value) : new Date();
    if(!S('t-as').value) S('t-as').value = asOn.toISOString().slice(0,10);
    if(isNaN(dob)) { set('t-age-out', 'Enter your date of birth'); return; }
    var y = asOn.getFullYear() - dob.getFullYear();
    var m = asOn.getMonth() - dob.getMonth();
    if(m < 0 || (m === 0 && asOn.getDate() < dob.getDate())) y--;
    var limit = num('t-max') + num('t-relax');
    var ok = y <= limit && y >= 18;
    set('t-age-out', 'Your age is ' + y + ' years (limit ' + limit + ') — ' +
      (ok ? 'eligible \\u2714 you can apply' : 'not eligible \\u2716 (limit crossed)'));
  }
  function score(){
    if(!S('t-total')) return;
    var marks = num('t-right') - (num('t-wrong') * num('t-neg'));
    var left = num('t-total') - num('t-right') - num('t-wrong');
    set('t-score-out', 'Score approx ' + marks.toFixed(2) + ' / ' + num('t-total') +
      '  ·  attempted ' + (num('t-right') + num('t-wrong')) + ' · left ' + (left < 0 ? 0 : left));
  }
  function fee(){
    if(!S('t-fee')) return;
    var pct = parseFloat((S('t-cat')||{}).value || 0);
    var pay = num('t-fee') * pct / 100;
    set('t-fee-out', 'You pay approx ' + inr(pay) +
      (pct === 0 ? ' (full exemption)' : ' (' + pct + '% of ' + inr(num('t-fee')) + ')'));
  }
  function admit(){
    var ids = ['t-ad-1','t-ad-2','t-ad-3','t-ad-4','t-ad-5'], done = 0;
    ids.forEach(function(id){ var el = S(id); if(el && el.checked) done++; });
    var exam = (S('t-admit-exam')||{}).value || 'your exam';
    set('t-admit-out', done + ' of 5 ready — ' + exam + (done === 5 ? ' \\u2714 packed, go score.' : ''));
  }
  function resume(){
    var name = (S('t-res-name')||{}).value || '';
    var phone = (S('t-res-phone')||{}).value || '';
    var qual = (S('t-res-qual')||{}).value || '';
    var post = (S('t-res-post')||{}).value || '';
    set('t-res-out', name + ' · ' + phone + ' — ' + qual + ', applying for ' + post +
      '. Studied from official notifications on StudentUp (studentup.in); available for joining immediately.');
  }
  function syllabus(){
    var ids = ['t-sy-1','t-sy-2','t-sy-3','t-sy-4','t-sy-5','t-sy-6'], done = 0;
    ids.forEach(function(id){ var el = S(id); if(el && el.checked) done++; });
    var pct = Math.round(done / ids.length * 100);
    set('t-syl-out', done + ' of ' + ids.length + ' subjects done (' + pct + '%)');
  }

  var WIRE = {
    salary: ['t-basic','t-da','t-hra','t-ded'],
    age: ['t-dob','t-as','t-max','t-relax'],
    score: ['t-total','t-right','t-wrong','t-neg'],
    fee: ['t-fee','t-cat'],
    admit: ['t-ad-1','t-ad-2','t-ad-3','t-ad-4','t-ad-5','t-admit-exam'],
    resume: ['t-res-name','t-res-phone','t-res-qual','t-res-post'],
    syllabus: ['t-sy-1','t-sy-2','t-sy-3','t-sy-4','t-sy-5','t-sy-6']
  };
  var FN = { salary: salary, age: age, score: score, fee: fee, admit: admit,
             resume: resume, syllabus: syllabus };
  Object.keys(WIRE).forEach(function(k){
    WIRE[k].forEach(function(id){
      var el = S(id);
      if(!el) return;
      el.addEventListener('change', FN[k]);
      el.addEventListener('input', FN[k]);
    });
  });
  var go = S('t-res-go'); if(go) go.addEventListener('click', resume);
  Object.keys(FN).forEach(function(k){ FN[k](); });
})();
</script>
'''


def icon(name, size=16):
    return (f'<svg class="su-uicon su-uicon-{name}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-{name}"/></svg>')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # tab strip
    buttons = []
    for i, (tid, label, ic, _cat, _keys, _f, _s, _b) in enumerate(TABS):
        buttons.append(
            f'        <button type="button" class="su-ttab{" active" if i == 0 else ""}" role="tab" '
            f'id="su-ttab-{tid}" aria-controls="su-tool-{tid}" aria-selected="{"true" if i == 0 else "false"}" '
            f'tabindex="{"0" if i == 0 else "-1"}" data-su-cat="{_cat}" data-su-keywords="{_keys}">'
            f'{icon(ic)} <span>{label}</span></button>')

    # category chips (same contract as the theme; counts computed from TABS)
    cats = [("all", "All tools"), ("money", "Money"), ("eligibility", "Eligibility"),
            ("exams", "Exams"), ("career", "Career"), ("deadlines", "Deadlines")]
    chips = []
    for cid, clabel in cats:
        n = len(TABS) if cid == "all" else sum(1 for t in TABS if t[3] == cid)
        if cid != "all" and not n:
            continue
        on = " on" if cid == "all" else ""
        chips.append(f'          <button type="button" class="su-tcat{on}" data-su-tool-cat="{cid}" '
                     f'aria-pressed="{"true" if cid == "all" else "false"}">{clabel} <b>{n}</b></button>')

    # panels
    panels = []
    for i, (tid, label, ic, _cat, _keys, formula, source, body) in enumerate(TABS):
        on = " on" if i == 0 else ""
        panels.append(
            f'      <div class="su-toolpanel{on}" id="su-tool-{tid}" role="tabpanel"\n'
            f'        aria-labelledby="su-ttab-{tid}"\n'
            f'        data-su-formula="{formula}"\n'
            f'        data-su-source="{source}"{" hidden" if i else ""}>\n'
            f'        <h3>{label}</h3>\n{body}\n'
            f'        <div class="su-tool-nav">\n'
            f'          <button type="button" class="su-tnext" data-su-next>'
            f'{icon("arrow", 15)} Next tool</button>\n'
            f'        </div>\n'
            f'      </div>')

    engine = THEME_JS.read_text(encoding="utf-8") if THEME_JS.exists() else ""
    html = (PAGE
            .replace("<!--SEARCHICON-->", icon("search", 17))
            .replace("<!--CHIPS-->", "\n".join(chips))
            .replace("<!--HEADER-->", B.header_html(topbar="Government jobs \u00b7 exams \u00b7 scholarships"))
            .replace("<!--FOOTERBAR-->", B.footer_html(pfx="../pages/"))
            .replace("<!--BOTTOMNAV-->", B.bottom_html())
            .replace("<!--PAGEJS-->", B.PAGE_JS)
            .replace("<!--TABBUTTONS-->", "\n".join(buttons))
            .replace("<!--PANELS-->", "\n".join(panels))
            + "\n<!-- tools engine: theme file inline (single source of truth) -->\n<script>\n"
            + engine + "\n</script>\n</body>\n</html>\n")
    out = OUT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  wrote tools/index.html ({len(html.encode())} bytes · {len(TABS)} tools · engine {len(engine.encode())} B)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
