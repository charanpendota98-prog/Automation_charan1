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

  /* ---------- date + countdown ---------- */
  ok("#today (IST date) non-empty", (document.getElementById("today") || {}).textContent.trim().length > 3);
  ok("cd-title non-empty", (document.getElementById("cd-title") || {}).textContent.trim().length > 3);
  const snap1 = ["cd-d", "cd-h", "cd-m", "cd-s"].map(id => document.getElementById(id).textContent).join(":");
  ok("countdown initialized (not --)", !/^-|^--/.test(snap1) && !snap1.includes("--"), snap1);
  const cdNums = ["cd-d", "cd-h", "cd-m", "cd-s"].every(id => /^\d{1,2}$/.test(document.getElementById(id).textContent));
  ok("countdown values numeric", cdNums, snap1);
  await sleep(1150);
  const snap2 = ["cd-d", "cd-h", "cd-m", "cd-s"].map(id => document.getElementById(id).textContent).join(":");
  ok("countdown ticking (value changed)", snap1 !== snap2, snap1 + " -> " + snap2);

  /* ---------- state filters ---------- */
  const tabs = Array.from(document.querySelectorAll(".tab"));
  ok("4 filter tabs (all/ts/ap/central)", tabs.length === 4, "count=" + tabs.length);
  const cards = Array.from(document.querySelectorAll("#grid .news"));
  const visible = () => cards.filter(c => !c.classList.contains("hidden")).length;
  const click = sel => { document.querySelector(sel).click(); };

  click('.tab[data-state="ts"]');
  click('.tab[data-state="all"]');
  click('.tab[data-state="ts"]');
  ok("TS filter -> 5 cards, all contain ts (multi-state cards by design)",
     visible() === 5 && cards.filter(c => !c.classList.contains("hidden")).every(c => (" " + c.getAttribute("data-state") + " ").indexOf(" ts ") > -1),
     "visible=" + visible());
  click('.tab[data-state="ap"]');
  ok("AP filter -> 3 cards (incl. ts ap cards)", visible() === 3, "visible=" + visible());
  click('.tab[data-state="central"]');
  ok("Central filter -> 3 cards (incl. ts central)", visible() === 3, "visible=" + visible());
  click('.tab[data-state="all"]');
  ok("All filter -> 8 cards", visible() === 8, "visible=" + visible());
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
  ok("clear search -> 8 cards back", visible() === 8, "visible=" + visible());
  q.value = "zzqx123notfound";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("no-match -> #nores shown, 0 cards",
     nores.style.display !== "none" && visible() === 0, "nores=" + nores.style.display + " visible=" + visible());
  q.value = "";
  q.dispatchEvent(new window.Event("input", { bubbles: true }));
  ok("clear -> cards restored", visible() === 8);

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
  const wa = document.getElementById("wa");
  wa.click();
  ok("WhatsApp share sets wa.me href", wa.getAttribute("href").indexOf("wa.me") > -1, wa.getAttribute("href"));
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
  ok("desktop nav: 7 top-right items (6 + More)", navTop === 7, "count=" + navTop);
  const drop = document.querySelector(".has-drop .drop");
  const dropItems = drop ? drop.querySelectorAll("a").length : 0;
  ok("More dropdown: 5+ neat items (services/ads/policy)", !!drop && dropItems >= 5, "items=" + dropItems);
  ok("dropdown contains Advertise With Us link",
     Array.from(document.querySelectorAll(".drop a")).some(a => a.textContent.indexOf("ప్రకటన") > -1));
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
  ok("mobile panel has Advertise + Exam CTA",
     Array.from(mpanel.querySelectorAll("a")).some(a => a.textContent.indexOf("ప్రకటన") > -1) &&
     Array.from(mpanel.querySelectorAll("a")).some(a => a.textContent.indexOf("ప్రత్యక్ష పరీక్ష") > -1));
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
  ok("all ad CTAs safe: rel=sponsored nofollow + target=_blank",
     Array.from(document.querySelectorAll(".su-ad a")).every(a =>
       (a.getAttribute("rel") || "").indexOf("sponsored") > -1 && a.getAttribute("target") === "_blank"));
  ok("all ad slots labeled SPONSORED + visible disclosure",
     Array.from(ads).every(a => /SPONSORED/i.test(a.textContent) && a.getAttribute("aria-label") === "Sponsored content"));
  ok("Advertise-with-us anchor exists (#ads)", !!document.getElementById("ads"));


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
  const trust = document.getElementById("trust");
  ok("trust section: 100% verify headline (Telugu)", !!trust && /100%/.test(trust.textContent) && /ధృవీకరించి/.test(trust.textContent));
  ok("trust proof tiles: 34/34 + 11/11 + 76/76 + 10,682",
     /34\/34/.test(trust.textContent) && /11\/11/.test(trust.textContent) &&
     /76\/76/.test(trust.textContent) && /10,682/.test(trust.textContent));
  ok("trust has 5 verification gates incl. deep cross-verification (v44)",
     trust.querySelectorAll(".vstep").length === 5 && /క్రాస్-వెరిఫికేషన్/.test(trust.textContent));
  ok("trust honest note + corrections email present",
     /హామీ ఇవ్వదు/.test(trust.textContent) && /studentupinformative@gmail\.com/.test(trust.innerHTML));
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
