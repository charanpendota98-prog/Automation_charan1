/* StudentUp v123 premium layer — daily quiz, instant alerts (push-style),
   bottom nav search, hot-jobs rail. No dependencies, no jQuery. */
(function () {
  var SUICON = function (d, s) { return '<svg viewBox="0 0 24 24" width="' + (s || 14) + '" height="' + (s || 14) + '" fill="currentColor" aria-hidden="true" focusable="false"><path d="' + d + '"/></svg>'; };
  var I = {
    check: SUICON("M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"),
    close: SUICON("M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"),
    bell: SUICON("M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"),
    clock: SUICON("M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"),
    calendar: SUICON("M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM5 8V6h14v2H5z"),
    wallet: SUICON("M21 7.28V5c0-1.1-.9-2-2-2H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-2.28c.59-.35 1-.98 1-1.72V9c0-.74-.41-1.37-1-1.72zM20 9v6h-7V9h7zM5 19V5h14v2h-6c-1.1 0-2 .9-2 2v6c0 1.1.9 2 2 2h6v2H5z"),
    card: SUICON("M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"),
    speaker: SUICON("M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1-3.29-2.5-4.03v8.05c1.5-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"),
    search: SUICON("M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z")
  };
  "use strict";

  /* ---------------- Daily quiz ---------------- */
  function quiz() {
    var box = document.querySelector("[data-su-quiz]");
    if (!box) return;
    var data;
    try { data = JSON.parse(box.getAttribute("data-su-quiz") || "[]"); } catch (e) { return; }
    if (!data.length) return;

    var scoreEl = document.querySelector("[data-su-quiz-score]");
    var barEl = document.querySelector("[data-su-quiz-bar]");
    var key = "su_quiz_" + new Date().toISOString().slice(0, 10);
    var score = 0, done = 0;

    function paint() {
      if (scoreEl) scoreEl.textContent = String(score);
      if (barEl) barEl.style.width = Math.round((done / data.length) * 100) + "%";
    }

    function build() {
      box.innerHTML = "";
      score = 0; done = 0;
      data.forEach(function (item, qi) {
        var wrap = document.createElement("div");
        wrap.className = "su-q";
        var h = document.createElement("p");
        h.className = "su-q-title";
        h.innerHTML = '<span class="su-q-n">' + (qi + 1) + "</span>";
        h.appendChild(document.createTextNode(" " + item.q));
        wrap.appendChild(h);

        var opts = document.createElement("div");
        opts.className = "su-q-opts";
        item.a.forEach(function (txt, ai) {
          var b = document.createElement("button");
          b.type = "button";
          b.className = "su-q-opt";
          b.textContent = String.fromCharCode(65 + ai) + ". " + txt;
          b.addEventListener("click", function () {
            if (wrap.classList.contains("answered")) return;
            wrap.classList.add("answered");
            var right = ai === item.c;
            b.classList.add(right ? "ok" : "bad");
            if (!right) {
              var correct = opts.children[item.c];
              if (correct) correct.classList.add("ok");
            }
            if (right) score++;
            done++;
            paint();
            var why = document.createElement("p");
            why.className = "su-q-why " + (right ? "good" : "miss");
            why.innerHTML = (right ? I.check + " Correct — " : I.close + " Answer: " + item.a[item.c] + " — ") + item.why;
            wrap.appendChild(why);
            try { localStorage.setItem(key, String(score)); } catch (e) {}
            if (done === data.length) {
              var fin = document.createElement("p");
              fin.className = "su-q-final";
              fin.textContent = "Today's score: " + score + "/" + data.length +
                (score === data.length ? " — perfect! Repu malli try cheyandi." : " — repu kotha questions vastayi.");
              box.appendChild(fin);
            }
          });
          opts.appendChild(b);
        });
        wrap.appendChild(opts);
        box.appendChild(wrap);
      });
      paint();
    }

    build();
    var rs = document.querySelector("[data-su-quiz-restart]");
    if (rs) rs.addEventListener("click", build);
  }

  /* ---------------- Instant alerts (browser notifications) ---------------- */
  function alerts() {
    var btns = document.querySelectorAll("[data-su-push]");
    if (!btns.length && !localStorage.getItem("su_push_on")) return;
    var state = document.querySelector("[data-su-push-state]");
    var supported = "Notification" in window;

    function say(msg) { if (state) state.textContent = msg; }

    function sync() {
      var on = supported && Notification.permission === "granted" && localStorage.getItem("su_push_on") === "1";
      Array.prototype.forEach.call(btns, function (b) {
        b.classList.toggle("on", on);
        b.innerHTML = on ? I.check + " Alerts are ON" : I.bell + " Turn on alerts";
      });
      if (on) say("You'll get an instant alert whenever a new job, result or hall ticket is posted.");
      return on;
    }

    Array.prototype.forEach.call(btns, function (b) {
      b.addEventListener("click", function () {
        if (!supported) { say("Ee browser notifications support cheyyadu — WhatsApp/Telegram join cheyandi."); return; }
        if (localStorage.getItem("su_push_on") === "1" && Notification.permission === "granted") {
          localStorage.setItem("su_push_on", "0"); sync(); say("Alerts turned off."); return;
        }
        Notification.requestPermission().then(function (p) {
          if (p === "granted") {
            localStorage.setItem("su_push_on", "1");
            sync();
            notify("StudentUp alerts ON", "Kotha job/result post ayina vent ne ikkade alert vastundi.", location.href);
            poll();
          } else {
            say("Notifications blocked — browser settings lo allow cheyandi, leda Telegram join cheyandi.");
          }
        });
      });
    });

    function notify(title, body, url) {
      try {
        var n = new Notification(title, { body: body, icon: (window.STUDENTUP && STUDENTUP.icon) || undefined, tag: url });
        n.onclick = function () { window.open(url, "_blank"); n.close(); };
      } catch (e) {}
    }

    function poll() {
      if (!(window.STUDENTUP && STUDENTUP.rest)) return;
      if (localStorage.getItem("su_push_on") !== "1" || Notification.permission !== "granted") return;
      fetch(STUDENTUP.rest + "posts?per_page=3&_fields=id,link,title,date_gmt", { credentials: "omit" })
        .then(function (r) { return r.ok ? r.json() : []; })
        .then(function (list) {
          if (!list || !list.length) return;
          var seen = Number(localStorage.getItem("su_push_last") || 0);
          var newest = seen;
          list.slice().reverse().forEach(function (p) {
            if (p.id > seen) {
              if (seen) {
                var t = (p.title && p.title.rendered) ? p.title.rendered.replace(/<[^>]*>/g, "") : "New update";
                notify(t, "Tap to open the full notification details.", p.link);
              }
              newest = Math.max(newest, p.id);
            }
          });
          localStorage.setItem("su_push_last", String(newest));
        })
        .catch(function () {});
    }

    if (sync()) poll();
    setInterval(poll, 180000);
    document.addEventListener("visibilitychange", function () { if (!document.hidden) poll(); });
  }

  /* ---------------- Bottom nav search ---------------- */
  function bnav() {
    var b = document.getElementById("su-bnav-search");
    if (!b) return;
    b.addEventListener("click", function () {
      var t = document.getElementById("searchbtn");
      if (t) { t.click(); window.scrollTo({ top: 0, behavior: "smooth" }); }
      else { location.href = (window.STUDENTUP && STUDENTUP.home ? STUDENTUP.home : "/") + "?s="; }
      setTimeout(function () { var i = document.getElementById("qtop"); if (i) i.focus(); }, 260);
    });
  }

  /* ---------------- Hot rail: arrows + drag + keyboard + snap ------- */
  function rail() {
    Array.prototype.forEach.call(document.querySelectorAll(".su-hot-rail"), function (r) {
      var host = r.parentNode;
      if (!host) return;
      host.classList.add("su-rail-host");
      r.setAttribute("tabindex", "0");
      r.setAttribute("role", "group");
      r.setAttribute("aria-label", "Scrollable cards - swipe or use arrow keys");

      function step() {
        var c = r.firstElementChild;
        return (c ? c.getBoundingClientRect().width : 260) + 14;
      }
      function go(dir) { r.scrollBy({ left: dir * step(), behavior: "smooth" }); }

      /* pointer drag (mouse) - touch keeps native momentum scrolling */
      var down = false, x0 = 0, sl = 0, moved = false;
      r.addEventListener("pointerdown", function (e) {
        if (e.pointerType === "touch") return;
        down = true; moved = false; x0 = e.clientX; sl = r.scrollLeft;
      });
      window.addEventListener("pointerup", function () {
        down = false; r.classList.remove("dragging");
      });
      r.addEventListener("pointermove", function (e) {
        if (!down) return;
        var d = e.clientX - x0;
        if (Math.abs(d) > 4) { moved = true; r.classList.add("dragging"); }
        r.scrollLeft = sl - d;
      });
      r.addEventListener("click", function (e) {
        if (moved) { e.preventDefault(); e.stopPropagation(); moved = false; }
      }, true);

      /* wheel: a vertical wheel/trackpad gesture over the rail scrolls it sideways,
         but the page gets its scroll back once the rail hits an edge */
      r.addEventListener("wheel", function (e) {
        if (Math.abs(e.deltaX) > Math.abs(e.deltaY)) return;
        var max = r.scrollWidth - r.clientWidth;
        if (max <= 0) return;
        var next = r.scrollLeft + e.deltaY;
        if (next < 0 || next > max) return;
        e.preventDefault();
        r.scrollLeft = next;
      }, { passive: false });

      r.addEventListener("keydown", function (e) {
        if (e.key !== "ArrowRight" && e.key !== "ArrowLeft") return;
        e.preventDefault();
        go(e.key === "ArrowRight" ? 1 : -1);
      });

      /* arrow buttons (JS-added so no-JS readers still get a plain scroller) */
      var nav = {};
      ["prev", "next"].forEach(function (kind) {
        var b = host.querySelector(".su-rail-" + kind);
        if (!b) {
          b = document.createElement("button");
          b.type = "button";
          b.className = "su-rail-nav su-rail-" + kind;
          b.setAttribute("aria-label", kind === "prev" ? "Scroll left" : "Scroll right");
          b.innerHTML = kind === "prev" ? "\u2039" : "\u203a";
          host.appendChild(b);
        }
        b.addEventListener("click", function () { go(kind === "prev" ? -1 : 1); });
        nav[kind] = b;
      });

      function edges() {
        var max = r.scrollWidth - r.clientWidth - 2;
        nav.prev.disabled = r.scrollLeft <= 2;
        nav.next.disabled = r.scrollLeft >= max;
      }
      r.addEventListener("scroll", edges, { passive: true });
      window.addEventListener("resize", edges);
      edges();
    });
  }

  /* ---------------- v191: tools tabs (8 calculators → one neat card) ------- */
  function tools() {
    Array.prototype.forEach.call(document.querySelectorAll(".su-tooltabs"), function (strip) {
      // v198: strip ni advanced engine (studentup-tools.js) handle chestundi —
      // appudu idi duplicate ga arrow keys/selection cheyyakoodadu (hidden
      // tabs ni select cheyyadam valla empty panel vachhe bug kuda ade).
      if (strip.hasAttribute("data-su-tool-strip")) return;
      var tabs = Array.prototype.slice.call(strip.querySelectorAll(".su-ttab"));
      if (!tabs.length) return;
      function select(tab) {
        tabs.forEach(function (t) {
          var on = t === tab;
          t.setAttribute("aria-selected", on ? "true" : "false");
          t.tabIndex = on ? 0 : -1;
          var panel = document.getElementById(t.getAttribute("aria-controls"));
          if (!panel) return;
          panel.classList.toggle("on", on);
          if (on) panel.removeAttribute("hidden");
          else panel.setAttribute("hidden", "");
        });
      }
      tabs.forEach(function (t, i) {
        t.addEventListener("click", function () { select(t); });
        t.addEventListener("keydown", function (e) {
          var n = null;
          if (e.key === "ArrowRight") n = tabs[(i + 1) % tabs.length];
          if (e.key === "ArrowLeft") n = tabs[(i - 1 + tabs.length) % tabs.length];
          if (e.key === "Home") n = tabs[0];
          if (e.key === "End") n = tabs[tabs.length - 1];
          if (n) { e.preventDefault(); n.focus(); select(n); }
        });
      });
    });
  }

  function init() { quiz(); alerts(); bnav(); rail(); tools(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
