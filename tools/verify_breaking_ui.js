#!/usr/bin/env node
/*!
 * v202 — Breaking News nav item: PHONE + LAPTOP layout proof (real browser).
 *
 * Owner: "phone and laptop lo neat ga undali" + "same like Central Jobs".
 * Static checks layout ni prove cheyyavu — ee tool nijamaina Chromium ni
 * puppeteer-core tho drive chesi, nijamaina clicks (element.click()) tho
 * panel/drawer terichi, **measurements** teesukuntundi:
 *
 *   · horizontal overflow (scrollWidth − innerWidth) har width ki
 *   · desktop: panel viewport lopala + geometry (radius/z/pos) + "All updates" CTA
 *   · panel top offset ni mega (Central Jobs) panel tho compare (same feel)
 *   · phone: desktop panel hidden + ☰ drawer lo breaking rows overflow kaavu
 *   · dark mode lo kuda same numbers
 *
 * Usage:
 *   NODE_PATH=/path/to/node_modules node tools/verify_breaking_ui.js            # table
 *   NODE_PATH=... node tools/verify_breaking_ui.js --json                       # full JSON
 *   CHROMIUM=/usr/bin/chromium NODE_PATH=... node tools/verify_breaking_ui.js
 *
 * puppeteer/chromium dorakanappudu SKIP (env per-user) — exit 0, "SKIP" print.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const DEMO = path.join(ROOT, "preview", "worldclass", "index.html");

const WIDTHS = [
  ["phone-360", 360, 780],
  ["phone-390", 390, 844],
  ["phone-414", 414, 896],
  ["tablet-768", 768, 1024],
  ["laptop-1024", 1024, 800],
  ["laptop-1280", 1280, 880],
  ["laptop-1440", 1440, 940],
  ["desktop-1920", 1920, 1000],
];

function loadPuppeteer() {
  const tries = [process.env.PUPPETEER, "puppeteer-core", "puppeteer",
                 "/tmp/chr/node_modules/puppeteer-core"];
  for (const t of tries) {
    try { return require(t); } catch (e) { /* next */ }
  }
  return null;
}

function findChromium() {
  const cands = [process.env.CHROMIUM, "/tmp/chromium92",
                 "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"];
  for (const c of cands) { if (c && fs.existsSync(c)) return c; }
  return null;
}

const MEASURE = () => {
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return { l: Math.round(r.left), t: Math.round(r.top), r: Math.round(r.right),
             b: Math.round(r.bottom), w: Math.round(r.width), h: Math.round(r.height),
             radius: cs.borderRadius, z: cs.zIndex, pos: cs.position,
             vis: cs.visibility, op: cs.opacity, bg: cs.backgroundColor };
  };
  const out = { w: window.innerWidth, sw: document.documentElement.scrollWidth };
  const dark = document.body.classList.contains("dark");
  const brkLi = document.querySelector("li.su-navbrk");
  const brkA = brkLi ? brkLi.querySelector("a[aria-haspopup]") : null;
  const mpanel = document.getElementById("mpanel");
  const menubtn = document.getElementById("menubtn");
  const desktop = window.innerWidth >= 981;

  if (desktop && brkA) brkA.click();
  else if (!desktop && menubtn) menubtn.click();

  document.querySelectorAll("*").forEach((el) => {
    el.style.transition = "none"; el.style.animation = "none";
  });

  out.dark = dark;
  out.desktop = desktop;
  out.brkLi = !!brkLi;
  out.brkOpen = !!(brkLi && brkLi.classList.contains("su-open"));
  out.panel = box(document.getElementById("su-brkdd"));
  out.rows = [];
  document.querySelectorAll("#su-brkdd li.menu-item a").forEach((a) => {
    const r = a.getBoundingClientRect();
    out.rows.push({ href: a.getAttribute("href"), w: Math.round(r.width), h: Math.round(r.height) });
  });
  const cta = document.querySelector("#su-brkdd .su-brkdd-cta");
  out.cta = box(cta);
  out.drawer = mpanel ? { open: mpanel.classList.contains("open"),
                          w: Math.round(mpanel.getBoundingClientRect().width) } : null;
  out.mbrk = [];
  document.querySelectorAll(".mpanel a.su-mbrk").forEach((a) => {
    out.mbrk.push({ h: Math.round(a.getBoundingClientRect().height),
                    ok: a.scrollWidth <= a.clientWidth + 1,
                    href: a.getAttribute("href") });
  });
  out.mbrkAll = !!document.querySelector(".mpanel .su-mbrk-all");

  if (desktop && brkA) {
    const megaA = document.querySelector("li.su-mega-li a[aria-haspopup]");
    if (megaA) {
      brkA.click();                                  /* close breaking */
      megaA.click();                                 /* open first mega group */
      out.mega = box(document.querySelector("li.su-mega-li .sub-menu[data-su-mega]"));
    }
  }
  return out;
};

(async () => {
  if (!fs.existsSync(DEMO)) { console.log("SKIP: demo ledu"); process.exit(0); }
  const puppeteer = loadPuppeteer();
  const chromium = findChromium();
  if (!puppeteer || !chromium) {
    console.log("SKIP: puppeteer/chromium ledu (NODE_PATH + CHROMIUM pettandi)");
    process.exit(0);
  }
  const browser = await puppeteer.launch({
    executablePath: chromium,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--hide-scrollbars",
           "--no-first-run", "--force-device-scale-factor=1"],
    env: Object.assign({}, process.env, {
      LD_LIBRARY_PATH: "/tmp/nsprdist/lib:/tmp/insp/aws/lib",
    }),
  });

  const rows = [];
  const fails = [];
  for (const [name, w, h] of WIDTHS) {
    for (const dark of [false, true]) {
      const page = await browser.newPage();
      await page.setViewport({ width: w, height: h, deviceScaleFactor: 1 });
      await page.goto("file://" + DEMO, { waitUntil: "networkidle0" });
      if (dark) await page.click("#su-theme");
      await new Promise((r) => setTimeout(r, 350));
      const m = await page.evaluate(MEASURE);
      await page.close();

      const label = name + (dark ? "-dark" : "");
      const over = m.sw - m.w;
      const line = { name: label, w, overflow: over, desktop: m.desktop };
      if (!m.brkLi) fails.push(label + ": Breaking News item ledu");
      if (over > 1) fails.push(label + ": horizontal overflow " + over + "px");
      if (m.desktop) {
        const p = m.panel || {};
        if (!m.brkOpen) fails.push(label + ": click cheste panel open avvaledu");
        if (p.l < -1 || p.r > m.w + 1 || p.t < 0 || p.h < 240) {
          fails.push(label + ": panel viewport bayata/chinna " + JSON.stringify(p));
        }
        line.panel = p.w + "x" + p.h + " @" + p.l + "," + p.t + " r=" + p.radius + " z=" + p.z;
        line.rows = m.rows.length;
        line.cta = !!(m.cta && m.cta.h >= 30);
        if (m.rows.length < 5) fails.push(label + ": panel rows takkuva (" + m.rows.length + ")");
        if (!line.cta) fails.push(label + ": All-updates CTA ledu/chinna");
        if (m.mega) {
          line.megaTopDiff = Math.abs(m.mega.t - p.t);
          line.megaRadius = m.mega.radius;
          if (line.megaTopDiff > 6) {
            fails.push(label + ": panel top mega (Central Jobs) tho match avvatledu (diff "
                       + line.megaTopDiff + "px)");
          }
        }
      } else {
        const vis = m.panel && m.panel.h > 4 && m.panel.vis !== "hidden" && m.panel.op !== "0";
        if (vis) fails.push(label + ": phone lo desktop panel inka kanipistundi");
        if (!(m.drawer && m.drawer.open)) fails.push(label + ": ☰ click cheste drawer open avvaledu");
        if (m.mbrk.length < 4 || !m.mbrkAll) fails.push(label + ": drawer lo breaking block ledu");
        const bad = m.mbrk.filter((x) => !x.ok);
        if (bad.length) fails.push(label + ": drawer rows overflow " + JSON.stringify(bad.slice(0, 2)));
        if (m.drawer && m.drawer.w > m.w) fails.push(label + ": drawer viewport kanna peddaga");
        line.drawer = (m.drawer ? m.drawer.w : 0) + "px · rows=" + m.mbrk.length;
      }
      rows.push(line);
    }
  }
  await browser.close();

  console.log("  width              overflow  details");
  for (const r of rows) {
    const detail = r.panel
      ? "panel " + r.panel + " · rows=" + r.rows + " · CTA=" + (r.cta ? "ok" : "NO")
      : "drawer " + r.drawer;
    const mega = r.megaTopDiff !== undefined ? " · megaTopΔ=" + r.megaTopDiff + "px" : "";
    console.log("   " + r.name.padEnd(18) + String(r.overflow).padStart(4) + "px   " + detail + mega);
  }
  if (process.argv.includes("--json")) console.log(JSON.stringify(rows, null, 1));
  if (fails.length) {
    console.log("\n  ❌ " + fails.length + " FAIL");
    fails.forEach((f) => console.log("     - " + f));
    process.exit(1);
  }
  console.log("\n  ✅ " + rows.length + "/" + rows.length +
              " viewports clean (light+dark · no overflow · panel in viewport · drawer rows fit)");
})().catch((e) => { console.error("verify_breaking_ui error:", e && e.message); process.exit(2); });
