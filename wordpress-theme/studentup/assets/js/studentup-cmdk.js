/* StudentUp v127 — command palette (Ctrl/⌘+K) + "Picked for you" rail.
   Local only: reading history never leaves the browser. */
(function () {
  "use strict";

  var HIST = "su_hist_v1";

  function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
  }); }

  function readHist() {
    try { return JSON.parse(localStorage.getItem(HIST) || "[]"); } catch (e) { return []; }
  }

  /* -------- reading history (single posts) -------- */
  function track() {
    var body = document.body;
    if (!body || body.className.indexOf("single-post") === -1) return;
    var t = document.querySelector(".entry-title, .article-head h1, h1.entry-title");
    var img = document.querySelector('meta[property="og:image"]');
    var cat = document.querySelector(".crumbs a:last-of-type, .cat, .catname");
    var item = {
      u: location.href.split("#")[0],
      t: t ? t.textContent.trim().slice(0, 120) : document.title,
      c: cat ? cat.textContent.trim().slice(0, 40) : "",
      i: img ? img.getAttribute("content") : "",
      ts: Date.now()
    };
    var list = readHist().filter(function (x) { return x.u !== item.u; });
    list.unshift(item);
    try { localStorage.setItem(HIST, JSON.stringify(list.slice(0, 12))); } catch (e) {}
  }

  /* -------- Picked for you -------- */
  function forYou() {
    var sec = document.querySelector("[data-su-foryou]");
    if (!sec) return;
    var grid = sec.querySelector("[data-su-foryou-grid]");
    var list = readHist().filter(function (x) { return x.u !== location.href.split("#")[0]; });
    if (list.length < 2) return;
    sec.hidden = false;
    grid.innerHTML = list.slice(0, 6).map(function (x) {
      return '<a class="su-fycard" href="' + esc(x.u) + '">' +
        (x.i ? '<span class="su-fyimg" style="background-image:url(' + esc(x.i) + ')"></span>' : '<span class="su-fyimg su-fyph">📄</span>') +
        '<span class="su-fytext"><b>' + esc(x.t) + "</b>" + (x.c ? "<small>" + esc(x.c) + "</small>" : "") + "</span></a>";
    }).join("");
    var clear = sec.querySelector("[data-su-foryou-clear]");
    if (clear) clear.addEventListener("click", function () {
      try { localStorage.removeItem(HIST); } catch (e) {}
      sec.hidden = true;
    });
  }

  /* -------- Command palette -------- */
  function palette() {
    var root = document.getElementById("su-cmdk");
    if (!root) return;
    var input = document.getElementById("su-cmdk-input");
    var list = document.getElementById("su-cmdk-list");
    var quick = [];
    try { quick = JSON.parse(list.getAttribute("data-su-cmdk-links") || "[]"); } catch (e) {}
    var items = [], idx = 0, timer = null, lastQuery = "";

    function paint() {
      list.innerHTML = items.map(function (it, i) {
        return '<a class="su-cmdk-item' + (i === idx ? " on" : "") + '" role="option" aria-selected="' +
          (i === idx) + '" href="' + esc(it.u) + '"><span class="su-cmdk-i">' + esc(it.i || "🔎") +
          "</span><span>" + esc(it.t) + "</span></a>";
      }).join("") || '<p class="su-cmdk-empty">No matches — press Enter for the full search page.</p>';
    }

    function setQuick() { items = quick.slice(0); idx = 0; paint(); }

    /* v153: static index first.
       One small JSON file is fetched once, kept in localStorage against the
       theme version, and searched locally. That makes typing instant, keeps
       working offline, and stops one REST query per keystroke hitting the
       database. If the index is unavailable we fall back to the REST search. */
    var INDEX_KEY = "su-search-index-v1";
    var indexData = null, indexTried = false;

    function cacheRead() {
      try {
        var raw = JSON.parse(localStorage.getItem(INDEX_KEY) || "null");
        if (raw && raw.v && window.STUDENTUP && raw.v === STUDENTUP.indexVer) { return raw; }
      } catch (e) {}
      return null;
    }

    function loadIndex() {
      if (indexTried || !(window.STUDENTUP && STUDENTUP.indexUrl)) { return; }
      indexTried = true;
      var cached = cacheRead();
      if (cached) { indexData = cached; return; }
      fetch(STUDENTUP.indexUrl, { credentials: "omit" })
        .then(function (r) { return r.ok ? r.json() : null; })
        .then(function (data) {
          if (!data || !data.items) { return; }
          indexData = data;
          try { localStorage.setItem(INDEX_KEY, JSON.stringify(data)); } catch (e) {}
          if (lastQuery) { search(lastQuery); }
        })
        .catch(function () {});
    }

    function localHits(q) {
      if (!indexData || !indexData.items) { return null; }
      var needle = q.toLowerCase(), words = needle.split(/\s+/).filter(Boolean), out = [];
      for (var i = 0; i < indexData.items.length && out.length < 8; i++) {
        var it = indexData.items[i];
        var hay = (it.t + " " + (it.c || "")).toLowerCase();
        var ok = true;
        for (var w = 0; w < words.length; w++) { if (hay.indexOf(words[w]) === -1) { ok = false; break; } }
        if (ok) { out.push({ i: "📄", t: it.t, u: it.u }); }
      }
      return out;
    }

    function search(q) {
      loadIndex();
      var local = localHits(q);
      if (local && local.length) { items = local; idx = 0; paint(); return; }
      if (!(window.STUDENTUP && STUDENTUP.rest)) {
        items = quick.filter(function (k) { return k.t.toLowerCase().indexOf(q.toLowerCase()) > -1; });
        idx = 0; paint();
        return;
      }
      fetch(STUDENTUP.rest + "posts?per_page=6&_fields=title,link&search=" + encodeURIComponent(q), { credentials: "omit" })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (rows) {
          if (q !== lastQuery) return;
          items = (rows || []).map(function (p) {
            return { i: "📄", t: (p.title && p.title.rendered ? p.title.rendered : "").replace(/<[^>]*>/g, ""), u: p.link };
          });
          if (!items.length) items = quick.filter(function (k) { return k.t.toLowerCase().indexOf(q.toLowerCase()) > -1; });
          idx = 0; paint();
        })
        .catch(function () {
          var fb = localHits(q);
          items = (fb && fb.length) ? fb : quick.filter(function (k) { return k.t.toLowerCase().indexOf(q.toLowerCase()) > -1; });
          idx = 0; paint();
        });
    }

    function open() {
      root.hidden = false;
      loadIndex();
      document.body.classList.add("mlock");
      setQuick();
      setTimeout(function () { input.focus(); input.select(); }, 20);
    }
    function close() { root.hidden = true; document.body.classList.remove("mlock"); }

    input.addEventListener("input", function () {
      var q = input.value.trim();
      lastQuery = q;
      clearTimeout(timer);
      if (!q) { setQuick(); return; }
      timer = setTimeout(function () { search(q); }, 180);
    });

    root.addEventListener("click", function (e) { if (e.target === root) close(); });

    document.addEventListener("keydown", function (e) {
      var k = (e.key || "").toLowerCase();
      if ((e.metaKey || e.ctrlKey) && k === "k") { e.preventDefault(); root.hidden ? open() : close(); return; }
      if (root.hidden) return;
      if (k === "escape") { close(); return; }
      if (k === "arrowdown" || k === "arrowup") {
        e.preventDefault();
        if (!items.length) return;
        idx = (idx + (k === "arrowdown" ? 1 : -1) + items.length) % items.length;
        paint();
        var on = list.querySelector(".su-cmdk-item.on");
        if (on && on.scrollIntoView) on.scrollIntoView({ block: "nearest" });
      }
      if (k === "enter") {
        if (items[idx]) { e.preventDefault(); location.href = items[idx].u; }
        else if (input.value.trim()) {
          e.preventDefault();
          location.href = (window.STUDENTUP && STUDENTUP.home ? STUDENTUP.home : "/") + "?s=" + encodeURIComponent(input.value.trim());
        }
      }
    });

    /* header 🔍 long-press / desktop hint */
    var sbtn = document.getElementById("searchbtn");
    if (sbtn) sbtn.setAttribute("title", "Search (Ctrl/⌘ + K)");
  }

  function init() { track(); forYou(); palette(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
