"""v193d — preview TOOLS page (real theme design) — tools live ONLY here, never home.

The demo home has no tools section (owner rule: "e tools em avasram ledu" on home),
so the "Tools" buttons used to point at a dead #tools anchor. This page is the
real target — same shell, same CSS as every other preview page, and every tool
actually works (no fake UI).
"""
from pathlib import Path
import sys

ROOT = Path("/home/user/Automation_charan1")
sys.path.insert(0, str(ROOT / "tools"))
import build_policy_pages as B  # noqa: E402

OUT = ROOT / "preview" / "tools"
THEME_CSS = "../../wordpress-theme/studentup"

SPRITE = B.SPRITE if hasattr(B, "SPRITE") else ""

TABS = [
    ("salary", "In-hand salary", "wallet",
     '''      <div class="su-fields">
        <label>Basic pay (₹)
          <input id="t-basic" type="number" inputmode="numeric" min="0" step="100" value="18000">
        </label>
        <label>DA % (ప్రస్తుతం)
          <input id="t-da" type="number" inputmode="numeric" min="0" step="1" value="55">
        </label>
        <label>HRA % (X / Y / Z city)
          <input id="t-hra" type="number" inputmode="numeric" min="0" step="1" value="18">
        </label>
        <label>Deductions (NPS + tax, ₹)
          <input id="t-ded" type="number" inputmode="numeric" min="0" step="50" value="2200">
        </label>
      </div>
      <p class="su-tout" id="t-salary-out" role="status">—</p>
      <p class="su-note">ఇది అంచనా మాత్రమే. ప్రతి department pay slip + 7th CPC fitment batti మారుతుంది.</p>'''),
    ("age", "Age / eligibility", "person",
     '''      <div class="su-fields">
        <label>పుట్టిన తేదీ
          <input id="t-dob" type="date" value="2002-06-15">
        </label>
        <label>అప్లై చేసే తేదీ (as on)
          <input id="t-as" type="date">
        </label>
        <label>అపర్ లిమిట్ (సంవత్సరాలు)
          <input id="t-max" type="number" inputmode="numeric" min="18" max="60" value="27">
        </label>
        <label>రిజర్వేషన్ సడలింపు (సంవత్సరాలు)
          <input id="t-relax" type="number" inputmode="numeric" min="0" max="15" value="0">
        </label>
      </div>
      <p class="su-tout" id="t-age-out" role="status">—</p>
      <p class="su-note">Age అనేది నోటిఫికేషన్‌లో చెప్పిన “crucial date” నాటికి లెక్కిస్తారు — ఇక్కడ అదే చేస్తుంది.</p>'''),
    ("score", "Score + negative", "chart",
     '''      <div class="su-fields">
        <label>మొత్తం ప్రశ్నలు
          <input id="t-total" type="number" inputmode="numeric" min="1" value="100">
        </label>
        <label>సరైనవి
          <input id="t-right" type="number" inputmode="numeric" min="0" value="72">
        </label>
        <label>తప్పులు
          <input id="t-wrong" type="number" inputmode="numeric" min="0" value="14">
        </label>
        <label>Negative mark (ప్రతి తప్పుకు)
          <input id="t-neg" type="number" inputmode="decimal" min="0" step="0.05" value="0.25">
        </label>
      </div>
      <p class="su-tout" id="t-score-out" role="status">—</p>
      <p class="su-note">TSPSC/SSC exams లో negative marking pattern నోటిఫికేషన్ లో ఉంటుంది — అదే విలువ పెట్టండి.</p>'''),
    ("fee", "Fee + concession", "tag",
     '''      <div class="su-fields">
        <label>అప్లికేషన్ ఫీసు (₹)
          <input id="t-fee" type="number" inputmode="numeric" min="0" value="200">
        </label>
        <label>మీ category
          <select id="t-cat">
            <option value="100">General / OBC (full fee)</option>
            <option value="0">SC / ST (మినహాయింపు)</option>
            <option value="60">BC / PH (సాధారణంగా తక్కువ)</option>
            <option value="0">మహిళ (చాలా నోటిఫికేషన్‌లలో మినహాయింపు)</option>
          </select>
        </label>
      </div>
      <p class="su-tout" id="t-fee-out" role="status">—</p>
      <p class="su-note">Concession శాతం exam-wise మారుతుంది — నోటిఫికేషన్ చదివి confirm చేసుకోండి.</p>'''),
]

PAGE = '''<!DOCTYPE html>
<html lang="te" data-su-theme="light">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Free student tools — salary · age · score · fee · studentup.in</title>
<meta name="description" content="Free government-job tools for TS &amp; AP students: in-hand salary estimate, age eligibility check, exam score with negative marking and fee concession.">
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
{"@context":"https://schema.org","@type":"WebPage","name":"Free student tools","inLanguage":"te-IN",
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
      <div><h1>Free tools for students</h1><p>Salary, age, score, fee — ఒక్కో ట్యాబ్‌లో ఒక్కో టూల్. అన్నీ ఇక్కడే, ఫోన్‌లోనే పనిచేస్తాయి.</p></div>
      <a class="su-viewall" href="../worldclass/index.html#jobs">Jobs ki vellu →</a>
    </div>

    <section class="su-tools" aria-label="Student tools">
      <div class="su-tooltabs" role="tablist" aria-label="Tools">
<!--TABBUTTONS-->
      </div>
<!--PANELS-->
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
(function(){
  var S = function(id){ return document.getElementById(id); };
  var num = function(id){ var v = parseFloat((S(id)||{}).value || 0); return isNaN(v) ? 0 : v; };
  var inr = function(v){ return '\\u20b9' + Math.round(v).toLocaleString('en-IN'); };

  function salary(){
    if(!S('t-basic')) return;
    var basic = num('t-basic'), da = num('t-da')/100, hra = num('t-hra')/100, ded = num('t-ded');
    var gross = basic * (1 + da + hra);
    var net = gross - ded;
    S('t-salary-out').textContent = 'Gross ' + inr(gross) + ' / నెల  ·  In-hand approx ' + inr(net) + ' / నెల';
  }
  function age(){
    if(!S('t-dob')) return;
    var dob = new Date(S('t-dob').value);
    var asOn = S('t-as').value ? new Date(S('t-as').value) : new Date();
    if(!S('t-as').value) S('t-as').value = asOn.toISOString().slice(0,10);
    if(isNaN(dob)) { S('t-age-out').textContent = 'పుట్టిన తేదీ పెట్టండి'; return; }
    var y = asOn.getFullYear() - dob.getFullYear();
    var m = asOn.getMonth() - dob.getMonth();
    if(m < 0 || (m === 0 && asOn.getDate() < dob.getDate())) y--;
    var limit = num('t-max') + num('t-relax');
    var ok = y <= limit && y >= 18;
    S('t-age-out').textContent = 'మీ వయస్సు ' + y + ' సంవత్సరాలు (limit ' + limit + ') — ' +
      (ok ? 'అర్హులు ✔ అప్లై చేయవచ్చు' : 'అర్హత లేదు ✘ (limit దాటింది)');
  }
  function score(){
    if(!S('t-total')) return;
    var total = num('t-total'), right = num('t-right'), wrong = num('t-wrong'), neg = num('t-neg');
    var marks = right - (wrong * neg);
    var left = total - right - wrong;
    S('t-score-out').textContent = 'Score approx ' + marks.toFixed(2) + ' / ' + total +
      '  ·  attempted ' + (right+wrong) + ' · left ' + (left < 0 ? 0 : left);
  }
  function fee(){
    if(!S('t-fee')) return;
    var fee = num('t-fee'), pct = parseFloat(S('t-cat').value);
    var pay = fee * pct / 100;
    S('t-fee-out').textContent = 'మీరు చెల్లించాల్సిన ఫీసు approx ' + inr(pay) +
      (pct === 0 ? ' (పూర్తి మినహాయింపు)' : ' (' + pct + '% of ' + inr(fee) + ')');
  }
  var ALL = [salary, age, score, fee];
  ['t-basic','t-da','t-hra','t-ded'].forEach(function(id){ var el=S(id); if(el) el.addEventListener('input', salary); });
  ['t-dob','t-as','t-max','t-relax'].forEach(function(id){ var el=S(id); if(el) el.addEventListener('input', age); });
  ['t-total','t-right','t-wrong','t-neg'].forEach(function(id){ var el=S(id); if(el) el.addEventListener('input', score); });
  ['t-fee','t-cat'].forEach(function(id){ var el=S(id); if(el) el.addEventListener('input', fee); });
  ALL.forEach(function(fn){ fn(); });
})();
</script>
</body>
</html>
'''


def icon(name, size=16):
    return (f'<svg class="su-uicon su-uicon-{name}" width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="currentColor" aria-hidden="true" focusable="false"><use href="#su-i-{name}"/></svg>')


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    buttons, panels = [], []
    for i, (tid, label, ic, body) in enumerate(TABS):
        on = " on" if i == 0 else ""
        buttons.append(
            f'        <button type="button" class="su-ttab{" active" if i == 0 else ""}" role="tab" '
            f'id="su-ttab-{tid}" aria-controls="su-tool-{tid}" aria-selected="{"true" if i == 0 else "false"}" '
            f'tabindex="{"0" if i == 0 else "-1"}">{icon(ic)} <span>{label}</span></button>')
        panels.append(
            f'      <div class="su-toolpanel{on}" id="su-tool-{tid}" role="tabpanel" '
            f'aria-labelledby="su-ttab-{tid}"{" hidden" if i else ""}>\n'
            f'        <h3>{label}</h3>\n{body}\n      </div>')
    html = (PAGE
            .replace("<!--HEADER-->", B.header_html(topbar="ఉద్యోగ · పరీక్షలు · స్కాలర్‌షిప్"))
            .replace("<!--FOOTERBAR-->", B.footer_html(pfx="../pages/"))
            .replace("<!--BOTTOMNAV-->", B.bottom_html())
            .replace("<!--PAGEJS-->", B.PAGE_JS)
            .replace("<!--TABBUTTONS-->", "\n".join(buttons))
            .replace("<!--PANELS-->", "\n".join(panels)))
    out = OUT / "index.html"
    out.write_text(html, encoding="utf-8")
    print(f"  wrote tools/index.html ({len(html.encode())} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
