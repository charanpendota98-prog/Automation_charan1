/*!
 * v198 TOOLS ENGINE — one dependency-free layer that makes the Tools page feel
 * advanced on a phone (~9 KB, deferred, loaded on the Tools page only).
 *
 * Enti add avutundi (anni progressive — JS lekapote page normal ga pani chestundi):
 *   · TOOL FINDER   — search box + category chips → tabs filter instantly.
 *   · STICKY STRIP  — tab bar sticks under the header; active tab auto-scrolls
 *                     into view; phone lo swipe (left/right) tho tool maaruthundi.
 *   · DEEP LINKS    — /tools/?tool=age shareable/bookmarkable (Back kuda pani).
 *   · STEPPERS      — prathi number field ki − / + (48 px) buttons → phone lo
 *                     keyboard avasaram ledu.
 *   · RESULT CARD   — Copy result · Share · Print · Reset okka row lo.
 *   · HOW IT WORKS  — formula + source line (details) — E-E-A-T, no guesswork.
 *   · NO-JS SAFE    — server rendered markup; JS unte mattrame enhancement.
 *
 * Rules: no external requests, no cookies, no personal data, Telugu ledu (UI),
 * 48 px tap targets, prefers-reduced-motion respect.
 */
(function () {
  "use strict";

  var doc = document;
  var reduce = false;
  try {
    reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  } catch (e) { /* old browser */ }

  function $(sel, root) { return (root || doc).querySelector(sel); }
  function $$(sel, root) { return [].slice.call((root || doc).querySelectorAll(sel)); }
  function on(el, ev, fn, opt) { if (el) el.addEventListener(ev, fn, opt || false); }

  function smooth(el, top) {
    if (!el) return;
    try {
      el.scrollIntoView({ behavior: reduce ? "auto" : "smooth", block: "start" });
    } catch (e) {
      window.scrollTo(0, top || 0);
    }
  }

  /* ------------------------------------------------------------ result text */
  function resultEl(panel) {
    return $("[data-su-result]", panel) || $(".su-tout", panel) ||
           $('[id$="-result"]', panel) || $('[id$="-out"]', panel) ||
           $('[id$="-final-score"]', panel);
  }

  function resultText(panel) {
    var r = resultEl(panel);
    if (!r) return "";
    var t = (r.textContent || "").replace(/\s+/g, " ").trim();
    return t;
  }

  /* ---------------------------------------------------------------- steppers */
  function addSteppers(panel) {
    $$('input[type="number"]', panel).forEach(function (inp) {
      if (inp.getAttribute("data-su-step-done")) return;
      inp.setAttribute("data-su-step-done", "1");
      var wrap = doc.createElement("span");
      wrap.className = "su-tstep";
      var step = parseFloat(inp.getAttribute("step")) || 1;
      var min = inp.getAttribute("min") !== null ? parseFloat(inp.getAttribute("min")) : null;
      var max = inp.getAttribute("max") !== null ? parseFloat(inp.getAttribute("max")) : null;

      function bump(dir) {
        var v = parseFloat(inp.value || "0");
        if (isNaN(v)) v = 0;
        v = v + dir * step;
        if (min !== null && v < min) v = min;
        if (max !== null && v > max) v = max;
        inp.value = String(Math.round(v * 100) / 100);
        inp.dispatchEvent(new Event("input", { bubbles: true }));
        inp.dispatchEvent(new Event("change", { bubbles: true }));
      }

      function mk(label, dir, cls) {
        var b = doc.createElement("button");
        b.type = "button";
        b.className = "su-tstep-btn " + cls;
        b.setAttribute("aria-label", label);
        b.textContent = dir > 0 ? "+" : "\u2212";
        on(b, "click", function () { bump(dir); });
        return b;
      }

      inp.parentNode.insertBefore(wrap, inp);
      wrap.appendChild(mk("Decrease", -1, "su-tstep-minus"));
      wrap.appendChild(inp);
      wrap.appendChild(mk("Increase", 1, "su-tstep-plus"));
    });
  }

  /* ----------------------------------------------------------------- actions */
  function addActions(panel, name) {
    if (!resultEl(panel) || $(".su-tool-actions", panel)) return;
    var bar = doc.createElement("div");
    bar.className = "su-tool-actions";
    bar.setAttribute("role", "group");
    bar.setAttribute("aria-label", "Result actions: copy, share, print, reset");

    function btn(label, cls) {
      var b = doc.createElement("button");
      b.type = "button";
      b.className = "su-tact " + cls;
      b.textContent = label;
      return b;
    }

    var copy = btn("Copy result", "su-tact-copy");
    on(copy, "click", function () {
      var txt = name + ": " + (resultText(panel) || "\u2014") + "\n" + location.href;
      function done() {
        copy.textContent = "Copied \u2713";
        window.setTimeout(function () { copy.textContent = "Copy result"; }, 1800);
      }
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(txt).then(done, function () { fallback(txt, done); });
      } else { fallback(txt, done); }
    });

    function fallback(txt, done) {
      try {
        var ta = doc.createElement("textarea");
        ta.value = txt;
        ta.setAttribute("readonly", "");
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        doc.body.appendChild(ta);
        ta.select();
        doc.execCommand("copy");
        doc.body.removeChild(ta);
        done();
      } catch (e) { /* clipboard blocked — silent */ }
    }

    var share = btn("Share", "su-tact-share");
    on(share, "click", function () {
      var txt = name + " \u2014 " + (resultText(panel) || "") + " | StudentUp free tool: " + location.href;
      if (navigator.share) {
        navigator.share({ title: name + " \u00b7 StudentUp", text: txt }).catch(function () {});
      } else {
        window.open("https://wa.me/?text=" + encodeURIComponent(txt), "_blank",
                    "noopener,noreferrer");
      }
    });

    var print = btn("Print", "su-tact-print");
    on(print, "click", function () { window.print(); });

    var reset = btn("Reset", "su-tact-reset");
    on(reset, "click", function () {
      $$("input, select", panel).forEach(function (el) {
        if (el.type === "checkbox" || el.type === "radio") {
          el.checked = el.getAttribute("data-su-def-checked") === "1";
        } else if (el.getAttribute("data-su-def") !== null) {
          el.value = el.getAttribute("data-su-def");
        } else if (el.type === "date" && el.getAttribute("data-su-def-date")) {
          el.value = el.getAttribute("data-su-def-date");
        }
        el.dispatchEvent(new Event("input", { bubbles: true }));
        el.dispatchEvent(new Event("change", { bubbles: true }));
      });
      reset.textContent = "Reset \u2713";
      window.setTimeout(function () { reset.textContent = "Reset"; }, 1500);
    });

    bar.appendChild(copy);
    bar.appendChild(share);
    bar.appendChild(print);
    bar.appendChild(reset);
    var r = resultEl(panel);
    r.parentNode.insertBefore(bar, r.nextSibling);
  }

  /* ------------------------------------------------------------- how it works */
  function addHow(panel) {
    var f = panel.getAttribute("data-su-formula");
    var s = panel.getAttribute("data-su-source");
    if ((!f && !s) || $(".su-tool-how", panel)) return;
    var d = doc.createElement("details");
    d.className = "su-tool-how";
    var sum = doc.createElement("summary");
    sum.textContent = "How this is calculated";
    var p = doc.createElement("p");
    p.className = "su-tool-how-t";
    p.textContent = (f || "") + (s ? (f ? " " : "") + "Source: " + s + "." : "");
    d.appendChild(sum);
    d.appendChild(p);
    var r = resultEl(panel);
    (r ? r.parentNode : panel).appendChild(d);
  }

  /* ------------------------------------------------------------- default snap */
  function snapDefaults(panel) {
    $$("input, select", panel).forEach(function (el) {
      if (el.type === "checkbox" || el.type === "radio") {
        el.setAttribute("data-su-def-checked", el.checked ? "1" : "0");
      } else if (el.getAttribute("data-su-def") === null) {
        el.setAttribute("data-su-def", el.value || "");
      }
    });
  }

  /* ============================================================== main wiring */
  // v198: `.su-tools[data-su-tools]` mattrame — single posts lo unna
  // `.su-student-tools[data-su-tools]` (compare/reminder buttons) ki tagalakoodadu.
  var hub = $(".su-tools[data-su-tools]") || $("[data-su-tool-strip]");
  if (!hub) return;

  var strip = $("[data-su-tool-strip]", hub) || $(".su-tooltabs", hub);
  var tabs = strip ? $$(".su-ttab", strip) : [];
  var find = $("[data-su-tool-find]", hub);
  var noneMsg = $("[data-su-tool-none]", hub);
  var topBtn = $("[data-su-tool-top]", hub);
  var panelsBox = $("[data-su-tool-swipe]", hub) || $(".su-toolpanels", hub);

  function tabLabel(t) { return (t.textContent || "").replace(/\s+/g, " ").trim(); }

  function tabPanel(t) {
    var id = t.getAttribute("aria-controls");
    return id ? doc.getElementById(id) : null;
  }

  /* panel switching — engine self-sufficient (theme's premium.js does the same,
     rendu okesari run aina idempotent) */
  function select(tab) {
    if (!tab) return;
    tabs.forEach(function (t) {
      var isOn = t === tab;
      t.setAttribute("aria-selected", isOn ? "true" : "false");
      t.tabIndex = isOn ? 0 : -1;
      var p = tabPanel(t);
      if (!p) return;
      p.classList.toggle("on", isOn);
      if (isOn) { p.removeAttribute("hidden"); } else { p.setAttribute("hidden", ""); }
    });
    syncHash(tab);
    autoScroll(tab);
  }

  function activeTab() {
    for (var i = 0; i < tabs.length; i++) {
      if (tabs[i].getAttribute("aria-selected") === "true") return tabs[i];
    }
    return tabs[0] || null;
  }

  function visibleTabs() {
    return tabs.filter(function (t) { return !t.hasAttribute("hidden"); });
  }

  /* panels: annotate + enhance (once) */
  tabs.forEach(function (t) {
    var p = tabPanel(t);
    if (!p) return;
    if (!p.getAttribute("data-su-ready")) {
      p.setAttribute("data-su-ready", "1");
      snapDefaults(p);
      addSteppers(p);
      addHow(p);
      addActions(p, tabLabel(t));
      on(p, "keydown", function (e) {
        /* typing in a field is not tab navigation */
        if (e.target && /^(INPUT|SELECT|TEXTAREA)$/.test(e.target.tagName)) return;
        if (e.key === "ArrowRight" || e.key === "ArrowLeft") {
          var n = e.key === "ArrowRight" ? nextTab(t, 1) : nextTab(t, -1);
          if (n) { e.preventDefault(); n.focus(); n.click(); }
        }
      });
    }
  });

  function nextTab(from, dir) {
    var list = visibleTabs();
    var i = list.indexOf(from);
    if (i < 0) i = 0;
    return list[(i + dir + list.length) % list.length];
  }

  /* when a tab gets selected (click / deep link / swipe) keep things in sync */
  tabs.forEach(function (t) {
    on(t, "click", function () { select(t); });
  });

  on(strip, "keydown", function (e) {
    var t = e.target;
    if (!t || !t.classList || !t.classList.contains("su-ttab")) return;
    var list = visibleTabs();
    var i = list.indexOf(t);
    if (i < 0) return;
    var n = null;
    if (e.key === "ArrowRight") n = list[(i + 1) % list.length];
    if (e.key === "ArrowLeft") n = list[(i - 1 + list.length) % list.length];
    if (e.key === "Home") n = list[0];
    if (e.key === "End") n = list[list.length - 1];
    if (n) { e.preventDefault(); n.focus(); select(n); }
  });

  function syncHash(t) {
    var id = (t.id || "").replace("su-ttab-", "");
    if (!id || !window.history || !history.replaceState) return;
    try {
      var url = location.pathname + location.search.replace(/([?&])tool=[^&]*/g, "$1")
                                            .replace(/[?&]$/, "");
      var sep = url.indexOf("?") >= 0 ? "&" : "?";
      history.replaceState(null, "", url + sep + "tool=" + encodeURIComponent(id) + location.hash);
    } catch (e) { /* file:// — ignore */ }
  }

  function autoScroll(t) {
    if (!strip) return;
    var left = t.offsetLeft - (strip.clientWidth - t.offsetWidth) / 2;
    try { strip.scrollTo({ left: Math.max(0, left), behavior: reduce ? "auto" : "smooth" }); }
    catch (e) { strip.scrollLeft = Math.max(0, left); }
  }

  /* deep link (?tool=age) — boots the right panel on load and on Back */
  function fromHash() {
    var m = /[?&]tool=([a-z0-9_-]+)/i.exec(location.search);
    if (!m) return null;
    var t = null;
    tabs.forEach(function (x) { if (x.id === "su-ttab-" + m[1]) t = x; });
    return t;
  }
  function applyDeepLink(focusIt) {
    var t = fromHash();
    if (!t || t.hasAttribute("hidden")) return;
    select(t);
    if (focusIt) t.focus();
  }
  applyDeepLink(false);
  on(window, "popstate", function () { applyDeepLink(false); });

  /* --------------------------------------------------------------- finder */
  function norm(s) { return (s || "").toLowerCase().replace(/\s+/g, " ").trim(); }

  function applyFilter() {
    var q = find ? norm(find.value) : "";
    var cat = hub.getAttribute("data-su-cat-active") || "all";
    var shown = 0;
    tabs.forEach(function (t) {
      var hay = norm(tabLabel(t) + " " + (t.getAttribute("data-su-keywords") || ""));
      var ok = (!q || hay.indexOf(q) >= 0) &&
               (cat === "all" || t.getAttribute("data-su-cat") === cat);
      if (ok) { t.removeAttribute("hidden"); shown++; } else { t.setAttribute("hidden", ""); }
      var p = tabPanel(t);
      if (p && !ok) { p.classList.remove("on"); p.setAttribute("hidden", ""); }
    });
    if (noneMsg) {
      noneMsg.hidden = shown !== 0;
      var qs = $("[data-su-tool-q]", noneMsg);
      if (qs) qs.textContent = q || cat;
    }
    if ($("[data-su-tool-clear]", hub)) {
      $("[data-su-tool-clear]", hub).hidden = !q;
    }
    var act = activeTab();
    if (act && act.hasAttribute("hidden")) {
      var first = visibleTabs()[0];
      if (first) select(first);
    }
  }

  if (find) {
    var tmr = null;
    on(find, "input", function () {
      if (tmr) window.clearTimeout(tmr);
      tmr = window.setTimeout(applyFilter, 120);
    });
    on(find, "keydown", function (e) {
      if (e.key === "Escape") { find.value = ""; applyFilter(); }
      if (e.key === "Enter") {
        e.preventDefault();
        var first = visibleTabs()[0];
        if (first) { select(first); first.focus(); smoothTarget(); }
      }
    });
  }

  var clearBtn = $("[data-su-tool-clear]", hub);
  on(clearBtn, "click", function () {
    if (find) { find.value = ""; find.focus(); }
    applyFilter();
  });

  $$("[data-su-tool-cat]", hub).forEach(function (c) {
    on(c, "click", function () {
      $$("[data-su-tool-cat]", hub).forEach(function (o) {
        var on_ = o === c;
        o.classList.toggle("on", on_);
        o.setAttribute("aria-pressed", on_ ? "true" : "false");
      });
      hub.setAttribute("data-su-cat-active", c.getAttribute("data-su-tool-cat") || "all");
      applyFilter();
    });
  });

  function smoothTarget() {
    smooth(hub, 0);
  }

  /* ------------------------------------------------------------------ swipe */
  if (panelsBox) {
    var x0 = null, y0 = null, lock = null;
    on(panelsBox, "touchstart", function (e) {
      if (e.touches.length !== 1) { x0 = null; return; }
      x0 = e.touches[0].clientX;
      y0 = e.touches[0].clientY;
      lock = null;
    }, { passive: true });
    on(panelsBox, "touchmove", function (e) {
      if (x0 === null || e.touches.length !== 1) return;
      if (lock === null) {
        var dx = e.touches[0].clientX - x0;
        var dy = e.touches[0].clientY - y0;
        if (Math.abs(dx) > 12 || Math.abs(dy) > 12) lock = Math.abs(dx) > Math.abs(dy) ? "x" : "y";
      }
    }, { passive: true });
    on(panelsBox, "touchend", function (e) {
      if (x0 === null || lock !== "x") { x0 = null; return; }
      var dx = (e.changedTouches && e.changedTouches[0] ? e.changedTouches[0].clientX : x0) - x0;
      x0 = null;
      if (Math.abs(dx) < 55) return;
      var cur = activeTab();
      var n = nextTab(cur, dx < 0 ? 1 : -1);
      if (n && n !== cur) { select(n); }
    }, { passive: true });
  }

  /* ------------------------------------------------------------ next / top */
  on(hub, "click", function (e) {
    var nx = e.target && e.target.closest ? e.target.closest("[data-su-next]") : null;
    if (nx) {
      var cur = activeTab();
      var n = nextTab(cur, 1);
      if (n) { n.click(); n.focus(); smooth(hub, 0); }
    }
  });

  on(topBtn, "click", function () { smooth(hub, 0); });
  if (topBtn) {
    on(window, "scroll", function () {
      topBtn.hidden = (window.pageYOffset || doc.documentElement.scrollTop || 0) < 700;
    }, { passive: true });
  }

  /* keyboard shortcut: "/" focuses the finder (tools page only, not in fields) */
  on(doc, "keydown", function (e) {
    if (e.key !== "/" || !find) return;
    var t = e.target;
    if (t && (/^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName) || t.isContentEditable)) return;
    if (find.offsetParent === null) return;
    e.preventDefault();
    find.focus();
  });

  applyFilter();
})();
