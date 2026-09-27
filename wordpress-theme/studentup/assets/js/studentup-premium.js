/* StudentUp v123 premium layer — daily quiz, instant alerts (push-style),
   bottom nav search, hot-jobs rail. No dependencies, no jQuery. */
(function () {
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
            why.textContent = (right ? "✅ Correct — " : "❌ Answer: " + item.a[item.c] + " — ") + item.why;
            wrap.appendChild(why);
            try { localStorage.setItem(key, String(score)); } catch (e) {}
            if (done === data.length) {
              var fin = document.createElement("p");
              fin.className = "su-q-final";
              fin.textContent = "🎉 Today's score: " + score + "/" + data.length +
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
        b.textContent = on ? "✅ Alerts are ON" : "🔔 Turn on alerts";
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
            notify("StudentUp alerts ON 🎉", "Kotha job/result post ayina vent ne ikkade alert vastundi.", location.href);
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
                notify("🔔 " + t, "Tap to open the full notification details.", p.link);
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

  /* ---------------- Hot rail keyboard/drag niceties ---------------- */
  function rail() {
    var r = document.querySelector(".su-hot-rail");
    if (!r) return;
    var down = false, x = 0, sl = 0;
    r.addEventListener("pointerdown", function (e) { down = true; x = e.clientX; sl = r.scrollLeft; });
    window.addEventListener("pointerup", function () { down = false; r.classList.remove("dragging"); });
    r.addEventListener("pointermove", function (e) {
      if (!down) return;
      var d = e.clientX - x;
      if (Math.abs(d) > 4) r.classList.add("dragging");
      r.scrollLeft = sl - d;
    });
  }

  function init() { quiz(); alerts(); bnav(); rail(); }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", init);
  else init();
})();
