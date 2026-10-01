// v180 audit: run LIVE site pages in jsdom with real scripts — catch runtime JS errors.
"use strict";
const fs = require("fs");
const { JSDOM, VirtualConsole, ResourceLoader } = require("jsdom");

const BASE = "http://127.0.0.1:9400";
const PAGES = [
  "/",
  "/page/2/",
  "/?qual=degree",
  "/category/ts-jobs/",
  "/tspsc-group-1-recruitment-2026-500-posts/",
  "/tspsc-group-1-hall-ticket-2026/",
  "/workspace/",
  "/saved/",
  "/compare/",
  "/latest-jobs/",
];

class LiveLoader extends ResourceLoader {
  fetch(url, options) {
    // only same-origin + live site resources
    if (url.startsWith(BASE) || url.startsWith("http://127.0.0.1:9400")) {
      return super.fetch(url, options);
    }
    return Promise.resolve(Buffer.from("")); // block third-party (ads etc.)
  }
}

(async () => {
  let totalErr = 0;
  for (const p of PAGES) {
    const errors = [];
    const vc = new VirtualConsole();
    vc.on("jsdomError", (e) => {
      const msg = String(e.message || e);
      // css parse noise is fine; we want JS errors
      if (/Could not parse CSS/i.test(msg)) return;
      if (e.detail && e.detail.stack) {
        errors.push(msg + " @ " + String(e.detail.stack).split("\n")[0]);
      } else {
        errors.push(msg);
      }
    });
    vc.on("error", (msg) => errors.push("console.error: " + msg));
    try {
      const dom = await JSDOM.fromURL(BASE + p, {
        runScripts: "dangerously",
        resources: new LiveLoader(),
        virtualConsole: vc,
        pretendToBeVisual: true,
      });
      // give async handlers a moment
      await new Promise((r) => setTimeout(r, 2500));
      // window errors captured?
      const w = dom.window;
      if (w.__errors) errors.push(...w.__errors);
      dom.window.close();
    } catch (e) {
      errors.push("LOAD FAIL: " + String(e).slice(0, 120));
    }
    const uniq = [...new Set(errors.map((e) => e.slice(0, 130)))];
    totalErr += uniq.length;
    console.log(`${p.padEnd(46)} ${uniq.length === 0 ? "CLEAN ✔" : "ERRORS:"}`);
    uniq.slice(0, 6).forEach((e) => console.log("    ", e));
  }
  console.log("TOTAL JS ERRORS:", totalErr);
  fs.writeFileSync("/tmp/js_errors.txt", String(totalErr));
})();
