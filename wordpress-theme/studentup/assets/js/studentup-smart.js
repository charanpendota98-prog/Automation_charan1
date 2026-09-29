/* StudentUp v124 smart layer — AI job match + eligibility, salary calculator,
   state-first homepage. Everything runs locally in the browser. */
(function () {
  "use strict";

  var LS_STATE = "su_state_pref";

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  }); }

  /* ------------ AI Job Match + Eligibility ------------ */
  function finder() {
    var form = document.querySelector("[data-su-finder]");
    if (!form) return;
    var rows;
    try { rows = JSON.parse(form.getAttribute("data-su-finder") || "[]"); } catch (e) { return; }
    var out = document.querySelector("[data-su-finder-results]");
    var cnt = document.querySelector("[data-su-finder-count]");
    var qEl = form.querySelector("[data-su-f-qual]");
    var sEl = form.querySelector("[data-su-f-state]");
    var aEl = form.querySelector("[data-su-f-age]");
    var oEl = form.querySelector("[data-su-f-sort]");
    var rEl = form.querySelector("[data-su-f-reset]");

    var pref = localStorage.getItem(LS_STATE);
    if (pref && sEl) sEl.value = pref;

    function ageVerdict(row, age) {
      if (!age) return null;
      if (!row.amin && !row.amax) return { ok: null, text: "Age limit not published — check the notification" };
      var lo = row.amin || 0, hi = row.amax || 99;
      if (age >= lo && age <= hi) return { ok: true, text: "Eligible by age (" + lo + "–" + hi + ")" };
      return { ok: false, text: "Age limit " + lo + "–" + hi + " — not eligible" };
    }

    function render() {
      var q = qEl.value, st = sEl.value, age = parseInt(aEl.value, 10) || 0, sort = oEl.value;
      if (st) localStorage.setItem(LS_STATE, st);
      var list = rows.filter(function (r) {
        if (q && r.qual && r.qual.length && r.qual.indexOf(q) === -1) return false;
        if (st && r.state !== st && !(st !== "central" && r.state === "central")) return false;
        if (age) { var v = ageVerdict(r, age); if (v && v.ok === false) return false; }
        return true;
      });
      list.sort(function (a, b) {
        if (sort === "new") return (b.date || "").localeCompare(a.date || "");
        if (a.last && b.last) return a.last.localeCompare(b.last);
        if (a.last) return -1;
        if (b.last) return 1;
        return (b.date || "").localeCompare(a.date || "");
      });
      if (cnt) cnt.textContent = list.length + " matching update" + (list.length === 1 ? "" : "s");
      if (!list.length) {
        out.innerHTML = '<p class="su-finder-empty">Ee filters ki match ledu — qualification "Any" pettandi leda state marchandi.</p>';
        return;
      }
      out.innerHTML = list.slice(0, 12).map(function (r) {
        var v = ageVerdict(r, age);
        var badge = v ? '<span class="su-elig ' + (v.ok === true ? "yes" : v.ok === false ? "no" : "may") + '">' +
          (v.ok === true ? "✅ " : v.ok === false ? "❌ " : "ℹ️ ") + esc(v.text) + "</span>" : "";
        return '<article class="su-fcard">' +
          (r.img ? '<a class="su-fthumb" href="' + esc(r.link) + '"><img src="' + esc(r.img) + '" alt="" loading="lazy"></a>' : "") +
          '<div class="su-fbody"><h3><a href="' + esc(r.link) + '">' + esc(r.title) + "</a></h3>" +
          '<div class="su-fmeta">' +
            '<span class="su-pill su-pill-amber">📅 ' + esc(r.last || "Date in notification") + "</span>" +
            (r.pay ? '<span class="su-pill su-pill-green">💰 ' + esc(r.pay) + "</span>" : "") +
            (r.vac ? '<span class="su-pill">🧾 ' + esc(r.vac) + " posts</span>" : "") +
            (r.days != null && r.days >= 0 ? '<span class="su-pill' + (r.days <= 3 ? " su-pill-hot" : "") + '">⏳ ' + r.days + "d left</span>" : "") +
          "</div>" + badge +
          '<div class="su-frow"><a class="su-hot-apply" href="' + esc(r.apply || r.link) + '"' + (r.apply ? ' target="_blank" rel="nofollow noopener"' : "") + ">Apply / Details →</a>" +
          '<button type="button" class="su-tool-btn" data-su-compare data-id="' + esc(r.id) + '" data-title="' + esc(r.title) +
          '" data-url="' + esc(r.link) + '" data-cat="" data-date="' + esc(r.last || "") + '" data-apply="' + esc(r.apply || "") +
          '" aria-pressed="false">⚖️ Compare</button></div></div></article>';
      }).join("");
      document.dispatchEvent(new CustomEvent("studentup:compare-refresh"));
    }

    [qEl, sEl, aEl, oEl].forEach(function (el) {
      if (!el) return;
      el.addEventListener("change", render);
      el.addEventListener("input", render);
    });
    if (rEl) rEl.addEventListener("click", function () {
      qEl.value = ""; sEl.value = ""; aEl.value = ""; oEl.value = "last"; render();
    });
    render();
  }

  /* ------------ Salary calculator ------------ */
  function calc() {
    var box = document.querySelector("[data-su-calc-out]");
    if (!box) return;
    var g = function (sel) { var el = document.querySelector(sel); return el ? parseFloat(el.value) || 0 : 0; };
    function run() {
      var basic = g("[data-su-c-basic]"), da = g("[data-su-c-da]"), hra = g("[data-su-c-hra]"),
          ta = g("[data-su-c-ta]"), ded = g("[data-su-c-ded]");
      var daAmt = basic * da / 100, hraAmt = basic * hra / 100;
      var gross = basic + daAmt + hraAmt + ta;
      var net = Math.max(0, gross - ded);
      var f = function (n) { return "₹" + Math.round(n).toLocaleString("en-IN"); };
      box.innerHTML =
        '<div class="su-calc-big"><span>Expected in-hand / month</span><b>' + f(net) + "</b></div>" +
        '<ul class="su-calc-rows">' +
          "<li>Basic pay<b>" + f(basic) + "</b></li>" +
          "<li>DA (" + da + "%)<b>" + f(daAmt) + "</b></li>" +
          "<li>HRA (" + hra + "%)<b>" + f(hraAmt) + "</b></li>" +
          "<li>TA<b>" + f(ta) + "</b></li>" +
          "<li>Gross<b>" + f(gross) + "</b></li>" +
          "<li>Deductions<b>− " + f(ded) + "</b></li>" +
          "<li>Yearly (approx)<b>" + f(net * 12) + "</b></li>" +
        "</ul>" +
        '<p class="su-calc-note">Estimate only — actual figures depend on the pay commission, city class and department deductions.</p>';
    }
    Array.prototype.forEach.call(document.querySelectorAll(".su-calc-form input"), function (i) {
      i.addEventListener("input", run);
    });
    run();
  }

  /* ------------ Dynamic homepage: state first ------------ */
  function stateFirst() {
    var bar = document.querySelector("[data-su-state-bar]");
    var pref = localStorage.getItem(LS_STATE);
    if (!pref) {
      var tz = "";
      try { tz = Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch (e) {}
      pref = /Kolkata|Calcutta/i.test(tz) ? "ts" : "central";
    }
    function apply(v) {
      localStorage.setItem(LS_STATE, v);
      if (bar) Array.prototype.forEach.call(bar.querySelectorAll("button"), function (b) {
        b.classList.toggle("on", b.getAttribute("data-su-state") === v);
      });
      var sel = document.querySelector("[data-su-f-state]");
      if (sel && sel.value !== v) { sel.value = v; sel.dispatchEvent(new Event("change")); }
      /* Category tiles: chosen state top-lo */
      var grid = document.querySelector(".usedgrid");
      if (grid) {
        var want = v === "ap" ? "AP " : v === "ts" ? "TS " : "Central";
        var cards = Array.prototype.slice.call(grid.children);
        cards.sort(function (a, b) {
          var at = (a.textContent || "").indexOf(want) === 0 ? 0 : 1;
          var bt = (b.textContent || "").indexOf(want) === 0 ? 0 : 1;
          return at - bt;
        });
        cards.forEach(function (c) { grid.appendChild(c); });
      }
    }
    if (bar) Array.prototype.forEach.call(bar.querySelectorAll("button"), function (b) {
      b.addEventListener("click", function () { apply(b.getAttribute("data-su-state")); });
    });
    apply(pref);
  }

  function init() { finder(); calc(); stateFirst(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
