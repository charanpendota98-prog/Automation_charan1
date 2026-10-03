/*!
 * v197 ADVANCED MENU — mega panel behaviour (no dependencies, ~4 KB).
 *
 * Enduku kotha file:
 *  · v93 CSS dropdown hover ki mattrame pani chestundi. Phone lo hover ledu,
 *    keyboard user ki Escape/arrows ledu, screen reader ki aria-expanded
 *    update avvaledu — adi "advanced menu" kaadu.
 *  · Ippudu: Enter/Space toggle · ArrowDown first link · ArrowLeft/Right top
 *    items · Escape close + focus return · outside click · touch · focus trap
 *    lite · mobile accordion auto-open (active group) · sticky shrink.
 *
 * Performance: module top-level lo querySelectorAll okkate; scroll listener
 * passive; resize debounce ledu (CSS ne handle chestundi).
 */
(function () {
  "use strict";

  var nav = document.querySelector(".nav");
  var panel = document.getElementById("mpanel");
  var btn = document.getElementById("menubtn");

  /* ------------------------------------------------------------- desktop */
  function items(root) {
    /* v197.1 FIX: WP `wp_nav_menu` ul.menu-primary ni <nav> lopala pettundi —
       `:scope > li` vethikithe 0 items (menu keyboard tho open avvaledu).
       Rendu structure ni support cheyyali: nav > li … leda nav > ul > li … */
    var direct = [].slice.call(root.querySelectorAll(":scope > li.menu-item"));
    if (direct.length) return direct;
    return [].slice.call(root.querySelectorAll(":scope > ul > li.menu-item"));
  }

  function topLink(li) {
    return li.querySelector(":scope > a");
  }

  function subOf(li) {
    return li.querySelector(":scope > .sub-menu");
  }

  function setOpen(li, open) {
    var a = topLink(li);
    if (a) a.setAttribute("aria-expanded", open ? "true" : "false");
    li.classList.toggle("su-open", open);
  }

  function closeAll(except) {
    if (!nav) return;
    items(nav).forEach(function (li) {
      if (li !== except && li.classList.contains("su-open")) setOpen(li, false);
    });
  }

  function focusables(li) {
    var sub = subOf(li);
    if (!sub) return [];
    return [].slice.call(sub.querySelectorAll("a")).filter(function (a) {
      return a.offsetParent !== null;
    });
  }

  function wireDesktop() {
    if (!nav) return;
    var tops = items(nav);
    tops.forEach(function (li) {
      var a = topLink(li);
      if (!a) return;
      var sub = subOf(li);
      if (!sub) return;

      /* touch / click: first tap opens, second tap follows the link */
      a.addEventListener("click", function (e) {
        var isTouch = window.matchMedia && window.matchMedia("(hover: none)").matches;
        if (!li.classList.contains("su-open") && (isTouch || e.detail === 0)) {
          e.preventDefault();
          closeAll(li);
          setOpen(li, true);
          var f = focusables(li);
          if (f[0] && !isTouch) f[0].focus();
        } else if (isTouch && !a.getAttribute("data-su-go")) {
          e.preventDefault();
          closeAll(li);
          setOpen(li, true);
          a.setAttribute("data-su-go", "1");
        } else {
          a.removeAttribute("data-su-go");
        }
      });

      a.addEventListener("keydown", function (e) {
        var k = e.key;
        if (k === "ArrowDown" || k === "Down") {
          e.preventDefault();
          closeAll(li);
          setOpen(li, true);
          var f = focusables(li);
          if (f[0]) f[0].focus();
        } else if (k === "ArrowRight" || k === "ArrowLeft") {
          e.preventDefault();
          var dir = k === "ArrowRight" ? 1 : -1;
          var i = tops.indexOf(li);
          var next = tops[(i + dir + tops.length) % tops.length];
          var na = topLink(next);
          closeAll(null);
          if (na) na.focus();
        } else if (k === "Escape") {
          setOpen(li, false);
        }
      });

      /* keyboard inside the panel */
      sub.addEventListener("keydown", function (e) {
        var k = e.key;
        if (k === "Escape") {
          e.preventDefault();
          setOpen(li, false);
          a.focus();
        } else if (k === "ArrowDown" || k === "ArrowUp") {
          e.preventDefault();
          var f = focusables(li);
          var i = f.indexOf(document.activeElement);
          var n = k === "ArrowDown" ? i + 1 : i - 1;
          if (n < 0) n = f.length - 1;
          if (n >= f.length) n = 0;
          if (f[n]) f[n].focus();
        }
      });

      /* focus leaving the item → close (mouse users unaffected) */
      li.addEventListener("focusout", function (e) {
        if (!li.contains(e.relatedTarget)) setOpen(li, false);
      });
    });

    document.addEventListener("click", function (e) {
      if (nav && !nav.contains(e.target)) closeAll(null);
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") closeAll(null);
    });
  }

  /* -------------------------------------------------- mobile accordion */
  function wireMobile() {
    if (!panel) return;
    /* active group (or first) auto-open — reader 2 taps save chestadu */
    var groups = [].slice.call(panel.querySelectorAll("details.mgroup"));
    if (!groups.length) return;
    var current = null;
    groups.forEach(function (d) {
      var on = d.querySelector("a[aria-current], a.current, a[data-su-current]");
      if (on && !current) current = d;
    });
    (current || groups[0]).open = true;

    /* okate group open (accordion) — panel scroll chinnadi ga untundi */
    groups.forEach(function (d) {
      d.addEventListener("toggle", function () {
        if (!d.open) return;
        groups.forEach(function (o) {
          if (o !== d) o.open = false;
        });
      });
    });

    /* panel open ayyaka focus search ki (keyboard) */
    if (btn) {
      btn.addEventListener("click", function () {
        var first = panel.querySelector("a, summary, button");
        if (first) window.setTimeout(function () { first.focus(); }, 60);
      });
    }
  }

  /* ---------------------------------------------------------- sticky */
  function wireSticky() {
    var head = document.querySelector(".header");
    if (!head || !("onscroll" in window)) return;
    var last = -1;
    window.addEventListener("scroll", function () {
      var y = window.pageYOffset || document.documentElement.scrollTop || 0;
      var small = y > 90 ? 1 : 0;
      if (small !== last) {
        last = small;
        head.classList.toggle("su-head-small", !!small);
      }
    }, { passive: true });
  }

  function boot() {
    wireDesktop();
    wireMobile();
    wireSticky();
  }

  if (document.readyState !== "loading") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
