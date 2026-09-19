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
  var QUAL_LABELS = { "10th": "10th", "inter": "Inter (10+2)", "iti": "ITI",
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


  /* ---------- v72: header search (menu pakkana 🔍) ---------- */
  var sbtn = document.getElementById("searchbtn");
  var spanel = document.getElementById("searchpanel");
  var sinput = document.getElementById("qtop");
  var sclose = document.getElementById("searchclose");
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
