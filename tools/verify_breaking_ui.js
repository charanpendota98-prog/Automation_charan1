#!/usr/bin/env node
/*!
 * Responsive StudentUp homepage/menu proof (v1.9.44+).
 *
 * When Puppeteer + Chromium are available, measure the canonical preview at
 * phone/tablet/laptop widths in light and dark mode. This checks the real
 * visible hamburger/drawer, the compact desktop More dropdown, card/table
 * overflow and the restrained wordmark. It deliberately tests the current
 * single Home / TS / AP / Central / More hierarchy, not the retired Breaking
 * News top-level dropdown.
 *
 * Usage:
 *   NODE_PATH=/path/to/node_modules node tools/verify_breaking_ui.js [--json]
 *   CHROMIUM=/usr/bin/chromium NODE_PATH=... node tools/verify_breaking_ui.js
 *
 * Missing browser dependencies produce SKIP (exit 0); static gates still run.
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..");
const DEMO = path.join(ROOT, "preview", "index.html");
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
  for (const candidate of tries) {
    if (!candidate) continue;
    try { return require(candidate); } catch (e) { /* try the next location */ }
  }
  return null;
}

function findChromium() {
  const candidates = [process.env.CHROMIUM, "/tmp/chromium92",
    "/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome"];
  return candidates.find((candidate) => candidate && fs.existsSync(candidate)) || null;
}

const MEASURE = () => {
  const box = (el) => {
    if (!el) return null;
    const r = el.getBoundingClientRect();
    const cs = getComputedStyle(el);
    return {
      left: Math.round(r.left), right: Math.round(r.right), top: Math.round(r.top),
      width: Math.round(r.width), height: Math.round(r.height), display: cs.display,
      visibility: cs.visibility, shadow: cs.boxShadow, textShadow: cs.textShadow,
    };
  };
  const width = window.innerWidth;
  const desktop = width >= 981;
  const menuButton = document.getElementById("menubtn");
  const panel = document.getElementById("mpanel");
  const moreItem = document.querySelector(".su-more-menu");
  const moreLink = moreItem && moreItem.querySelector(":scope > a");
  const morePanel = moreItem && moreItem.querySelector(":scope > .sub-menu");

  if (desktop && moreLink) moreLink.click();
  if (!desktop && menuButton) {
    menuButton.click();
    const moreDetails = document.getElementById("su-mobile-more");
    if (moreDetails) moreDetails.querySelector("summary").click();
  }

  document.querySelectorAll("*").forEach((el) => {
    el.style.transition = "none";
    el.style.animation = "none";
  });

  const brand = document.querySelector(".header .logo .brand, .header .custom-logo");
  const primaryItems = document.querySelectorAll(".nav .menu-primary > li");
  const mobileMore = document.querySelector("#su-mobile-more .mgroup-body");
  const mobileMoreStyle = mobileMore ? getComputedStyle(mobileMore) : null;
  return {
    width,
    scrollWidth: document.documentElement.scrollWidth,
    desktop,
    primaryLabels: Array.from(primaryItems).map((li) => li.querySelector(":scope > a")?.textContent.trim()),
    brand: box(brand),
    menuButton: box(menuButton),
    menuButtonExpanded: menuButton && menuButton.getAttribute("aria-expanded"),
    menuButtonVisible: !!(menuButton && getComputedStyle(menuButton).display !== "none" && menuButton.getBoundingClientRect().width > 0),
    desktopMoreVisible: !!(morePanel && getComputedStyle(morePanel).display !== "none"),
    desktopMoreLinks: morePanel ? morePanel.querySelectorAll("a").length : 0,
    drawerOpen: !!(panel && panel.classList.contains("open") && panel.getAttribute("aria-hidden") === "false"),
    drawer: box(panel),
    mobileMoreLinks: mobileMore ? mobileMore.querySelectorAll("a").length : 0,
    mobileMoreVisible: !!(mobileMoreStyle && mobileMoreStyle.display !== "none"),
    bottomNav: !!document.querySelector(".su-bnav"),
  };
};

(async () => {
  if (!fs.existsSync(DEMO)) {
    console.log("SKIP: canonical preview/index.html is missing");
    process.exit(0);
  }
  const puppeteer = loadPuppeteer();
  const chromium = findChromium();
  if (!puppeteer || !chromium) {
    console.log("SKIP: Puppeteer/Chromium unavailable; static responsive gates remain active");
    process.exit(0);
  }

  const browser = await puppeteer.launch({
    executablePath: chromium,
    headless: true,
    args: ["--no-sandbox", "--disable-gpu", "--disable-dev-shm-usage", "--hide-scrollbars",
      "--no-first-run", "--force-device-scale-factor=1"],
  });
  const results = [];
  const failures = [];

  for (const [name, width, height] of WIDTHS) {
    for (const dark of [false, true]) {
      const page = await browser.newPage();
      await page.setViewport({ width, height, deviceScaleFactor: 1 });
      await page.goto("file://" + DEMO, { waitUntil: "networkidle0" });
      if (dark) await page.evaluate(() => document.body.classList.add("dark"));
      await new Promise((resolve) => setTimeout(resolve, 80));
      const measured = await page.evaluate(MEASURE);
      await page.close();

      const label = name + (dark ? "-dark" : "");
      const overflow = measured.scrollWidth - measured.width;
      results.push({ name: label, overflow, ...measured });
      if (overflow > 1) failures.push(label + ": horizontal overflow " + overflow + "px");
      if (measured.desktop) {
        const expected = ["Home", "Telangana", "Andhra Pradesh", "Central Govt", "More"];
        if (JSON.stringify(measured.primaryLabels) !== JSON.stringify(expected)) {
          failures.push(label + ": desktop nav hierarchy is not Home/TS/AP/Central/More");
        }
        if (!measured.desktopMoreVisible || measured.desktopMoreLinks < 8) {
          failures.push(label + ": desktop More dropdown is hidden or incomplete");
        }
        if (measured.menuButtonVisible) failures.push(label + ": phone hamburger is shown on desktop");
      } else {
        if (!measured.menuButtonVisible) failures.push(label + ": visible phone Menu button is missing");
        if (!measured.drawerOpen) failures.push(label + ": tapping Menu does not open the drawer");
        if (!measured.mobileMoreVisible || measured.mobileMoreLinks < 8) {
          failures.push(label + ": More accordion does not reveal categories");
        }
        if (measured.drawer && measured.drawer.width > width) failures.push(label + ": drawer exceeds viewport width");
        if (measured.bottomNav) failures.push(label + ": duplicate bottom navigation remains on home");
      }
      if (measured.brand && (/^(?!none$).+/.test(measured.brand.shadow) || /^(?!none$).+/.test(measured.brand.textShadow))) {
        failures.push(label + ": wordmark has a glow/shadow");
      }
    }
  }
  await browser.close();

  console.log("  viewport             overflow   result");
  for (const result of results) {
    const status = result.desktop
      ? "More links=" + result.desktopMoreLinks + " · brand=" + (result.brand ? result.brand.width + "px" : "missing")
      : "Menu=" + (result.menuButtonVisible ? "visible" : "missing") + " · drawer=" + (result.drawer ? result.drawer.width + "px" : "missing") + " · More=" + result.mobileMoreLinks;
    console.log("  " + result.name.padEnd(20) + String(result.overflow).padStart(3) + "px     " + status);
  }
  if (process.argv.includes("--json")) console.log(JSON.stringify(results, null, 2));
  if (failures.length) {
    console.log("\n  FAIL " + failures.length);
    failures.forEach((failure) => console.log("   - " + failure));
    process.exit(1);
  }
  console.log("\n  PASS " + results.length + "/" + results.length + " responsive states (8 widths × light/dark)");
})().catch((error) => {
  console.error("homepage UI verification error:", error && error.message);
  process.exit(2);
});
