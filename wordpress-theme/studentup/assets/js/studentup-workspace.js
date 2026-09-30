/* StudentUp v172 — COMMAND CENTER (My Workspace).
 *
 * Enti chestundi:
 *   1) Profile (qual · age · state) → localStorage `su_profile_v1`
 *   2) Smart dataset (server-side JSON attr) ni profile tho match chesi
 *      eligible jobs deadline order lo chupistundi (instant, offline)
 *   3) Application pipeline — saved + apply stores tho counts (saved panel sync)
 *   4) Deadline radar — save chesina jobs lo urgent (3/7/14 days) first
 *
 * Rules: vanilla only · no jQuery · no fetch (data embedded) · XSS-safe esc()
 * · storage block aithe soft-empty state (crash ledu).
 */
(function () {
  "use strict";

  var D = window.STUDENTUP_WS || {};
  var I18N = D.i18n || {};
  var PKEY = D.profile || "su_profile_v1";
  var SKEY = D.saved || "studentup_saved_v1";
  var AKEY = D.apply || "studentup_apply_v1";
  var SAVED_ON = !!D.savedOn;

  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function read(key, fallback) {
    try {
      var raw = window.localStorage.getItem(key);
      var val = raw ? JSON.parse(raw) : null;
      return val || fallback;
    } catch (e) { return fallback; }
  }
  function write(key, val) {
    try { window.localStorage.setItem(key, JSON.stringify(val)); return true; }
    catch (e) { return false; }
  }
  function profile() { return read(PKEY, {}); }
  function savedList() {
    var v = read(SKEY, []);
    return Object.prototype.toString.call(v) === "[object Array]" ? v : [];
  }
  function applyMap() {
    var v = read(AKEY, {});
    return (v && typeof v === "object" && !Array.isArray(v)) ? v : {};
  }

  /* ---------- time ---------- */
  function daysLeft(last) {
    if (!last) { return null; }
    var d = new Date(String(last) + "T23:59:59");
    if (isNaN(d.getTime())) { return null; }
    return Math.ceil((d.getTime() - Date.now()) / 86400000);
  }

  /* ---------- matching ---------- */
  function verdict(row, p) {
    /* returns {cls:"yes"|"maybe"|"no", why:string} — profile lekapothe null */
    if (!p.q && !p.a && !p.s) { return null; }
    var why = [], no = false, maybe = false;

    if (p.q) {
      if (row.qual && row.qual.length) {
        if (row.qual.indexOf(p.q) > -1) { why.push(I18N.eligible || "Eligible"); }
        else { no = true; why.push((I18N.qualLabel || "Qualification") + ": " + row.qual.join(", ")); }
      } else {
        maybe = true; why.push((I18N.qualLabel || "Qualification") + " — see notification");
      }
    }
    if (p.s && row.state) {
      if (row.state === p.s || (p.s !== "central" && row.state === "central")) {
        why.push(row.state.toUpperCase());
      } else if (row.state !== "other") {
        no = true; why.push(row.state.toUpperCase());
      }
    }
    if (p.a) {
      var lo = row.amin || 0, hi = row.amax || 0;
      if (lo && hi) {
        if (p.a >= lo && p.a <= hi) { why.push((I18N.ageElig || "Eligible by age") + " (" + lo + "–" + hi + ")"); }
        else { no = true; why.push((I18N.ageNo || "Age limit") + " " + lo + "–" + hi); }
      } else {
        maybe = true;
      }
    }
    return { cls: no ? "no" : (maybe ? "maybe" : "yes"), why: why.join(" · ") };
  }

  function chip(days) {
    if (days === null) { return ""; }
    if (days < 0) { return '<span class="su-ws-chip off">' + esc(I18N.expired || "Closed") + "</span>"; }
    if (days === 0) { return '<span class="su-ws-chip hot">' + esc(I18N.lastDay || "Last day") + "</span>"; }
    var cls = days <= 3 ? " hot" : days <= 7 ? " warm" : " ok";
    return '<span class="su-ws-chip' + cls + '">' + days + " " + esc(I18N.daysLeft || "days left") + "</span>";
  }

  /* ---------- renders ---------- */
  function renderMatches() {
    var host = document.querySelector("[data-su-ws-matches]");
    if (!host) { return; }
    var sec = document.querySelector("[data-su-ws]");
    var rows = [];
    try { rows = JSON.parse(sec.getAttribute("data-su-ws") || "[]"); } catch (e) { rows = []; }
    var p = profile();
    var has = !!(p.q || p.a || p.s);

    var out = [], i, r, v;
    for (i = 0; i < rows.length; i++) {
      r = rows[i];
      v = verdict(r, p);
      if (v && v.cls === "no") { continue; }
      out.push({ row: r, v: v });
    }
    /* deadline urgent first (closed/unknown last), then newest */
    out.sort(function (a, b) {
      var da = daysLeft(a.row.last), db = daysLeft(b.row.last);
      var av = (da === null || da < 0) ? 99999 : da;
      var bv = (db === null || db < 0) ? 99999 : db;
      if (av !== bv) { return av - bv; }
      return (b.row.date || "").localeCompare(a.row.date || "");
    });

    var cnt = document.querySelector("[data-su-ws-mcount]");
    if (cnt) { cnt.textContent = has ? "(" + out.length + ")" : ""; }

    if (!has) {
      host.innerHTML = '<p class="su-ws-empty">' + esc(I18N.noProfile || "Set your qualification above.") + "</p>";
      return;
    }
    if (!out.length) {
      host.innerHTML = '<p class="su-ws-empty">' + esc(I18N.noMatch || "No matching posts yet.") + "</p>";
      return;
    }
    var html = [];
    var top = out.slice(0, 8);
    for (i = 0; i < top.length; i++) {
      r = top[i].row;
      v = top[i].v;
      var meta = [];
      if (r.pay) { meta.push(esc(I18N.pay || "Pay") + ": " + esc(r.pay)); }
      if (r.vac) { meta.push(esc(I18N.vac || "Posts") + ": " + esc(r.vac)); }
      html.push(
        '<div class="su-ws-job">' +
          '<div class="su-ws-job-main">' +
            '<a class="su-ws-job-t" href="' + esc(r.link) + '">' + esc(r.title) + "</a>" +
            '<div class="su-ws-job-meta">' +
              (meta.length ? "<span>" + meta.join("</span><span>") + "</span>" : "") +
              (r.last ? "<span>" + esc(I18N.deadline || "Deadline") + ": " + esc(r.last) + "</span>" : "") +
            "</div>" +
            (v && v.why ? '<div class="su-ws-elig ' + v.cls + '">' + esc(v.why) + "</div>" : "") +
          "</div>" +
          '<div class="su-ws-job-side">' + chip(daysLeft(r.last)) +
            (SAVED_ON ? '<button type="button" class="su-save-btn su-ws-save" data-su-save data-id="' + esc(r.id) +
              '" data-title="' + esc(r.title) + '" data-url="' + esc(r.link) + '" aria-pressed="false" aria-label="' +
              esc(I18N.save || "Save") + '"><span class="su-save-ico" aria-hidden="true">+</span><span class="su-save-txt">' +
              esc(I18N.save || "Save") + "</span></button>" : "") +
          "</div>" +
        "</div>"
      );
    }
    host.innerHTML = html.join("");
  }

  function renderPipe() {
    var host = document.querySelector("[data-su-ws-pipe]");
    if (!host) { return; }
    var list = savedList(), am = applyMap(), i, st;
    var counts = { saved: 0, applied: 0, interview: 0, result: 0 }, rows = [];
    for (i = 0; i < list.length; i++) {
      st = am[String(list[i].id)] || "";
      if (st === "applied") { counts.applied++; }
      else if (st === "interview") { counts.interview++; }
      else if (st === "result") { counts.result++; }
      else { counts.saved++; }
      rows.push({ t: list[i].title, u: list[i].url, st: st });
    }
    rows.reverse(); /* newest save first */

    var tiles = [
      ["saved", I18N.pipeSaved || "Saved"],
      ["applied", I18N.pipeApplied || "Applied"],
      ["interview", I18N.pipeInter || "Interview"],
      ["result", I18N.pipeResult || "Result"],
    ];
    var html = ['<div class="su-ws-tiles-row">'];
    for (i = 0; i < tiles.length; i++) {
      html.push('<div class="su-ws-tile t-' + tiles[i][0] + '"><b>' + counts[tiles[i][0]] + "</b><span>" + esc(tiles[i][1]) + "</span></div>");
    }
    html.push("</div>");
    if (!rows.length) {
      html.push('<p class="su-ws-empty">' + esc(I18N.pipeEmpty || "Save jobs from any card.") + "</p>");
    } else {
      html.push('<div class="su-ws-pipe-list">');
      var shown = rows.slice(0, 6);
      for (i = 0; i < shown.length; i++) {
        var label = shown[i].st ?
          (tiles.filter(function (t) { return t[0] === shown[i].st; })[0] || ["", ""])[1] :
          (I18N.pipeSaved || "Saved");
        html.push('<div class="su-ws-pipe-item"><a href="' + esc(shown[i].u) + '">' + esc(shown[i].t) + "</a>" +
          '<span class="su-status' + (shown[i].st ? " su-status-" + shown[i].st : "") + '">' + esc(label) + "</span></div>");
      }
      html.push("</div>");
    }
    host.innerHTML = html.join("");
  }

  function renderRadar() {
    var host = document.querySelector("[data-su-ws-radar]");
    if (!host) { return; }
    var list = savedList(), i, d;
    var items = [];
    for (i = 0; i < list.length; i++) {
      d = daysLeft(list[i].date);
      if (d !== null && d >= 0) { items.push({ row: list[i], d: d }); }
    }
    items.sort(function (a, b) { return a.d - b.d; });
    if (!items.length) {
      host.innerHTML = '<p class="su-ws-empty">' + esc(I18N.radarEmpty || "Saved jobs with deadlines will show up here.") + "</p>";
      return;
    }
    var html = [];
    var top = items.slice(0, 6);
    for (i = 0; i < top.length; i++) {
      var cls = top[i].d <= 3 ? "hot" : top[i].d <= 7 ? "warm" : "ok";
      var label = top[i].d <= 3 ? (I18N.radarUrgent || "Closing in 3 days")
        : top[i].d <= 7 ? (I18N.radarSoon || "Closing this week")
        : (I18N.radarOk || "Closing soon");
      html.push('<div class="su-ws-radar-item ' + cls + '">' +
        '<a href="' + esc(top[i].row.url) + '">' + esc(top[i].row.title) + "</a>" +
        '<span class="su-ws-chip ' + cls + '">' + (top[i].d === 0 ? esc(I18N.lastDay || "Last day") : top[i].d + " " + esc(I18N.daysLeft || "days left")) + "</span>" +
        '<small>' + esc(label) + " · " + esc(I18N.deadline || "Deadline") + ": " + esc(top[i].row.date) + "</small>" +
        "</div>");
    }
    host.innerHTML = html.join("");
  }

  function renderAll() { renderMatches(); renderPipe(); renderRadar(); }

  /* ---------- profile form ---------- */
  function wireForm() {
    var form = document.querySelector("[data-su-ws-form]");
    if (!form) { return; }
    var q = form.querySelector("[data-su-ws-qual]");
    var a = form.querySelector("[data-su-ws-age]");
    var s = form.querySelector("[data-su-ws-state]");
    var p = profile();
    if (q && p.q) { q.value = p.q; }
    if (a && p.a) { a.value = p.a; }
    if (s && p.s) { s.value = p.s; }
    function save() {
      var next = { q: q ? q.value : "", a: a ? (parseInt(a.value, 10) || 0) : 0, s: s ? s.value : "" };
      write(PKEY, next);
      renderAll();
    }
    if (q) { q.addEventListener("change", save); }
    if (a) { a.addEventListener("input", save); }
    if (s) { s.addEventListener("change", save); }
  }

  function init() {
    wireForm();
    renderAll();
    /* cross-tab + back-forward sync (saved panel lo save chesthe idi update avvali) */
    window.addEventListener("storage", function (e) {
      if (!e.key || e.key === SKEY || e.key === AKEY || e.key === PKEY) { renderAll(); }
    });
    window.addEventListener("pageshow", renderAll);
    /* save/un-save workspace list lo kuda reflect avvali (same-page click) */
    document.addEventListener("click", function (e) {
      if (e.target && e.target.closest && e.target.closest("[data-su-save]")) {
        setTimeout(renderAll, 60);   /* saved.js modalu store update chestundi — tarvata repaint */
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
