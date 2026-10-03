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

      /* touch / click: click toggles the dropdown, prevent hash jump */
      a.addEventListener("click", function (e) {
        var isTouch = window.matchMedia && window.matchMedia("(hover: none)").matches;
        e.preventDefault();
        var wasOpen = li.classList.contains("su-open");
        closeAll(li);
        if (!wasOpen) {
          setOpen(li, true);
          var f = focusables(li);
          if (f[0] && !isTouch) f[0].focus();
        } else {
          setOpen(li, false);
        }
      });

      /* hover on desktop */
      li.addEventListener("mouseenter", function () {
        var isTouch = window.matchMedia && window.matchMedia("(hover: none)").matches;
        if (!isTouch) {
          closeAll(li);
          setOpen(li, true);
        }
      });
      li.addEventListener("mouseleave", function () {
        var isTouch = window.matchMedia && window.matchMedia("(hover: none)").matches;
        if (!isTouch) {
          setOpen(li, false);
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

  /* -------------------------------------------------- mobile drawer & accordion */
  function wireMobile() {
    if (!panel) return;
    var backdrop = document.getElementById("mbackdrop");
    var panelClose = document.getElementById("mpanelclose");
    var bnavMenu = document.getElementById("su-bnav-menu");

    function setDrawer(open) {
      panel.classList.toggle("open", open);
      panel.setAttribute("aria-hidden", open ? "false" : "true");
      if (backdrop) {
        backdrop.classList.toggle("show", open);
        backdrop.classList.toggle("open", open);
      }
      document.body.classList.toggle("mlock", open);
      if (btn) {
        btn.setAttribute("aria-expanded", open ? "true" : "false");
        btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      }
      if (open && panelClose) {
        window.setTimeout(function () { panelClose.focus(); }, 60);
      }
    }

    if (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        setDrawer(!panel.classList.contains("open"));
      });
    }

    if (bnavMenu) {
      bnavMenu.addEventListener("click", function (e) {
        e.preventDefault();
        setDrawer(!panel.classList.contains("open"));
      });
    }

    if (backdrop) {
      backdrop.addEventListener("click", function () {
        setDrawer(false);
      });
    }

    if (panelClose) {
      panelClose.addEventListener("click", function (e) {
        e.preventDefault();
        setDrawer(false);
        if (btn) btn.focus();
      });
    }

    /* any link clicked inside panel closes drawer */
    panel.addEventListener("click", function (e) {
      if (e.target && (e.target.tagName === "A" || e.target.closest("a"))) {
        setDrawer(false);
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && panel.classList.contains("open")) {
        setDrawer(false);
        if (btn) btn.focus();
      }
    });

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

  /* ---------------------------------------------------------- floating social rail (right side · 5-min dismiss) */
  function wireSocialRail() {
    var rail = document.getElementById("surail");
    var railTab = document.getElementById("sutab");
    var railClose = document.getElementById("suclose");
    if (!rail) return;

    var DURATION_5MIN = 5 * 60 * 1000;
    var SU_DISMISS_KEY = "su_social_dismissed";
    var timer = null;

    function show() {
      if (timer) clearTimeout(timer);
      rail.classList.remove("su-out");
      rail.removeAttribute("aria-hidden");
      if (railTab) railTab.classList.remove("on");
    }

    function hide(userInitiated) {
      if (timer) clearTimeout(timer);
      rail.classList.add("su-out");
      rail.setAttribute("aria-hidden", "true");
      if (railTab) railTab.classList.add("on");

      if (userInitiated) {
        try { localStorage.setItem(SU_DISMISS_KEY, Date.now().toString()); } catch (e) {}
      }
      timer = setTimeout(show, DURATION_5MIN);
    }

    /* Check previous dismissal timestamp */
    try {
      var dismissed = parseInt(localStorage.getItem(SU_DISMISS_KEY) || "0", 10);
      var elapsed = Date.now() - dismissed;
      if (dismissed && elapsed < DURATION_5MIN) {
        hide(false);
        timer = setTimeout(show, DURATION_5MIN - elapsed);
      } else {
        show();
      }
    } catch (e) {
      show();
    }

    if (railClose) {
      railClose.addEventListener("click", function (e) {
        e.preventDefault();
        hide(true);
      });
    }

    if (railTab) {
      railTab.addEventListener("click", function (e) {
        e.preventDefault();
        try { localStorage.removeItem(SU_DISMISS_KEY); } catch (e) {}
        show();
      });
    }

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && !rail.classList.contains("su-out")) {
        hide(true);
      }
    });
  }

  /* ---------------------------------------------------------- ticker controls */
  function wireTicker() {
    var tmove = document.querySelector(".tickerwrap .tmove");
    var tToggle = document.getElementById("su-t-toggle");
    var tPrev = document.getElementById("su-t-prev");
    var tNext = document.getElementById("su-t-next");
    if (!tmove) return;

    var tPaused = false;
    var tickerTimer = null;

    function getTransformX(el) {
      var st = window.getComputedStyle(el);
      var tr = st.transform || st.webkitTransform;
      if (!tr || tr === "none") return 0;
      var values = tr.split("(")[1].split(")")[0].split(",");
      return parseFloat(values[4]) || 0;
    }

    function nudgeTicker(direction) {
      var curX = getTransformX(tmove);
      var step = 180;
      var newX = curX + (direction * step);
      var half = tmove.scrollWidth / 2;
      if (newX > 0) newX = -half + step;
      if (newX < -half) newX = 0;

      tmove.style.animation = "none";
      tmove.style.transform = "translateX(" + newX + "px)";

      clearTimeout(tickerTimer);
      tickerTimer = setTimeout(function () {
        if (!tPaused) {
          tmove.style.animation = "";
          tmove.style.transform = "";
        }
      }, 2800);
    }

    if (tToggle) {
      tToggle.addEventListener("click", function (e) {
        e.preventDefault();
        tPaused = !tPaused;
        tmove.style.animationPlayState = tPaused ? "paused" : "running";
        tToggle.textContent = tPaused ? "▶" : "⏸";
        tToggle.setAttribute("aria-label", tPaused ? "Resume ticker" : "Pause ticker");
      });
    }

    if (tPrev) {
      tPrev.addEventListener("click", function (e) {
        e.preventDefault();
        nudgeTicker(1);
      });
    }

    if (tNext) {
      tNext.addEventListener("click", function (e) {
        e.preventDefault();
        nudgeTicker(-1);
      });
    }
  }

  function boot() {
    wireDesktop();
    wireMobile();
    wireSticky();
    wireSocialRail();
    wireTicker();
  }

  if (document.readyState !== "loading") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
