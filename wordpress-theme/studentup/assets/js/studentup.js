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

  /* ---------- chips filter (front page grid) ---------- */
  var grid = document.getElementById("grid");
  var chips = document.querySelectorAll(".chip[data-cat]");
  var nores = document.getElementById("nores");
  function applyCat(cat) {
    if (!grid) return;
    var shown = 0;
    Array.prototype.forEach.call(grid.querySelectorAll(".news"), function (card) {
      var ok = cat === "all" || (" " + (card.getAttribute("data-cat") || "") + " ").indexOf(" " + cat + " ") > -1;
      card.classList.toggle("hidden", !ok);
      if (ok) shown++;
    });
    if (nores) nores.style.display = shown ? "none" : "block";
  }
  Array.prototype.forEach.call(chips, function (chip) {
    chip.addEventListener("click", function () {
      Array.prototype.forEach.call(chips, function (c) {
        c.classList.remove("active");
        c.setAttribute("aria-selected", "false");
      });
      chip.classList.add("active");
      chip.setAttribute("aria-selected", "true");
      applyCat(chip.getAttribute("data-cat"));
    });
  });
  /* hash deep-link (#cat-ts-jobs) */
  (function () {
    var m = (location.hash || "").match(/^#cat-([a-z0-9-]+)$/);
    if (!m || !grid) return;
    Array.prototype.forEach.call(chips, function (c) {
      if (c.getAttribute("data-cat") === m[1]) c.click();
    });
  })();

  /* ---------- deadline countdown ---------- */
  var timer = document.querySelector(".timer[data-deadline]");
  if (timer) {
    var target = Date.parse(timer.getAttribute("data-deadline"));
    var pad = function (n) { return (n < 10 ? "0" : "") + n; };
    var tick = function () {
      var left = Math.max(0, target - Date.now());
      var d = Math.floor(left / 86400000);
      var h = Math.floor((left % 86400000) / 3600000);
      var m = Math.floor((left % 3600000) / 60000);
      var s = Math.floor((left % 60000) / 1000);
      var set = function (k, v) {
        var el = timer.querySelector('[data-cd="' + k + '"]');
        if (el) el.textContent = pad(v);
      };
      set("d", d); set("h", h); set("m", m); set("s", s);
    };
    tick();
    setInterval(tick, 1000);
  }

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
        btn.textContent = "✅ కాపీ అయింది";
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
    if (el.textContent.indexOf("అప్డేట్") === -1 && el.textContent.indexOf("త్వరలో") === -1) {
      el.textContent = S.i18n && S.i18n.updates ? "—" : el.textContent;
    }
  });
})();
