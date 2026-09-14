/**
 * v39 Exam Portal — OPTIONAL browser-level smoke test (jsdom).
 *
 * Python test suite (tests/v39_exam_portal_test.py section 14) JS syntax ni
 * check chestundi; ee script asalu pages ni DOM lo run chesi FULL flow
 * (admin login → exam create → questions → roster → publish → START →
 *  student join → answers → submit → CLOSE → exports) verify chestundi.
 *
 * Usage (jsdom optional dependency — repo lo install cheyyaru):
 *   mkdir -p /tmp/uismoke && cd /tmp/uismoke && npm init -y && npm i jsdom
 *   # portal ni okka port lo start cheyandi:
 *   python run.py --exam-portal --exam-port 8098   # inkoka terminal lo
 *   cp <repo>/tools/ui_smoke.mjs .
 *   BASE=http://127.0.0.1:8098 ADMIN_KEY=<mee key> node ui_smoke.mjs
 *
 * Note: idi repo test-suite lo part kaadu (node + jsdom optional). CI/dev
 * machine lo node unte run cheyochu — real browser typos ikkade pattukovachu.
 */
import { JSDOM, VirtualConsole } from "jsdom";

const BASE = process.env.BASE || "http://127.0.0.1:8098";
const KEY = process.env.ADMIN_KEY || "testadmin";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
let errors = [];
let checks = 0;

function ok(label, cond, extra = "") {
  checks++;
  if (cond) console.log(`  ✔ ${label}${extra ? " — " + extra : ""}`);
  else {
    console.log(`  ✘ ${label}${extra ? " — " + extra : ""}`);
    errors.push(label);
  }
}

async function openPage(path) {
  const vc = new VirtualConsole();
  vc.on("jsdomError", (e) => {
    const msg = String(e.message || e);
    if (msg.includes("navigation") || msg.includes("Not implemented")) return;
    if (msg.includes("Could not load style") || msg.includes("Could not load link")) return;
    errors.push(`jsdomError@${path}: ${msg}`);
    console.log(`  ✘ JS error @ ${path}: ${msg}`);
  });
  const dom = await JSDOM.fromURL(BASE + path, {
    runScripts: "dangerously",
    resources: "usable",
    pretendToBeVisual: true,
    virtualConsole: vc,
    beforeParse(window) {
      // page scripts boot avvakamundhe inject (real browser la fetch/clipboard untayi)
      window.fetch = (url, opts) => fetch(new URL(String(url), BASE).toString(), opts);
      window.navigator.clipboard = { writeText: async () => {} };
      window.Element.prototype.scrollIntoView = function () {};
      window.HTMLElement.prototype.focus = function () {};
      window.document.execCommand = () => true;
    },
  });
  const w = dom.window;
  await sleep(700);
  return dom;
}

const txt = (w, sel) => (w.document.querySelector(sel) || {}).textContent || "";
const click = (w, sel) => {
  const el = w.document.querySelector(sel);
  if (!el) throw new Error(`element not found: ${sel}`);
  el.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  return el;
};
const setVal = (w, sel, v) => {
  const el = w.document.querySelector(sel);
  if (!el) throw new Error(`input not found: ${sel}`);
  el.value = v;
  el.dispatchEvent(new w.Event("input", { bubbles: true }));
  return el;
};
const confirmModal = async (w, label) => {
  const btns = [...w.document.querySelectorAll("#modalBox button")];
  const target = btns.find((b) => (b.textContent || "").includes(label)) || btns[btns.length - 1];
  if (!target) throw new Error("confirm modal button not found");
  target.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(400);
};

async function waitFor(fn, ms = 6000, step = 150) {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    try { if (fn()) return true; } catch (e) { /* keep waiting */ }
    await sleep(step);
  }
  return false;
}

const RAW_QUESTIONS = `1. Capital of Telangana?
A) Warangal
B) Hyderabad
C) Karimnagar
D) Nizamabad
Answer: B
Explanation: Hyderabad Telangana rajadhani.

2. 2 + 2 = ?
A) 3
B) 4
Answer: B

3. TSPSC full form?
A) Telangana State Public Service Commission
B) Telangana Staff Selection Commission
Answer: A
`;

async function main() {
  console.log("v39 UI (jsdom) validation — BASE=" + BASE);

  /* ---------------------------------------------------------------- admin */
  console.log("\n[1] /admin — login + create exam");
  let dom = await openPage("/admin");
  let w = dom.window;
  ok("login card visible", !w.document.querySelector("#loginCard").classList.contains("hide"));
  setVal(w, "#keyInput", "wrong-key");
  click(w, "#loginBtn");
  await sleep(600);
  ok("wrong key → error message", /tappu|unauthorized|key/i.test(txt(w, "#loginMsg")), txt(w, "#loginMsg").slice(0, 60));
  setVal(w, "#keyInput", KEY);
  click(w, "#loginBtn");
  await sleep(800);
  ok("correct key → dashboard shown", w.document.querySelector("#dash") && !w.document.querySelector("#dash").classList.contains("hide"));

  const newExamBtn = [...w.document.querySelectorAll("#dash button")]
    .find((b) => (b.textContent || "").includes("New exam"));
  newExamBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(200);
  ok("create form opened", !w.document.querySelector("#createCard").classList.contains("hide"));
  setVal(w, "#f_college", "UI Test College");
  setVal(w, "#f_title", "UI Driven Test — GK");
  setVal(w, "#f_subject", "GK");
  setVal(w, "#f_duration", "5");
  setVal(w, "#f_marks", "2");
  setVal(w, "#f_neg", "0.5");
  setVal(w, "#f_pass", "4");
  setVal(w, "#f_roster", "1");        // roster compulsory (roll list gate test)
  click(w, "#createBtn");
  await sleep(900);
  const toastTxt = txt(w, "#toast");
  const m = toastTxt.match(/Exam create ayyindi\s+([A-Z0-9]{4,8})/);
  ok("create exam via UI", !!m, toastTxt.slice(0, 60));
  const code = m ? m[1] : null;
  console.log("     CODE =", JSON.stringify(code), "| toast:", JSON.stringify(toastTxt.slice(0, 70)));
  ok("admin key stored in localStorage", !!w.localStorage.getItem("su_admin_key"));
  dom.window.close();

  /* --------------------------------------------------------------- manage */
  console.log("\n[2] /manage — questions, roster, publish, START");
  const examsOut = await (await fetch(`${BASE}/api/admin/exams?key=${KEY}`)).json();
  const created = (examsOut.exams || []).find((e) => e.code === code);
  const token = created && created.admin_token;
  ok("exam listed in admin API with per-exam manage token", !!token,
    `code=${code} link=/manage/${code}`);
  dom = await openPage(`/manage/${code}?key=${token}`);
  w = dom.window;
  await waitFor(() => /UI Driven Test/.test(txt(w, "#examTitle")));
  ok("exam title rendered", /UI Driven Test/.test(txt(w, "#examTitle")), txt(w, "#examTitle"));
  ok("start button initially disabled (no questions)",
    w.document.querySelector("#startBtn").disabled === true);
  ok("blockers visible", /Questions/i.test(txt(w, "#warnBox").replace(/\s+/g, " ")), txt(w, "#warnBox").slice(0, 70));

  // questions tab
  const tabLabelNow = () => [...w.document.querySelectorAll("#tabs button")]
    .map((b) => (b.textContent || "").trim());
  const tabBtn = (label) => {
    const b = [...w.document.querySelectorAll("#tabs button")]
      .find((x) => (x.textContent || "").includes(label));
    if (!b) throw new Error(`tab "${label}" not found; have: ${JSON.stringify(tabLabelNow())}`);
    return b;
  };
  tabBtn("Questions").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(300);
  setVal(w, "#bulk", RAW_QUESTIONS);
  const addBtn = [...w.document.querySelectorAll("#tabBody button")]
    .find((b) => (b.textContent || "").includes("Parse & add"));
  addBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(900);
  ok("bulk questions added", /Added:\s*3/.test(txt(w, "#bulkReport")) && !/errors/.test(txt(w, "#bulkReport")),
    txt(w, "#bulkReport").replace(/\s+/g, " ").slice(0, 70));
  ok("question list rendered with options", /Hyderabad/.test(txt(w, "#tabBody")));

  // roster tab
  tabBtn("Student list").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(500);
  setVal(w, "#rosterBox", "R001, Ravi\nR002, Sita\nR002, Duplicate\n");
  const saveBtn = [...w.document.querySelectorAll("#tabBody button")]
    .find((b) => (b.textContent || "").includes("Save list"));
  saveBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(800);
  const rosterReport = txt(w, "#rosterReport").replace(/\s+/g, " ");
  ok("roster saved + duplicate flagged", /Saved: 2/.test(rosterReport) && /Duplicate skip: R002/.test(rosterReport),
    rosterReport.slice(0, 80));
  ok("roster preview table renders (no JS error)", /students/.test(rosterReport));

  // settings tab: turn off shuffle + pass marks
  tabBtn("Settings").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(300);
  const settBtn = [...w.document.querySelectorAll("#tabBody button")]
    .find((b) => (b.textContent || "").includes("Save settings"));
  ok("settings tab renders", !!settBtn);
  if (settBtn) { settBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true })); await sleep(700); }

  // publish
  const pubBtn = [...w.document.querySelectorAll("button")]
    .find((b) => (b.textContent || "").includes("Publish"));
  ok("publish button present", !!pubBtn);
  if (pubBtn) { pubBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true })); await sleep(900); }
  ok("status shows PUBLISHED", /PUBLISHED|published/i.test(txt(w, "#statusRow")), txt(w, "#statusRow").slice(0, 60));
  ok("start button now enabled", w.document.querySelector("#startBtn").disabled === false);

  /* -------------------------------------------------------------- student */
  console.log("\n[3] /exam — student join (waiting room)");
  const sdom = await openPage(`/exam/${code}`);
  const sw = sdom.window;
  await sleep(800);
  ok("join form rendered", !!sw.document.querySelector("#rollInput") && /Join exam/.test(txt(sw, "#app")));
  setVal(sw, "#rollInput", "R404");
  click(sw, "#joinBtn");
  await sleep(800);
  ok("unknown roll blocked with message", /ledu|confirm/i.test(txt(sw, "#app").replace(/\s+/g, " ")),
    txt(sw, "#app").replace(/\s+/g, " ").slice(0, 70));
  setVal(sw, "#rollInput", "r001");
  setVal(sw, "#nameInput", "Ravi");
  click(sw, "#joinBtn");
  await sleep(900);
  ok("valid roll → waiting room", /wait|start/i.test(txt(sw, "#app")),
    txt(sw, "#app").replace(/\s+/g, " ").slice(0, 70));
  const stuToken = sw.localStorage.getItem("su_exam_token_" + code);
  ok("student token stored", !!stuToken);

  console.log("\n[4] admin START → student gets paper");
  click(w, "#startBtn");
  await sleep(400);
  await confirmModal(w, "START");
  await sleep(1200);
  ok("START toast", /START/.test(txt(w, "#toast")), txt(w, "#toast").slice(0, 60));
  tabBtn("Control").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(600);
  ok("control tab shows student writing/waiting", /writing|waiting/.test(txt(w, "#tabBody")),
    txt(w, "#tabBody").replace(/\s+/g, " ").slice(0, 70));

  // student page heartbeat (10s interval) nunchi state transition — force okka beat
  await sw.eval("beat()");
  await sleep(1500);
  const paperTxt = txt(sw, "#app").replace(/\s+/g, " ");
  ok("paper rendered after start", sw.document.querySelectorAll("#app .opt").length >= 2,
    paperTxt.slice(0, 80));
  ok("timer visible", /\d+:\d\d/.test(txt(sw, "#timer")), txt(sw, "#timer"));
  ok("options rendered", sw.document.querySelectorAll("#app .opt").length >= 2,
    sw.document.querySelectorAll("#app .opt").length + " options");

  const qText = () => txt(sw, "#app .qtext");
  const gotoQuestion = async (needle) => {
    for (let i = 0; i < 8; i++) {
      if (qText().includes(needle)) return true;
      const nb = sw.document.querySelector("#nextBtn");
      if (!nb || nb.disabled) break;
      nb.dispatchEvent(new sw.MouseEvent("click", { bubbles: true }));
      await sleep(260);
    }
    return qText().includes(needle);
  };
  const chooseOptByText = async (needle) => {
    const opts = [...sw.document.querySelectorAll("#app .opt")];
    const target = opts.find((o) => (o.textContent || "").includes(needle));
    if (!target) throw new Error(`option "${needle}" not found; question="${qText()}"`);
    target.dispatchEvent(new sw.MouseEvent("click", { bubbles: true }));
    await sleep(500);
  };

  let paperState = await (await fetch(`${BASE}/api/session?token=${stuToken}`)).json();
  ok("paper API returns shuffled student paper (no answer key leak)",
    (paperState.questions || []).length === 3 &&
    !Object.keys(paperState.questions[0]).includes("correct_index"),
    (paperState.questions || []).map((q) => q.text.slice(0, 12)).join(" | "));

  // student paper order lo ne forward-ga velli, correct option TEXT click (shuffle safe)
  const ANSW = { "Capital of Telangana?": "Hyderabad", "2 + 2 = ?": "4",
                 "TSPSC full form?": "Telangana State Public Service Commission" };
  for (const item of paperState.questions) {
    const key = Object.keys(ANSW).find((k) => item.text.includes(k.slice(0, 14)));
    ok(`navigated to "${item.text.slice(0, 24)}"`, await gotoQuestion(item.text.slice(0, 14)),
      qText().slice(0, 32));
    await chooseOptByText(ANSW[key]);
  }
  const stuState = await (await fetch(`${BASE}/api/session?token=${stuToken}`)).json();
  const answered = Object.values(stuState.answers || {}).filter((a) => a.choice !== null).length;
  ok("3 answers stored server-side", answered === 3, "answered=" + answered);

  // announcement + extend reach the student screen
  tabBtn("Control").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(300);
  setVal(w, "#annInput", "Q3 lo spelling mistake — ignore cheyandi");
  const annBtn = [...w.document.querySelectorAll("#tabBody button")]
    .find((b) => (b.textContent || "").includes("Send to all students"));
  annBtn.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(800);
  await sw.eval("beat()");            // announcement student screen ki vellinda?
  await sleep(900);
  ok("announcement banner reached student screen",
    /spelling mistake/.test(txt(sw, "#announce")), txt(sw, "#announce").replace(/\s+/g, " ").slice(0, 60));
  const ext5 = [...w.document.querySelectorAll("#quickRow button")]
    .find((b) => (b.textContent || "").includes("+5"));
  ok("quick +5 min button present", !!ext5);
  if (ext5) { ext5.dispatchEvent(new w.MouseEvent("click", { bubbles: true })); await sleep(700); }

  console.log("\n[5] student submit → result + review");
  await sw.eval("void askSubmit()");       // student UI: Submit exam → confirm modal
  await sleep(700);
  const sBtns = [...sw.document.querySelectorAll("#modalBox button")];
  ok("submit confirm modal has buttons", sBtns.length >= 2,
    sBtns.map((b) => (b.textContent || "").trim()).join(" / "));
  const sOk = sBtns.find((b) => /Submit|Confirm/i.test(b.textContent || "")) || sBtns[sBtns.length - 1];
  sOk.dispatchEvent(new sw.MouseEvent("click", { bubbles: true }));
  await sleep(1500);
  const resTxt = txt(sw, "#app").replace(/\s+/g, " ");
  ok("result card shown", /Result|score|Score/.test(resTxt), resTxt.slice(0, 90));
  ok("review with option text", /Hyderabad/.test(resTxt) && /Mee answer/.test(resTxt));
  ok("score 3 Q × 2 marks = 6, correct 3, rank #1, PASS",
    /Score \/ 6/.test(resTxt) && /3Correct/.test(resTxt) && /#1Rank/.test(resTxt) &&
    /PASS/.test(resTxt), resTxt.slice(0, 110));

  console.log("\n[6] admin CLOSE → results, exports, audit");
  click(w, "#closeBtn");
  await sleep(400);
  await confirmModal(w, "CLOSE");
  await sleep(1400);
  ok("CLOSE toast (auto-submit count)", /CLOSED/.test(txt(w, "#toast")), txt(w, "#toast").slice(0, 60));
  ok("status CLOSED", /CLOSED/i.test(txt(w, "#statusRow")), txt(w, "#statusRow").slice(0, 50));
  tabBtn("Results").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(700);
  const resTab = txt(w, "#tabBody").replace(/\s+/g, " ");
  ok("results tab renders (students, avg, topper)", /R001/.test(resTab) && /Average|Topper/i.test(resTab),
    resTab.slice(0, 90));
  tabBtn("Share & Notify").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(500);
  ok("share tab shows student link + templates", new RegExp(`/exam/${code}`).test(txt(w, "#tabBody")) &&
    /WhatsApp|notice/i.test(txt(w, "#tabBody")));
  tabBtn("Audit & Data").dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
  await sleep(500);
  const audit = txt(w, "#tabBody").replace(/\s+/g, " ");
  ok("audit tab lists events", /started|closed|joined|question/i.test(audit), audit.slice(0, 80));

  // exports return real CSV
  for (const kind of ["results", "questions", "analysis", "audit"]) {
    const r = await fetch(`${BASE}/api/admin/exam/${code}/export/${kind}.csv?key=${token}`);
    const body = await r.text();
    ok(`export ${kind}.csv`, r.status === 200 && body.split("\n").length >= 2 && /"/.test(body) || body.includes(","),
      `${body.split("\n").length - 1} rows`);
  }

  // duplicate device block (UI level, second window)
  const sdom2 = await openPage(`/exam/${code}`);
  await sleep(600);
  ok("closed exam → join blocked in UI", /CLOSE|close|results/i.test(txt(sdom2.window, "#app").replace(/\s+/g, " ")),
    txt(sdom2.window, "#app").replace(/\s+/g, " ").slice(0, 70));

  // landing page
  const ldom = await openPage("/");
  await sleep(400);
  ok("landing page renders", /College Exams/.test(txt(ldom.window, "body")));

  [dom, sdom, sdom2, ldom].forEach((d) => d.window.close());
  console.log(`\n${checks - errors.length}/${checks} UI checks passed`);
  if (errors.length) {
    console.log("FAILURES:\n - " + errors.join("\n - "));
    process.exit(1);
  }
  console.log("ALL v39 UI (jsdom) CHECKS PASSED ✔");
}

main().catch((e) => {
  console.error("DRIVER CRASH:", e);
  process.exit(2);
});
