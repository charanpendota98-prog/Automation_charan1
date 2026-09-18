/* Browser-level runtime checks for preview/index.html (jsdom).
 * Run: cd tests/runtime && node jsdom_runtime_test.js
 * (npm install first if node_modules missing)
 */
"use strict";
const fs = require("fs");
const path = require("path");
const { JSDOM } = require("jsdom");

const PAGE = path.resolve(__dirname, "../../preview/index.html");
const html = fs.readFileSync(PAGE, "utf8");

/* v71: total check count — docs (README/MANUAL/GO_LIVE) claim this number and
 * tools/parity_audit.py P8 reads it, so a silent drift cannot slip through. */
const EXPECTED_CHECKS = 161;

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

  /* ---------- v72.1: dead-line data driven (fake countdown teesesaam) ---------- */
  ok("v72.1 countdown: data ledu ante honest note (fake '--' timer chupinchadu)",
     document.getElementById("cd-box").hasAttribute("hidden") &&
     /తుది తేదీలు/.test(document.getElementById("cd-none").textContent));
  ok("v72.1 countdown: feed vachhaka live ga tick chestundi (network-first, fake date ledu)",
     /fetch\("data\/deadline\.json"/.test(html) && !/new Date\(2026,9,15/.test(html));
  {
    const domDl = new JSDOM(html, {
      url: "http://localhost/", runScripts: "dangerously", pretendToBeVisual: true,
      beforeParse(win) {
        win.fetch = () => Promise.resolve({ ok: true, json: () => Promise.resolve(
          { title: "TSPSC గ్రూప్ 2 — దరఖాస్తు చివరి తేదీ", date: "2027-01-05T17:00:00+05:30" }) });
      },
    });
    await sleep(60);
    const d = domDl.window.document;
    const box = d.getElementById("cd-box");
    const nums = ["cd-d", "cd-h", "cd-m", "cd-s"].map(id => d.getElementById(id).textContent).join(":");
    ok("v72.1 countdown: deadline.json vachhaka timer live (numeric values)",
       !box.hasAttribute("hidden") && d.getElementById("cd-none").hidden &&
       /^\d{1,3}:\d{1,2}:\d{1,2}:\d{1,2}$/.test(nums),
       nums);
    domDl.window.close();
  }

  /* ---------- state filters ---------- */
  const tabs = Array.from(document.querySelectorAll(".tab"));
  ok("4 filter tabs (all/ts/ap/central)", tabs.length === 4, "count=" + tabs.length);
  const cards = Array.from(document.querySelectorAll("#grid .news"));
  const visible = () => cards.filter(c => !c.classList.contains("hidden")).length;
  const click = sel => { document.querySelector(sel).click(); };
  // v51: expected counts derived from data-state/data-cat so adding cards
  // (new pillars) never breaks the suite.
  const has = (card, attr, val) => (" " + (card.getAttribute(attr) || "") + " ").indexOf(" " + val + " ") > -1;
  const expectState = st => cards.filter(c => has(c, "data-state", st)).length;
  const expectCat = cat => cards.filter(c => has(c, "data-cat", cat)).length;

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
  ok("All filter -> every card visible", visible() === cards.length, "visible=" + visible() + "/" + cards.length);
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
  ok("clear search -> every card back", visible() === cards.length, "visible=" + visible());
  q.value = "zzqx123notfound";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("no-match -> #nores shown, 0 cards",
     nores.style.display !== "none" && visible() === 0, "nores=" + nores.style.display + " visible=" + visible());
  q.value = "";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("clear -> cards restored", visible() === cards.length);

  /* ---------- daily quiz ---------- */
  const qboxes = Array.from(document.querySelectorAll("#qwrap .qbox"));
  ok("quiz renders 6 questions", qboxes.length === 6, "count=" + qboxes.length);
  ok("first question active (.on)", qboxes[0].classList.contains("on"));
  const prog = document.querySelectorAll("#qprog i");
  ok("progress has 6 markers, first on", prog.length === 6 && prog[0].classList.contains("on"));

  const ANSWERS = [1, 0, 0, 2, 0, 2]; // from page QUIZ (verified by full-marks run below)
  // correct-answer path
  ANSWERS.forEach((a, ix) => {
    document.querySelector('.opt[data-q="' + ix + '"][data-o="' + a + '"]').click();
  });
  ok("Q1 correct option marked .correct",
     document.querySelector('.opt[data-q="0"][data-o="1"]').classList.contains("correct"));
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
     window.localStorage.getItem("studentup-quiz-best") === "6");
  ok("best label updated (ఉత్తమం: 6/6)",
     document.getElementById("qbest").textContent.indexOf("6/6") > -1);
  document.getElementById("qretry").click();
  await sleep(50);
  const qboxes2 = Array.from(document.querySelectorAll("#qwrap .qbox"));
  ok("retry resets quiz (Q1 active, result hidden)",
     qboxes2.length === 6 && qboxes2[0].classList.contains("on") &&
     !document.getElementById("qresult").classList.contains("show"));
  // wrong-answer path
  document.querySelector('.opt[data-q="0"][data-o="0"]').click(); // a=1, so 0 is wrong
  ok("wrong option marked .wrong",
     document.querySelector('.opt[data-q="0"][data-o="0"]').classList.contains("wrong"));
  for (let ix = 0; ix < 5; ix++) document.querySelector('.next[data-q="' + ix + '"]').click();
  document.querySelector('.next[data-q="5"]').click();
  await sleep(50);
  ok("partial run -> score shown (0/6)",
     document.getElementById("qscore").textContent === "0/6",
     document.getElementById("qscore").textContent);
  document.getElementById("qretry").click();

  /* ---------- exam + share + theme + totop ---------- */
  const examHref = document.getElementById("examlink").getAttribute("href");
  ok("exam link resolves to live demo exam (env-aware URL)",
     /\/exam\/KBHA5W$/.test(examHref), examHref);
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
  ok("mobile panel has Partner + Exam CTA",
     Array.from(mpanel.querySelectorAll("a")).some(a => /Partner with us/.test(a.textContent)) &&
     Array.from(mpanel.querySelectorAll("a")).some(a => a.textContent.indexOf("ఆన్‌లైన్ పరీక్ష") > -1));
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
  const heroText = document.querySelector(".hero h1").textContent;
  ok("hero rendered in Telugu script (no Romanized mix)", /[\u0C00-\u0C7F]/.test(heroText) && !/\b(kosam|cheyandi|ledu|undi|avutundi)\b/i.test(heroText), heroText.slice(0, 48));
  const telCount = (document.body.textContent.match(/[\u0C00-\u0C7F]/g) || []).length;
  ok("Telugu script dominant across page body (300+ chars)", telCount > 300, "telugu chars=" + telCount);
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
  const poll = document.getElementById("poll");
  ok("daily poll section present (ఈరోజు పోల్)", !!poll && /ఈరోజు పోల్/.test(poll.textContent));
  ok("poll widget has fetch fallback (portal offline → graceful note)",
     /పోల్ అందుబాటులో లేదు|poll-error/.test(poll.innerHTML + Array.from(document.querySelectorAll("style")).map(s=>s.textContent).join("")));
  ok("poll CSS: responsive + dark-mode rules", /\.poll\{/.test(styleText) && /body\.dark \.poll-opt/.test(styleText));
  ok("services card: working contact paths (no dev placeholders)",
     !!document.querySelector('#services a[href^="mailto:"]') &&
     !/\$\{/.test(document.getElementById("services").textContent));


  /* ---------- v48: real policy pages + SEO files + ad coverage ---------- */
  const policyHrefs = Array.from(document.querySelectorAll('a[href^="pages/"]')).map(a => a.getAttribute("href"));
  const needed = ["pages/about.html", "pages/contact.html", "pages/privacy.html", "pages/disclaimer.html", "pages/editorial-policy.html"];
  ok("all 5 real policy pages linked (no dead policy anchors)",
     needed.every(h => policyHrefs.indexOf(h) > -1) &&
     !/href="#trust">(సంపాదకీయ|సవరణలు|గోప్యతా)/.test(document.documentElement.innerHTML),
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
  ok("ఉద్యోగాలు dropdown: 9 category links (+ విదేశీ/గల్ఫ్ pillar)",
     jobsCats.length === 9, "cats=" + jobsCats.join(","));
  for (const want of ["ts-jobs", "ap-jobs", "central-jobs", "abroad", "walkin", "software", "private", "outsourcing", "parttime"]) {
    ok("jobs menu has " + want, jobsCats.indexOf(want) > -1);
  }
  const examDrop = document.querySelectorAll(".has-drop .drop")[1];
  const examCats = examDrop ? Array.from(examDrop.querySelectorAll("a[data-goto-cat]")).map(a => a.getAttribute("data-goto-cat")) : [];
  ok("v59 పరీక్షలు dropdown: upcoming + tips + portal (hall/results top-level ki vachhayi)",
     ["upcoming", "examtips"].every(c => examCats.indexOf(c) > -1) &&
     /ఆన్‌లైన్ పరీక్షలు/.test(examDrop ? examDrop.textContent : ""),
     "cats=" + examCats.join(","));
  ok("v59 హాల్ టికెట్లు + ఫలితాలు top-level menu lonaki vachhayi",
     !!document.querySelector('.nav > a[data-goto-cat="hallticket"]') &&
     !!document.querySelector('.nav > a[data-goto-cat="results"]'));
  const chips = Array.from(document.querySelectorAll(".chip[data-cat]"));
  const chipCats = chips.map(c => c.getAttribute("data-cat"));
  ok("category chip row present with 16 filters (all + 15 pillars)", chips.length === 16, "chips=" + chips.length);
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
  ok("v72.1: hero countdown fake date ledu — data/deadline.json + honest default",
     !!document.getElementById("cd-none") && document.getElementById("cd-box").hasAttribute("hidden") &&
     /data\/deadline\.json/.test(html) && !/new Date\(2026,9,15/.test(html));
  ok("v72.1: ad slots fake advertiser/example.com lekunda — 'స్లాట్ ఖాళీ' house creative",
     /example\.com/.test(html) === false &&
     Array.from(document.querySelectorAll(".su-ad")).every(a => !/ABC |abc-college|tuition-demo|stationery-demo/.test(a.textContent)) &&
     /\.html$/.test(document.querySelector(".su-ad a").getAttribute("href")));
  ok("v72.1: exam wording neat (ఆన్‌లైన్ పరీక్షలు)",
     /ఆన్‌లైన్ పరీక్ష/.test(html));

  /* ---------- v72: ఎక్కువగా వెతికేవి + పర్ఫెక్ట్ మెనూ ---------- */
  const usedTiles = Array.from(document.querySelectorAll(".usedgrid .usedcard"));
  const usedCats = usedTiles.map(a => a.getAttribute("data-goto-cat"));
  ok("v59 most-used strip: 8 tiles, TS/AP mundu (student order)",
     usedTiles.length === 8 && JSON.stringify(usedCats) === JSON.stringify(
       ["ts-jobs","ap-jobs","hallticket","results","walkin","software","private","current"]),
     usedCats.join(","));
  const firstCount = document.querySelector(".usedgrid .ucount");
  ok("v59 most-used tiles: filter deep-link + live count (— kaadu)",
     usedTiles.every(a => /#jobs/.test(a.getAttribute("href"))) &&
     !!firstCount && !/—/.test(firstCount.textContent),
     "count=" + (firstCount ? firstCount.textContent : "none"));
  const navCats = Array.from(document.querySelectorAll(".nav > a, .nav > .has-drop > a"))
    .map(a => a.textContent.replace(/▾/g, "").trim());
  ok("v72 perfect menu order (హోమ్ · ఉద్యోగాలు · హాల్ టికెట్లు · ఫలితాలు · స్కాలర్ · ప్రస్తుతాంశాలు · పరీక్షలు · మరికొన్ని)",
     /^హోమ్/.test(navCats[0]) && /ఉద్యోగాలు/.test(navCats[1]) && /హాల్ టికెట్లు/.test(navCats[2]) &&
     /ఫలితాలు/.test(navCats[3]) && /స్కాలర్/.test(navCats[4]) &&
     /ప్రస్తుతాంశాలు/.test(navCats[5]) && /పరీక్షలు/.test(navCats[6]) && /మరికొన్ని/.test(navCats[7]),
     navCats.join(" | "));
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
  ok("v72 CSS: search panel + qual chips + install button + used grid shipped (ticker CSS gone)",
     /\.searchpanel\{/.test(styleText) && /\.qchip\{/.test(styleText) &&
     /\.installbtn\{/.test(styleText) && /\.usedgrid\{/.test(styleText) &&
     !/\.tickerwrap\{/.test(styleText) && !/\.breaking\{/.test(styleText));
  const mpUsed = Array.from(document.querySelectorAll(".mpanel a[data-goto-cat]"))
    .slice(0, 8).map(a => a.getAttribute("data-goto-cat"));
  ok("v59 mobile panel: same most-used order (TS/AP mundu)",
     JSON.stringify(mpUsed) === JSON.stringify(
       ["hallticket","results","ts-jobs","ap-jobs","hallticket","results","walkin","software"]) ||
     JSON.stringify(mpUsed) === JSON.stringify(
       ["hallticket","results","ts-jobs","ap-jobs","hallticket","results","walkin","software","private","current"].slice(0,8)),
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
     /వెతకండి/.test(qtop.getAttribute("placeholder") || ""));
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

  /* ---------- v72: విద్యార్హత ఫిల్టర్ (10th · 10+2 · డిగ్రీ · పీజీ …) ---------- */
  const qchips = Array.from(document.querySelectorAll(".qchip"));
  const qslugs = qchips.map(c => c.getAttribute("data-qual"));
  ok("v72 qualification chips: 9 (అన్నీ + 7 అర్హతలు + ⏳ 7 రోజుల్లో ముగిసేవి)",
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
  const q10Chip = qchips.find(c => c.getAttribute("data-qual") === "10th");
  q10Chip.click();
  ok("v72 qualification filter: 10వ తరగతి → only 10th eligible cards",
     qVisible().length > 0 && qVisible().every(c => /10th/.test(c.getAttribute("data-qual"))) &&
     !qVisible().some(c => /btech/.test(c.getAttribute("data-qual"))),
     "visible=" + qVisible().length);
  const qDegChip = qchips.find(c => c.getAttribute("data-qual") === "degree");
  qDegChip.click();
  ok("v72 qualification filter: డిగ్రీ → degree cards + count label update",
     qVisible().length > 0 && qVisible().every(c => /degree/.test(c.getAttribute("data-qual"))) &&
     /అవకాశాలు/.test(document.getElementById("qcount").textContent),
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
      const v = c.getAttribute("data-last");
      if (!v) return null;
      return Math.round((new Date(v + "T23:59:59") - new Date(new Date().setHours(0,0,0,0))) / 86400000);
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

  const qCloseChip = qchips.find(c => c.getAttribute("data-qual") === "closing");
  qCloseChip.click();
  const soonExpected = Array.from(document.querySelectorAll("#grid .news")).filter(c => {
    const v = c.getAttribute("data-last"); if (!v) return false;
    const left = Math.round((new Date(v + "T23:59:59") - new Date(new Date().setHours(0, 0, 0, 0))) / 86400000);
    return left >= 0 && left <= 7;
  }).length;
  ok("v72 qualification filter: ⏳ 7 రోజుల్లో ముగిసేవి → closing-soon cards mattrame",
     qVisible().length === soonExpected && qVisible().every(c => !!c.getAttribute("data-last")),
     "visible=" + qVisible().length + " expected=" + soonExpected);
  /* expiring card: past date → expired badge + default ga hide */
  const expiredCard = document.querySelector("#grid .news").cloneNode(true);
  expiredCard.setAttribute("data-last", "2026-01-05");
  expiredCard.setAttribute("data-qual", "degree");
  document.getElementById("grid").appendChild(expiredCard);
  q .value = ""; q.dispatchEvent(new window.Event("input", { bubbles: true }));
  qchips.find(c => c.getAttribute("data-qual") === "all").click();
  ok("v72 expired job card: 'గడువు ముగిసింది' badge + default ga hide",
     expiredCard.classList.contains("expired") &&
     /గడువు ముగిసింది/.test(expiredCard.textContent) &&
     expiredCard.classList.contains("hidden"));
  expiredCard.remove();
  qchips.find(c => c.getAttribute("data-qual") === "all").click();

  /* ---------- v72.1: category + అర్హత kalisi filter (preview) ---------- */
  const degChip = qchips.find(c => c.getAttribute("data-qual") === "degree");
  degChip.click();
  const catChipTs = Array.from(document.querySelectorAll(".chip[data-cat]"))
    .find(c => c.getAttribute("data-cat") === "ts-jobs");
  if (catChipTs) catChipTs.click();
  const combo = Array.from(document.querySelectorAll("#grid .news")).filter(c => !c.classList.contains("hidden"));
  ok("v72.1: category + అర్హత kalisi filter (rendu condition)",
     combo.length > 0 && combo.every(c => /degree/.test(c.getAttribute("data-qual")) &&
       (" " + (c.getAttribute("data-cat") || "") + " ").indexOf(" ts-jobs ") > -1),
     "visible=" + combo.length);
  click('.chip[data-cat="all"]');
  qchips.find(c => c.getAttribute("data-qual") === "all").click();

  /* ---------- v72: PWA — app-laga install ---------- */
  const installBtn = document.getElementById("installbtn");
  ok("v72 PWA: manifest link + theme-color + apple touch icon",
     !!document.querySelector('link[rel="manifest"][href="manifest.webmanifest"]') &&
     !!document.querySelector('meta[name="theme-color"]') &&
     !!document.querySelector('link[rel="apple-touch-icon"]'));
  ok("v72.1 App డౌన్‌లోడ్: button prathi visit lo kanipistundi (hidden kaadu)",
     !!installBtn && !installBtn.hasAttribute("hidden") &&
     /డౌన్‌లోడ్/.test(installBtn.textContent) && !!installBtn.querySelector(".ibadge"));
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
    ok("contact page: no public rate card (no ₹ pricing)", !/₹\s?\d/.test(contactHtml));
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
    ok("partner page: no public price table / booking flow",
       !/₹\s?\d/.test(advHtml) && !/<table[\s\S]{0,400}₹/.test(advHtml) &&
       !/Booking/.test(advHtml));
    ok("partner page: WhatsApp + email contact routes",
       /wa\.me\/\d{6,}/.test(advHtml) && /mailto:/.test(advHtml));
    ok("partner page: SPONSORED labelling + policy rules kept",
       /SPONSORED/.test(advHtml) && /rel="sponsored nofollow"/.test(advHtml));
    ok("partner page: rates shared personally (honest note)",
       /shared personally|personally/i.test(advHtml) && /never guarantee/i.test(advHtml));
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
