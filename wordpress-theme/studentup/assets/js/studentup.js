/* StudentUp theme JS (v64) — dark mode, mobile menu, chips filter, countdown,
 * reading progress, copy link, sticky ad close, TOC smooth scroll.
 * No external JS library. Vanilla, tiny, mobile-first.
 */
(function () {
  "use strict";
  var S = window.STUDENTUP || {};

  /* ---------- dark mode ---------- */
  var themeBtn = document.getElementById("theme");
  function applyTheme(dark) {
    document.body.classList.toggle("dark", dark);
    if (themeBtn) {
      themeBtn.textContent = dark ? "☀" : "☾";
      themeBtn.setAttribute("aria-pressed", dark ? "true" : "false");
    }
  }
  var saved = null;
  try { saved = localStorage.getItem("su_theme"); } catch (e) { saved = null; }
  if (saved === "dark" || (!saved && window.matchMedia &&
      window.matchMedia("(prefers-color-scheme: dark)").matches)) {
    applyTheme(true);
  }
  if (themeBtn) {
    themeBtn.addEventListener("click", function () {
      var dark = !document.body.classList.contains("dark");
      applyTheme(dark);
      try { localStorage.setItem("su_theme", dark ? "dark" : "light"); } catch (e) {}
    });
  }

  /* ---------- mobile panel ---------- */
  var menuBtn = document.getElementById("menubtn");
  var panel = document.getElementById("mpanel");
  var backdrop = document.getElementById("mbackdrop");
  function setMenu(open) {
    if (!panel) return;
    panel.classList.toggle("open", open);
    if (backdrop) backdrop.classList.toggle("show", open);
    document.body.classList.toggle("mlock", open);
    if (menuBtn) menuBtn.setAttribute("aria-expanded", open ? "true" : "false");
  }
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      setMenu(!panel.classList.contains("open"));
    });
  }
  if (backdrop) backdrop.addEventListener("click", function () { setMenu(false); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") setMenu(false);
  });
  if (panel) {
    panel.addEventListener("click", function (e) {
      if (e.target && e.target.tagName === "A") setMenu(false);
    });
  }

  /* ---------- chips filter (front page grid) + v76 qualification dropdown ---------- */
  var grid = document.getElementById("grid");
  var chips = document.querySelectorAll(".chip[data-cat]");
  var qualsel = document.getElementById("qualsel");
  var nores = document.getElementById("nores");
  var activeCat = "all";
  var activeQual = "all";
  /* v76: server-rendered ?qual= state tho JS sync (select value = truth) */
  if (qualsel && qualsel.value && qualsel.value !== "all") activeQual = qualsel.value;
  var today = new Date();
  today.setHours(0, 0, 0, 0);

  function daysLeft(card) {
    var v = card.getAttribute("data-last");
    if (!v) return null;
    var d = new Date(v + "T23:59:59");
    if (isNaN(d)) return null;
    return Math.round((d - today) / 86400000);
  }
  function decorate(card) {                    /* ⏳/expired badge (server-side kuda undi) */
    var left = daysLeft(card);
    if (left === null) return;
    var foot = card.querySelector(".newsfoot");
    if (left < 0) card.classList.add("expired");
    if (!foot) return;
    var old = foot.querySelector(".qbadge");
    if (old) old.remove();
    var b = document.createElement("span");
    if (left < 0) { b.className = "qbadge done"; b.textContent = "Deadline passed"; }
    else if (left <= 7) { b.className = "qbadge soon"; b.textContent = (left === 0 ? "Last day today" : left + " days left"); }
    else { return; }
    foot.appendChild(b);
  }
  function applyFilter() {
    if (!grid) return;
    var shown = 0, hiddenExpired = 0;
    Array.prototype.forEach.call(grid.querySelectorAll(".news"), function (card) {
      decorate(card);
      var qua = (card.getAttribute("data-qual") || "").toLowerCase();
      var left = daysLeft(card);
      var expired = left !== null && left < 0;
      var okCat = activeCat === "all" ||
        (" " + (card.getAttribute("data-cat") || "") + " ").indexOf(" " + activeCat + " ") > -1;
      var okQual = true;
      if (activeQual === "closing") okQual = left !== null && left >= 0 && left <= 7;
      else if (activeQual !== "all") okQual = qua.indexOf(activeQual) > -1;
      if (activeQual !== "expired" && expired) { okQual = false; hiddenExpired++; }
      var ok = okCat && okQual;
      card.classList.toggle("hidden", !ok);
      if (ok) shown++;
    });
    if (nores) nores.style.display = shown ? "none" : "block";
    var note = document.getElementById("su-hidden-note");
    if (note) {
      if (hiddenExpired) {
        note.hidden = false;
        note.textContent = hiddenExpired + " expired post" + (hiddenExpired > 1 ? "s" : "") + " hidden.";
      } else { note.hidden = true; }
    }
  }
  Array.prototype.forEach.call(chips, function (chip) {
    chip.addEventListener("click", function () {
      Array.prototype.forEach.call(chips, function (c) {
        c.classList.remove("active");
        c.setAttribute("aria-selected", "false");
      });
      chip.classList.add("active");
      chip.setAttribute("aria-selected", "true");
      activeCat = chip.getAttribute("data-cat") || "all";
      applyFilter();
    });
  });
  /* v76: qualification dropdown — with JS the filter combines with category without reloading
   * (form GET server-side/SEO + no-JS kosam alage untundi; JS unna browser lo URL history update). */
  if (qualsel) {
    qualsel.addEventListener("change", function () {
      var slug = qualsel.value || "all";
      activeQual = slug;
      try {                                   /* shareable URL — server-side tho same */
        var url = new URL(location.href);
        if (slug === "all") url.searchParams.delete("qual");
        else url.searchParams.set("qual", slug);
        history.replaceState({}, "", url.toString());
      } catch (err) {}
      applyFilter();
      if (grid && grid.scrollIntoView) grid.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }
  /* hash deep-link (#cat-ts-jobs) */
  (function () {
    var m = (location.hash || "").match(/^#cat-([a-z0-9-]+)$/);
    if (!m || !grid) return;
    Array.prototype.forEach.call(chips, function (c) {
      if (c.getAttribute("data-cat") === m[1]) c.click();
    });
  })();
  /* ---------- v72.1: sections by qualification (grid nunchi automatic build) ---------- */
  var QUAL_LABELS = { "10th": "SSC · 10th", "inter": "Inter (10+2)", "iti": "ITI",
                      "diploma": "Diploma", "degree": "Degree", "pg": "PG", "btech": "B.Tech" };
  function buildQualSections() {
    var host = document.getElementById("qsplit");
    if (!host || !grid) return;
    var groups = host.querySelectorAll("[data-qgroup]");
    var all = Array.prototype.slice.call(grid.querySelectorAll(".news"));
    Array.prototype.forEach.call(groups, function (g) {
      var key = g.getAttribute("data-qgroup");
      var items = [];
      all.forEach(function (card) {
        var qua = (card.getAttribute("data-qual") || "").toLowerCase();
        var left = daysLeft(card);
        var ok = key === "closing"
          ? (left !== null && left >= 0 && left <= 7)
          : (qua.indexOf(key) > -1 && !(left !== null && left < 0));
        if (ok) items.push(card);
      });
      if (!items.length) { g.hidden = true; g.innerHTML = ""; return; }
      var h = document.createElement("h3");
      h.innerHTML = (key === "closing" ? "⏳ Closing in 7 days" : (QUAL_LABELS[key] || key)) +
        ' <span class="qgnum">' + items.length + "</span>";
      var sub = document.createElement("p");
      sub.className = "qgsub";
      sub.textContent = key === "closing" ? "Deadline is close — check now" : "Anyone with this qualification can apply";
      var ul = document.createElement("ul");
      items.slice(0, 6).forEach(function (card) {
        var a = card.querySelector("h3 a") || card.querySelector("a");
        if (!a) return;
        var left = daysLeft(card);
        var meta = (left !== null && left >= 0 && left <= 7)
          ? (left === 0 ? "Last day today" : left + " days left") : "";
        var li = document.createElement("li");
        var link = document.createElement("a");
        link.href = a.getAttribute("href") || a.href;
        link.textContent = a.textContent.trim();
        li.appendChild(link);
        if (meta) {
          var span = document.createElement("span");
          span.className = "qgmeta";
          span.textContent = meta;
          li.appendChild(span);
        }
        ul.appendChild(li);
      });
      g.innerHTML = "";
      g.appendChild(h);
      g.appendChild(sub);
      g.appendChild(ul);
      g.hidden = false;
    });
  }
  buildQualSections();
  applyFilter();                              /* modati load lo expired hide + badges */

  /* ---------- deadline countdown ---------- */

  /* ---------- v64: reading progress bar ---------- */
  var bar = document.getElementById("su-progress-bar");
  var article = document.querySelector(".article-content");
  if (bar && article) {
    var onScroll = function () {
      var top = article.getBoundingClientRect().top + window.pageYOffset;
      var total = article.offsetHeight - window.innerHeight;
      var pct = total > 0 ? ((window.pageYOffset - top) / total) * 100 : 0;
      bar.style.width = Math.max(0, Math.min(100, pct)) + "%";
    };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    onScroll();
  }

  /* ---------- v64: copy link button ---------- */
  Array.prototype.forEach.call(document.querySelectorAll(".su-copy"), function (btn) {
    btn.addEventListener("click", function () {
      var url = btn.getAttribute("data-url") || window.location.href;
      var done = function () {
        var t = btn.textContent;
        btn.textContent = "✅ Copied";
        setTimeout(function () { btn.textContent = t; }, 1600);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(url).then(done, done);
      } else {
        var ta = document.createElement("textarea");
        ta.value = url; document.body.appendChild(ta); ta.select();
        try { document.execCommand("copy"); } catch (e) {}
        document.body.removeChild(ta); done();
      }
    });
  });

  /* ---------- v64: sticky ad close ---------- */
  var sticky = document.getElementById("su-stickyad");
  if (sticky) {
    var hide = function () { sticky.style.display = "none"; };
    try { if (localStorage.getItem("su_sticky_off") === "1") hide(); } catch (e) {}
    var close = sticky.querySelector(".su-sticky-close");
    if (close) {
      close.addEventListener("click", function () {
        hide();
        try { localStorage.setItem("su_sticky_off", "1"); } catch (e) {}
      });
    }
  }

  /* ---------- v64: TOC smooth scroll ---------- */
  Array.prototype.forEach.call(document.querySelectorAll(".su-toc a"), function (a) {
    a.addEventListener("click", function (ev) {
      var id = (a.getAttribute("href") || "").replace("#", "");
      var target = id && document.getElementById(id);
      if (target) {
        ev.preventDefault();
        target.scrollIntoView({ behavior: "smooth", block: "start" });
        if (history.replaceState) history.replaceState(null, "", "#" + id);
      }
    });
  });

  /* ---------- most-used live counts (site side, WP-print chesina numbers ki fallback) ---------- */
  Array.prototype.forEach.call(document.querySelectorAll(".ucount"), function (el) {
    if (el.textContent.indexOf("update") === -1 && el.textContent.indexOf("Soon") === -1) {
      el.textContent = S.i18n && S.i18n.updates ? "—" : el.textContent;
    }
  });

  /* ---------- v71: floating social rail — show, auto-hide, return every 2 minutes ----------
     Eppudu kanipisthe mobile lo article chadavadam kastam — anduku 9s chupi, pakkaki
     velli, prati 2 nimishalaki malli vastundi. Close = ventane hide, 2 min tarvata malli. */
  var rail = document.getElementById("surail"), railTab = document.getElementById("sutab"),
      railClose = document.getElementById("suclose");
  if (rail && railTab) {
    var SU_SHOW = 9000, SU_CYCLE = 120000, SU_HOVER = 3500, suHideT = null, suCycleT = null;
    var suShow = function () {
      clearTimeout(suHideT);
      rail.classList.remove("su-out");
      rail.removeAttribute("aria-hidden");
      railTab.classList.remove("on");
      suHideT = setTimeout(suHide, SU_SHOW);
    };
    var suHide = function () {
      clearTimeout(suHideT);
      rail.classList.add("su-out");
      rail.setAttribute("aria-hidden", "true");
      railTab.classList.add("on");
    };
    var suRestart = function () {
      clearInterval(suCycleT);
      suCycleT = setInterval(function () {
        if (document.body.classList.contains("mlock")) return;  /* menu open — wait */
        suShow();
      }, SU_CYCLE);
    };
    if (railClose) {
      railClose.addEventListener("click", function () { suHide(); suRestart(); });
    }
    railTab.addEventListener("click", function () { suShow(); suRestart(); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") suHide(); });
    rail.addEventListener("mouseenter", function () { clearTimeout(suHideT); });
    rail.addEventListener("mouseleave", function () { clearTimeout(suHideT); suHideT = setTimeout(suHide, SU_HOVER); });
    rail.addEventListener("focusin", function () { clearTimeout(suHideT); });
    rail.addEventListener("focusout", function () { clearTimeout(suHideT); suHideT = setTimeout(suHide, SU_HOVER); });
    suShow();
    suRestart();
  }


  /* ---------- v72: header search (menu pakkana 🔍) — elements ---------- */
  var sbtn = document.getElementById("searchbtn");
  var spanel = document.getElementById("searchpanel");
  var sinput = document.getElementById("qtop");
  var sclose = document.getElementById("searchclose");

  /* ---------- v89: animated custom qualification dropdown (quadd) ----------
     Native <select> = source of truth (SEO/no-JS form form GET alage pani chestundi).
     JS browser lo quadd UI: icon + label + count, animate-open panel, keyboard safe. */
  (function () {
    if (!qualsel) return;
    var form = qualsel.closest ? qualsel.closest("form.qualform") : null;
    if (!form) return;
    var icons = {};
    try { icons = JSON.parse(form.getAttribute("data-icons") || "{}"); } catch (e) { icons = {}; }
    function parseCount(t) {
      var m = t.match(/\((\d+)\)\s*$/);
      return m ? m[1] : "";
    }
    function clean(t) { return t.replace(/\s*\(\d+\)\s*$/, "").trim(); }

    var wrap = document.createElement("div");
    wrap.className = "quadd";
    var btn = document.createElement("button");
    btn.type = "button";
    btn.className = "quadd-btn";
    btn.setAttribute("aria-haspopup", "listbox");
    btn.setAttribute("aria-expanded", "false");
    var panel = document.createElement("div");
    panel.className = "quadd-panel";
    panel.setAttribute("role", "listbox");
    panel.setAttribute("aria-label", "Qualification");
    panel.hidden = true;

    var optData = [];
    Array.prototype.forEach.call(qualsel.options, function (o, idx) {
      var slug = o.value || "all";
      var it = document.createElement("button");
      it.type = "button";
      it.className = "quadd-item";
      it.setAttribute("role", "option");
      it.setAttribute("data-slug", slug);
      it.setAttribute("aria-selected", o.selected ? "true" : "false");
      var ic = icons[slug] || "▸";
      it.innerHTML = '<span class="qi" aria-hidden="true">' + ic + "</span>" +
        '<span class="qt">' + clean(o.textContent) + "</span>" +
        (parseCount(o.textContent) ? '<span class="qn">' + parseCount(o.textContent) + "</span>" : "");
      it.addEventListener("click", function () {
        setValue(slug);
        closePanel();
        btn.focus();
      });
      panel.appendChild(it);
      optData.push({ slug: slug, el: it, index: idx });
    });

    function labelFor(slug) {
      for (var i = 0; i < optData.length; i++) if (optData[i].slug === slug) return i;
      return 0;
    }
    function renderBtn() {
      var i = labelFor(qualsel.value || "all");
      var o = qualsel.options[i];
      var slug = o.value || "all";
      btn.innerHTML = '<span class="qi" aria-hidden="true">' + (icons[slug] || "🎓") + "</span>" +
        '<span class="qt">' + clean(o.textContent) + "</span>" +
        '<span class="qchev" aria-hidden="true"></span>';
      Array.prototype.forEach.call(optData, function (d) {
        d.el.setAttribute("aria-selected", d.slug === slug ? "true" : "false");
      });
    }
    function setValue(slug) {
      if (qualsel.value !== slug) {
        qualsel.value = slug;
        var evt;
        try { evt = new Event("change", { bubbles: true }); }
        catch (e) { evt = document.createEvent("Event"); evt.initEvent("change", true, true); }
        qualsel.dispatchEvent(evt);          /* existing change handler = filter + URL sync */
      }
      renderBtn();
    }
    function openPanel() {
      panel.hidden = false;
      requestAnimationFrame(function () { wrap.classList.add("open"); });
      btn.setAttribute("aria-expanded", "true");
      var cur = labelFor(qualsel.value || "all");
      if (optData[cur]) optData[cur].el.classList.add("focus");
    }
    function closePanel() {
      wrap.classList.remove("open");
      btn.setAttribute("aria-expanded", "false");
      setTimeout(function () { panel.hidden = true; }, 160);
      Array.prototype.forEach.call(optData, function (d) { d.el.classList.remove("focus"); });
    }
    btn.addEventListener("click", function () {
      if (wrap.classList.contains("open")) closePanel(); else openPanel();
    });
    document.addEventListener("click", function (e) {
      if (!wrap.contains(e.target) && wrap.classList.contains("open")) closePanel();
    });
    wrap.addEventListener("keydown", function (e) {
      if (!wrap.classList.contains("open")) {
        if (e.key === "ArrowDown" || e.key === "Enter" || e.key === " ") {
          e.preventDefault(); openPanel();
        }
        return;
      }
      var cur = labelFor(qualsel.value || "all");
      if (e.key === "Escape") { e.preventDefault(); closePanel(); btn.focus(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); focus(Math.min(cur + 1, optData.length - 1)); }
      else if (e.key === "ArrowUp") { e.preventDefault(); focus(Math.max(cur - 1, 0)); }
      else if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setValue(optData[cur].slug); closePanel(); btn.focus(); }
    });
    function focus(i) {
      Array.prototype.forEach.call(optData, function (d) { d.el.classList.remove("focus"); });
      optData[i].el.classList.add("focus");
      optData[i].el.scrollIntoView({ block: "nearest" });
      /* visual-only cursor; selection Enter/click tho */
      var slug = optData[i].slug;
      Array.prototype.forEach.call(optData, function (d) {
        d.el.setAttribute("aria-selected", d.slug === slug ? "true" : "false");
      });
    }
    /* server ?qual= state tho sync — page load */
    renderBtn();
    qualsel.addEventListener("change", renderBtn);
    qualsel.classList.add("quadd-src");
    qualsel.setAttribute("aria-hidden", "true");
    qualsel.tabIndex = -1;
    wrap.appendChild(btn);
    wrap.appendChild(panel);
    qualsel.parentNode.insertBefore(wrap, qualsel);
  })();

  /* ---------- v89: LIVE search — type chestuntene results dropdown ----------
     WP REST /wp/v2/search (public). Debounced fetch, abort on new key,
     keyboard ↑↓ Enter Esc, click → aa post open avutundi. */
  (function () {
    var box = document.getElementById("su-sres");
    if (!sinput || !box) return;
    var rest = (S && S.rest) ? S.rest : "/wp-json/wp/v2/";
    var tmr = null, ctrl = null, items = [], cursor = -1;
    var combo = sinput.closest ? sinput.closest(".su-livesearch") : null;

    function esc(t) { var d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
    function close() {
      box.hidden = true; box.innerHTML = ""; items = []; cursor = -1;
      if (combo) combo.setAttribute("aria-expanded", "false");
      sinput.removeAttribute("aria-activedescendant");
    }
    function paint() {
      Array.prototype.forEach.call(box.querySelectorAll(".su-srow"), function (row, i) {
        row.classList.toggle("active", i === cursor);
        row.setAttribute("aria-selected", i === cursor ? "true" : "false");
      });
      if (cursor >= 0 && items[cursor]) {
        sinput.setAttribute("aria-activedescendant", "su-srow-" + cursor);
        var el = document.getElementById("su-srow-" + cursor);
        if (el && el.scrollIntoView) el.scrollIntoView({ block: "nearest" });
      }
    }
    function render(list, q) {
      items = list; cursor = -1;
      var html = "";
      if (!list.length) {
        html = '<div class="su-sempty" role="option" aria-disabled="true">' +
          esc((S.i18n && S.i18n.noresults) || "No posts found") + "</div>";
      } else {
        list.forEach(function (r, i) {
          html += '<a class="su-srow" id="su-srow-' + i + '" role="option" aria-selected="false" href="' +
            esc(r.url) + '"><span class="su-stitle">' + esc(r.title) + "</span>" +
            '<span class="su-stype">' + esc(r.type === "post" ? "Post" : r.type) + "</span></a>";
        });
        html += '<a class="su-srow su-sall" role="option" aria-selected="false" href="' +
          esc((S.home || "/") + "?s=" + encodeURIComponent(q)) + '">' +
          esc((S.i18n && S.i18n.viewall) || "See all results") + " →</a>";
      }
      box.innerHTML = html;
      box.hidden = false;
      if (combo) combo.setAttribute("aria-expanded", "true");
    }
    function run(q) {
      if (ctrl) ctrl.abort();
      ctrl = ("AbortController" in window) ? new AbortController() : null;
      box.innerHTML = '<div class="su-sloading">' + esc((S.i18n && S.i18n.searching) || "Searching…") + "</div>";
      box.hidden = false;
      var url = rest + "search?search=" + encodeURIComponent(q) + "&per_page=7&type=post&_fields=id,title,url,type";
      fetch(url, ctrl ? { signal: ctrl.signal } : {})
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (rows) {
          if ((sinput.value || "").trim() !== q) return;   /* newer query already running */
          var list = (rows || []).map(function (r) {
            return { title: (r.title || "").replace(/<[^>]*>/g, ""), url: r.url || "#", type: r.type || "post" };
          }).filter(function (r) { return r.title && r.url !== "#"; });
          render(list, q);
        })
        .catch(function (e) {
          if (e && e.name === "AbortError") return;
          box.hidden = true;
        });
    }
    sinput.addEventListener("input", function () {
      var q = (sinput.value || "").trim();
      clearTimeout(tmr);
      if (q.length < 2) { if (ctrl) ctrl.abort(); close(); return; }
      tmr = setTimeout(function () { run(q); }, 220);
    });
    sinput.addEventListener("keydown", function (e) {
      if (box.hidden) return;
      var rowsCount = box.querySelectorAll(".su-srow").length;
      if (e.key === "Escape") { e.preventDefault(); close(); }
      else if (e.key === "ArrowDown") { e.preventDefault(); cursor = Math.min(cursor + 1, rowsCount - 1); paint(); }
      else if (e.key === "ArrowUp") { e.preventDefault(); cursor = Math.max(cursor - 1, -1); paint(); }
      else if (e.key === "Enter" && cursor >= 0) {
        e.preventDefault();
        var row = box.querySelectorAll(".su-srow")[cursor];
        if (row) window.location.href = row.getAttribute("href");
      }
    });
    document.addEventListener("click", function (e) {
      if (!box.hidden && !box.contains(e.target) && e.target !== sinput) close();
    });
  })();


  function searchOpen(on) {
    if (!spanel || !sbtn) return;
    spanel.hidden = !on;
    sbtn.setAttribute("aria-expanded", on ? "true" : "false");
    if (on && sinput) setTimeout(function () { sinput.focus(); }, 30);
  }
  if (sbtn && spanel) {
    sbtn.addEventListener("click", function () { searchOpen(spanel.hidden); });
    if (sclose) sclose.addEventListener("click", function () { searchOpen(false); });
    document.addEventListener("keydown", function (e) {
      var tag = (e.target && e.target.tagName) || "";
      if (e.key === "/" && tag !== "INPUT" && tag !== "TEXTAREA" && tag !== "SELECT") {
        e.preventDefault(); searchOpen(true);
      }
      if (e.key === "Escape" && !spanel.hidden) searchOpen(false);
    });
  }

  /* ---------- v80 (P25): outbound + apply-link click tracking (GA4 gated) ---------- */
  document.addEventListener("click", function (e) {
    if (typeof window.gtag !== "function") return;  /* GA4 ledu → track cheyyamu */
    var a = e.target && e.target.closest ? e.target.closest("a[href]") : null;
    if (!a) return;
    var href = a.getAttribute("href") || "";
    if (!/^https?:\/\//i.test(href)) return;
    var same = false;
    try { same = new URL(href, location.href).host === location.host; } catch (err) { return; }
    if (same) return;
    var isApply = /apply|application|register|registration|form/i.test(href) ||
      /apply|register/i.test(a.textContent || "");
    window.gtag("event", isApply ? "apply_click" : "outbound_click", {
      event_category: "engagement",
      event_label: href.slice(0, 200)
    });
  });

  /* ---------- v81 (§37): site-search tracking (GA4 gated) ---------- */
  document.addEventListener("submit", function (e) {
    if (typeof window.gtag !== "function") return;
    var f = e.target && e.target.tagName === "FORM" ? e.target : null;
    if (!f) return;
    var q = f.querySelector('input[name="s"]');
    if (!q || !q.value) return;
    window.gtag("event", "search", {
      event_category: "engagement",
      event_label: String(q.value).slice(0, 100)
    });
  });
})();

/* ---------- v90: critical notify banner — localStorage dismiss ----------
 * Prathi banner ki data-code undi; reader ✕ kottaka aa code localStorage lo
 * save → reload ayina hide ga untundi (server round-trip ledu). Admin alert
 * fix ayyaka queue nunchi clear chestundi — dismiss state automatic ga reset.
 */
(function () {
  "use strict";
  function key(code) { return "suNotifyHidden_" + code; }
  var banners = document.querySelectorAll(".su-notify[data-code]");
  Array.prototype.forEach.call(banners, function (el) {
    var code = el.getAttribute("data-code") || "";
    var hiddenAt = null;
    try { hiddenAt = localStorage.getItem(key(code)); } catch (e) { hiddenAt = null; }
    if (hiddenAt) { el.setAttribute("hidden", ""); return; }
    var btn = el.querySelector(".su-notify-close");
    if (btn) {
      btn.addEventListener("click", function () {
        el.setAttribute("hidden", "");
        try { localStorage.setItem(key(code), String(Date.now())); } catch (e) { /* private mode */ }
      });
    }
  });
})();

/* ---------- v96: Up Next sticky bar (session depth, policy-safe) ----------
 * Rules jagratha ga follow ayyam:
 *   · NO timer-based ad refresh, NO auto redirect, NO forced reload.
 *     (AdSense invalid-traffic policy — account ban risk.)
 *   · Bar 55% scroll tarvata MATRAME kanipistundi (reader article lo
 *     engage ayyaka) → annoying kaadu, CLS ledu (fixed element).
 *   · Reader ✕ kottite aa session lo malli raadhu (sessionStorage).
 *   · Already chusina link aithe (localStorage history) bar hide —
 *     same page ki malli pampinchamu.
 */
(function () {
  "use strict";
  var bar = document.querySelector("[data-su-nextbar]");
  if (!bar) { return; }
  var link = bar.querySelector(".su-nextbar-link");
  var HIST = "suSeenPosts";
  function seen() {
    try { return JSON.parse(sessionStorage.getItem(HIST) || "[]"); }
    catch (e) { return []; }
  }
  function remember(href) {
    try {
      var list = seen();
      if (list.indexOf(href) === -1) { list.push(href); }
      sessionStorage.setItem(HIST, JSON.stringify(list.slice(-40)));
    } catch (e) { /* private mode — feature optional */ }
  }
  remember(location.pathname);
  if (link && seen().indexOf(new URL(link.href, location.href).pathname) !== -1) {
    return;   // ee post already chusaru — bar chupinchamu
  }
  var dismissed = false;
  try { dismissed = !!sessionStorage.getItem("suNextbarClosed"); } catch (e) { dismissed = false; }
  if (dismissed) { return; }
  var closeBtn = bar.querySelector("[data-su-nextbar-close]");
  if (closeBtn) {
    closeBtn.addEventListener("click", function () {
      bar.setAttribute("hidden", "");
      try { sessionStorage.setItem("suNextbarClosed", "1"); } catch (e) { /* ignore */ }
    });
  }
  function onScroll() {
    var h = document.documentElement;
    var max = (h.scrollHeight - h.clientHeight) || 1;
    var pct = (h.scrollTop || document.body.scrollTop) / max;
    if (pct > 0.55) {
      bar.removeAttribute("hidden");
      window.removeEventListener("scroll", onScroll);
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();
})();
