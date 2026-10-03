/*!
 * v197 DAILY QUIZ + READER POLL — instant layer (~5 KB, no dependencies).
 *
 * Progressive enhancement only: the server already rendered questions, answers
 * and results. Ee file JS unte instant ga chestundi — JS lekapoyina quiz
 * submit chesi, poll form POST chesi pani chestayi.
 *
 * Privacy: localStorage lo score/streak mattrame (device nunchi bayataki
 * velladu). Vote ki emi store cheyyamu — server count okkate.
 */
(function () {
  "use strict";

  function $(sel, root) {
    return (root || document).querySelector(sel);
  }

  function $$(sel, root) {
    return [].slice.call((root || document).querySelectorAll(sel));
  }

  function todayKey() {
    var d = new Date();
    return d.getFullYear() + "-" + (d.getMonth() + 1) + "-" + d.getDate();
  }

  function store(key, val) {
    try {
      if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null");
      localStorage.setItem(key, JSON.stringify(val));
    } catch (e) {
      /* private mode — ignore */
    }
    return null;
  }

  /* ------------------------------------------------------------- quiz */
  function wireQuiz() {
    var form = $("[data-su-quiz-form]");
    if (!form) return;

    var scoreEl = $("[data-su-quiz-score]");
    var barEl = $("[data-su-quiz-bar]");
    var checkBtn = $("[data-su-quiz-check]");
    var restart = $("[data-su-quiz-restart]");
    var share = $("[data-su-quiz-share]");
    var streakEl = $("[data-su-quiz-streak]");
    var qs = $$("fieldset.su-q", form);
    var total = qs.length;
    if (!total) return;

    var saved = store("su_quiz_" + todayKey()) || {};
    var picked = saved.picked || {};
    var score = 0;

    /* Exam filter pills */
    var examTabs = $$(".su-qtab");
    if (examTabs.length) {
      examTabs.forEach(function (btn) {
        btn.addEventListener("click", function () {
          examTabs.forEach(function (b) {
            b.classList.remove("active");
            b.setAttribute("aria-selected", "false");
          });
          btn.classList.add("active");
          btn.setAttribute("aria-selected", "true");
          var targetExam = (btn.getAttribute("data-exam") || "all").toLowerCase();
          qs.forEach(function (fs) {
            var ex = (fs.getAttribute("data-exam") || "all").toLowerCase().split(",");
            if (targetExam === "all" || ex.indexOf(targetExam) !== -1 || ex.indexOf("all") !== -1) {
              fs.style.display = "";
            } else {
              fs.style.display = "none";
            }
          });
        });
      });
    }

    if (checkBtn) checkBtn.hidden = true; /* JS unte submit avasaram ledu */

    function paintScore(animate) {
      var done = Object.keys(picked).length;
      if (scoreEl) scoreEl.textContent = String(score);
      if (barEl) barEl.style.width = Math.round((done / total) * 100) + "%";
      if (animate === false) return;
    }

    function mark(fs, chosen) {
      var right = parseInt(fs.getAttribute("data-c"), 10);
      $$(".su-opt", fs).forEach(function (lab) {
        var input = lab.querySelector("input");
        if (!input) return;
        var val = parseInt(input.value, 10);
        lab.classList.remove("right", "wrong", "on");
        input.disabled = true;
        if (val === right) lab.classList.add("right");
        if (val === chosen && chosen !== right) lab.classList.add("wrong");
      });
      var why = $("[data-su-why]", fs);
      if (why) why.hidden = false;
    }

    function restore() {
      var done = 0;
      score = 0;
      qs.forEach(function (fs) {
        var i = fs.getAttribute("data-i");
        if (picked[i] === undefined) return;
        mark(fs, picked[i]);
        if (picked[i] === parseInt(fs.getAttribute("data-c"), 10)) score++;
        done++;
      });
      paintScore();
      if (done === total) finish();
    }

    function streak() {
      var cur = store("su_quiz_streak") || { last: "", n: 0, best: 0 };
      var y = new Date(Date.now() - 86400000);
      var yKey = y.getFullYear() + "-" + (y.getMonth() + 1) + "-" + y.getDate();
      if (cur.last === todayKey()) return cur;
      cur.n = cur.last === yKey ? (cur.n || 0) + 1 : 1;
      cur.last = todayKey();
      cur.best = Math.max(cur.best || 0, cur.n);
      store("su_quiz_streak", cur);
      return cur;
    }

    function finish() {
      var st = streak();
      if (streakEl) {
        streakEl.hidden = false;
        streakEl.textContent = "🔥 " + st.n + "-day streak · best " + st.best;
      }
      if (share) {
        share.hidden = false;
        var txt =
          "I scored " + score + "/" + total + " in today's StudentUp Daily Quiz. Practice free: " +
          location.origin + "/";
        share.href = "https://wa.me/?text=" + encodeURIComponent(txt);
      }
    }

    function answer(fs, chosen) {
      var i = fs.getAttribute("data-i");
      if (picked[i] !== undefined) return;
      picked[i] = chosen;
      if (chosen === parseInt(fs.getAttribute("data-c"), 10)) score++;
      mark(fs, chosen);
      store("su_quiz_" + todayKey(), { picked: picked, score: score });
      paintScore();
      if (Object.keys(picked).length === total) finish();
    }

    form.addEventListener("click", function (e) {
      var lab = e.target.closest ? e.target.closest(".su-opt") : null;
      if (!lab || !form.contains(lab)) return;
      var input = lab.querySelector("input");
      var fs = lab.closest("fieldset.su-q");
      if (!input || !fs) return;
      e.preventDefault();
      if (input.disabled) return;
      input.checked = true;
      answer(fs, parseInt(input.value, 10));
    });

    /* keyboard 1-4 — focused question ki (fast practice) */
    form.addEventListener("keydown", function (e) {
      var k = e.key;
      if (["1", "2", "3", "4"].indexOf(k) < 0) return;
      var fs = (document.activeElement || {}).closest ? document.activeElement.closest("fieldset.su-q") : null;
      if (!fs) return;
      var lab = $$(".su-opt", fs)[parseInt(k, 10) - 1];
      if (!lab) return;
      var input = lab.querySelector("input");
      if (!input || input.disabled) return;
      e.preventDefault();
      input.checked = true;
      answer(fs, parseInt(input.value, 10));
    });

    if (restart) {
      restart.hidden = false;
      restart.addEventListener("click", function () {
        picked = {};
        score = 0;
        store("su_quiz_" + todayKey(), { picked: {}, score: 0 });
        qs.forEach(function (fs) {
          $$(".su-opt", fs).forEach(function (lab) {
            lab.classList.remove("right", "wrong", "on");
            var input = lab.querySelector("input");
            if (input) {
              input.disabled = false;
              input.checked = false;
            }
          });
          var why = $("[data-su-why]", fs);
          if (why) why.hidden = true;
        });
        if (share) share.hidden = true;
        if (streakEl) streakEl.hidden = true;
        paintScore();
        var done = $(".su-quiz-done");
        if (done) done.remove();
        var first = $(".su-opt", form);
        if (first && first.focus) first.focus();
      });
    }

    if (share) {
      share.addEventListener("click", function () {
        /* native share (phone) — lekapote wa.me href ne follow avutundi */
        if (navigator.share) {
          navigator
            .share({ title: "StudentUp Daily Quiz", text: share.textContent.trim(), url: location.href })
            .catch(function () {});
          return false;
        }
        return true;
      });
    }

    restore();
  }

  /* ------------------------------------------------------------- poll */
  function wirePoll() {
    var box = $("[data-su-poll]");
    if (!box) return;
    var form = $("[data-su-poll-form]", box);
    if (!form) return;
    var id = box.getAttribute("data-su-poll");
    var labels = $$(".su-poll-opt", form);
    var sent = false;

    function show(data) {
      var total = data.total || 0;
      labels.forEach(function (lab, i) {
        var c = (data.counts && data.counts[i]) || 0;
        var pct = total > 0 ? Math.round((c / total) * 100) : 0;
        var bar = $("[data-su-bar]", lab);
        var pctEl = $("[data-su-pct]", lab);
        if (bar) bar.style.width = pct + "%";
        if (pctEl) pctEl.textContent = pct + "%";
        lab.setAttribute("data-su-done", "1");
        lab.classList.remove("on");
        var input = lab.querySelector("input");
        if (input) input.disabled = true;
      });
      var foot = $(".su-poll-foot", form);
      var voteBtn = $("[data-su-poll-vote]", form);
      if (voteBtn) voteBtn.remove();
      var hint = foot ? $("span", foot) : null;
      if (hint) hint.textContent = "Thanks — your vote is counted.";
      if (foot && total > 0) {
        var t = foot.querySelector("[data-su-total]");
        if (!t) {
          t = document.createElement("span");
          t.setAttribute("data-su-total", "1");
          foot.appendChild(t);
        }
        t.textContent = total + (total === 1 ? " vote" : " votes");
      }
      var sub = $(".su-poll-sub", box);
      if (sub && total > 0) {
        sub.textContent = total + (total === 1 ? " reader voted" : " readers voted") + " — results are live.";
      }
    }

    labels.forEach(function (lab) {
      lab.addEventListener("click", function () {
        labels.forEach(function (o) { o.classList.remove("on"); });
        lab.classList.add("on");
      });
    });

    form.addEventListener("submit", function (e) {
      var chosen = form.querySelector("input[name=su_poll_opt]:checked");
      if (!chosen) {
        e.preventDefault();
        var first = labels[0];
        if (first) first.classList.add("on");
        return;
      }
      if (sent) {
        e.preventDefault();
        return;
      }
      if (!window.fetch) return; /* no fetch → normal form POST (no-JS path) */
      e.preventDefault();
      sent = true;
      var opt = parseInt(chosen.value, 10);
      fetch("/wp-json/studentup/v1/poll", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: id, opt: opt })
      })
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data && data.counts) {
            show(data);
          } else {
            form.submit();
          }
        })
        .catch(function () {
          form.submit(); /* network fail → server path (still counts) */
        });
    });
  }

  function boot() {
    wireQuiz();
    wirePoll();
  }

  if (document.readyState !== "loading") boot();
  else document.addEventListener("DOMContentLoaded", boot);
})();
