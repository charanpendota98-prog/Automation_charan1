/* v92 — SAVED engine: real behavioural test (jsdom).
 *
 * Entuku: static source audit chaalu kaadu — localStorage save/un-save, count
 * badge, panel render, XSS-safety, private-mode fallback, FIFO cap — ivi
 * **nijam ga** pani cheyyali. Ee test theme JS ni oka harness DOM lo load
 * chesi, real clicks tho verify chestundi.
 *
 * Run: node tests/runtime/saved_runtime_test.js
 *      (tests/v92_test.py kuda idi automatic ga run chestundi)
 */
"use strict";

const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const JS_FILE = path.resolve(
  __dirname, "../../wordpress-theme/studentup/assets/js/studentup-saved.js"
);
const CODE = fs.readFileSync(JS_FILE, "utf8");

const KEY = "studentup_saved_v1";
const RKEY = "studentup_recent_v1";

const passed = [];
const failed = [];
function ok(name, cond, extra) {
  if (cond) passed.push(name);
  else failed.push(name + (extra ? " — " + extra : ""));
}

/* ---------------- harness ---------------- */
async function harness(opts) {
  opts = opts || {};
  const html = `<!doctype html><html><body class="${opts.bodyClass || "single postid-4242"}">
    <button type="button" class="su-save-btn" data-su-save data-id="11"
      data-title="SSC CGL 2026 Notification" data-url="https://studentup.in/ssc-cgl/"
      data-cat="Central Govt Jobs" aria-pressed="false">
      <span class="su-save-ico">🔖</span><span class="su-save-txt">Save</span></button>
    <button type="button" class="su-save-btn" data-su-save data-id="22"
      data-title="TSPSC Group 2 Hall Ticket" data-url="https://studentup.in/tspsc-g2/"
      data-cat="Hall Tickets" aria-pressed="false">
      <span class="su-save-ico">🔖</span><span class="su-save-txt">Save</span></button>
    <span class="su-saved-count" data-su-saved-count hidden>0</span>
    <button type="button" class="su-saved-tab" id="su-saved-tab" data-su-saved-open
      aria-expanded="false" aria-controls="su-saved-panel">🔖</button>
    <div class="su-saved-panel" id="su-saved-panel" role="dialog" hidden>
      <div class="su-saved-body" data-su-saved-body></div>
      <button type="button" id="su-saved-close">x</button>
      <button type="button" id="su-saved-clear">clear</button>
    </div>
    <div class="su-saved-page" id="su-saved-page" data-su-saved-page></div>
    <h1 class="article-head-title">Current article</h1>
    <div class="article-content">body</div>
  </body></html>`;

  const dom = new JSDOM(html, {
    url: "https://studentup.in/ssc-cgl/",
    runScripts: "outside-only",
    pretendToBeVisual: true,
  });
  const { window } = dom;

  window.STUDENTUP_SAVED = {
    store: KEY,
    recent: RKEY,
    max: opts.max || 60,
    i18n: {
      save: "Save", saved: "Saved", removed: "Removed from saved",
      savedmsg: "Post saved", nomore: "Storage is not available",
      empty: "No saved posts yet.", confirm: "Remove all?", cleared: "All removed",
    },
  };
  window.confirm = () => (opts.confirm === undefined ? true : opts.confirm);

  if (opts.breakStorage) {
    Object.defineProperty(window, "localStorage", {
      configurable: true,
      get() { throw new Error("blocked (private mode)"); },
    });
  }

  window.eval(CODE);

  /* jsdom readyState "loading" tho start avutundi — script DOMContentLoaded
   * kosam wait chestundi (real browser laage). Anduke ee event kosam wait. */
  await new Promise((res) => {
    if (window.document.readyState === "complete") { return res(); }
    window.addEventListener("DOMContentLoaded", () => res(), { once: true });
    window.addEventListener("load", () => res(), { once: true });
    setTimeout(res, 300);
  });

  return { window, document: window.document };
}

function savedList(window) {
  const raw = window.localStorage.getItem(KEY);
  return raw ? JSON.parse(raw) : [];
}
function click(window, el) {
  el.dispatchEvent(new window.MouseEvent("click", { bubbles: true, cancelable: true }));
}

(async function main() {

/* ---------------- 1) init ---------------- */
{
  const { window, document } = await harness();
  const body = document.querySelector("[data-su-saved-body]");
  const count = document.querySelector(".su-saved-count");

  ok("script loads, no crash", typeof window.STUDENTUP_SAVED === "object");
  ok("empty state rendered on first visit",
    /No saved posts yet/.test(body.textContent), body.textContent);
  ok("count stays 0 when nothing saved", count.textContent === "0", count.textContent);
  ok("badge hidden while count is 0", count.hidden === true);

  /* ---------------- 2) save ---------------- */
  const b1 = document.querySelector('[data-id="11"]');
  click(window, b1);
  let list = savedList(window);
  ok("save writes one item to localStorage", list.length === 1, "len=" + list.length);
  ok("saved item keeps id", list[0] && String(list[0].id) === "11");
  ok("saved item keeps title", list[0] && list[0].title === "SSC CGL 2026 Notification");
  ok("saved item keeps url", list[0] && /ssc-cgl/.test(list[0].url));
  ok("saved item keeps category", list[0] && list[0].cat === "Central Govt Jobs");
  ok("saved item has timestamp", list[0] && typeof list[0].ts === "number");
  ok("button aria-pressed=true after save", b1.getAttribute("aria-pressed") === "true");
  ok("button label switches to Saved",
    b1.querySelector(".su-save-txt").textContent === "Saved");
  ok("button gets .on class", b1.classList.contains("on"));
  ok("count badge becomes 1", count.textContent === "1", count.textContent);
  ok("badge visible when count > 0", count.hidden === false);

  /* ---------------- 3) un-save (toggle) ---------------- */
  click(window, b1);
  ok("second click removes the item", savedList(window).length === 0);
  ok("aria-pressed back to false", b1.getAttribute("aria-pressed") === "false");
  ok("label back to Save", b1.querySelector(".su-save-txt").textContent === "Save");
  ok("badge hidden again at 0", count.hidden === true);

  /* ---------------- 4) multiple + panel order (newest first) ---------------- */
  click(window, b1);
  click(window, document.querySelector('[data-id="22"]'));
  list = savedList(window);
  ok("two items stored", list.length === 2, "len=" + list.length);
  const savedBox = body.querySelector(".su-saved-list");
  ok("panel wraps saved items in .su-saved-list", !!savedBox);
  const rows = savedBox ? savedBox.querySelectorAll(".su-saved-row") : [];
  ok("panel renders one row per saved item", rows.length === 2, "rows=" + rows.length);
  ok("reading history shown in its own block",
    !!body.querySelector(".su-saved-recent"));
  ok("newest item shown first",
    /TSPSC Group 2/.test(rows[0].textContent), rows[0] && rows[0].textContent);
  ok("row links to the saved url",
    rows[0].querySelector("a").getAttribute("href") === "https://studentup.in/tspsc-g2/");
  ok("count badge shows 2", count.textContent === "2", count.textContent);

  /* ---------------- 5) remove one from the panel ---------------- */
  const del = rows[0].querySelector("[data-su-remove]");
  click(window, del);
  ok("panel remove deletes that item", savedList(window).length === 1);
  ok("remaining item is the other post",
    String(savedList(window)[0].id) === "11");
  ok("badge counts down to 1", count.textContent === "1", count.textContent);

  /* ---------------- 6) panel open/close ---------------- */
  const panel = document.getElementById("su-saved-panel");
  const tab = document.getElementById("su-saved-tab");
  click(window, tab);
  ok("rail tab opens the panel", panel.hidden === false);
  ok("tab aria-expanded=true when open", tab.getAttribute("aria-expanded") === "true");
  click(window, tab);
  ok("rail tab closes the panel again", panel.hidden === true);
  click(window, tab);
  window.document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape" }));
  ok("Escape closes the panel", panel.hidden === true);

  /* ---------------- 7) clear all ---------------- */
  click(window, document.getElementById("su-saved-clear"));
  ok("clear all empties the store", savedList(window).length === 0);
  ok("empty state returns after clear",
    /No saved posts yet/.test(body.textContent), body.textContent);

  /* ---------------- 8) cancel on confirm keeps data ---------------- */
  click(window, b1);
  const { window: w2, document: d2 } = await harness({ confirm: false });
  click(w2, d2.querySelector('[data-id="11"]'));
  click(w2, d2.getElementById("su-saved-clear"));
  ok("cancel (confirm=false) keeps saved items", savedList(w2).length === 1);
}

/* ---------------- 9) XSS safety ---------------- */
{
  const { window, document } = await harness();
  const evil = document.querySelector('[data-id="11"]');
  evil.setAttribute("data-title", '<img src=x onerror="window.__pwned=1">');
  click(window, evil);
  const body = document.querySelector("[data-su-saved-body]");
  ok("malicious title does not create elements",
    body.querySelectorAll("img").length === 0, "img count=" + body.querySelectorAll("img").length);
  ok("malicious title rendered as plain text",
    body.textContent.indexOf("<img") > -1);
  ok("no script execution from title", window.__pwned !== 1);
}

/* ---------------- 10) /saved/ page grid ---------------- */
{
  const { window, document } = await harness();
  click(window, document.querySelector('[data-id="11"]'));
  click(window, document.querySelector('[data-id="22"]'));
  const page = document.querySelector("[data-su-saved-page]");
  const grid = page.querySelector(".su-saved-grid");
  ok("saved page renders a grid", !!grid);
  ok("saved page grid holds both items",
    grid.querySelectorAll(".su-saved-row").length === 2);
  const emptyH = await harness();
  const emptyP = emptyH.document.querySelector("[data-su-saved-page]");
  ok("saved page shows empty state when nothing saved",
    /No saved posts yet/.test(emptyP.textContent), emptyP.textContent);
}

/* ---------------- 11) reading history ---------------- */
{
  const { window } = await harness();
  const rec = JSON.parse(window.localStorage.getItem(RKEY) || "[]");
  ok("reading history records the current post", rec.length === 1, "len=" + rec.length);
  ok("history entry uses the post id from body class",
    rec[0] && String(rec[0].id) === "4242", rec[0] && String(rec[0].id));
  ok("history entry stores the url", rec[0] && /ssc-cgl/.test(rec[0].url));

  const archive = await harness({ bodyClass: "archive" });
  ok("reading history skipped on non-single pages",
    (archive.window.localStorage.getItem(RKEY) || "[]") === "[]");
}

/* ---------------- 12) FIFO cap ---------------- */
{
  const { window, document } = await harness({ max: 5 });
  for (let i = 0; i < 6; i++) {
    const btn = document.createElement("button");
    btn.setAttribute("data-su-save", "");
    btn.setAttribute("data-id", "90" + i);
    btn.setAttribute("data-title", "post " + i);
    btn.setAttribute("data-url", "https://studentup.in/p" + i + "/");
    document.body.appendChild(btn);
    click(window, btn);
  }
  const list = savedList(window);
  ok("storage capped at the configured max", list.length === 5, "len=" + list.length);
  ok("oldest entries dropped first (FIFO)",
    String(list[list.length - 1].id) === "905", "last=" + (list[list.length - 1] || {}).id);
  ok("cap keeps the newest item", String(list[list.length - 1].id) === "905");
}

/* ---------------- 13) private mode / blocked storage ---------------- */
{
  const { window, document } = await harness({ breakStorage: true });
  let crashed = false;
  try {
    const b = document.querySelector('[data-id="11"]');
    click(window, b);
    click(window, document.getElementById("su-saved-tab"));
  } catch (e) { crashed = true; }
  ok("blocked localStorage does not crash the page", crashed === false);
  ok("count stays 0 when storage is unavailable",
    document.querySelector(".su-saved-count").textContent === "0");
  const toast = document.getElementById("su-saved-toast");
  ok("soft note shown when storage is unavailable", !!toast);
  if (toast) {
    ok("note text is the i18n message",
      /Storage is not available/.test(toast.textContent), toast.textContent);
  } else {
    ok("note text is the i18n message", false, "no toast element");
  }
}

  report();
})();

/* ---------------- report ---------------- */
function report() {
const total = passed.length + failed.length;
console.log("=".repeat(64));
console.log("  v92 SAVED engine — real behaviour (jsdom)");
console.log("=".repeat(64));
if (failed.length) {
  for (const f of failed) console.log("  FAIL  " + f);
  console.log("-".repeat(64));
  console.log(`  ${passed.length}/${total} checks passed`);
  process.exit(1);
}
console.log(`  ${passed.length}/${total} checks passed`);
console.log("=".repeat(64));
}
