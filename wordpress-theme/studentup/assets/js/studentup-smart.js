/* StudentUp v124 smart layer — AI job match + eligibility, salary calculator,
   state-first homepage. Everything runs locally in the browser. */
(function () {
  var SUICON = function (d, s) { return '<svg viewBox="0 0 24 24" width="' + (s || 14) + '" height="' + (s || 14) + '" fill="currentColor" aria-hidden="true" focusable="false"><path d="' + d + '"/></svg>'; };
  var I = {
    check: SUICON("M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"),
    close: SUICON("M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"),
    bell: SUICON("M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"),
    info: SUICON("M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm1-11h-2V7h2v2z"),
    calendar: SUICON("M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM5 8V6h14v2H5z"),
    wallet: SUICON("M21 7.28V5c0-1.1-.9-2-2-2H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-2.28c.59-.35 1-.98 1-1.72V9c0-.74-.41-1.37-1-1.72zM20 9v6h-7V9h7zM5 19V5h14v2h-6c-1.1 0-2 .9-2 2v6c0 1.1.9 2 2 2h6v2H5z"),
    card: SUICON("M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"),
    speaker: SUICON("M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1-3.29-2.5-4.03v8.05c1.5-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"),
    menu: SUICON("M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"),
    school: SUICON("M12 3 1 9l11 6 9-4.91V17h2V9L12 3zM5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82z")
  };
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
          (v.ok === true ? I.check + " " : v.ok === false ? I.close + " " : I.info + " ") + esc(v.text) + "</span>" : "";
        return '<article class="su-fcard">' +
          (r.img ? '<a class="su-fthumb" href="' + esc(r.link) + '"><img src="' + esc(r.img) + '" alt="" loading="lazy"></a>' : "") +
          '<div class="su-fbody"><h3><a href="' + esc(r.link) + '">' + esc(r.title) + "</a></h3>" +
          '<div class="su-fmeta">' +
            '<span class="su-pill su-pill-amber">' + I.calendar + " " + esc(r.last || "Date in notification") + "</span>" +
            (r.pay ? '<span class="su-pill su-pill-green">' + I.wallet + " " + esc(r.pay) + "</span>" : "") +
            (r.vac ? '<span class="su-pill">' + I.card + " " + esc(r.vac) + " posts</span>" : "") +
            (r.days != null && r.days >= 0 ? '<span class="su-pill' + (r.days <= 3 ? " su-pill-hot" : "") + '">⏳ ' + r.days + "d left</span>" : "") +
          "</div>" + badge +
          '<div class="su-frow"><a class="su-hot-apply" href="' + esc(r.apply || r.link) + '"' + (r.apply ? ' target="_blank" rel="nofollow noopener"' : "") + ">Apply / Details →</a>" +
          '<button type="button" class="su-tool-btn" data-su-compare data-id="' + esc(r.id) + '" data-title="' + esc(r.title) +
          '" data-url="' + esc(r.link) + '" data-cat="" data-date="' + esc(r.last || "") + '" data-apply="' + esc(r.apply || "") +
          '" aria-pressed="false">Compare</button></div></div></article>';
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
