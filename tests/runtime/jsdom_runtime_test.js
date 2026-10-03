/* Browser-level runtime checks for preview/index.html (jsdom).
 * Run: cd tests/runtime && node jsdom_runtime_test.js
 * (npm install first if node_modules missing)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const PAGE = path.resolve(__dirname, "../../preview/index.html");
let html = fs.readFileSync(PAGE, "utf8");

/* v174: demo data-last dates ROLLING ga maintain chestundi.
 * Static dates (2026-09-30 lanti vi) real calendar kalipoyaka "expired"
 * ayi jsdom checks date-drift tho fail avtayi. Rank-based offset mapping:
 * sorted unique dates → today + N (order preserve, idempotent — same-day
 * rerun same output; roju +1 shift automatic ga补偿). Closing demo (0-7 days)
 * rank-1 (+5) tho eppudu untundi. Static hand-edit ki chance ledu. */
(function rollDates(src) {
  const re = /data-last="(\d{4}-\d{2}-\d{2})"/g;
  const dates = Array.from(new Set(Array.from(src.matchAll(re)).map(m => m[1]))).sort();
  const OFF = [5, 8, 9, 12, 14, 20, 26, 35, 45, 61, 75, 91];
  const map = {};
  dates.forEach((d, i) => {
    const off = OFF[i] !== undefined ? OFF[i] : 91 + (i - OFF.length + 1) * 14;
    const t = new Date(); t.setHours(0, 0, 0, 0); t.setDate(t.getDate() + off);
    map[d] = t.getFullYear() + "-" + String(t.getMonth() + 1).padStart(2, "0") + "-" + String(t.getDate()).padStart(2, "0");
  });
  const out = src.replace(re, (m, d) => 'data-last="' + (map[d] || d) + '"');
  if (out !== src) {
    fs.writeFileSync(PAGE, out);
    html = out;
  }
})(html);

/* v71: total check count — docs (README/MANUAL/GO_LIVE) claim this number and
 * tools/parity_audit.py P8 reads it, so a silent drift cannot slip through. */
const EXPECTED_CHECKS = 196;

const passed = [];
const failed = [];
function ok(name, cond, extra) {
  if (cond) passed.push(name);
  else failed.push(name + (extra ? " — " + extra : ""));
}
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

(async function main() {
  const dom = new JSDOM(html, {
    url: "http://localhost/",
    runScripts: "dangerously",
    pretendToBeVisual: true,
  });
  const { window } = dom;
  const { document } = window;

  // let inline scripts run
  await sleep(300);

  /* ---------- document basics ---------- */
  const title = document.title;
  ok("title present, <=60 chars", title.length > 10 && title.length <= 60, "len=" + title.length);
  const desc = document.querySelector('meta[name="description"]');
  ok("meta description 120-160 chars", !!desc && desc.content.length >= 120 && desc.content.length <= 160,
     desc ? "len=" + desc.content.length : "missing");
  ok("exactly one H1", document.querySelectorAll("h1").length === 1,
     "count=" + document.querySelectorAll("h1").length);
  ok("html lang set", (document.documentElement.getAttribute("lang") || "").length > 0);
  ok("canonical link present", !!document.querySelector('link[rel="canonical"]'));
  const lds = document.querySelectorAll('script[type="application/ld+json"]');
  let ldOk = lds.length >= 2;
  lds.forEach(s => { try { JSON.parse(s.textContent); } catch (e) { ldOk = false; } });
  ok("2+ JSON-LD blocks, all valid JSON", ldOk, "count=" + lds.length);

  /* ---------- v73: slim hero + countdown/deadline teesesaam + English UI ---------- */
  ok("v73 hero: slim hero English h1 (countdown card ledu)",
     !!document.querySelector(".hero-slim") && !document.querySelector(".timer") &&
     (document.querySelector(".hero-slim h1") || { textContent: "" }).textContent.length > 20);
  ok("v73: countdown UI + data plumbing ledu (cd-box · data-deadline · deadline.json)",
     !document.getElementById("cd-box") && !document.querySelector("[data-deadline]") &&
     !/cd-none|deadline\.json|new Date\(2026,9,15/.test(html));
  ok("v73: HTML head English (lang=en · og:locale en_IN · ld inLanguage en-IN)",
     document.documentElement.getAttribute("lang") === "en" &&
     /og:locale" content="en_IN"/.test(html) && /"inLanguage": "en-IN"/.test(html));
  /* v73: UI chrome (header/footer/menu/rail/qualification/ads) lo Telugu undakoodadu —
   * Telugu mattrame job/article content + daily quiz lo (scope: ui_english_body_telugu). */
  {
    const chrome = ["header", "footer", ".mpanel", ".usedwrap", ".sectionhead", ".qsplit-head",
                    ".su-ad", ".joinbox", ".chiprow", ".surail"]
      .map(sel => document.querySelector(sel)).filter(Boolean)
      .map(e => e.textContent).join(" ");
    ok("v73: header/footer/menu/qualification chrome lo Telugu ledu", !/[\u0C00-\u0C7F]/.test(chrome));
  }
  ok("v73: job/article content Telugu ga undi (scope = content only)",
     /[\u0C00-\u0C7F]/.test((document.getElementById("grid") || { textContent: "" }).textContent || ""));

  /* ---------- state filters ---------- */
  const tabs = Array.from(document.querySelectorAll(".tab"));
  ok("4 filter tabs (all/ts/ap/central)", tabs.length === 4, "count=" + tabs.length);
  const cards = Array.from(document.querySelectorAll("#grid .news"));
  const visible = () => cards.filter(c => !c.classList.contains("hidden")).length;
  const click = sel => { document.querySelector(sel).click(); };
  // v51: expected counts derived from data-state/data-cat so adding cards
  // (new pillars) never breaks the suite.
  const has = (card, attr, val) => (" " + (card.getAttribute(attr) || "") + " ").indexOf(" " + val + " ") > -1;
  // v134: cards whose last date has passed are hidden by design, so every
  // expectation counts live cards only.
  const today = new Date().toISOString().slice(0, 10);
  const isLive = c => {
    const last = c.getAttribute("data-last");
    return !last || last >= today;
  };
  const liveCards = cards.filter(isLive);
  const expectState = st => liveCards.filter(c => has(c, "data-state", st)).length;
  const expectCat = cat => liveCards.filter(c => has(c, "data-cat", cat)).length;

  click('.tab[data-state="ts"]');
  click('.tab[data-state="all"]');
  click('.tab[data-state="ts"]');
  ok("TS filter -> all ts cards (count from DOM, multi-state by design)",
     visible() === expectState("ts") && cards.filter(c => !c.classList.contains("hidden")).every(c => has(c, "data-state", "ts")),
     "visible=" + visible() + " expected=" + expectState("ts"));
  click('.tab[data-state="ap"]');
  ok("AP filter -> all ap cards (incl. ts+ap)", visible() === expectState("ap"), "visible=" + visible());
  click('.tab[data-state="central"]');
  ok("Central filter -> all central cards", visible() === expectState("central"), "visible=" + visible());
  click('.tab[data-state="all"]');
  ok("All filter -> every live card visible", visible() === liveCards.length, "visible=" + visible() + "/" + liveCards.length);
  click('.tab[data-state="ts"]');
  ok("active class follows clicks",
     document.querySelector('.tab[data-state="ts"]').classList.contains("active") &&
     !document.querySelector('.tab[data-state="all"]').classList.contains("active"));

  /* ---------- search ---------- */
  const q = document.getElementById("q");
  const nores = document.getElementById("nores");
  const tsCard = cards.find(c => (" " + c.getAttribute("data-state") + " ").indexOf(" ts ") > -1);
  const word = ((tsCard.getAttribute("data-text") || tsCard.textContent) || "x").trim().split(/\s+/)[1] || "x";
  q.value = word;
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("search narrows within TS filter (1 card)", visible() === 1, "visible=" + visible() + " word=" + word);
  click('.tab[data-state="all"]');
  q.value = "";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("clear search -> every live card back", visible() === liveCards.length, "visible=" + visible());
  q.value = "zzqx123notfound";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("no-match -> #nores shown, 0 cards",
     nores.style.display !== "none" && visible() === 0, "nores=" + nores.style.display + " visible=" + visible());
  q.value = "";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("clear -> live cards restored", visible() === liveCards.length);

  /* ---------- daily quiz ---------- */
  const qboxes = Array.from(document.querySelectorAll("#qwrap .qbox"));
  ok("quiz renders 6 questions", qboxes.length === 6, "count=" + qboxes.length);
  ok("first question active (.on)", qboxes[0].classList.contains("on"));
  const prog = document.querySelectorAll("#qprog i");
  ok("progress has 6 markers, first on", prog.length === 6 && prog[0].classList.contains("on"));

  // v145: the quiz rotates daily, so the answer key is read from the page's
  // own paper (window.SU_QUIZ) instead of a hard-coded array that would rot.
  const ANSWERS = window.SU_QUIZ.map(q => q.a);
  ok("daily quiz paper exposed (6 questions, rotates by IST day)",
     Array.isArray(window.SU_QUIZ) && window.SU_QUIZ.length === 6);
  // correct-answer path
  ANSWERS.forEach((a, ix) => {
    document.querySelector('.opt[data-q="' + ix + '"][data-o="' + a + '"]').click();
  });
  ok("Q1 correct option marked .correct",
     document.querySelector('.opt[data-q="0"][data-o="' + ANSWERS[0] + '"]').classList.contains("correct"));
  // walk to the end via Next buttons
  for (let ix = 0; ix < 5; ix++) {
    document.querySelector('.next[data-q="' + ix + '"]').click();
  }
  document.querySelector('.next[data-q="5"]').click(); // Finish ✔
  await sleep(50);
  ok("finish -> result shown 6/6",
     document.getElementById("qresult").classList.contains("show") &&
     document.getElementById("qscore").textContent === "6/6",
     document.getElementById("qscore").textContent);
  ok("best score persisted to localStorage",
     window.localStorage.getItem(window.SU_QUIZ_KEY) === "6");
  ok("best label updated (ఉత్తమం: 6/6)",
     document.getElementById("qbest").textContent.indexOf("6/6") > -1);
  document.getElementById("qretry").click();
  await sleep(50);
  const qboxes2 = Array.from(document.querySelectorAll("#qwrap .qbox"));
  ok("retry resets quiz (Q1 active, result hidden)",
     qboxes2.length === 6 && qboxes2[0].classList.contains("on") &&
     !document.getElementById("qresult").classList.contains("show"));
  // wrong-answer path
  const wrongIdx = (ANSWERS[0] + 1) % 4;
  document.querySelector('.opt[data-q="0"][data-o="' + wrongIdx + '"]').click();
  ok("wrong option marked .wrong",
     document.querySelector('.opt[data-q="0"][data-o="' + wrongIdx + '"]').classList.contains("wrong"));
  for (let ix = 0; ix < 5; ix++) document.querySelector('.next[data-q="' + ix + '"]').click();
  document.querySelector('.next[data-q="5"]').click();
  await sleep(50);
  ok("partial run -> score shown (0/6)",
     document.getElementById("qscore").textContent === "0/6",
     document.getElementById("qscore").textContent);
  document.getElementById("qretry").click();

  /* ---------- quiz promo + share + theme + totop ---------- */
  const quizHref = document.getElementById("quizlink").getAttribute("href");
  ok("v74: sidebar quiz card links to #quiz (no portal)",
     quizHref === "#quiz", quizHref);
  ok("v74: no portal links anywhere (no /exam/, no examlink)",
     !document.getElementById("examlink") &&
     !/\/exam\//.test(document.documentElement.innerHTML));
  ok("v72.1: 7-point article + దాని share buttons teesesaam (demo content ledu)",
     !document.getElementById("wa") && !document.getElementById("copylink") &&
     !/7 విషయాలు|QUICK ANSWER|ఎడిటర్ ఎంపిక/.test(html));
  const themeBtn = document.getElementById("theme");
  const wasDark = document.body.classList.contains("dark");
  themeBtn.click();
  ok("theme toggle flips body.dark", document.body.classList.contains("dark") !== wasDark);
  ok("theme persisted to localStorage",
     ["0", "1"].indexOf(window.localStorage.getItem("studentup-theme")) > -1);
  // totop: stub scrollY, fire scroll
  let fakeY = 0;
  Object.defineProperty(window, "scrollY", { get: () => fakeY, configurable: true });
  const totop = document.getElementById("totop");
  ok("totop hidden at top", !totop.classList.contains("show"));
  fakeY = 900;
  window.dispatchEvent(new window.Event("scroll"));
  ok("totop appears after scroll", totop.classList.contains("show"));
  ok("mobile nav present (4+ links)",
     document.querySelectorAll(".mobile-nav a").length >= 4,
     "count=" + document.querySelectorAll(".mobile-nav a").length);

  /* ---------- v45 social rail ---------- */
  const rail = document.querySelector(".su-social");
  const socials = rail ? Array.from(rail.querySelectorAll("a")) : [];
  ok("social rail present with exactly 4 buttons", !!rail && socials.length === 4, "count=" + socials.length);
  const styleText = Array.from(document.querySelectorAll("style")).map(s => s.textContent).join("\n");
  ok("social rail CSS: fixed right-side, vertically centered",
     /\.su-social\{[^}]*position:fixed[^}]*right:16px[^}]*top:50%/.test(styleText));
  const hosts = socials.map(a => { try { return new URL(a.getAttribute("href")).host; } catch (e) { return ""; } });
  ok("social hrefs: wa.me / t.me / instagram / youtube (https)",
     hosts.some(h => h.indexOf("wa.me") > -1) && hosts.some(h => h.indexOf("t.me") > -1) &&
     hosts.some(h => h.indexOf("instagram.com") > -1) && hosts.some(h => h.indexOf("youtube.com") > -1),
     hosts.join(","));
  ok("social links safe: target=_blank + rel=noopener + aria-label",
     socials.every(a => a.getAttribute("target") === "_blank" &&
       (a.getAttribute("rel") || "").indexOf("noopener") > -1 &&
       (a.getAttribute("aria-label") || "").length > 0));
  ok("social tooltips (data-label) on all 4",
     socials.every(a => (a.getAttribute("data-label") || "").length > 0),
     socials.map(a => a.getAttribute("data-label")).join(","));

  /* ---------- v46: top-right menu (desktop nav + mobile hamburger) ---------- */
  const navTop = document.querySelectorAll(".nav > a").length
    + document.querySelectorAll(".nav > .has-drop > a").length;
  ok("v72 desktop nav: 8 top-right items (5 + 3 dropdowns)", navTop === 8, "count=" + navTop);
  const drop = document.querySelector(".has-drop .drop");
  const dropItems = drop ? drop.querySelectorAll("a").length : 0;
  ok("dropdowns present with 5+ items each (jobs / exams / more)", !!drop && dropItems >= 5, "items=" + dropItems);
  ok("dropdown contains Partner with us link (v71 label)",
     Array.from(document.querySelectorAll(".drop a")).some(a => /Partner with us/.test(a.textContent)));
  ok("desktop nav underline animation CSS (scaleX)", /\.nav a::after\{[^}]*transform:scaleX\(0\)/.test(styleText));
  // hamburger
  const menubtn = document.getElementById("menubtn");
  const mpanel = document.getElementById("mpanel");
  ok("hamburger button present (top-right headactions)",
     !!menubtn && !!mpanel && document.querySelector(".headactions").contains(menubtn));
  ok("menu closed initially (aria-expanded=false)", menubtn.getAttribute("aria-expanded") === "false");
  menubtn.click();
  ok("click -> panel opens + aria-expanded=true + scroll-lock",
     mpanel.classList.contains("open") && menubtn.getAttribute("aria-expanded") === "true" &&
     document.body.classList.contains("mlock"));
  ok("mobile panel: 11 links + CTA + 4 socials",
     mpanel.querySelectorAll("a").length >= 15,
     "links=" + mpanel.querySelectorAll("a").length);
  ok("mobile panel has Partner + Quiz CTA",
     Array.from(mpanel.querySelectorAll("a")).some(a => /Partner with us/.test(a.textContent)) &&
     Array.from(mpanel.querySelectorAll("a")).some(a => a.textContent.indexOf("Daily Quiz") > -1));
  mpanel.querySelector('a[href="#jobs"]').click();
  ok("panel link click closes menu", !mpanel.classList.contains("open") && !document.body.classList.contains("mlock"));
  menubtn.click();
  document.dispatchEvent(new window.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
  ok("Escape closes menu", !mpanel.classList.contains("open"));

  /* ---------- v46: advanced ad slots ---------- */
  const ads = document.querySelectorAll(".su-ad");
  ok("4 ad slots total (leaderboard + in-feed + mid + sidebar)", ads.length === 4, "count=" + ads.length);
  const slots = Array.from(ads).map(a => a.getAttribute("data-slot")).sort();
  ok("slot map: in-feed, mid, sidebar, top-leaderboard",
     slots.join(",") === "in-feed,mid,sidebar,top-leaderboard", slots.join(","));
  ok("top leaderboard above hero (highest visibility)",
     document.querySelector('.su-ad[data-slot="top-leaderboard"]').closest(".wrap") !== null &&
     (document.querySelector('.su-ad[data-slot="top-leaderboard"]').compareDocumentPosition(
       document.querySelector(".hero")) & 4) !== 0); // 4 = DOCUMENT_POSITION_FOLLOWING
  ok("in-feed ad inside news grid (not .news — filters never hide ads)",
     document.getElementById("grid").contains(document.querySelector('.su-ad[data-slot="in-feed"]')) &&
     !document.querySelector('.su-ad[data-slot="in-feed"]').classList.contains("news"));
  ok("all ad CTAs safe: rel=sponsored nofollow (+ target=_blank external ki)",
     Array.from(document.querySelectorAll(".su-ad a")).every(a => {
       var rel = a.getAttribute("rel") || "";
       var ext = /^https?:/.test(a.getAttribute("href") || "");
       return /sponsored/.test(rel) && /nofollow/.test(rel) && (!ext || a.getAttribute("target") === "_blank");
     }));
  ok("all ad slots labeled SPONSORED + visible disclosure",
     Array.from(ads).every(a => /SPONSORED/i.test(a.textContent) && a.getAttribute("aria-label") === "Sponsored content"));
  ok("sidebar promo card removed — no public rate-card anchor (#ads)",
     !document.getElementById("ads") && !!document.getElementById("services"));


  /* ---------- v47: pure-Telugu content + trust + daily poll ---------- */
  const heroText = document.querySelector(".hero-slim h1").textContent;
  ok("v73 hero: English h1 (UI English — Telugu mattrame post content lo)",
     /[A-Za-z]{4,}/.test(heroText) && !/[\u0C00-\u0C7F]/.test(heroText), heroText.slice(0, 48));
  const telCount = (document.body.textContent.match(/[\u0C00-\u0C7F]/g) || []).length;
  ok("v73 scope: post/article content Telugu ga undi (300+ chars, UI kaadu)",
     telCount > 300, "telugu chars=" + telCount);
  const bodyTxt = document.body.textContent;
  ok("developer-facing demo text removed (no .env / Demo contact leaks)",
     !/\.env/.test(bodyTxt) && !/Demo contact/i.test(bodyTxt) && !/Call \(demo\)/i.test(bodyTxt) &&
     !/real number/i.test(bodyTxt));
  const tenglish = ["kosam", "cheyandi", "cheyali", "avutundi", "matrame", "ledu ", "undi ", "cheyyandi", "vachey", "petandi"];
  const tenglishHits = tenglish.filter(w => new RegExp("\\b" + w.trim() + "\\b", "i").test(bodyTxt));
  ok("no Romanized Tenglish words in visible text", tenglishHits.length === 0, "hits=" + tenglishHits.join(","));
  /* v70: developer proof text public site lo undakoodadu (user rule) */
  ok("developer proof text ledu (టెస్ట్ సూట్ tiles / verification gates / bug counts)",
     !document.getElementById("trust") && !document.querySelector(".qtile") &&
     !document.querySelector(".vsteps") && !/టెస్ట్ సూట్/.test(bodyTxt) &&
     !/బగ్గులు/.test(bodyTxt) && !/హామీ ఇవ్వదు/.test(bodyTxt));
  ok("policy links mobile panel lo nijamaina pages ki (broken #trust anchor ledu)",
     !/href="#trust"/.test(document.body.innerHTML) &&
     /pages\/editorial-policy\.html/.test(document.body.innerHTML));
  /* v146: deadline radar + scrollable rail */
  const radar = document.getElementById("suradar");
  ok("v146: deadline radar built from real card last dates (or hidden when none)",
     !!radar && (radar.hidden
       ? document.querySelectorAll("#suradarlist li").length === 0
       : document.querySelectorAll("#suradarlist .su-radar-item a[href]").length > 0));
  const rail0 = document.querySelector(".su-hot-rail");
  ok("v146: hot rail is a focusable horizontal scroller with arrow buttons",
     !!rail0 && rail0.getAttribute("tabindex") === "0" &&
     !!rail0.parentNode.querySelector(".su-rail-prev") &&
     !!rail0.parentNode.querySelector(".su-rail-next"));

  /* v147: homepage tools */
  document.getElementById("sufindbtn").click();
  await sleep(20);
  ok("v147: job finder returns matches for degree + Telangana",
     /\d+ match/.test(document.getElementById("sufindout").textContent) &&
     document.querySelectorAll("#sufindout li a[href]").length > 0);
  document.getElementById("subasic").value = "30000";
  document.getElementById("suda").value = "30";
  document.getElementById("suhra").value = "10";
  document.getElementById("sudeduct").value = "2000";
  document.getElementById("sucalcbtn").click();
  await sleep(20);
  ok("v147: salary calculator maths (30000 +30% DA +10% HRA -2000 = 40,000)",
     /Rs 40,000/.test(document.getElementById("sucalcout").textContent),
     document.getElementById("sucalcout").textContent.slice(0, 40));
  ok("v147: last-date calendar lists upcoming deadlines in order",
     document.querySelectorAll("#sucallist .su-cal-item a[href]").length > 0);

  /* v150: save-for-later (localStorage only) */
  const firstSave = document.querySelector("#grid .news .su-save");
  ok("v150: every card gets a Save button", !!firstSave &&
     document.querySelectorAll("#grid .news .su-save").length ===
     document.querySelectorAll("#grid .news").length);
  firstSave.click();
  await sleep(20);
  ok("v150: saving marks the button and fills the saved panel from localStorage",
     firstSave.getAttribute("aria-pressed") === "true" &&
     document.querySelectorAll("#susavebody li a[href]").length === 1 &&
     JSON.parse(window.localStorage.getItem("studentup-saved-v1") || "[]").length === 1);
  firstSave.click();
  await sleep(20);
  ok("v150: un-saving clears it again (no server, no account)",
     firstSave.getAttribute("aria-pressed") === "false" &&
     JSON.parse(window.localStorage.getItem("studentup-saved-v1") || "[]").length === 0);

  /* v155: personalised "your 5 today" */
  document.getElementById("suyouqual").value = "degree";
  document.getElementById("suyoustate").value = "ts";
  document.getElementById("suyoubtn").click();
  await sleep(20);
  const youRows = document.querySelectorAll("#suyoulist li a[href]");
  ok("v155: personalised list builds 1-5 ranked matches with a reason",
     youRows.length >= 1 && youRows.length <= 5 &&
     document.querySelectorAll("#suyoulist .su-you-why").length === youRows.length,
     "rows=" + youRows.length);
  ok("v155: profile saved in this browser only",
     JSON.parse(window.localStorage.getItem("studentup-profile-v1") || "{}").q === "degree");
  document.getElementById("suyoureset").click();
  await sleep(20);
  ok("v155: reset deletes the profile and the list",
     !window.localStorage.getItem("studentup-profile-v1") &&
     document.querySelectorAll("#suyoulist li").length === 0);

  const poll = document.getElementById("poll");
  ok("daily question section present (Today's question)",
     !!poll && /Today's question/.test(poll.textContent));
  ok("v74/v145: static poll bank (19 questions, daily rotation, no fetch, no server)",
     Array.isArray(window.POLL_BANK) && window.POLL_BANK.length === 19 &&
     window.POLL_BANK.every(q => q.o && q.o.length === 4 && q.a >= 0 && q.a < 4) &&
     !/\/poll\//.test(html));
  document.querySelector("#pollbox .poll-opt").click();
  await sleep(50);
  ok("v74: poll vote reveals correct answer + explanation (localStorage)",
     !!document.querySelector("#pollbox .poll-opt.correct") &&
     /correct one has|Correct!/.test(document.getElementById("pollbox").textContent) &&
     !!document.querySelector("#pollbox .poll-result-note"));
  ok("poll CSS: responsive + dark-mode rules", /\.poll\{/.test(styleText) && /body\.dark \.poll-opt/.test(styleText));
  ok("services card: working contact paths (no dev placeholders)",
     !!document.querySelector('#services a[href^="mailto:"]') &&
     !/\$\{/.test(document.getElementById("services").textContent));


  /* ---------- v48: real policy pages + SEO files + ad coverage ---------- */
  const policyHrefs = Array.from(document.querySelectorAll('a[href^="pages/"]')).map(a => a.getAttribute("href"));
  const needed = ["pages/about.html", "pages/contact.html", "pages/privacy.html", "pages/disclaimer.html", "pages/editorial-policy.html"];
  ok("all 5 real policy pages linked (no dead policy anchors)",
     needed.every(h => policyHrefs.indexOf(h) > -1) &&
     !/href="#trust">(About|Editorial|Privacy)/.test(document.documentElement.innerHTML),
     "links=" + policyHrefs.length);
  const fav = document.querySelector('link[rel="icon"]');
  ok("favicon declared", !!fav && /favicon\.svg$/.test(fav.getAttribute("href")), fav ? fav.getAttribute("href") : "none");
  const adSlots = Array.from(document.querySelectorAll(".su-ad"));
  ok("ad slots all labelled + sponsored rel (no unlabelled promo)",
     adSlots.length >= 4 && adSlots.every(a => /SPONSORED/i.test(a.textContent)));


  /* ---------- v50: phone neatness (tap targets, overflow, zoom) ---------- */
  ok("phone: horizontal-overflow guard on html/body",
     /html,body\{overflow-x:hidden/.test(styleText));
  ok("phone: tap targets >= 44px (nav, menu, buttons)",
     /\.nav a,\.drop a,\.mobile-nav a,\.mpanel a,\.round,[^{]*\{min-height:44px\}/.test(styleText));
  ok("phone: media never exceeds screen",
     /img,video,iframe,table\{max-width:100%\}/.test(styleText) && /img,video\{height:auto\}/.test(styleText));
  ok("phone: 16px inputs (no iOS zoom-jump on focus)",
     /input,select,textarea\{font-size:16px\}/.test(styleText));
  ok("phone: single-column layout switch at <=600px",
     /@media\(max-width:600px\)/.test(styleText) && /@media\(max-width:920px\)/.test(styleText));
  const navLinks = Array.from(document.querySelectorAll(".mobile-nav a"));
  ok("phone: bottom nav has 5 labelled destinations",
     navLinks.length === 5 && navLinks.every(a => a.textContent.trim().length > 0),
     "count=" + navLinks.length);


  /* ---------- v51: category menu + filter chips ---------- */
  const jobsDrop = document.querySelector(".has-drop .drop");
  const jobsItems = jobsDrop ? Array.from(jobsDrop.querySelectorAll("a")) : [];
  const jobsCats = jobsItems.map(a => a.getAttribute("data-goto-cat")).filter(Boolean);
  ok("jobs dropdown: 10 category links (incl. success stories + abroad pillar)",
     jobsCats.length === 10, "cats=" + jobsCats.join(","));
  for (const want of ["ts-jobs", "ap-jobs", "central-jobs", "abroad", "walkin", "software", "private", "outsourcing", "parttime", "success-stories"]) {
    ok("jobs menu has " + want, jobsCats.indexOf(want) > -1);
  }
  const examDrop = document.querySelectorAll(".has-drop .drop")[1];
  const examCats = examDrop ? Array.from(examDrop.querySelectorAll("a[data-goto-cat]")).map(a => a.getAttribute("data-goto-cat")) : [];
  ok("v74 exams dropdown: upcoming + tips + quiz (portal poyindi)",
     ["upcoming", "examtips"].every(c => examCats.indexOf(c) > -1) &&
     /Daily Quiz/.test(examDrop ? examDrop.textContent : "") &&
     !/Online Exams/.test(examDrop ? examDrop.textContent : ""),
     "cats=" + examCats.join(","));
  ok("v59 హాల్ టికెట్లు + ఫలితాలు top-level menu lonaki vachhayi",
     !!document.querySelector('.nav > a[data-goto-cat="hallticket"]') &&
     !!document.querySelector('.nav > a[data-goto-cat="results"]'));
  const chips = Array.from(document.querySelectorAll(".chip[data-cat]"));
  const chipCats = chips.map(c => c.getAttribute("data-cat"));
  ok("category chip row present with 17 filters (all + 16 pillars)", chips.length === 17, "chips=" + chips.length);
  const articleCats = new Set();
  Array.from(document.querySelectorAll("#grid .news")).forEach(n =>
    (n.getAttribute("data-cat") || "").split(" ").forEach(c => c && articleCats.add(c)));
  const orphan = chipCats.filter(c => c !== "all" && !articleCats.has(c));
  ok("every chip has matching content (no dead filter)", orphan.length === 0, "orphans=" + orphan.join(","));
  // clicking a chip filters the grid
  const walkinChip = chips.find(c => c.getAttribute("data-cat") === "walkin");
  walkinChip.click();
  const visibleAfter = Array.from(document.querySelectorAll("#grid .news"))
    .filter(n => !n.classList.contains("hidden"));
  ok("clicking వాక్-ఇన్ chip filters to only walk-in cards",
     visibleAfter.length > 0 && visibleAfter.every(n => (n.getAttribute("data-cat") || "").indexOf("walkin") > -1),
     "visible=" + visibleAfter.length);
  // menu deep-link also sets the filter (shareable behaviour)
  const tsLink = jobsItems.find(a => a.getAttribute("data-goto-cat") === "ts-jobs");
  tsLink.click();
  const afterMenu = Array.from(document.querySelectorAll("#grid .news")).filter(n => !n.classList.contains("hidden"));
  ok("menu link (టీఎస్ ఉద్యోగాలు) deep-filters the grid",
     afterMenu.length > 0 && afterMenu.every(n => (n.getAttribute("data-cat") || "").indexOf("ts-jobs") > -1),
     "visible=" + afterMenu.length);
  ok("chip CSS: active state + dark mode + tap size",
     /\.chip\.active\{/.test(styleText) && /body\.dark \.chip/.test(styleText) &&
     /\.chip\{[^}]*border-radius:999px/.test(styleText));
  // reset back to all for later checks
  chips.find(c => c.getAttribute("data-cat") === "all").click();
  ok("'అన్నీ' chip restores the full grid",
     Array.from(document.querySelectorAll("#grid .news")).filter(n => !n.classList.contains("hidden")).length >= 13);


  /* ---------- v52 + v71: revenue wiring (partner page, no public rate card) ---------- */
  const advLinks = Array.from(document.querySelectorAll('a[href="pages/advertise.html"]'));
  ok("site links the partner page (2+ places: dropdown + mobile panel)",
     advLinks.length >= 2, "links=" + advLinks.length);
  ok("no sidebar rate card — pricing handled personally (v71)",
     !document.getElementById("ads") && !/₹\s?\d/.test(document.body.textContent));
  ok("house ads documented on site (StudentUp own promos, not SPONSORED)",
     /StudentUp/.test(document.body.textContent));


  /* ---------- v71: join block (WhatsApp + Telegram) — lead form ippudu contact page lo ---------- */
  ok("homepage lead form removed (v71 — contact page ki move ayyindi)",
     !document.getElementById("leadform"));
  const join = document.getElementById("join");
  ok("join block present on homepage", !!join);
  const joinWa = join ? join.querySelector('a[href*="wa.me"]') : null;
  const joinTg = join ? join.querySelector('a[href*="t.me"]') : null;
  ok("join block: WhatsApp + Telegram channel buttons",
     !!joinWa && !!joinTg && /wa\.me\/\d{6,}/.test(joinWa.getAttribute("href")));
  ok("join block: free + no-spam promise", !!join && /free/i.test(join.textContent),
     join ? join.textContent.slice(0, 40) : "missing");

  /* ---------- v71: Students Internet Center (apply from home) ---------- */
  const ic = document.getElementById("services");
  ok("Students Internet Center block present",
     !!ic && /Students Internet Center/.test(ic.textContent));
  const icWa = ic ? ic.querySelector('a[href*="wa.me"]') : null;
  ok("Internet Center: WhatsApp box opens our chat (wa.me)",
     !!icWa && /wa\.me\/\d{6,}/.test(icWa.getAttribute("href")),
     icWa ? icWa.getAttribute("href").slice(0, 32) : "missing");
  ok("Internet Center: 3 steps (call → documents → PDF)",
     !!ic && /Call/i.test(ic.textContent) && /documents/i.test(ic.textContent) &&
     /PDF/.test(ic.textContent));
  ok("Internet Center: call + email fallback",
     !!ic && !!ic.querySelector('a[href^="tel:"]') && !!ic.querySelector('a[href^="mailto:"]'));
  ok("no public rate card anywhere on homepage (no ₹ pricing)",
     !/₹\s?\d/.test(document.body.textContent));

  /* ---------- v71: social rail — auto-hide cycle + controls ---------- */
  const railClose = document.getElementById("suclose");
  const railTab = document.getElementById("sutab");
  ok("rail cycle: hide (✕) + instant show (‹) controls present", !!railClose && !!railTab);
  ok("rail cycle: 9s show / 2-minute return coded",
     /SHOW_MS\s*=\s*9000/.test(html) && /CYCLE_MS\s*=\s*120000/.test(html));
  ok("rail cycle CSS: hidden state slides away",
     /\.su-social\.su-out\{[^}]*visibility:hidden/.test(styleText));
  if (rail && railClose && railTab) {
    railClose.dispatchEvent(new window.Event("click", { bubbles: true }));
    await sleep(30);
    const hiddenOk = rail.classList.contains("su-out") && railTab.classList.contains("on") &&
                     rail.getAttribute("aria-hidden") === "true";
    railTab.dispatchEvent(new window.Event("click", { bubbles: true }));
    await sleep(30);
    const backOk = !rail.classList.contains("su-out") && !railTab.classList.contains("on");
    ok("rail cycle: ✕ hides it, ‹ brings it back (aria-hidden toggles)", hiddenOk && backOk,
       "hidden=" + hiddenOk + " back=" + backOk);
  } else {
    ok("rail cycle: ✕ hides it, ‹ brings it back (aria-hidden toggles)", false, "controls missing");
  }
  ok("mobile: social chips smaller (<= 34px) + mobile nav icons smaller",
     /\.su-social a\{width:34px;height:34px/.test(styleText) &&
     /\.mobile-nav b\{display:block;font-size:13px/.test(styleText));

  /* ---------- v72: బ్రేకింగ్ teesesaam (public surface clean) ---------- */
  ok("v72: బ్రేకింగ్ టికర్/section/nav link public surface nunchi teesesaam",
     !document.getElementById("tickerwrap") && !document.getElementById("breaking") &&
     !document.querySelector(".navbrk") && !/బ్రేకింగ్/.test(document.body.textContent),
     "ticker=" + !!document.getElementById("tickerwrap") + " section=" + !!document.getElementById("breaking"));
  ok("v72: internal metrics public ga levu (11,192 · 143 sources · 59 జిల్లాల · radar)",
     !/11,192|143 మూలాల|59 జిల్లాల|రాడార్|కీవర్డ్లు/.test(html) &&
     !/జిల్లాల పర్యవేక్షణ/.test(html));
  ok("v72: నమూనా/DEMO labels public copy nunchi poyayi",
     !/నమూనా|DEMO/.test(document.body.textContent.replace(/\s+/g, " ")));
  ok("v72: hero-proof stats row teesesaam",
     !document.querySelector(".hero-proof") && !document.querySelector(".proof"));

  /* ---------- v72.1: public copy clean (topbar, demo ads, fake countdown) ---------- */
  ok("v72.1: coverage topbar teesesaam (jillalu/update-count line public lo ledu)",
     !document.querySelector(".topbar") &&
     !/\(33 జిల్లాలు\)|\(26 జిల్లాలు\)|జిల్లాల పర్యవేక్షణ|ప్రతిరోజూ ధృవీకృత అప్డేట్/.test(html));
  ok("v72.1: ad slots fake advertiser/example.com lekunda — 'slot available' house creative",
     /example\.com/.test(html) === false &&
     Array.from(document.querySelectorAll(".su-ad")).every(a => !/ABC |abc-college|tuition-demo|stationery-demo/.test(a.textContent)) &&
     /\.html$/.test(document.querySelector(".su-ad a").getAttribute("href")));
  ok("v74: quiz wording English, portal wording gone (no Online Exams)",
     /Daily Quiz/.test(html) && !/Online Exams/.test(html));

  /* ---------- v72: ఎక్కువగా వెతికేవి + పర్ఫెక్ట్ మెనూ ---------- */
  const usedTiles = Array.from(document.querySelectorAll(".usedgrid .usedcard"));
  const usedCats = usedTiles.map(a => a.getAttribute("data-goto-cat"));
  ok("v59/v89/v134 most-used strip: 10 tiles, TS/AP/Central mundu (student order)",
     usedTiles.length === 10 && JSON.stringify(usedCats) === JSON.stringify(
       ["ts-jobs","ap-jobs","central-jobs","hallticket","results","walkin","software","success-stories","private","current"]),
     usedCats.join(","));
  // v134: update-count badges removed by design — they covered the tile text.
  const anyCount = document.querySelector(".usedgrid .ucount, [data-ucount]");
  ok("v134 most-used tiles: filter deep-link, no update-count badge",
     usedTiles.every(a => /#jobs/.test(a.getAttribute("href"))) && !anyCount,
     anyCount ? "badge inka undi" : "clean");
  const navCats = Array.from(document.querySelectorAll(".nav > a, .nav > .has-drop > a"))
    .map(a => a.textContent.replace(/▾/g, "").trim());
  ok("v72 perfect menu order (Home · Jobs · Hall Tickets · Results · Scholarships · Current Affairs · Exams · More)",
     /^Home/.test(navCats[0]) && /Jobs/.test(navCats[1]) && /Hall Tickets/.test(navCats[2]) &&
     /Results/.test(navCats[3]) && /Scholarships/.test(navCats[4]) &&
     /Current Affairs/.test(navCats[5]) && /Exams/.test(navCats[6]) && /More/.test(navCats[7]),
     /**/ navCats.join(" | "));
  const jobDrop = Array.from(document.querySelectorAll(".nav .drop a[data-goto-cat]"))
    .slice(0, 6).map(a => a.getAttribute("data-goto-cat"));
  ok("v59 jobs dropdown order: TS · AP · Central · Private · Walk-in · Software",
     JSON.stringify(jobDrop) === JSON.stringify(
       ["ts-jobs","ap-jobs","central-jobs","private","walkin","software"]),
     jobDrop.join(","));
  const firstCards = Array.from(document.querySelectorAll("#grid .news"))
    .slice(0, 3).map(c => c.getAttribute("data-cat"));
  ok("v59 grid: TS/AP govt cards mundu (student-first order)",
     /ts-jobs/.test(firstCards[0]) && /ts-jobs|ap-jobs/.test(firstCards[1]) && /ap-jobs/.test(firstCards[2]),
     firstCards.join(" | "));
  ok("v76 CSS: search panel + qual dropdown + install button + used grid shipped (ticker CSS gone)",
     /\.searchpanel\{/.test(styleText) && /\.qualsel\{/.test(styleText) &&
     /\.installbtn\{/.test(styleText) && /\.usedgrid\{/.test(styleText) &&
     !/\.tickerwrap\{/.test(styleText) && !/\.breaking\{/.test(styleText));
  const mpUsed = Array.from(document.querySelectorAll(".mpanel a[data-goto-cat]"))
    .slice(0, 8).map(a => a.getAttribute("data-goto-cat"));
  ok("v59/v89 mobile panel: same most-used order (TS/AP/Central mundu)",
     JSON.stringify(mpUsed) === JSON.stringify(
       ["hallticket","results","ts-jobs","ap-jobs","central-jobs","hallticket","results","walkin"]),
     mpUsed.join(","));
  ok("v72 mobile panel: search link undi, breaking link ledu",
     !!document.querySelector('.mpanel a[href="#searchpanel"], .mpanel a[href*="?s="]') &&
     !document.querySelector(".mpanel .mbrk"));

  /* ---------- v72: menu pakkana search (🔍 panel) ---------- */
  const sbtn = document.getElementById("searchbtn");
  const spanel = document.getElementById("searchpanel");
  const qtop = document.getElementById("qtop");
  ok("v72 header search: 🔍 button + panel + input (menu pakkana)",
     !!sbtn && !!spanel && !!qtop && spanel.hasAttribute("hidden") &&
     sbtn.getAttribute("aria-controls") === "searchpanel" &&
     /Search jobs/.test(qtop.getAttribute("placeholder") || ""));
  sbtn.click();
  ok("v72 search panel opens on 🔍 click (aria-expanded true)",
     !spanel.hasAttribute("hidden") && sbtn.getAttribute("aria-expanded") === "true");
  qtop.value = "TSPSC";
  document.getElementById("searchgo").click();
  await sleep(30);
  const visAfterSearch = Array.from(document.querySelectorAll("#grid .news"))
    .filter(c => !c.classList.contains("hidden")).length;
  ok("v72 search panel drives grid filter (TSPSC → few cards, panel closes)",
     visAfterSearch > 0 && visAfterSearch < cards.length && spanel.hasAttribute("hidden"),
     "visible=" + visAfterSearch);
  document.getElementById("searchclose").click();
  q.value = ""; q.dispatchEvent(new window.Event("input", { bubbles: true }));
  click('.tab[data-state="all"]');

  /* ---------- v76: విద్యార్హత dropdown (10th · 10+2 · డిగ్రీ · పీజీ …) ---------- */
  const qualSel = document.getElementById("qualsel");
  const qslugs = Array.from(qualSel.options).map(o => o.value);
  function setQual(v) {
    qualSel.value = v;
    qualSel.dispatchEvent(new window.Event("change", { bubbles: true }));
  }
  ok("v76 qualification dropdown: 9 options (అన్నీ + 7 అర్హతలు + ⏳ 7 రోజుల్లో ముగిసేవి)",
     !!qualSel && !!document.querySelector('label[for="qualsel"]') &&
     JSON.stringify(qslugs) === JSON.stringify(
       ["all","10th","inter","iti","diploma","degree","pg","btech","closing"]),
     qslugs.join(","));
  ok("v72 every job card ki data-qual tag undi (auto tag)",
     Array.from(document.querySelectorAll("#grid .news"))
       .every(c => (c.getAttribute("data-qual") || "").length > 0));
  function qVisible() {
    return Array.from(document.querySelectorAll("#grid .news"))
      .filter(c => !c.classList.contains("hidden"));
  }
  setQual("10th");
  ok("v76 qualification filter: 10వ తరగతి → only 10th eligible cards + live count",
     qVisible().length > 0 && qVisible().every(c => /10th/.test(c.getAttribute("data-qual"))) &&
     !qVisible().some(c => /btech/.test(c.getAttribute("data-qual"))) &&
     /10th Pass \(\d+\)/.test(qualSel.options[1].textContent),
     "visible=" + qVisible().length);
  setQual("degree");
  ok("v76 qualification filter: డిగ్రీ → degree cards + count label update",
     qVisible().length > 0 && qVisible().every(c => /degree/.test(c.getAttribute("data-qual"))) &&
     /opportunities/.test(document.getElementById("qcount").textContent),
     "visible=" + qVisible().length + " count=" + document.getElementById("qcount").textContent);
  /* ---------- v72.1: అర్హత ప్రకారం విభాగాలు (automatic grouping) ---------- */
  {
    const host = document.getElementById("qualsplit");
    const groups = host ? Array.from(host.querySelectorAll(".qgroup")) : [];
    ok("v72.1 అర్హత విభాగాలు: 8 groups (7 అర్హతలు + ⏳ closing)",
       groups.length === 8 &&
       JSON.stringify(groups.map(g => g.getAttribute("data-qgroup"))) ===
         JSON.stringify(["10th","inter","iti","diploma","degree","pg","btech","closing"]),
       "groups=" + groups.length);
    const visibleGroups = groups.filter(g => !g.hidden);
    ok("v72.1 అర్హత విభాగాలు: grid nunchi automatic ga nimpabaddayi (count + links)",
       visibleGroups.length >= 3 && visibleGroups.every(g =>
         !!g.querySelector("h3 .qgnum") && g.querySelectorAll("li a").length > 0),
       "visible=" + visibleGroups.length);
    const first = visibleGroups[0];
    const gKey = first.getAttribute("data-qgroup");
    const titled = first.querySelectorAll("li a").length;
    const gridCards = Array.from(document.querySelectorAll("#grid .news"));
    const left = c => {
      /* v174: page v150 math ye — whole-day UTC floor (23:59:59+round version
       * midnight boundary drifty: yesterday date -0 la count ayedi). */
      const v = c.getAttribute("data-last");
      if (!v) return null;
      const p = v.split("-");
      const t0 = new Date(); t0.setHours(0, 0, 0, 0);
      return Math.floor((Date.UTC(+p[0], +p[1] - 1, +p[2]) -
        Date.UTC(t0.getFullYear(), t0.getMonth(), t0.getDate())) / 86400000);
    };
    const expected = gridCards.filter(c => {
      const l = left(c);
      const qua = (c.getAttribute("data-qual") || "").toLowerCase();
      return gKey === "closing" ? (l !== null && l >= 0 && l <= 7)
                                : (qua.indexOf(gKey) > -1 && !(l !== null && l < 0));
    }).length;
    ok("v72.1 అర్హత విభాగాలు: group content grid tho exact match (auto, manual ledu)",
       titled === expected, "group=" + gKey + " listed=" + titled + " expected=" + expected);
    const counter = visibleGroups.find(g => g.querySelector("h3 .qgnum"));
    ok("v72.1 అర్హత విభాగాలు: count chip chupistundi",
       /^\d+$/.test(counter.querySelector(".qgnum").textContent), counter.querySelector(".qgnum").textContent);
  }

  setQual("closing");
  // v150: whole-day maths, same as the page. The old 23:59:59 + Math.round
  // version drifted by a day around midnight and made this check flaky.
  const soonExpected = Array.from(document.querySelectorAll("#grid .news")).filter(c => {
    const v = c.getAttribute("data-last"); if (!/^\d{4}-\d{2}-\d{2}$/.test(v || "")) return false;
    const p = v.split("-");
    const now = new Date();
    const left = Math.floor((Date.UTC(+p[0], +p[1] - 1, +p[2]) -
                 Date.UTC(now.getFullYear(), now.getMonth(), now.getDate())) / 86400000);
    return left >= 0 && left <= 7;
  }).length;
  ok("v76 qualification filter: ⏳ 7 రోజుల్లో ముగిసేవి → closing-soon cards mattrame",
     qVisible().length === soonExpected && qVisible().every(c => !!c.getAttribute("data-last")),
     "visible=" + qVisible().length + " expected=" + soonExpected);
  /* expiring card: past date → expired badge + default ga hide */
  const expiredCard = document.querySelector("#grid .news").cloneNode(true);
  expiredCard.setAttribute("data-last", "2026-01-05");
  expiredCard.setAttribute("data-qual", "degree");
  document.getElementById("grid").appendChild(expiredCard);
  q .value = ""; q.dispatchEvent(new window.Event("input", { bubbles: true }));
  setQual("all");
  ok("v72 expired job card: 'Deadline passed' badge + default ga hide",
     expiredCard.classList.contains("expired") &&
     /Deadline passed/.test(expiredCard.textContent) &&
     expiredCard.classList.contains("hidden"));
  expiredCard.remove();
  setQual("all");

  /* ---------- v72.1: category + అర్హత kalisi filter (preview) ---------- */
  setQual("degree");
  const catChipTs = Array.from(document.querySelectorAll(".chip[data-cat]"))
    .find(c => c.getAttribute("data-cat") === "ts-jobs");
  if (catChipTs) catChipTs.click();
  const combo = Array.from(document.querySelectorAll("#grid .news")).filter(c => !c.classList.contains("hidden"));
  ok("v72.1: category + అర్హత kalisi filter (rendu condition)",
     combo.length > 0 && combo.every(c => /degree/.test(c.getAttribute("data-qual")) &&
       (" " + (c.getAttribute("data-cat") || "") + " ").indexOf(" ts-jobs ") > -1),
     "visible=" + combo.length);
  click('.chip[data-cat="all"]');
  setQual("all");

  /* ---------- v72: PWA — app-laga install ---------- */
  const installBtn = document.getElementById("installbtn");
  ok("v72 PWA: manifest link + theme-color + apple touch icon",
     !!document.querySelector('link[rel="manifest"][href="manifest.webmanifest"]') &&
     !!document.querySelector('meta[name="theme-color"]') &&
     !!document.querySelector('link[rel="apple-touch-icon"]'));
  ok("v72.1 Download App: button prathi visit lo kanipistundi (hidden kaadu)",
     !!installBtn && !installBtn.hasAttribute("hidden") &&
     /Download App/.test(installBtn.textContent) && !!installBtn.querySelector(".ibadge"));
  const isheet = document.getElementById("installhint");
  ok("v72.1 App డౌన్‌లోడ్: device-wise install sheet (Android/iPhone/Computer steps)",
     !!isheet && isheet.hasAttribute("hidden") &&
     isheet.querySelectorAll("#isteps li").length === 3 &&
     /Android/.test(isheet.textContent) && /iPhone/.test(isheet.textContent) &&
     !!document.getElementById("installnow") && !!document.getElementById("installclose"));
  installBtn.click();
  ok("v72.1 App డౌన్‌లోడ్: prompt lekapote sheet terustundi (steps chupistundi)",
     !isheet.hasAttribute("hidden") && /Add to Home Screen/.test(isheet.textContent));
  document.getElementById("installclose").click();
  ok("v72.1 sheet close button pani chestundi", isheet.hasAttribute("hidden"));
  {
    const ev = new window.Event("beforeinstallprompt");
    let prompted = 0;
    ev.prompt = () => { prompted++; };
    ev.userChoice = Promise.resolve({ outcome: "accepted" });
    window.dispatchEvent(ev);
    installBtn.click();
    await sleep(20);
    ok("v72.1 App డౌన్‌లోడ్: beforeinstallprompt unte click tho prompt open",
       prompted === 1, "prompted=" + prompted);
    ok("v72.1 App డౌన్‌లోడ్: install ayyaka button hide (appinstalled)",
       (window.dispatchEvent(new window.Event("appinstalled")), installBtn.hasAttribute("hidden")));
  }

  /* ---------- v71: contact page (lead form) + partner page (no public rates) ---------- */
  {
    const contactHtml = fs.readFileSync(path.resolve(__dirname, "../../preview/pages/contact.html"), "utf8");
    const cdom = new JSDOM(contactHtml, {
      url: "http://localhost/pages/contact.html", runScripts: "dangerously", pretendToBeVisual: true,
    });
    await sleep(200);
    const cdoc = cdom.window.document;
    const cform = cdoc.getElementById("leadform");
    ok("contact page: free-updates form present", !!cform);
    ok("contact page: name + phone + interest + city fields",
       !!cdoc.getElementById("ld-name") && !!cdoc.getElementById("ld-phone") &&
       !!cdoc.getElementById("ld-interest") && !!cdoc.getElementById("ld-city"));
    const chp = cdoc.getElementById("ld-website");
    ok("contact page: honeypot hidden (spam trap)",
       !!chp && chp.getAttribute("aria-hidden") === "true" && /lead-hp/.test(chp.className));
    ok("contact page: Internet Center WhatsApp box (wa.me)",
       !!cdoc.querySelector('a.wa-box[href*="wa.me"]'));
    ok("contact page: call link (tel:) + email link",
       !!cdoc.querySelector('a[href^="tel:"]') && !!cdoc.querySelector('a[href^="mailto:"]'));
    const contactBody = contactHtml.replace(/<nav[\s\S]*?<\/nav>/g, "")
      .replace(/<ul class="sub-menu"[\s\S]*?<\/li><\/ul>/g, "");
    ok("contact page: no public ad rate card in the page body (service price list is v196 public)",
       !/₹\s?\d/.test(contactBody) && !/rate card|per post|sponsor rate/i.test(contactBody));
    if (cform) {
      let sent = false;
      cform.addEventListener("submit", () => { sent = true; }, true);
      cdoc.getElementById("ld-name").value = "Ravi";
      cdoc.getElementById("ld-phone").value = "123";
      cform.dispatchEvent(new cdom.window.Event("submit", { bubbles: true, cancelable: true }));
      await sleep(80);
      const cmsg = cdoc.getElementById("ld-msg");
      ok("contact page: bad phone → error shown, form not sent",
         sent === true && !!cmsg && /10-digit/.test(cmsg.textContent) && /err/.test(cmsg.className),
         cmsg ? cmsg.textContent.slice(0, 40) : "no message");
    } else {
      ok("contact page: bad phone → error shown, form not sent", false, "no form");
    }
    cdom.window.close();

    const advHtml = fs.readFileSync(path.resolve(__dirname, "../../preview/pages/advertise.html"), "utf8");
    const advBody = advHtml.replace(/<nav[\s\S]*?<\/nav>/g, "")
      .replace(/<ul class="sub-menu"[\s\S]*?<\/li><\/ul>/g, "");
    ok("partner page: no public ad price table / booking flow in the body",
       !/₹\s?\d/.test(advBody) && !/<table[\s\S]{0,400}₹/.test(advBody) &&
       !/Booking/.test(advBody));
    ok("partner page: WhatsApp + email contact routes",
       /wa\.me\/\d{6,}/.test(advHtml) && /mailto:/.test(advHtml));
    ok("partner page: SPONSORED labelling + policy rules kept",
       /SPONSORED/.test(advHtml) && /rel="sponsored nofollow"/.test(advHtml));
    ok("partner page: rates shared personally (honest note)",
       /shared personally|personally/i.test(advHtml) && /never guarantee/i.test(advHtml));
  }


  /* ---------- v197: advanced mega menu + daily quiz + reader poll ----------
   * Owner ask (2026-10-03): "quiz polls daily advancedga ... advanced menu
   * build cheyu". Ee block preview/worldclass/index.html (real-theme mirror)
   * ni jsdom lo run chesi — mega panel behaviour, quiz grading, poll vote,
   * sprite completeness mariyu "raw SVG text" regression ni gate chestundi. */
  {
    const wcHtml = fs.readFileSync(path.resolve(__dirname, "../../preview/worldclass/index.html"), "utf8");
    const menuJs = fs.readFileSync(path.resolve(__dirname,
      "../../wordpress-theme/studentup/assets/js/studentup-menu.js"), "utf8");
    const wdom = new JSDOM(wcHtml, {
      url: "https://studentup.in/", runScripts: "dangerously", pretendToBeVisual: true,
    });
    const w = wdom.window, wd = w.document;
    await sleep(250);
    try { w.eval(menuJs); } catch (e) { failed.push("v197 menu JS eval: " + e.message); }

    /* --- mega nav structure --- */
    const navEl = wd.querySelector("nav.nav");
    const primary = wd.querySelector("ul.menu-primary");
    const topLis = primary ? [].slice.call(primary.children).filter(n => n.tagName === "LI") : [];
    const megaLis = topLis.filter(li => li.querySelector("[data-su-mega]"));
    ok("v197 mega nav: 5 advanced groups (Jobs · Exams · Scholarships · Tools · More)",
       megaLis.length >= 5, "groups=" + megaLis.length);

    let wiredOk = megaLis.length > 0;
    let colsOk = true, featOk = true;
    megaLis.forEach(li => {
      const a = li.querySelector("a[aria-haspopup]");
      const panel = li.querySelector("[data-su-mega]");
      if (!a || !panel) { wiredOk = false; return; }
      const id = a.getAttribute("aria-controls");
      if (!id || !wd.getElementById(id) || id !== panel.id) wiredOk = false;
      if (a.getAttribute("aria-expanded") !== "false") wiredOk = false;
      if (panel.querySelectorAll(".su-mega-col").length < 2) colsOk = false;
      if (!panel.querySelector(".su-mega-feat") || !panel.querySelector(".su-mega-cta")) featOk = false;
      if (!panel.querySelector(".su-mega-list a")) colsOk = false;
    });
    ok("v197 mega nav: every trigger wired (aria-haspopup/expanded/controls → real panel)", wiredOk);
    ok("v197 mega nav: panels have 2+ columns with links + recommended card", colsOk && featOk);

    /* --- keyboard: ArrowDown opens, Escape closes --- */
    const firstLi = megaLis[0];
    const firstA = firstLi ? firstLi.querySelector("a[aria-haspopup]") : null;
    if (firstA) {
      firstA.dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    }
    ok("v197 menu: ArrowDown opens the group (aria-expanded=true)",
       !!firstLi && firstLi.classList.contains("su-open") &&
       firstA.getAttribute("aria-expanded") === "true");
    if (firstA) firstA.dispatchEvent(new w.KeyboardEvent("keydown", { key: "Escape", bubbles: true }));
    ok("v197 menu: Escape closes it again (aria-expanded=false, class removed)",
       !!firstLi && !firstLi.classList.contains("su-open") &&
       firstA.getAttribute("aria-expanded") === "false");

    /* --- outside click closes an open panel --- */
    if (firstA) firstA.dispatchEvent(new w.KeyboardEvent("keydown", { key: "ArrowDown", bubbles: true }));
    wd.body.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
    ok("v197 menu: outside click closes every panel", !firstLi.classList.contains("su-open"));

    /* --- regression: theme toggle must render real SVG, never raw markup --- */
    const themeBtn = wd.getElementById("su-theme");
    ok("v197 theme toggle: renders an inline <svg> child (no raw markup text)",
       !!themeBtn && !!themeBtn.querySelector("svg") && themeBtn.textContent.indexOf("<svg") === -1,
       themeBtn ? themeBtn.textContent.slice(0, 30) : "no button");

    /* --- daily quiz: server-rendered + JS grading --- */
    const qForm = wd.querySelector("[data-su-quiz-form]");
    const qFields = qForm ? [].slice.call(qForm.querySelectorAll("fieldset.su-q")) : [];
    ok("v197 quiz: 5 questions server-rendered with answer keys (data-c)",
       qFields.length === 5 && qFields.every(f => /^\d+$/.test(f.getAttribute("data-c") || "")));
    ok("v197 quiz: options + explanation markup pre-rendered (no-JS readable)",
       !!qForm && qForm.querySelectorAll(".su-opt").length >= 20 &&
       qForm.querySelectorAll("[data-su-why]").length === qFields.length);

    let rightMarked = 0, wrongMarked = 0;
    qFields.forEach(fs => {
      const lab = fs.querySelector(".su-opt");
      if (lab) lab.dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
      if (fs.querySelector(".su-opt.right")) rightMarked++;
      if (fs.querySelector(".su-opt.wrong")) wrongMarked++;
    });
    const scoreEl = wd.querySelector("[data-su-quiz-score]");
    ok("v197 quiz: instant grading marks right + wrong options",
       rightMarked === 5 && wrongMarked === 4, "right=" + rightMarked + " wrong=" + wrongMarked);
    ok("v197 quiz: score + progress bar update after answering",
       !!scoreEl && scoreEl.textContent === "1" &&
       /100%/.test((wd.querySelector("[data-su-quiz-bar]") || {}).getAttribute
         ? wd.querySelector("[data-su-quiz-bar]").getAttribute("style") : ""),
       "score=" + (scoreEl ? scoreEl.textContent : "?"));
    ok("v197 quiz: every explanation is revealed after answering",
       qFields.every(fs => { const p = fs.querySelector("[data-su-why]"); return p && !p.hasAttribute("hidden"); }));
    const shareEl = wd.querySelector("[data-su-quiz-share]");
    ok("v197 quiz: share link appears with the real score (wa.me)",
       !!shareEl && !shareEl.hasAttribute("hidden") && /wa\.me\/\?text=/.test(shareEl.getAttribute("href") || "") &&
       /1\/5/.test(decodeURIComponent(shareEl.getAttribute("href") || "")));
    const streakEl = wd.querySelector("[data-su-quiz-streak]");
    ok("v197 quiz: streak line shows after finishing (device-only, no server)",
       !!streakEl && !streakEl.hasAttribute("hidden") && /done today/.test(streakEl.textContent));

    /* --- poll: JS vote path + no-JS fallback --- */
    const pollBox = wd.querySelector("[data-su-poll]");
    const pollForm = pollBox ? pollBox.querySelector("[data-su-poll-form]") : null;
    const pollOpts = pollBox ? [].slice.call(pollBox.querySelectorAll(".su-poll-opt")) : [];
    ok("v197 poll: 4 options + form present (server can count a plain POST)",
       pollOpts.length === 4 && !!pollForm &&
       pollForm.getAttribute("method") === "post" && !!pollForm.querySelector("input[name=su_poll_opt]"));
    if (pollOpts[1]) pollOpts[1].dispatchEvent(new w.MouseEvent("click", { bubbles: true }));
    ok("v197 poll: selecting an option marks it (keyboard/touch friendly)",
       pollOpts.length > 1 && pollOpts[1].classList.contains("on"));
    if (pollForm) pollForm.dispatchEvent(new w.Event("submit", { bubbles: true, cancelable: true }));
    const pcts = pollBox ? [].slice.call(pollBox.querySelectorAll("[data-su-pct]")) : [];
    ok("v197 poll: vote shows percentages and locks the ballot (no double vote)",
       pcts.length === 4 && /%/.test(pcts[1].textContent) &&
       pollOpts.every(o => { const i = o.querySelector("input"); return !i || i.disabled; }) &&
       !pollBox.querySelector("[data-su-poll-vote]"));

    /* --- sprite completeness (no blank icon boxes) --- */
    const symbols = {};
    [].slice.call(wd.querySelectorAll("symbol[id]")).forEach(s => { symbols[s.id] = 1; });
    const uses = [].slice.call(wd.querySelectorAll("use")).map(u => (u.getAttribute("href") || "").replace("#", ""));
    ok("v197 preview: every <use> icon resolves to a sprite symbol",
       uses.length > 0 && uses.every(k => symbols[k]), "uses=" + uses.length + " symbols=" + Object.keys(symbols).length);

    /* --- quiz/poll UI stays English (v73 invariant) --- */
    const engScope = (qForm ? qForm.textContent : "") + (pollBox ? pollBox.textContent : "");
    ok("v197 quiz/poll UI is English-only (v73 invariant)",
       !/[\u0C00-\u0C7F]/.test(engScope));

    wdom.window.close();
  }

  /* ---------- check-count drift guard (docs parity) ---------- */
  if (passed.length !== EXPECTED_CHECKS) {
    failed.push(`check count drift: ${passed.length} ran vs EXPECTED_CHECKS ${EXPECTED_CHECKS} ` +
                `(jsdom counts ni README/MANUAL/GO_LIVE lo update cheyandi)`);
  }

  /* ---------- summary ---------- */
  console.log("=".repeat(64));
  console.log("  JSDOM RUNTIME CHECKS — preview/index.html");
  console.log("=".repeat(64));
  passed.forEach(p => console.log("  PASS  " + p));
  failed.forEach(f => console.log("  FAIL  " + f));
  console.log("-".repeat(64));
  console.log(`  ${passed.length}/${passed.length + failed.length} checks passed`);
  console.log("=".repeat(64));
  window.close();
  process.exit(failed.length ? 1 : 0);
})().catch(e => { console.error("HARNESS ERROR:", e); process.exit(2); });
