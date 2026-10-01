/* v173 — WORKSPACE RUNTIME test (jsdom, real behaviour).
 *
 * Enduku: static audit kaadu — real WordPress install lo workspace page
 * data-su-ws JSON shape (smart dataset) ni load chesi, studentup-workspace.js
 * REAL ga pani chestunda prove chestundi:
 *   1) profile set cheyyadam → localStorage `su_profile_v1`
 *   2) qualification match → matching post matrame render
 *   3) not-eligible post → hidden
 *   4) deadline order → urgent first
 *   5) pipeline tiles → saved store + apply store counts
 *   6) deadline radar → colour classes
 *
 * Run: node tests/runtime/workspace_runtime_test.js
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const WS = path.resolve(__dirname, "../../wordpress-theme/studentup/assets/js/studentup-workspace.js");
const code = fs.readFileSync(WS, "utf8");

const TODAY = new Date();
function iso(days) {
  const d = new Date(TIME);
  d.setDate(d.getDate() + days);
  return d.toISOString().slice(0, 10);
}
const TIME = Date.now();

/* REAL dataset shape (smart.php studentup_smart_dataset rows) */
const DATA = [
  { id: "101", title: "SSC CGL 2026 Notification", link: "/ssc-cgl/", qual: ["degree"], state: "central", last: iso(2), days: 2, pay: "Pay Level-7", vac: "12000", amin: 18, amax: 32, apply: "", date: "2026-09-28" },
  { id: "102", title: "TSPSC Group-1 Recruitment", link: "/tspsc-group-1/", qual: ["degree", "pg"], state: "ts", last: iso(5), days: 5, pay: "Rs. 37,100", vac: "500", amin: 18, amax: 39, apply: "", date: "2026-09-27" },
  { id: "103", title: "ITI Apprentice Posts", link: "/iti-apprentice/", qual: ["iti"], state: "ts", last: iso(9), days: 9, pay: "", vac: "80", amin: 18, amax: 30, apply: "", date: "2026-09-26" },
  { id: "104", title: "Old Closed Recruitment", link: "/closed/", qual: ["degree"], state: "central", last: iso(-3), days: -3, pay: "", vac: "", amin: 0, amax: 0, apply: "", date: "2026-08-01" },
  { id: "105", title: "Inter Qualification Teacher Job", link: "/inter-job/", qual: ["inter"], state: "ap", last: "", days: null, pay: "", vac: "", amin: 0, amax: 0, apply: "", date: "2026-09-25" },
];

const HTML = `<!doctype html><html><body class="page">
<section class="su-ws" id="workspace" data-su-ws='${JSON.stringify(DATA).replace(/'/g, "&#39;")}'>
  <form class="su-ws-form" data-su-ws-form>
    <select data-su-ws-qual><option value=""></option><option value="degree">Degree</option><option value="inter">Inter</option><option value="iti">ITI</option></select>
    <input type="number" data-su-ws-age>
    <select data-su-ws-state><option value=""></option><option value="ts">TS</option><option value="ap">AP</option><option value="central">Central</option></select>
  </form>
  <div class="su-ws-tiles" data-su-ws-pipe></div>
  <span class="su-ws-mcount" data-su-ws-mcount></span>
  <div class="su-ws-matches" data-su-ws-matches></div>
  <div class="su-ws-radar" data-su-ws-radar></div>
</section>
</body></html>`;

let pass = 0, fail = 0;
function check(name, ok) {
  if (ok) { pass++; console.log("  ✔ " + name); }
  else { fail++; console.log("  ✘ " + name); }
}

const dom = new JSDOM(HTML, { runScripts: "outside-only", url: "http://workspace.test/workspace/" });
const { window } = dom;

/* stores: 2 saved jobs, one marked applied */
window.localStorage.setItem("studentup_saved_v1", JSON.stringify([
  { id: "102", title: "TSPSC Group-1 Recruitment", url: "/tspsc-group-1/", cat: "", date: iso(5), ts: 1 },
  { id: "103", title: "ITI Apprentice Posts", url: "/iti-apprentice/", cat: "", date: iso(9), ts: 2 },
]));
window.localStorage.setItem("studentup_apply_v1", JSON.stringify({ "102": "applied" }));
window.STUDENTUP_WS = {
  profile: "su_profile_v1", saved: "studentup_saved_v1", apply: "studentup_apply_v1",
  savedOn: true,
  i18n: {
    eligible: "Eligible for you", savedmsg: "saved", empty: "empty", noProfile: "Set your qualification above.",
    noMatch: "No matching posts yet.", pipeSaved: "Saved", pipeApplied: "Applied", pipeInter: "Interview",
    pipeResult: "Result", pipeEmpty: "Save jobs from any card.", radarEmpty: "radar empty",
    lastDay: "Last day", daysLeft: "days left", deadline: "Deadline", save: "Save",
    qualLabel: "Qualification", ageElig: "Eligible by age", ageNo: "Age limit",
  },
};

/* run the real module */
try {
  dom.window.eval(code);
  window.document.dispatchEvent(new window.Event("DOMContentLoaded", { bubbles: true }));
} catch (e) {
  console.error("MODULE CRASH:", e.message);
  process.exit(1);
}

const doc = window.document;

/* 1 — no profile: hint, no jobs */
let matches = doc.querySelector("[data-su-ws-matches]");
check("no-profile empty hint shown", matches.textContent.indexOf("Set your qualification") !== -1);

/* 2 — set profile qual=degree (change event) */
const sel = doc.querySelector("[data-su-ws-qual]");
sel.value = "degree";
sel.dispatchEvent(new window.Event("change", { bubbles: true }));
check("profile saved to localStorage", window.localStorage.getItem("su_profile_v1").indexOf('"q":"degree"') !== -1);

const titles = Array.from(doc.querySelectorAll(".su-ws-job-t")).map((a) => a.textContent);
check("degree matches render (3 posts incl. closed)", titles.length === 3);
check("TSPSC (degree) matched", titles.some((t) => t.indexOf("TSPSC") !== -1));
check("SSC CGL (degree) matched", titles.some((t) => t.indexOf("SSC CGL") !== -1));
check("ITI post filtered out (qual mismatch)", !titles.some((t) => t.indexOf("ITI") !== -1));
check("closed post sorted LAST (design: Closed chip, 99999)",
  titles[titles.length - 1].indexOf("Closed") !== -1);
check("closed post shows Closed chip", !!doc.querySelector(".su-ws-chip.off"));
check("urgent deadline first (SSC 2d before TSPSC 5d)",
  titles[0].indexOf("SSC CGL") !== -1 && titles[1].indexOf("TSPSC") !== -1);
check("days-left chip present", !!doc.querySelector(".su-ws-chip"));

/* 3 — age filter: age 40 → SSC (18–32) and TSPSC (18–39) hidden;
 *     Closed post has no age limits → stays with "maybe" verdict (design). */
const age = doc.querySelector("[data-su-ws-age]");
age.value = "40";
age.dispatchEvent(new window.Event("input", { bubbles: true }));
const afterAge = Array.from(doc.querySelectorAll(".su-ws-job-t")).map((a) => a.textContent);
check("age 40 filters out both age-limited degree posts", afterAge.length === 1);
check("only age-unknown post remains (maybe verdict)", afterAge[0].indexOf("Closed") !== -1);
check("maybe eligibility tag rendered", !!doc.querySelector(".su-ws-elig.maybe"));

/* 4 — pipeline tiles */
const tiles = Array.from(doc.querySelectorAll(".su-ws-tile")).map((t) => t.textContent);
check("pipeline has 4 tiles", tiles.length === 4);
check("applied tile = 1", tiles.some((t) => t.indexOf("Applied") !== -1 && t.trim().startsWith("1")));
check("saved tile = 1", tiles.some((t) => t.indexOf("Saved") !== -1 && t.trim().startsWith("1")));
check("pipeline item list rendered", Array.from(doc.querySelectorAll(".su-ws-pipe-item")).length === 2);

/* 5 — deadline radar: saved = TSPSC (5d → warm) + ITI (9d → ok) */
const radar = Array.from(doc.querySelectorAll(".su-ws-radar-item")).map((r) => r.className);
check("radar renders saved jobs with deadlines", radar.length === 2);
check("radar warm class (5 days)", radar.some((c) => c.indexOf("warm") !== -1));
check("radar ok class (9 days)", radar.some((c) => c.indexOf("ok") !== -1));
check("radar order urgent first",
  Array.from(doc.querySelectorAll(".su-ws-radar-item a")).map((a) => a.textContent)[0].indexOf("TSPSC") !== -1);

/* 6 — save button present in matched list (interop: data-su-save handler shared with cards) */
check("save buttons rendered (data-su-save)", Array.from(doc.querySelectorAll("[data-su-save]")).length === 1);

console.log(fail === 0 ? `\nWORKSPACE RUNTIME: ${pass}/${pass} OK` : `\nWORKSPACE RUNTIME: ${fail} FAILED`);
process.exit(fail === 0 ? 0 : 1);
