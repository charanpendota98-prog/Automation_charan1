"""v39 Exam Portal — UI (landing + admin console + student exam app).

Everything is single-file HTML with vanilla JS (no build step, no CDN) so a
college can run it on any cheap server/VM. Mobile-first: students phones lo
join avutaru, so big touch targets, sticky timer, safe auto-save.
"""

from __future__ import annotations

BRAND = "studentup.in Exam Portal"


# ===========================================================================
# Shared CSS (design kit palette — navy/orange, Noto Sans Telugu)
# ===========================================================================

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Telugu:wght@400;600;700&display=swap');
:root{--navy:#12356B;--navy2:#1B4B90;--orange:#E8842B;--orange2:#F79B3E;
--ink:#152238;--muted:#5D6B80;--line:#E2E9F3;--soft:#F5F8FD;--white:#fff;
--green:#128A57;--red:#C0392B;--amber:#B57A00;--shadow:0 10px 30px rgba(18,53,107,.09)}
*{box-sizing:border-box}
html,body{margin:0;padding:0}
body{font-family:Inter,'Noto Sans Telugu',system-ui,-apple-system,sans-serif;
color:var(--ink);background:var(--soft);line-height:1.6;-webkit-text-size-adjust:100%}
a{color:var(--navy2)}
.wrap{max-width:1120px;margin:0 auto;padding:0 16px}
.topbar{background:linear-gradient(135deg,var(--navy),var(--navy2));color:#fff;
padding:12px 0}
.topbar .wrap{display:flex;align-items:center;gap:12px;flex-wrap:wrap}
.brand{font-weight:800;letter-spacing:-.02em;font-size:15px;display:flex;gap:8px;align-items:center}
.brand .dot{height:28px;width:28px;border-radius:9px;background:linear-gradient(135deg,var(--orange),var(--orange2));
display:grid;place-items:center;font-size:15px}
.topbar .spacer{flex:1}
.topbar .pill{background:rgba(255,255,255,.16);border-radius:999px;padding:5px 11px;
font-size:11.5px;font-weight:700}
.card{background:var(--white);border:1px solid var(--line);border-radius:18px;
padding:18px;margin:14px 0;box-shadow:var(--shadow)}
.card.tight{padding:14px}
h1{font-size:clamp(21px,3.4vw,30px);margin:0 0 6px;letter-spacing:-.03em;line-height:1.25}
h2{font-size:18px;margin:0 0 10px;color:var(--navy)}
h3{font-size:15px;margin:0 0 6px;color:var(--navy)}
p{margin:6px 0}
.muted{color:var(--muted);font-size:13px}
.tiny{font-size:11.5px;color:var(--muted)}
label{display:block;font-size:12.5px;font-weight:700;color:var(--navy);margin:10px 0 4px}
input,select,textarea,button{font:inherit;width:100%}
input,select,textarea{border:1px solid var(--line);border-radius:12px;padding:12px 13px;
background:#fff;color:var(--ink)}
input:focus,select:focus,textarea:focus{outline:2px solid #BFD4F2;border-color:#9DBEE9}
textarea{min-height:110px;resize:vertical;line-height:1.5}
.grid{display:grid;gap:12px}
.grid.c2{grid-template-columns:repeat(auto-fit,minmax(240px,1fr))}
.grid.c3{grid-template-columns:repeat(auto-fit,minmax(180px,1fr))}
.grid.c4{grid-template-columns:repeat(auto-fit,minmax(140px,1fr))}
.row{display:flex;gap:10px;flex-wrap:wrap;align-items:center}
.row.end{justify-content:flex-end}
.btn{border:0;border-radius:12px;padding:13px 18px;font-weight:800;cursor:pointer;
background:var(--navy);color:#fff;width:auto;transition:transform .06s ease}
.btn:hover{transform:translateY(-1px)}
.btn:disabled{opacity:.5;cursor:not-allowed;transform:none}
.btn.orange{background:linear-gradient(135deg,var(--orange),var(--orange2))}
.btn.green{background:var(--green)}
.btn.red{background:var(--red)}
.btn.ghost{background:#fff;color:var(--navy);border:1px solid var(--line)}
.btn.big{font-size:17px;padding:18px 26px;width:100%;border-radius:16px}
.btn.sm{padding:8px 12px;font-size:12.5px;border-radius:10px}
.btn.xs{padding:6px 9px;font-size:11.5px;border-radius:9px}
.kpi{background:var(--white);border:1px solid var(--line);border-radius:14px;padding:12px 14px}
.kpi b{display:block;font-size:22px;color:var(--navy);line-height:1.2}
.kpi span{font-size:11.5px;color:var(--muted);font-weight:600}
.tag{display:inline-block;border-radius:999px;padding:4px 10px;font-size:11px;font-weight:800}
.tag.draft{background:#EEF1F6;color:#5B6779}
.tag.published{background:#E9F3FE;color:#1957A8}
.tag.live{background:#E6F7EE;color:var(--green)}
.tag.closed{background:#FDECEA;color:var(--red)}
.tag.warn{background:#FFF6E5;color:var(--amber)}
.tag.ok{background:#E6F7EE;color:var(--green)}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{border:1px solid var(--line);padding:8px 9px;text-align:left;vertical-align:top}
th{background:var(--soft);color:var(--navy);font-size:12px;text-transform:uppercase;letter-spacing:.03em}
tr:nth-child(even) td{background:#FBFDFF}
.scroll{overflow:auto;max-width:100%}
.banner{border-radius:14px;padding:12px 14px;font-size:13.5px;margin:10px 0;border:1px solid}
.banner.info{background:#EEF5FF;border-color:#CFE0F7;color:#1C4C8F}
.banner.ok{background:#E9F8F0;border-color:#C7EAD6;color:#0F6B45}
.banner.warn{background:#FFF7E8;border-color:#F3DFB7;color:#8A5B00}
.banner.err{background:#FDECEA;border-color:#F5C6C0;color:#96271A}
.toast{position:fixed;left:50%;transform:translateX(-50%);bottom:18px;z-index:60;
background:#0E2449;color:#fff;padding:12px 18px;border-radius:12px;font-size:13.5px;
box-shadow:0 12px 30px rgba(14,36,73,.35);max-width:92vw;text-align:center;opacity:0;
transition:opacity .2s ease, transform .2s ease;pointer-events:none}
.toast.show{opacity:1;transform:translateX(-50%) translateY(-4px)}
.modal{position:fixed;inset:0;background:rgba(11,26,54,.55);display:none;z-index:70;
align-items:center;justify-content:center;padding:16px}
.modal.show{display:flex}
.modal .box{background:#fff;border-radius:18px;padding:20px;max-width:520px;width:100%;
max-height:88vh;overflow:auto;box-shadow:0 24px 60px rgba(11,26,54,.35)}
.tabs{display:flex;gap:6px;overflow:auto;padding-bottom:2px;margin:6px 0 12px}
.tab{border:1px solid var(--line);background:#fff;color:#4C5B72;border-radius:999px;
padding:9px 14px;font-size:12.5px;font-weight:800;cursor:pointer;white-space:nowrap;width:auto}
.tab.active{background:var(--navy);border-color:var(--navy);color:#fff}
.codebox{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12.5px;
background:#0E2449;color:#D9E6FF;border-radius:12px;padding:12px;white-space:pre-wrap;
word-break:break-all}
.hide{display:none !important}
.flex-between{display:flex;justify-content:space-between;align-items:center;gap:10px;flex-wrap:wrap}
"""

STUDENT_CSS = """
.timerbar{position:sticky;top:0;z-index:40;background:#0E2449;color:#fff;
padding:10px 0;box-shadow:0 6px 18px rgba(14,36,73,.28)}
.timerbar .wrap{display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.timer{font-size:clamp(22px,5vw,30px);font-weight:800;letter-spacing:.02em;
font-variant-numeric:tabular-nums}
.timer.warn{color:#FFD166}
.timer.danger{color:#FF8A80}
.progress{flex:1;min-width:120px;height:9px;background:rgba(255,255,255,.18);
border-radius:999px;overflow:hidden}
.progress i{display:block;height:100%;background:linear-gradient(90deg,#5FD08B,#F7C948);
width:0%}
.qcard{background:#fff;border:1px solid var(--line);border-radius:18px;padding:18px;
box-shadow:var(--shadow)}
.qnum{font-size:12px;font-weight:800;color:var(--orange);text-transform:uppercase;
letter-spacing:.06em}
.qtext{font-size:17.5px;font-weight:600;line-height:1.55;margin:8px 0 14px}
.opt{display:flex;gap:12px;align-items:flex-start;border:1.5px solid var(--line);
border-radius:14px;padding:13px 14px;margin:9px 0;cursor:pointer;background:#fff;
transition:border-color .12s ease, background .12s ease}
.opt:hover{border-color:#B9D1F0;background:#FBFDFF}
.opt.sel{border-color:var(--navy);background:#EEF5FF;box-shadow:inset 0 0 0 1px var(--navy)}
.opt .k{height:28px;width:28px;border-radius:9px;background:var(--soft);color:var(--navy);
display:grid;place-items:center;font-weight:800;font-size:13px;flex:0 0 auto}
.opt.sel .k{background:var(--navy);color:#fff}
.opt .t{font-size:15.5px;line-height:1.5}
.palette{display:grid;grid-template-columns:repeat(auto-fill,minmax(44px,1fr));gap:8px}
.pbtn{height:44px;border-radius:12px;border:1.5px solid var(--line);background:#fff;
font-weight:800;color:#42506A;cursor:pointer;width:100%}
.pbtn.answered{background:#E6F7EE;border-color:#BEE7D0;color:#0F6B45}
.pbtn.flagged{background:#FFF6E5;border-color:#F3DFB7;color:#8A5B00}
.pbtn.current{background:var(--navy);border-color:var(--navy);color:#fff}
.pbtn.seen{border-color:#C9D8EE}
.navbar{position:sticky;bottom:0;background:rgba(255,255,255,.97);backdrop-filter:blur(8px);
border-top:1px solid var(--line);padding:10px 0;z-index:35}
.navbar .wrap{display:flex;gap:8px;align-items:center}
.savechip{font-size:11.5px;font-weight:800;border-radius:999px;padding:4px 10px;
background:rgba(255,255,255,.16)}
.savechip.ok{background:#1E8E5A}.savechip.busy{background:#B57A00}.savechip.off{background:#A33B2E}
.result-score{font-size:clamp(38px,10vw,64px);font-weight:800;color:var(--navy);line-height:1}
.review{border:1px solid var(--line);border-radius:14px;padding:12px;margin:9px 0}
.review.correct{border-left:5px solid var(--green)}
.review.wrong{border-left:5px solid var(--red)}
.review.unattempted{border-left:5px solid #B9C4D4}
"""

ADMIN_CSS = """
.control{display:grid;gap:10px;grid-template-columns:1fr}
@media(min-width:620px){.control.two{grid-template-columns:1fr 1fr}}
.startbtn{background:linear-gradient(135deg,#128A57,#1FA86B);font-size:19px;padding:20px}
.closebtn{background:linear-gradient(135deg,#C0392B,#D9534F);font-size:19px;padding:20px}
.monitor{display:grid;gap:8px;grid-template-columns:repeat(auto-fill,minmax(160px,1fr))}
.stu{border:1px solid var(--line);border-radius:12px;padding:9px 11px;font-size:12.5px;background:#fff}
.stu b{display:block;font-size:13.5px}
.stu.active{border-color:#BEE7D0;background:#F5FDF9}
.stu.submitted{border-color:#C7DCF8;background:#F6FAFF}
.stu.waiting{background:#FFFDF6;border-color:#F0E3C4}
.stu.off{opacity:.75}
.qrow{border:1px solid var(--line);border-radius:14px;padding:12px;margin:9px 0;background:#fff}
.qrow.dropped{background:#FFF6F5;border-color:#F5C6C0}
.optline{font-size:13px;color:#3E4C63;margin:3px 0}
.optline.key{color:#0F6B45;font-weight:700}
"""

TOAST_JS = """
function toast(msg, ms){
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(window._toastT);
  window._toastT = setTimeout(()=>t.classList.remove('show'), ms||2600);
}
function h(tag, attrs, ...kids){
  const el = document.createElement(tag);
  for(const k in (attrs||{})){
    if(k === 'class') el.className = attrs[k];
    else if(k === 'text') el.textContent = attrs[k];
    else if(k === 'html') el.innerHTML = attrs[k];
    else if(k.startsWith('on')) el.addEventListener(k.slice(2), attrs[k]);
    else if(attrs[k] !== null && attrs[k] !== undefined) el.setAttribute(k, attrs[k]);
  }
  kids.flat().forEach(k => { if(k===null||k===undefined||k===false) return;
    el.appendChild(typeof k === 'string' ? document.createTextNode(k) : k); });
  return el;
}
async function api(path, opts){
  opts = opts || {};
  const init = {method: opts.method || (opts.body ? 'POST' : 'GET'),
    headers: {'Content-Type':'application/json'}};
  if(opts.body) init.body = JSON.stringify(opts.body);
  const r = await fetch(path, init);
  let data = null;
  try { data = await r.json(); } catch(e){ data = {error:'Server response ardham kaledu'}; }
  if(!r.ok) throw new Error(data && (data.error || data.message) || ('Error '+r.status));
  return data;
}
function copyText(text, label){
  const done = ()=>toast((label||'Copied')+' ✔');
  if(navigator.clipboard && window.isSecureContext){
    navigator.clipboard.writeText(text).then(done).catch(()=>fallbackCopy(text, done));
  } else fallbackCopy(text, done);
}
function fallbackCopy(text, done){
  const ta = document.createElement('textarea');
  ta.value = text; ta.style.position='fixed'; ta.style.top='-1000px';
  document.body.appendChild(ta); ta.select();
  try{ document.execCommand('copy'); done(); }catch(e){ toast('Copy cheyaledu — manual ga select cheyandi'); }
  ta.remove();
}
function confirmBox(title, bodyLines, okLabel, danger){
  return new Promise(resolve=>{
    const box = document.getElementById('modalBox');
    box.innerHTML = '';
    box.appendChild(h('h2', {text: title}));
    bodyLines.forEach(l => box.appendChild(
      typeof l === 'string' ? h('p', {class:'muted', text:l}) : l));
    box.appendChild(h('div', {class:'row end'}, 
      h('button', {class:'btn ghost', onclick:()=>{ closeModal(); resolve(false); }}, 'Cancel'),
      h('button', {class:'btn ' + (danger?'red':'orange'), onclick:()=>{ closeModal(); resolve(true); }},
        okLabel || 'Confirm')));
    document.getElementById('modal').classList.add('show');
  });
}
function closeModal(){ document.getElementById('modal').classList.remove('show'); }
function fmtTime(sec){
  sec = Math.max(0, Math.floor(sec));
  const h_ = Math.floor(sec/3600), m = Math.floor((sec%3600)/60), s = sec%60;
  const pad = n => String(n).padStart(2,'0');
  return (h_ ? h_ + ':' : '') + pad(m) + ':' + pad(s);
}
function statusTag(status){
  const map = {draft:'draft', published:'published', live:'live', closed:'closed'};
  return h('span', {class:'tag ' + (map[status]||'draft'), text: status.toUpperCase()});
}
"""


def _page(title: str, extra_css: str, body: str, script: str) -> str:
    return f"""<!doctype html>
<html lang="te">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#12356B">
<title>{title}</title>
<style>{BASE_CSS}{extra_css}</style>
</head>
<body>
{body}
<div class="toast" id="toast"></div>
<div class="modal" id="modal" onclick="if(event.target===this)closeModal()">
  <div class="box" id="modalBox"></div>
</div>
<script>
{TOAST_JS}
{script}
</script>
</body>
</html>"""


def _topbar(right: str = "", subtitle: str = BRAND) -> str:
    return f"""<div class="topbar"><div class="wrap">
  <div class="brand"><span class="dot">🎓</span><span>{subtitle}</span></div>
  <div class="spacer"></div>
  <div class="row" id="topActions">{right}</div>
</div></div>"""


# ===========================================================================
# Landing
# ===========================================================================

def landing_html() -> str:
    body = _topbar() + """
<div class="wrap">
  <div class="card">
    <h1>College Exams — online, easy, mistake-free 🎓</h1>
    <p class="muted">College exam create chestundi → students link + roll number tho join
    avutaru → admin one-click <b>START</b> / <b>CLOSE</b>. Timer, auto-save, auto-submit,
    results, reports — anni automatic.</p>
    <div class="grid c2" style="margin-top:14px">
      <div class="card tight">
        <h3>🏫 College admin</h3>
        <p class="muted">Exam create cheyandi, questions paste cheyandi (Excel/Word nunchi),
        roll numbers list pettandi, publish chesi link share cheyandi.</p>
        <a class="btn orange" style="display:inline-block;text-decoration:none"
           href="/admin">Admin console open chey</a>
      </div>
      <div class="card tight">
        <h3>🧑‍🎓 Student</h3>
        <p class="muted">College ichina exam link open chesi <b>roll number</b> matrame
        ivvandi — password/login avasaram ledu. Exam start ayye varaku wait
        cheyandi.</p>
        <div class="row" style="margin-top:8px">
          <input id="codeInput" placeholder="Exam code (ex: A7K2QX)" style="max-width:220px">
          <button class="btn" onclick="goExam()">Join</button>
        </div>
        <p class="tiny" id="codeHint"></p>
      </div>
    </div>
  </div>
  <div class="card">
    <h2>Mistakes lekunda — built-in protections</h2>
    <div class="grid c3">
      <div><h3>⏱️ Server timer</h3><p class="muted">Time server nunchi — phone clock
      marchina pani cheyyadu. Time ayyaka automatic submit.</p></div>
      <div><h3>💾 Auto-save</h3><p class="muted">Prathi option click ki answer save.
      Network poyina, page refresh chesina answers poyipovu.</p></div>
      <div><h3>🚀 One-click START</h3><p class="muted">Andaru join ayyaka START. Kotha
      joiners ki timer same end time (fair).</p></div>
      <div><h3>🔒 One-click CLOSE</h3><p class="muted">Close cheyagane pending students
      auto-submit + results compute. Double click chesina okkate.</p></div>
      <div><h3>📊 Reports</h3><p class="muted">Results, question-wise analysis, audit log,
      toppers — CSV download (Excel lo open).</p></div>
      <div><h3>📣 Notifications</h3><p class="muted">Publish/Start/Close/Results — in-app
      banner + Telegram/webhook + WhatsApp copy-paste messages.</p></div>
    </div>
  </div>
</div>"""
    script = """
function goExam(){
  const v = (document.getElementById('codeInput').value||'').trim().toUpperCase();
  if(!v){ toast('Exam code enter cheyandi'); return; }
  location.href = '/exam/' + encodeURIComponent(v);
}
document.getElementById('codeInput').addEventListener('keydown', e=>{
  if(e.key === 'Enter') goExam();
});
const m = location.pathname.match(/^\\/exam\\/([A-Za-z0-9]+)/);
if(m){ location.replace('/exam/' + m[1].toUpperCase()); }
"""
    return _page("College Exam Portal — studentup.in", "", body, script)


# ===========================================================================
# Admin console
# ===========================================================================

def admin_html() -> str:
    body = _topbar(
        right="""<span class="pill" id="keyPill">key: —</span>
        <button class="btn ghost sm" onclick="changeKey()">Key change</button>""",
        subtitle="Exam Portal — College Admin") + """
<div class="wrap">
  <div class="card" id="loginCard">
    <h1>College admin login</h1>
    <p class="muted">Admin key tho login cheyandi (server start appudu print avutundi;
    <code>EXAM_PORTAL_ADMIN_KEY</code> env lo set cheyochu). Idi college staff ki matrame.</p>
    <label>Admin key</label>
    <input id="keyInput" type="password" placeholder="admin key" autocomplete="off">
    <div class="row" style="margin-top:12px">
      <button class="btn orange" id="loginBtn">Login</button>
    </div>
    <div id="loginMsg" class="tiny" style="margin-top:8px"></div>
  </div>

  <div class="hide" id="dash">
    <div class="card">
      <div class="flex-between">
        <h1 style="margin:0">Exams</h1>
        <div class="row">
          <button class="btn ghost sm" onclick="loadExams()">Refresh</button>
          <button class="btn orange sm" onclick="showCreate()">+ New exam</button>
        </div>
      </div>
      <div class="scroll" style="margin-top:12px"><table id="examTable"></table></div>
      <p class="tiny" id="examEmpty"></p>
    </div>

    <div class="card hide" id="createCard">
      <h2>New exam</h2>
      <div class="grid c2">
        <div><label>College name</label><input id="f_college" placeholder="Sri Krishna Degree College"></div>
        <div><label>Exam title *</label><input id="f_title" placeholder="Internal Test 1 — General Knowledge"></div>
        <div><label>Subject</label><input id="f_subject" placeholder="GK / Maths / English"></div>
        <div><label>Exam date (display)</label><input id="f_date" placeholder="15-10-2026"></div>
        <div><label>Duration (minutes) *</label><input id="f_duration" type="number" value="30" min="1" max="480"></div>
        <div><label>Marks per question *</label><input id="f_marks" type="number" value="1" step="0.5" min="0.5"></div>
        <div><label>Negative marks (wrong answer ki)</label><input id="f_neg" type="number" value="0" step="0.25" min="0" max="5"></div>
        <div><label>Pass marks (0 = no pass/fail)</label><input id="f_pass" type="number" value="0" step="1" min="0"></div>
        <div><label>Shuffle questions</label><select id="f_shq"><option value="1">Yes (recommended)</option><option value="0">No</option></select></div>
        <div><label>Shuffle options</label><select id="f_sho"><option value="1">Yes (recommended)</option><option value="0">No</option></select></div>
        <div><label>Result mode</label><select id="f_result">
          <option value="immediate">Immediate — submit cheyagane result</option>
          <option value="after_publish">After results published (admin decides)</option>
          <option value="never">Hide — admin dashboard lo matrame</option>
        </select></div>
        <div><label>Late join</label><select id="f_late">
          <option value="1">Allow — start tarvata kuda join (fair: same end time)</option>
          <option value="0">Don't allow — start ayaka evaru join avvaleru</option>
        </select></div>
        <div><label>Late join grace (minutes, optional)</label><input id="f_grace" type="number" value="0" min="0" max="60"></div>
        <div><label>Auto-start (roster full aithe)</label><select id="f_auto">
          <option value="0">No — nenu START nokkutanu</option>
          <option value="1">Yes — andaru join ayyaka automatic START</option>
        </select></div>
        <div><label>Roster (roll list) compulsory</label><select id="f_roster">
          <option value="0">No — evaru ayina roll tho join avvochu</option>
          <option value="1">Yes — college list lo unna rolls matrame</option>
        </select></div>
      </div>
      <label>Student instructions (Telugu/English)</label>
      <textarea id="f_instr" placeholder="1. Roll number correct ga type cheyandi&#10;2. Prathi question ki okka option select cheyandi&#10;3. Time ayyaka auto-submit avutundi&#10;4. Phone silent lo pettandi"></textarea>
      <div class="row" style="margin-top:14px">
        <button class="btn orange" id="createBtn" onclick="createExam()">Create exam</button>
        <button class="btn ghost" onclick="hideCreate()">Cancel</button>
      </div>
      <p class="tiny">Create ayyaka exam code + student link vasthundi. Tarvata questions
      paste chesi, publish chesi, START nokkandi.</p>
    </div>
  </div>
</div>"""
    script = """
let ADMIN_KEY = localStorage.getItem('su_admin_key') || '';
function changeKey(){
  localStorage.removeItem('su_admin_key'); ADMIN_KEY = '';
  document.getElementById('dash').classList.add('hide');
  document.getElementById('loginCard').classList.remove('hide');
  document.getElementById('keyPill').textContent = 'key: —';
}
function keyOK(){ document.getElementById('keyPill').textContent =
  'key: ' + (ADMIN_KEY ? ADMIN_KEY.slice(0,4) + '…' : '—'); }
async function login(){
  const key = (document.getElementById('keyInput').value || '').trim();
  if(!key){ toast('Admin key enter cheyandi'); return; }
  try{
    await api('/api/admin/verify', {body:{key}});
    ADMIN_KEY = key; localStorage.setItem('su_admin_key', key); keyOK();
    document.getElementById('loginCard').classList.add('hide');
    document.getElementById('dash').classList.remove('hide');
    loadExams();
  }catch(e){ document.getElementById('loginMsg').textContent = e.message; toast(e.message); }
}
document.getElementById('loginBtn').addEventListener('click', login);
document.getElementById('keyInput').addEventListener('keydown', e=>{ if(e.key==='Enter') login(); });
async function loadExams(){
  const out = await api('/api/admin/exams?key=' + encodeURIComponent(ADMIN_KEY));
  const t = document.getElementById('examTable'); t.innerHTML = '';
  const head = h('tr', {}, ...['Code','Exam','College','Status','Questions','Joined',
    'Start','End','Actions'].map(x=>h('th',{text:x})));
  t.appendChild(head);
  (out.exams||[]).forEach(e=>{
    const manageUrl = '/manage/' + e.code + '?key=' + encodeURIComponent(e.admin_token);
    t.appendChild(h('tr', {},
      h('td', {}, h('b', {text: e.code})),
      h('td', {text: e.title}),
      h('td', {text: e.college || '-'}),
      h('td', {}, statusTag(e.status)),
      h('td', {text: String(e.question_count ?? '')}),
      h('td', {text: String(e.joined ?? 0)}),
      h('td', {class:'tiny', text: (e.start_at||'').slice(11,16) || '-'}),
      h('td', {class:'tiny', text: (e.end_at||'').slice(11,16) || '-'}),
      h('td', {}, h('a', {class:'btn xs', href: manageUrl, text:'Manage'}))));
  });
  document.getElementById('examEmpty').textContent = (out.exams||[]).length ? '' :
    'Inka exams levu — "+ New exam" nokkandi.';
}
function showCreate(){ document.getElementById('createCard').classList.remove('hide');
  document.getElementById('createCard').scrollIntoView({behavior:'smooth'}); }
function hideCreate(){ document.getElementById('createCard').classList.add('hide'); }
function val(id){ return (document.getElementById(id).value||'').trim(); }
function num(id){ return parseFloat(document.getElementById(id).value||'0') || 0; }
async function createExam(){
  const title = val('f_title');
  if(!title){ toast('Exam title ivvandi'); return; }
  const body = {key: ADMIN_KEY, college: val('f_college'), title,
    subject: val('f_subject'), exam_date: val('f_date'),
    instructions: document.getElementById('f_instr').value,
    duration_min: num('f_duration') || 30, per_q_marks: num('f_marks') || 1,
    negative_marks: num('f_neg'), pass_marks: num('f_pass'),
    shuffle_questions: val('f_shq') === '1', shuffle_options: val('f_sho') === '1',
    show_result: val('f_result'), allow_late_join: val('f_late') === '1',
    late_grace_min: num('f_grace'), auto_start_all_joined: val('f_auto') === '1',
    roster_required: val('f_roster') === '1'};
  document.getElementById('createBtn').disabled = true;
  try{
    const out = await api('/api/admin/exams', {body});
    const e = out.exam;
    toast('Exam create ayyindi ' + e.code + ' ✔', 4000);
    location.href = '/manage/' + e.code + '?key=' + encodeURIComponent(e.admin_token);
  }catch(e){ toast(e.message); }
  document.getElementById('createBtn').disabled = false;
}
if(ADMIN_KEY){ keyOK(); login(); } else { keyOK(); }
"""
    return _page("Admin — Exam Portal", ADMIN_CSS, body, script)


# ===========================================================================
# Manage console (single exam)
# ===========================================================================

def manage_html() -> str:
    body = _topbar(
        right="""<span class="pill" id="examPill">—</span>
        <button class="btn ghost sm" onclick="location.href='/admin'">All exams</button>""",
        subtitle="Exam Portal — Manage") + """
<div class="wrap" id="app">
  <div class="card" id="loading"><p class="muted">Load avutundi…</p></div>

  <div class="hide" id="head">
    <div class="card">
      <div class="flex-between">
        <div>
          <h1 id="examTitle" style="margin:0"></h1>
          <p class="muted" id="examSub"></p>
        </div>
        <div class="row" id="statusRow"></div>
      </div>
      <div class="grid c4" style="margin-top:12px" id="kpis"></div>
      <div id="warnBox"></div>
      <div class="grid c2" style="margin-top:14px">
        <button class="btn big startbtn" id="startBtn" onclick="doStart()">🚀 START EXAM</button>
        <button class="btn big closebtn" id="closeBtn" onclick="doClose()">🔒 CLOSE EXAM</button>
      </div>
      <div class="row" style="margin-top:10px" id="quickRow"></div>
      <p class="tiny" id="controlHint"></p>
    </div>

    <div class="tabs" id="tabs"></div>
    <div id="tabBody"></div>
  </div>
</div>"""
    script = """
const CODE = (location.pathname.split('/')[2] || '').toUpperCase();
let KEY = new URLSearchParams(location.search).get('key') || localStorage.getItem('su_manage_' + CODE) || '';
let STATE = null, POLL = null, TAB = 'control';

async function load(){
  try{
    STATE = await api('/api/admin/exam/' + CODE + '?key=' + encodeURIComponent(KEY));
    localStorage.setItem('su_manage_' + CODE, KEY);
    document.getElementById('loading').classList.add('hide');
    document.getElementById('head').classList.remove('hide');
    render();
  }catch(e){
    document.getElementById('loading').innerHTML = '';
    document.getElementById('loading').appendChild(h('div', {class:'banner err', text: e.message}));
    document.getElementById('loading').appendChild(h('p', {class:'muted',
      text:'Correct link: /manage/' + CODE + '?key=<admin token> — admin console nunchi open cheyandi.'}));
  }
}
function live(){ return STATE && STATE.exam.status === 'live'; }
function schedule(){ clearInterval(POLL); POLL = setInterval(()=>{ if(live()) load(); }, 4000); }

function render(){
  const e = STATE.exam, s = STATE.summary;
  document.getElementById('examPill').textContent = e.code;
  document.getElementById('examTitle').textContent = e.title;
  document.getElementById('examSub').textContent = [e.college, e.subject,
    (e.exam_date ? 'Exam: ' + e.exam_date : '')].filter(Boolean).join(' · ');
  const row = document.getElementById('statusRow'); row.innerHTML = '';
  row.appendChild(statusTag(e.status));
  row.appendChild(h('span', {class:'pill', text: e.duration_min + ' min'}));
  if(e.negative_marks) row.appendChild(h('span', {class:'tag warn', text:'−' + e.negative_marks + ' negative'}));
  document.getElementById('kpis').innerHTML = '';
  const kpis = [['Questions', s.questions], ['Total marks', s.total_marks],
    ['Joined', s.joined + (s.roster ? ' / ' + s.roster : '')],
    ['Submitted', s.submitted + ' / ' + (s.joined || 0)],
    ['Pending', s.pending], ['Average', s.average],
    ['Highest', s.highest], ['Toppers', s.topper || '—']];
  kpis.forEach(([label, value])=>{
    document.getElementById('kpis').appendChild(
      h('div', {class:'kpi'}, h('b', {text: String(value)}), h('span', {text: label})));
  });
  const wb = document.getElementById('warnBox'); wb.innerHTML = '';
  (STATE.blockers||[]).forEach(b => wb.appendChild(h('div', {class:'banner err', text:'⛔ ' + b})));
  (STATE.warnings||[]).forEach(b => wb.appendChild(h('div', {class:'banner warn', text:'⚠️ ' + b})));
  if(STATE.announcementLive) wb.appendChild(h('div', {class:'banner info',
    text:'📢 Live announcement students ki kanipistundi: ' + STATE.announcementLive}));
  const msg = STATE.notifyLast ? 'Last notification: ' + STATE.notifyLast : '';
  document.getElementById('controlHint').textContent = msg;

  document.getElementById('startBtn').disabled = !(e.status === 'published');
  document.getElementById('closeBtn').disabled = !(e.status === 'live' || e.status === 'published');
  const qr = document.getElementById('quickRow'); qr.innerHTML = '';
  if(live()){
    qr.appendChild(h('button', {class:'btn ghost sm', onclick:()=>doExtend(5)}, '⏱️ +5 min'));
    qr.appendChild(h('button', {class:'btn ghost sm', onclick:()=>doExtend(10)}, '⏱️ +10 min'));
    qr.appendChild(h('button', {class:'btn ghost sm',
      onclick:()=>toggleLate(!e.allow_late_join)},
      (e.allow_late_join ? '🚫 Late join off' : '✅ Late join on')));
    qr.appendChild(h('span', {class:'tiny',
      text:'Auto-close: ' + (e.end_at || '').slice(11,16) + ' ki automatic close avutundi'}));
  }
  renderTabs();
  schedule();
}

const TABLIST = [['control','Control & Monitor'],['questions','Questions'],
  ['roster','Student list'],['results','Results'],['share','Share & Notify'],
  ['settings','Settings'],['audit','Audit & Data']];
function renderTabs(){
  const t = document.getElementById('tabs'); t.innerHTML = '';
  TABLIST.forEach(([id, label])=>{
    t.appendChild(h('button', {class:'tab' + (TAB===id?' active':''),
      onclick:()=>{ TAB = id; renderTabs(); renderTab(); }}, label));
  });
  renderTab();
}
function renderTab(){
  const host = document.getElementById('tabBody');
  host.innerHTML = '';
  ({control: tabControl, questions: tabQuestions, roster: tabRoster,
    results: tabResults, share: tabShare, settings: tabSettings,
    audit: tabAudit}[TAB] || tabControl)(host);
}

/* ---------------------------------------------------------------- control */
function tabControl(host){
  const e = STATE.exam;
  const card = h('div', {class:'card'}, h('h2', {text:'Live monitor'}));
  if(!STATE.sessions.length){
    card.appendChild(h('p', {class:'muted',
      text:'Inka evaru join avvaledu. Student link share cheyandi (Share tab).'}));
  } else {
    const mon = h('div', {class:'monitor'});
    STATE.sessions.forEach(s=>{
      const cls = s.status === 'submitted' ? 'submitted' : (s.status === 'active' ? 'active'
        : (s.status === 'waiting' ? 'waiting' : ''));
      const offline = s.status === 'active' && STATE.serverNow &&
        (Date.parse(STATE.serverNow) - Date.parse(s.last_seen || STATE.serverNow) > 45000);
      mon.appendChild(h('div', {class:'stu ' + cls + (offline ? ' off' : '')},
        h('b', {text: s.roll + (s.name ? ' · ' + s.name : '')}),
        h('span', {class:'tiny', text: (s.status === 'submitted'
            ? '✅ submitted ' + (s.auto_submitted ? '(auto) ' : '') + 'score ' + (s.score ?? '-')
            : s.status === 'active' ? '📝 writing' + (offline ? ' · offline?' : '')
            : s.status === 'waiting' ? '⏳ waiting' : s.status) +
          (s.tab_switches ? ' · ⚠️' + s.tab_switches : '')})));
    });
    card.appendChild(mon);
    card.appendChild(h('p', {class:'tiny',
      text:'⚠️ = tab switch count (integrity signal). Offline? = 45s nunchi heartbeat ledu.'}));
  }
  host.appendChild(card);
  host.appendChild(h('div', {class:'card'},
    h('h2', {text:'Announcement (students screen lo live banner)'}),
    h('textarea', {id:'annInput', placeholder:'Ex: Q5 lo mistake undi — aa question drop chesam. Continue cheyandi.'}),
    h('div', {class:'row', style:'margin-top:10px'},
      h('button', {class:'btn orange sm', onclick:()=>doAnnounce()}, '📢 Send to all students'),
      h('button', {class:'btn ghost sm', onclick:()=>doAnnounce(true)}, 'Clear banner'))));
}
async function doStart(){
  const e = STATE.exam;
  const ok = await confirmBox('Exam START cheyyala?',
    ['Students ki timer ippude start avutundi (' + e.duration_min + ' nimishalu).',
     'Joined: ' + STATE.summary.joined + (STATE.summary.roster ? ' / ' + STATE.summary.roster + ' roster' : ''),
     'Waiting students ki question paper ippude lock avutundi.',
     'Start tarvata kuda join cheyyali ante Share/Settings lo late-join toggle on cheyandi.'],
    '🚀 START NOW');
  if(!ok) return;
  try{ const out = await api('/api/admin/exam/' + CODE + '/start',
      {body:{key: KEY}});
    toast('🚀 START ✔ (' + out.activated + ' students activated)', 3500); load();
  }catch(err){ toast(err.message, 4000); }
}
async function doClose(){
  const s = STATE.summary;
  const ok = await confirmBox('Exam CLOSE cheyyala?',
    ['Pending students (writing/waiting): ' + s.pending,
     'Vaalla answers tarvata auto-submit avutayi + results compute avutayi.',
     'Close ayyaka evaru join avvaleru. Idi idempotent — rendu sarlu chesina okkate.'],
    '🔒 CLOSE NOW', true);
  if(!ok) return;
  try{ const out = await api('/api/admin/exam/' + CODE + '/close', {body:{key: KEY}});
    toast('🔒 CLOSED ✔ auto-submit ' + (out.auto_submitted || 0), 3500); load();
  }catch(err){ toast(err.message, 4000); }
}
async function doExtend(min){
  try{ const out = await api('/api/admin/exam/' + CODE + '/extend',
      {body:{key: KEY, minutes: min}});
    toast('⏱️ +' + min + ' min (' + (out.end_at||'').slice(11,16) + ')', 3000); load();
  }catch(err){ toast(err.message); }
}
async function toggleLate(allow){
  try{ await api('/api/admin/exam/' + CODE + '/late-join', {body:{key: KEY, allow}});
    toast('Late join ' + (allow ? 'ON' : 'OFF')); load();
  }catch(err){ toast(err.message); }
}
async function doAnnounce(clear){
  const msg = clear ? '' : (document.getElementById('annInput') || {}).value || '';
  if(!clear && !msg.trim()){ toast('Message type cheyandi'); return; }
  try{ await api('/api/admin/exam/' + CODE + '/announce', {body:{key: KEY, message: msg}});
    toast(clear ? 'Banner clear ayyindi' : '📢 Students ki pampindi'); load();
  }catch(err){ toast(err.message); }
}

/* -------------------------------------------------------------- questions */
function tabQuestions(host){
  const card = h('div', {class:'card'}, h('h2', {text:'Bulk paste (Excel/Word nunchi)'}));
  card.appendChild(h('p', {class:'muted',
    text:'Format 1 (blocks): "1. Question? / A) one / B) two / C) three / D) four / Answer: B / Explanation: ..." — Format 2 (CSV): question,optA,optB,optC,optD,answer(A-D),explanation — Format 3 (JSON).'}));
  card.appendChild(h('textarea', {id:'bulk', style:'min-height:170px',
    placeholder:'1. Capital of Telangana?\\nA) Warangal\\nB) Hyderabad\\nC) Karimnagar\\nD) Nizamabad\\nAnswer: B\\nExplanation: Hyderabad Telangana capital.'}));
  card.appendChild(h('div', {class:'row', style:'margin-top:10px'},
    h('button', {class:'btn orange sm', onclick:()=>bulkAdd(false)}, 'Parse & add'),
    h('button', {class:'btn ghost sm', onclick:()=>bulkAdd(true)}, 'Validate only (dry run)')));
  const brep = h('div', {id:'bulkReport'});
  card.appendChild(brep);
  renderBulkReport(brep);
  host.appendChild(card);

  const list = h('div', {class:'card'}, h('h2', {text:'Questions (' + STATE.questions.length + ')'}));
  STATE.questions.forEach((q, i)=>{
    const row = h('div', {class:'qrow' + (q.dropped ? ' dropped' : '')});
    row.appendChild(h('div', {class:'flex-between'},
      h('b', {text: 'Q' + (i+1) + '. ' + q.text}),
      h('div', {class:'row'},
        q.dropped ? h('span', {class:'tag closed', text:'DROPPED'}) : null,
        h('button', {class:'btn xs ghost', onclick:()=>toggleDrop(q)}, q.dropped ? 'Restore' : 'Drop'),
        h('button', {class:'btn xs red', onclick:()=>delQuestion(q)}, 'Delete'))));
    q.options.forEach((o, oi)=>row.appendChild(h('div', {
      class:'optline' + (oi === q.correct_index ? ' key' : ''),
      text: String.fromCharCode(65+oi) + ') ' + o + (oi === q.correct_index ? '  ✔ (correct)' : '')})));
    if(q.explanation) row.appendChild(h('div', {class:'tiny', text:'Explanation: ' + q.explanation}));
    list.appendChild(row);
  });
  if(!STATE.questions.length) list.appendChild(h('p', {class:'muted', text:'Inka questions levu.'}));
  host.appendChild(list);
}
let BULK_REPORT = null;          // {cls, text}[] — refresh tarvata kuda kanipistundi
function renderBulkReport(host){
  if(!host) return;
  host.innerHTML = '';
  if(!BULK_REPORT) return;
  BULK_REPORT.forEach(r => host.appendChild(h('div', {class:'banner ' + r.cls, text:r.text})));
}
async function bulkAdd(dry){
  const raw = (document.getElementById('bulk') || {}).value || '';
  const host = document.getElementById('bulkReport');
  try{
    const out = await api('/api/admin/exam/' + CODE + '/questions',
      {body:{key: KEY, raw, dry_run: !!dry}});
    BULK_REPORT = [{cls:(out.errors.length ? 'warn' : 'ok'),
      text:(dry ? 'Dry run: ' : 'Added: ') + out.added + ' questions' +
        (out.errors.length ? ' · ' + out.errors.length + ' errors' : ' ✔')}]
      .concat((out.errors || []).slice(0, 12).map(e => ({cls:'err', text:e})));
  }catch(e){
    BULK_REPORT = [{cls:'err', text: e.message}];
  }
  renderBulkReport(document.getElementById('bulkReport') || host);
  if(!dry && BULK_REPORT.length && BULK_REPORT[0].cls === 'ok'){ load(); }
}
async function toggleDrop(q){
  try{ await api('/api/admin/exam/' + CODE + '/question/' + q.id + '/drop',
      {body:{key: KEY, dropped: !q.dropped}});
    toast(q.dropped ? 'Question restore ayyindi' : 'Question dropped — marks recalculated');
    load();
  }catch(e){ toast(e.message); }
}
async function delQuestion(q){
  const ok = await confirmBox('Question delete cheyyala?', [q.text], 'Delete', true);
  if(!ok) return;
  try{ await api('/api/admin/exam/' + CODE + '/question/' + q.id + '/delete',
      {body:{key: KEY, confirm: true}}); toast('Deleted'); load();
  }catch(e){ toast(e.message); }
}

/* ----------------------------------------------------------------- roster */
function tabRoster(host){
  const card = h('div', {class:'card'}, h('h2', {text:'Student roll numbers'}));
  card.appendChild(h('p', {class:'muted',
    text:'Okka line ki okka roll (Excel nunchi copy-paste cheyochu: "ROLL, Name"). Roster compulsory ON unte ee list lo unna rolls matrame join avutaru.'}));
  card.appendChild(h('textarea', {id:'rosterBox', style:'min-height:160px',
    placeholder:'21B01A0501, Ravi Kumar\\n21B01A0502, Sita Devi'}));
  card.appendChild(h('div', {class:'row', style:'margin-top:10px'},
    h('button', {class:'btn orange sm', onclick:()=>saveRoster()}, 'Save list'),
    h('button', {class:'btn ghost sm', onclick:()=>loadRosterPreview()}, 'Current list')));
  const rrep = h('div', {id:'rosterReport'});
  card.appendChild(rrep);
  card.appendChild(h('div', {id:'rosterPreview'}));
  renderRosterReport(rrep);
  host.appendChild(card);
  loadRosterPreview();
}
let ROSTER_REPORT = null;
function renderRosterReport(host){
  if(!host || !ROSTER_REPORT) return;
  ROSTER_REPORT.forEach(r => host.appendChild(h('div', {class:'banner ' + r.cls, text:r.text})));
}
async function saveRoster(){
  const raw = document.getElementById('rosterBox').value || '';
  try{
    const out = await api('/api/admin/exam/' + CODE + '/roster',
      {body:{key: KEY, raw}});
    ROSTER_REPORT = [{cls:'ok', text:'Saved: ' + out.added + ' students ✔'}]
      .concat((out.duplicates||[]).map(d => ({cls:'warn', text:'Duplicate skip: ' + d})))
      .concat((out.invalid||[]).map(d => ({cls:'err', text:'Invalid roll skip: ' + String(d)})));
  }catch(e){
    ROSTER_REPORT = [{cls:'err', text:'Save avvaledu: ' + e.message}];
  }
  const rep = document.getElementById('rosterReport');
  if(rep){ rep.innerHTML = ''; renderRosterReport(rep); }
  load();
}
async function loadRosterPreview(){
  try{
    const out = await api('/api/admin/exam/' + CODE + '/roster?key=' + encodeURIComponent(KEY));
    const rep = document.getElementById('rosterPreview')
      || document.getElementById('rosterReport');
    if(!rep) return;
    rep.innerHTML = '';
    rep.appendChild(h('p', {class:'tiny',
      text:'List lo unnaru: ' + out.rolls.length + ' students'}));
    if(out.rolls.length){
      const t = h('table', {}, h('tr', {}, h('th', {text:'Roll'}), h('th', {text:'Name'})));
      out.rolls.forEach(r => t.appendChild(h('tr', {}, h('td', {text:r.roll}), h('td', {text:r.name || '—'}))));
      rep.appendChild(h('div', {class:'scroll'}, t));
    }
  }catch(e){ /* silent */ }
}

/* ---------------------------------------------------------------- results */
function tabResults(host){
  const card = h('div', {class:'card'}, h('h2', {text:'Results & reports'}));
  const s = STATE.summary;
  card.appendChild(h('div', {class:'grid c4'},
    h('div', {class:'kpi'}, h('b', {text:String(s.submitted)}), h('span', {text:'Submitted'})),
    h('div', {class:'kpi'}, h('b', {text:String(s.pending)}), h('span', {text:'Pending'})),
    h('div', {class:'kpi'}, h('b', {text:String(s.average)}), h('span', {text:'Average'})),
    h('div', {class:'kpi'}, h('b', {text:String(s.highest)}), h('span', {text:'Highest'})),
    h('div', {class:'kpi'}, h('b', {text:String(s.lowest)}), h('span', {text:'Lowest'})),
    h('div', {class:'kpi'}, h('b', {text:s.passed === null ? '—' : String(s.passed)}), h('span', {text:'Passed'})),
    h('div', {class:'kpi'}, h('b', {text:String(s.total_marks)}), h('span', {text:'Total marks'})),
    h('div', {class:'kpi'}, h('b', {text:String(s.questions)}), h('span', {text:'Questions'})),
  ));
  const row = h('div', {class:'row', style:'margin-top:12px'},
    h('a', {class:'btn orange sm', href:'/api/admin/exam/' + CODE + '/export/results.csv?key=' + encodeURIComponent(KEY)}, '⬇️ Results CSV'),
    h('a', {class:'btn ghost sm', href:'/api/admin/exam/' + CODE + '/export/analysis.csv?key=' + encodeURIComponent(KEY)}, '⬇️ Question analysis CSV'),
    h('a', {class:'btn ghost sm', href:'/api/admin/exam/' + CODE + '/export/questions.csv?key=' + encodeURIComponent(KEY)}, '⬇️ Question paper CSV'),
    h('a', {class:'btn ghost sm', href:'/api/admin/exam/' + CODE + '/export/audit.csv?key=' + encodeURIComponent(KEY)}, '⬇️ Audit log CSV'));
  card.appendChild(row);
  if(!STATE.resultsPublished){
    card.appendChild(h('div', {class:'row', style:'margin-top:12px'},
      h('button', {class:'btn green sm', onclick:()=>publishResults()}, '🏆 Publish results to students'),
      h('span', {class:'tiny', text:'Students link lo result + review kanipistundi (immediate mode lo already kanipistundi).'})));
  } else {
    card.appendChild(h('div', {class:'banner ok', style:'margin-top:12px',
      text:'🏆 Results published: ' + STATE.resultsPublished}));
  }
  const t = h('table', {}, h('tr', {}, ...['Rank','Roll','Name','Score',
    'Correct','Wrong','Skip','Status','Tab','Submitted'].map(x=>h('th',{text:x}))));
  (STATE.leaderboard||[]).forEach(r => t.appendChild(h('tr', {},
    h('td', {text:String(r.rank || '-')}), h('td', {}, h('b', {text:r.roll})),
    h('td', {text:r.name || '-'}), h('td', {text:String(r.score ?? '-')}),
    h('td', {text:String(r.correct ?? '-')}), h('td', {text:String(r.wrong ?? '-')}),
    h('td', {text:String(r.unattempted ?? '-')}),
    h('td', {text:r.status}), h('td', {text:String(r.tab_switches || 0)}),
    h('td', {class:'tiny', text:(r.submitted_at||'').slice(11,19) || '-'}))));
  card.appendChild(h('div', {class:'scroll', style:'margin-top:12px'}, t));
  host.appendChild(card);

  if(STATE.analysis && STATE.analysis.length){
    const a = h('div', {class:'card'}, h('h2', {text:'Question-wise analysis (teaching insight)'}));
    const at = h('table', {}, h('tr', {}, ...['Q','Question','Correct','Wrong','Skip',
      'Correct %','Difficulty'].map(x=>h('th',{text:x}))));
    STATE.analysis.forEach(q => at.appendChild(h('tr', {},
      h('td', {text:String(q.order_no)}),
      h('td', {text:(q.text||'').slice(0,70) + (q.dropped ? ' (dropped)' : '')}),
      h('td', {text:String(q.correct)}), h('td', {text:String(q.wrong)}),
      h('td', {text:String(q.skipped)}),
      h('td', {}, h('span', {class:'tag ' + (q.correct_pct >= 70 ? 'ok' : q.correct_pct < 30 ? 'closed' : 'warn'),
        text:q.correct_pct + '%'})),
      h('td', {text:q.difficulty_seen}))));
    a.appendChild(h('div', {class:'scroll'}, at));
    a.appendChild(h('p', {class:'tiny',
      text:'Mistake unna question kanipisthe "Drop" cheyandi (Questions tab) — marks automatic recalculate avutayi.'}));
    host.appendChild(a);
  }
}
async function publishResults(){
  const ok = await confirmBox('Results publish cheyyala?',
    ['Students link lo score, rank, review kanipistundi.',
     'Ivvaraku submit cheyyani students ki "pending" ga kanipistundi.'], '🏆 Publish');
  if(!ok) return;
  try{ await api('/api/admin/exam/' + CODE + '/results/publish', {body:{key: KEY}});
    toast('🏆 Results published'); load();
  }catch(e){ toast(e.message); }
}

/* ------------------------------------------------------------------ share */
function tabShare(host){
  const link = STATE.studentLink;
  const card = h('div', {class:'card'}, h('h2', {text:'Student link & messages'}));
  card.appendChild(h('label', {text:'Student link (idi share cheyandi)'}));
  card.appendChild(h('div', {class:'codebox', text: link}));
  card.appendChild(h('div', {class:'row', style:'margin-top:10px'},
    h('button', {class:'btn orange sm', onclick:()=>copyText(link, 'Link copied')}, '📋 Copy link'),
    h('button', {class:'btn ghost sm', onclick:()=>copyText('Exam code: ' + CODE, 'Code copied')}, 'Copy exam code'),
    h('button', {class:'btn ghost sm', onclick:()=>window.open('https://wa.me/?text=' + encodeURIComponent(STATE.templates.whatsapp_group), '_blank')}, '💬 WhatsApp share')));
  card.appendChild(h('p', {class:'tiny',
    text:'QR kavali ante: browser address bar lo link ni QR generator lo paste cheyandi (example: qr.io) — hall/notice board ki print cheyochu.'}));
  host.appendChild(card);

  const t = h('div', {class:'card'}, h('h2', {text:'Copy-paste message templates'}));
  const items = [['whatsapp_group','WhatsApp group message'], ['sms','SMS / short'],
    ['start_alert','Exam START alert'], ['results_alert','Results alert'],
    ['notice_board','Notice board print'], ['email_line','Email line']];
  items.forEach(([k, label])=>{
    t.appendChild(h('div', {style:'margin-top:10px'},
      h('div', {class:'flex-between'}, h('b', {text:label}),
        h('button', {class:'btn xs ghost', onclick:()=>copyText(STATE.templates[k] || '', label + ' copied')}, 'Copy')),
      h('div', {class:'codebox', text: STATE.templates[k] || ''})));
  });
  host.appendChild(t);

  const n = h('div', {class:'card'}, h('h2', {text:'Notification log'}));
  (STATE.notifications||[]).forEach(x => n.appendChild(h('div', {class:'tiny',
    text: x.created_at.slice(11,19) + ' · ' + x.channel + ' · ' + x.status +
      (x.detail ? ' · ' + x.detail : '')})));
  if(!(STATE.notifications||[]).length) n.appendChild(h('p', {class:'muted',
    text:'Inka notifications levu. Telegram/webhook configure chesthe automatic ga pampabadutayi (Share tab lo templates eppudu ready).'}));
  n.appendChild(h('p', {class:'tiny',
    text:'Configure: EXAM_TELEGRAM_BOT_TOKEN + EXAM_TELEGRAM_CHAT_ID, leda EXAM_WEBHOOK_URL (WhatsApp Business API / SMS gateway / Slack).'}));
  host.appendChild(n);
}

/* --------------------------------------------------------------- settings */
function tabSettings(host){
  const e = STATE.exam;
  const card = h('div', {class:'card'}, h('h2', {text:'Exam settings'}));
  const fields = [['title','Exam title', e.title], ['college','College', e.college],
    ['subject','Subject', e.subject], ['exam_date','Exam date', e.exam_date],
    ['duration_min','Duration (min)', e.duration_min],
    ['per_q_marks','Marks per question', e.per_q_marks],
    ['negative_marks','Negative marks', e.negative_marks],
    ['pass_marks','Pass marks', e.pass_marks]];
  const grid = h('div', {class:'grid c2'});
  fields.forEach(([k, label, v])=>{
    grid.appendChild(h('div', {}, h('label', {text:label}),
      h('input', {id:'set_' + k, value: String(v ?? '')})));
  });
  grid.appendChild(h('div', {}, h('label', {text:'Result mode'}),
    h('select', {id:'set_show_result'},
      ...[['immediate','Immediate'],['after_publish','After publish'],['never','Hide']]
        .map(([v,l]) => h('option', {value:v, selected: e.show_result === v ? 'selected' : null}, l)))));
  grid.appendChild(h('div', {}, h('label', {text:'Allow late join'}),
    h('select', {id:'set_allow_late_join'},
      ...[['1','Yes'],['0','No']].map(([v,l]) =>
        h('option', {value:v, selected: String(e.allow_late_join) === v ? 'selected' : null}, l)))));
  grid.appendChild(h('div', {}, h('label', {text:'Auto-start when all joined'}),
    h('select', {id:'set_auto_start_all_joined'},
      ...[['1','Yes'],['0','No']].map(([v,l]) =>
        h('option', {value:v, selected: String(e.auto_start_all_joined) === v ? 'selected' : null}, l)))));
  grid.appendChild(h('div', {}, h('label', {text:'Roster compulsory'}),
    h('select', {id:'set_roster_required'},
      ...[['1','Yes'],['0','No']].map(([v,l]) =>
        h('option', {value:v, selected: String(e.roster_required) === v ? 'selected' : null}, l)))));
  card.appendChild(grid);
  card.appendChild(h('label', {text:'Instructions'}));
  card.appendChild(h('textarea', {id:'set_instructions'}, e.instructions || ''));
  card.appendChild(h('div', {class:'row', style:'margin-top:12px'},
    h('button', {class:'btn orange sm', onclick:()=>saveSettings()}, 'Save settings'),
    h('button', {class:'btn ghost sm', onclick:()=>doUnpublish()}, 'Unpublish (back to draft)'),
    e.status === 'draft' ? h('button', {class:'btn green sm', onclick:()=>doPublish()}, '✅ Publish exam') : null));
  card.appendChild(h('p', {class:'tiny',
    text:'Published exam settings change cheyyochemu kaani, live lo duration/negative marks marchadam students ki confuse avutundi — time kevalam +5/+10 min buttons tho penchandi.'}));
  host.appendChild(card);
}
async function saveSettings(){
  const body = {key: KEY};
  ['title','college','subject','exam_date','instructions','show_result'].forEach(k=>{
    const el = document.getElementById('set_' + k); if(el) body[k] = el.value;
  });
  ['duration_min','per_q_marks','negative_marks','pass_marks'].forEach(k=>{
    const el = document.getElementById('set_' + k); if(el) body[k] = parseFloat(el.value)||0;
  });
  ['allow_late_join','auto_start_all_joined','roster_required'].forEach(k=>{
    const el = document.getElementById('set_' + k);
    if(el) body[k] = el.value === '1';
  });
  try{ await api('/api/admin/exam/' + CODE + '/settings', {body}); toast('Settings saved ✔'); load(); }
  catch(e){ toast(e.message, 4000); }
}
async function doPublish(){
  try{ await api('/api/admin/exam/' + CODE + '/publish', {body:{key: KEY}});
    toast('✅ Published — student link share cheyandi'); load();
  }catch(e){ toast(e.message, 5000); }
}
async function doUnpublish(){
  try{ await api('/api/admin/exam/' + CODE + '/unpublish', {body:{key: KEY}});
    toast('Draft ki vellindi'); load();
  }catch(e){ toast(e.message); }
}

/* ------------------------------------------------------------------ audit */
function tabAudit(host){
  const card = h('div', {class:'card'}, h('h2', {text:'Audit log (eppudu em jarigindi)'}));
  const t = h('table', {}, h('tr', {}, ...['Time','Event','Session','Detail'].map(x=>h('th',{text:x}))));
  (STATE.events||[]).forEach(x => t.appendChild(h('tr', {},
    h('td', {class:'tiny', text:(x.created_at||'').slice(11,19)}),
    h('td', {text:x.kind}), h('td', {text:x.session_id ? String(x.session_id) : '-'}),
    h('td', {class:'tiny', text:x.detail || ''}))));
  card.appendChild(h('div', {class:'scroll'}, t));
  card.appendChild(h('p', {class:'tiny',
    text:'Ee log college ki proof — join, start, submit, question drop, publish anni record avutayi.'}));
  host.appendChild(card);
}

load();
"""
    return _page("Manage — Exam Portal", ADMIN_CSS, body, script)


# ===========================================================================
# Student exam app
# ===========================================================================

def student_html() -> str:
    body = _topbar(subtitle="Exam Portal — Student") + """
<div id="announce"></div>
<div id="timerbar" class="timerbar hide"><div class="wrap">
  <span class="timer" id="timer">--:--</span>
  <div class="progress"><i id="progress"></i></div>
  <span class="savechip" id="savechip">saved</span>
  <span class="savechip" id="netchip">online</span>
</div></div>
<div class="wrap" id="app"><div class="card"><p class="muted">Load avutundi…</p></div></div>
<div class="navbar hide" id="navbar"><div class="wrap">
  <button class="btn ghost sm" id="prevBtn">← Prev</button>
  <button class="btn ghost sm" id="flagBtn">⚑ Flag</button>
  <button class="btn ghost sm" id="clearBtn">Clear</button>
  <span style="flex:1"></span>
  <button class="btn sm" id="paletteBtn">Questions</button>
  <button class="btn orange sm" id="nextBtn">Next →</button>
</div></div>
<div class="modal" id="paletteModal" onclick="if(event.target===this)closePalette()">
  <div class="box"><h2>Question palette</h2>
    <p class="tiny">🟩 answered · 🟨 flagged · ⬜ not answered · 🔵 current</p>
    <div class="palette" id="paletteGrid"></div>
    <div class="row end" style="margin-top:14px">
      <button class="btn ghost" onclick="closePalette()">Close</button>
      <button class="btn orange" onclick="askSubmit()">✅ Submit exam</button>
    </div>
  </div>
</div>"""
    script = r"""
const CODE = (location.pathname.split('/')[2] || '').toUpperCase();
const TOKEN_KEY = 'su_exam_token_' + CODE;
const PENDING_KEY = 'su_exam_pending_' + CODE;
let S = null;                 // session payload
let QUESTIONS = [];           // paper
let ANSWERS = {};            // qid -> {choice, flagged}
let IDX = 0;
let OFFSET = 0;               // server_now - client_now (ms)
let TICK = null;
let SAVING = 0;

function tok(){ return localStorage.getItem(TOKEN_KEY) || ''; }
function setTok(t){ localStorage.setItem(TOKEN_KEY, t); }
function pending(){ try{ return JSON.parse(localStorage.getItem(PENDING_KEY) || '{}'); }catch(e){ return {}; } }
function setPending(obj){ localStorage.setItem(PENDING_KEY, JSON.stringify(obj)); }

function el(id){ return document.getElementById(id); }
function app(){ return el('app'); }
function clearApp(){ app().innerHTML = ''; }

/* -------------------------------------------------------------- lifecycle */
async function boot(){
  try{
    if(tok()){
      try{ await resume(); return; }catch(e){ localStorage.removeItem(TOKEN_KEY); }
    }
    await showJoin();
  }catch(e){
    clearApp();
    app().appendChild(h('div', {class:'card'}, h('h1', {text:'Problem'}),
      h('div', {class:'banner err', text:e.message}),
      h('button', {class:'btn', onclick:()=>location.reload()}, 'Retry')));
  }
}
async function resume(){
  S = await api('/api/session?token=' + encodeURIComponent(tok()));
  OFFSET = Date.parse(S.server_now) - Date.now();
  route();
}
function route(){
  if(S.status === 'waiting'){ renderWaiting(); return; }
  if(S.status === 'submitted'){ renderResult(); return; }
  QUESTIONS = S.questions || QUESTIONS;
  Object.keys(S.answers || {}).forEach(k => ANSWERS[k] = S.answers[k]);
  syncPending();
  renderExam();
  startTimer();
  startHeartbeat();
}

/* ------------------------------------------------------------------ join */
async function showJoin(){
  el('timerbar').classList.add('hide'); el('navbar').classList.add('hide');
  clearApp();
  const info = await api('/api/exam-info/' + CODE);
  const e = info.exam;
  S = {exam: e, status: 'join'};
  const card = h('div', {class:'card'});
  card.appendChild(h('h1', {text: e.title}));
  card.appendChild(h('p', {class:'muted', text: [e.college, e.subject,
    e.exam_date ? 'Exam date: ' + e.exam_date : ''].filter(Boolean).join(' · ')}));
  card.appendChild(h('div', {class:'row', style:'margin-top:8px'},
    h('span', {class:'tag ' + (e.status === 'live' ? 'live' : e.status === 'closed' ? 'closed' : 'published'),
      text: e.status.toUpperCase()}),
    h('span', {class:'pill tag', text: e.duration_min + ' min'}),
    h('span', {class:'pill tag', text: e.questions + ' questions'}),
    e.negative_marks ? h('span', {class:'tag warn', text:'−' + e.negative_marks + ' negative'}) : null,
    h('span', {class:'pill tag', text: 'Marks: ' + e.per_q_marks + ' each'})));
  if(e.instructions){
    card.appendChild(h('h3', {style:'margin-top:14px', text:'Instructions'}));
    card.appendChild(h('div', {class:'banner info', style:'white-space:pre-wrap', text:e.instructions}));
  }
  const form = h('div', {style:'margin-top:12px'});
  form.appendChild(h('label', {text:'Roll number *'}));
  form.appendChild(h('input', {id:'rollInput', placeholder:'21B01A0501', autocomplete:'off'}));
  form.appendChild(h('label', {text:'Name (optional)'}));
  form.appendChild(h('input', {id:'nameInput', placeholder:'Mee peru'}));
  form.appendChild(h('div', {class:'row', style:'margin-top:14px'},
    h('button', {class:'btn orange', id:'joinBtn', onclick:()=>joinNow()}, 'Join exam →')));
  form.appendChild(h('p', {class:'tiny',
    text:'Password avasaram ledu — roll number matrame. Okka roll number ki okka device matrame (duplicate attempt block avutundi).'}));
  card.appendChild(form);
  app().appendChild(card);
  el('rollInput').addEventListener('keydown', e2 => { if(e2.key === 'Enter') joinNow(); });
  el('rollInput').focus();
}
async function joinNow(){
  const roll = (el('rollInput').value || '').trim();
  const name = (el('nameInput').value || '').trim();
  if(!roll){ toast('Roll number type cheyandi'); return; }
  el('joinBtn').disabled = true;
  try{
    const out = await api('/api/join', {body:{code: CODE, roll, name, token: tok()}});
    setTok(out.token);
    S = out;
    OFFSET = Date.parse(S.server_now) - Date.now();
    toast('Joined ✔ — exam start ayye varaku wait cheyandi');
    route();
  }catch(e){
    toast(e.message, 5000);
    if(e.message.toLowerCase().indexOf('already') >= 0){
      app().appendChild(h('div', {class:'banner warn',
        text:e.message + ' — mee device lo already join ayyi undi ante, same browser/tab use cheyandi.'}));
    }
  }
  const jb = el('joinBtn');
  if(jb) jb.disabled = false;     // join success aithe screen maripoyindi — null check
}

/* ---------------------------------------------------------------- waiting */
function renderWaiting(){
  clearApp(); el('navbar').classList.add('hide');
  el('timerbar').classList.add('hide');
  const card = h('div', {class:'card'});
  card.appendChild(h('h1', {text:'⏳ Waiting — exam inka start kaledu'}));
  card.appendChild(h('p', {class:'muted',
    text:'Mee roll ' + (S.roll || '') + ' register ayyindi. College START nokkagane timer start avutundi — ee page ni open ga unchandi.'}));
  card.appendChild(h('div', {class:'banner info', text:'Tip: phone ni silent lo pettandi, screen lock cheyyakandi, internet on unchandi.'}));
  card.appendChild(h('p', {class:'tiny', id:'waitHint', text:'Status check avutundi…'}));
  app().appendChild(card);
  startHeartbeat();
}

/* ------------------------------------------------------------------- exam */
function renderExam(){
  el('navbar').classList.remove('hide');
  el('timerbar').classList.remove('hide');
  clearApp();
  if(!QUESTIONS.length){
    app().appendChild(h('div', {class:'card'}, h('div', {class:'banner err',
      text:'Question paper load avvaledu — page refresh cheyandi leda staff ni adagandi.'})));
    return;
  }
  const q = QUESTIONS[IDX];
  const a = ANSWERS[q.id] || {};
  const card = h('div', {class:'qcard'});
  card.appendChild(h('div', {class:'flex-between'},
    h('span', {class:'qnum', text:'Question ' + (IDX+1) + ' of ' + QUESTIONS.length +
      (q.marks ? ' · ' + q.marks + ' marks' : '')}),
    a.flagged ? h('span', {class:'tag warn', text:'⚑ Flagged'}) : null));
  card.appendChild(h('div', {class:'qtext', text: q.text}));
  q.options.forEach((opt, oi)=>{
    const sel = a.choice === oi;
    card.appendChild(h('div', {class:'opt' + (sel ? ' sel' : ''), onclick:()=>choose(q.id, oi)},
      h('span', {class:'k', text:String.fromCharCode(65+oi)}),
      h('span', {class:'t', text: opt})));
  });
  card.appendChild(h('div', {class:'row', style:'margin-top:12px'},
    h('span', {class:'tiny', id:'savedHint', text:'Prathi click ki automatic save avutundi.'})));
  app().appendChild(card);
  app().appendChild(h('div', {class:'card tight'},
    h('div', {class:'row'},
      h('button', {class:'btn ghost sm', onclick:()=>askSubmit()}, '✅ Submit exam'),
      h('button', {class:'btn ghost sm', onclick:()=>openPalette()}, 'Questions list'),
      h('button', {class:'btn ghost sm', onclick:()=>flagCurrent()}, ANSWERS[q.id] && ANSWERS[q.id].flagged ? '⚑ Unflag' : '⚑ Flag for review'))));
  updateNav();
}
function choose(qid, oi){
  ANSWERS[qid] = Object.assign({}, ANSWERS[qid] || {}, {choice: oi});
  const p = pending(); p[qid] = Object.assign({}, p[qid] || {}, {choice: oi});
  setPending(p);
  renderExam();
  flush();
}
function flagCurrent(){
  const qid = QUESTIONS[IDX].id;
  const cur = (ANSWERS[qid] || {}).flagged;
  ANSWERS[qid] = Object.assign({}, ANSWERS[qid] || {}, {flagged: !cur});
  const p = pending(); p[qid] = Object.assign({}, p[qid] || {}, {flagged: !cur});
  setPending(p);
  renderExam(); flush();
}
function updateNav(){
  el('prevBtn').disabled = IDX === 0;
  el('nextBtn').textContent = IDX === QUESTIONS.length - 1 ? 'Last question' : 'Next →';
  el('nextBtn').disabled = IDX === QUESTIONS.length - 1;
}
function nextQ(){ if(IDX < QUESTIONS.length - 1){ IDX++; renderExam(); } }
function prevQ(){ if(IDX > 0){ IDX--; renderExam(); } }
function openPalette(){
  const g = el('paletteGrid'); g.innerHTML = '';
  QUESTIONS.forEach((q, i)=>{
    const a = ANSWERS[q.id] || {};
    const cls = i === IDX ? 'current' : (a.flagged ? 'flagged' : (a.choice !== undefined && a.choice !== null ? 'answered' : ''));
    g.appendChild(h('button', {class:'pbtn ' + cls, text:String(i+1),
      onclick:()=>{ IDX = i; closePalette(); renderExam(); }}));
  });
  el('paletteModal').classList.add('show');
}
function closePalette(){ el('paletteModal').classList.remove('show'); }

/* ------------------------------------------------------------------ saving */
async function flush(){
  const p = pending();
  const ids = Object.keys(p);
  if(!ids.length){ setChip('saved'); return; }
  SAVING++;
  setChip('saving');
  for(const qid of ids){
    const a = p[qid];
    try{
      await api('/api/session/answer', {body:{token: tok(), question_id: parseInt(qid, 10),
        choice: (a.choice === undefined ? null : (a.choice === null ? -1 : a.choice)),
        flagged: (a.flagged === undefined ? null : a.flagged)}});
      const cur = pending(); delete cur[qid]; setPending(cur);
      setChip('saved');
    }catch(err){
      setChip('offline');
      break;
    }
  }
  SAVING--;
  const el2 = document.getElementById('savedHint');
  if(el2) el2.textContent = (pendingCount() ? 'Pending sync… (internet check cheyandi)' : 'Answers saved ✔');
}
function pendingCount(){ return Object.keys(pending()).length; }
function setChip(state){
  const c = el('savechip');
  if(!c) return;
  c.className = 'savechip ' + (state === 'saved' ? 'ok' : state === 'saving' ? 'busy' : 'off');
  c.textContent = state === 'saved' ? 'saved ✔' : state === 'saving' ? 'saving…' : 'offline ⚠';
}

/* ------------------------------------------------------------------- timer */
function startTimer(){
  clearInterval(TICK);
  tickTimer();
  TICK = setInterval(tickTimer, 1000);
}
function tickTimer(){
  const remaining = Math.max(0, (Date.parse(S.end_at) - (Date.now() + OFFSET)) / 1000);
  const t = el('timer');
  if(t){
    t.textContent = fmtTime(remaining);
    t.className = 'timer' + (remaining <= 60 ? ' danger' : remaining <= 300 ? ' warn' : '');
  }
  const total = (S.exam.duration_min || 1) * 60;
  const bar = el('progress');
  if(bar) bar.style.width = Math.min(100, Math.max(0, 100 * (1 - remaining / total))) + '%';
  if(remaining <= 0){
    clearInterval(TICK);
    autoSubmit();
  }
}
async function autoSubmit(){
  setChip('saving');
  toast('⏰ Time over — automatic submit avutundi…', 4000);
  try{
    await flush();
    const out = await api('/api/session/submit', {body:{token: tok(), auto: true}});
    S.result = out.result; S.status = 'submitted';
    renderResult();
  }catch(e){ toast('Submit lo problem — staff ki cheppandi: ' + e.message, 6000); }
}

/* --------------------------------------------------------------- heartbeat */
let HB = null;
function startHeartbeat(){
  clearInterval(HB);
  beat();
  HB = setInterval(beat, 10000);
}
async function beat(){
  try{
    const out = await api('/api/session/heartbeat', {body:{token: tok()}});
    OFFSET = Date.parse(out.server_now) - Date.now();
    el('netchip').className = 'savechip ok'; el('netchip').textContent = 'online';
    if(out.announcement){
      const host = el('announce');
      host.innerHTML = '';
      host.appendChild(h('div', {class:'wrap'}, h('div', {class:'banner info',
        text:'📢 ' + out.announcement})));
    }
    if(out.status === 'submitted'){
      clearInterval(HB); clearInterval(TICK);
      S.result = null;
      const st = await api('/api/session?token=' + encodeURIComponent(tok()));
      S = st; renderResult(); return;
    }
    if(out.exam_status === 'closed' && S.status !== 'submitted'){
      clearInterval(HB); clearInterval(TICK);
      toast('Exam close ayyindi — submit avutundi', 4000);
      await autoSubmit(); return;
    }
    if(out.questions && !QUESTIONS.length){
      QUESTIONS = out.questions; renderExam();
    }
    if(S.status === 'waiting'){
      const hint = el('waitHint');
      if(hint) hint.textContent = 'Waiting… (server ' + out.server_now.slice(11,19) + ')';
      if(out.status === 'active'){
        const st = await api('/api/session?token=' + encodeURIComponent(tok()));
        S = st; S.status = 'active';
        QUESTIONS = st.questions || [];
        Object.keys(st.answers || {}).forEach(k => ANSWERS[k] = st.answers[k]);
        toast('🚀 Exam START ayyindi — all the best!', 4000);
        renderExam(); startTimer();
      }
    }
    if(pendingCount()) flush();
  }catch(e){
    const n = el('netchip');
    if(n){ n.className = 'savechip off'; n.textContent = 'offline ⚠'; }
  }
}

/* ------------------------------------------------------------------ submit */
async function askSubmit(){
  closePalette();
  const answeredN = QUESTIONS.filter(q => ANSWERS[q.id] && ANSWERS[q.id].choice !== undefined
    && ANSWERS[q.id].choice !== null).length;
  const flaggedN = QUESTIONS.filter(q => ANSWERS[q.id] && ANSWERS[q.id].flagged).length;
  const ok = await confirmBox('Exam submit cheyyala?',
    ['Answered: ' + answeredN + ' / ' + QUESTIONS.length,
     'Not answered: ' + (QUESTIONS.length - answeredN),
     'Flagged: ' + flaggedN,
     'Submit tarvata answers marchadam possible kaadu.'],
    '✅ Submit now');
  if(!ok) return;
  const btn = document.getElementById('nextBtn');
  try{
    clearInterval(HB); clearInterval(TICK);
    await flush();
    const out = await api('/api/session/submit', {body:{token: tok()}});
    S.result = out.result; S.status = 'submitted';
    renderResult();
  }catch(e){ toast(e.message, 5000); startHeartbeat(); startTimer(); }
}

/* ------------------------------------------------------------------ result */
function renderResult(){
  clearApp(); el('navbar').classList.add('hide'); el('timerbar').classList.add('hide');
  const r = (S.result || {});
  const card = h('div', {class:'card'});
  if(S.status !== 'submitted'){
    card.appendChild(h('h1', {text:'✅ Submitted'}));
    card.appendChild(h('p', {class:'muted',
      text:'Mee answers submit ayyayi. Results publish ayyaka ee link lo kanipistundi.'}));
    app().appendChild(card); return;
  }
  card.appendChild(h('h1', {text:'✅ Exam submit ayyindi'}));
  const published = r.results_published || (r.show_result === 'immediate');
  if(!published){
    card.appendChild(h('div', {class:'banner info',
      text:'Results ippude publish cheyaledu. College publish cheyagane ee page lo kanipistundi (ee link/bookmark unchandi).'}));
  }
  card.appendChild(h('div', {class:'grid c3', style:'margin-top:10px'},
    h('div', {class:'kpi'}, h('b', {class:'result-score', text: published ? String(r.score) : '—'}),
      h('span', {text:'Score / ' + (r.total_marks || '-')})),
    h('div', {class:'kpi'}, h('b', {text: r.correct}), h('span', {text:'Correct'})),
    h('div', {class:'kpi'}, h('b', {text: r.wrong}), h('span', {text:'Wrong'})),
    h('div', {class:'kpi'}, h('b', {text: r.unattempted}), h('span', {text:'Not answered'})),
    h('div', {class:'kpi'}, h('b', {text: r.rank ? '#' + r.rank : '—'}), h('span', {text:'Rank'})),
    h('div', {class:'kpi'}, h('b', {text: r.passed === null || r.passed === undefined ? '—' : (r.passed ? 'PASS ✅' : 'FAIL')}),
      h('span', {text:'Result'}))));
  if(r.auto_submitted) card.appendChild(h('div', {class:'banner warn',
    text:'⏰ Time ayyaka automatic ga submit ayyindi.'}));
  if(r.review && r.review.length){
    card.appendChild(h('h2', {style:'margin-top:16px', text:'Question-wise review'}));
    r.review.forEach((x, i)=>{
      const row = h('div', {class:'review ' + x.result});
      row.appendChild(h('b', {text:'Q' + (i+1) + '. ' + x.text}));
      const fmtOpt = (idx, txt) => (idx === null || idx === undefined) ? '—'
        : String.fromCharCode(65 + idx) + (txt ? ') ' + txt : '');
      row.appendChild(h('div', {class:'tiny',
        text:'Mee answer: ' + (x.your_answer === null || x.your_answer === undefined
          ? '— (not answered)' : fmtOpt(x.your_answer, x.your_answer_text)) +
          ' · Correct: ' + fmtOpt(x.correct_index, x.correct_answer_text)}));
      if(x.explanation) row.appendChild(h('div', {class:'tiny', text:'వివరణ: ' + x.explanation}));
      card.appendChild(row);
    });
  }
  app().appendChild(card);
}

/* --------------------------------------------------------------- lifecycle */
document.addEventListener('visibilitychange', ()=>{
  if(document.hidden && S && S.status === 'active' && tok()){
    api('/api/session/tabswitch', {body:{token: tok()}}).catch(()=>{});
  }
});
window.addEventListener('online', ()=>{ if(tok() && S && S.status === 'active') flush(); });
window.addEventListener('beforeunload', e=>{
  if(S && S.status === 'active'){ e.preventDefault(); e.returnValue = ''; }
});
el('prevBtn').addEventListener('click', prevQ);
el('nextBtn').addEventListener('click', nextQ);
el('flagBtn').addEventListener('click', flagCurrent);
el('clearBtn').addEventListener('click', ()=>{
  const q = QUESTIONS[IDX]; if(!q) return;
  ANSWERS[q.id] = Object.assign({}, ANSWERS[q.id] || {}, {choice: null});
  const p = pending(); p[q.id] = Object.assign({}, p[q.id] || {}, {choice: null});
  setPending(p); renderExam(); flush();
});
el('paletteBtn').addEventListener('click', openPalette);
boot();
"""
    return _page("Exam — studentup.in", STUDENT_CSS, body, script)
