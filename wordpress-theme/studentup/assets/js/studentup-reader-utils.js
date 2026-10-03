/* v198: reader utilities — compare rail, calendar reminder (.ics), print/PDF,
   text-size buttons and the in-article calculator blocks.
   Ee file v120 nunchi vachindi: v198 lo tools-hub engine (studentup-tools.js)
   tools page ki separate ga undadam valla, ee utility layer ni ikkada
   restore chesam — compare/reminder/print buttons (single post + cards) malli
   panichestayi. Local-only: no account, no cookie, no analytics. */
(function () {
  var SUICON = function (d, s) { return '<svg viewBox="0 0 24 24" width="' + (s || 14) + '" height="' + (s || 14) + '" fill="currentColor" aria-hidden="true" focusable="false"><path d="' + d + '"/></svg>'; };
  var I = {
    check: SUICON("M9 16.17 4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"),
    close: SUICON("M19 6.41 17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"),
    bell: SUICON("M12 22c1.1 0 2-.9 2-2h-4c0 1.1.89 2 2 2zm6-6v-5c0-3.07-1.64-5.64-4.5-6.32V4c0-.83-.67-1.5-1.5-1.5s-1.5.67-1.5 1.5v.68C7.63 5.36 6 7.92 6 11v5l-2 2v1h16v-1l-2-2z"),
    info: SUICON("M11 17h2v-6h-2v6zm1-15C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8zm1-11h-2V7h2v2z"),
    calendar: SUICON("M19 4h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20a2 2 0 0 0 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V10h14v10zM5 8V6h14v2H5z"),
    wallet: SUICON("M21 7.28V5c0-1.1-.9-2-2-2H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2v-2.28c.59-.35 1-.98 1-1.72V9c0-.74-.41-1.37-1-1.72zM20 9v6h-7V9h7zM5 19V5h14v2h-6c-1.1 0-2 .9-2 2v6c0 1.1.9 2 2 2h6v2H5z"),
    card: SUICON("M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"),
    speaker: SUICON("M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1-3.29-2.5-4.03v8.05c1.5-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"),
    menu: SUICON("M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"),
    school: SUICON("M12 3 1 9l11 6 9-4.91V17h2V9L12 3zM5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82z"),
    clock: SUICON("M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67V7z"),
    play: SUICON("M8 5v14l11-7z"),
    pause: SUICON("M6 19h4V5H6v14zm8-14v14h4V5h-4z"),
  };
  "use strict";
  var cfg = window.STUDENTUP_TOOLS || {};
  var I = cfg.i18n || {};
  var key = cfg.store || "studentup_tools_v1";
  var max = 3;
  var panel = document.getElementById("su-compare-rail");
  var items = panel && panel.querySelector("[data-su-compare-items]");
  var count = panel && panel.querySelector("[data-su-compare-count]");
  var openBtn = panel && panel.querySelector("[data-su-compare-open]");
  var list = [];

  function esc(v) {
    return String(v == null ? "" : v).replace(/[&<>"']/g, function (c) {
      return ({"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#039;"})[c];
    });
  }
  function read() {
    try {
      var raw = JSON.parse(localStorage.getItem(key) || "[]");
      return Array.isArray(raw) ? raw.slice(0, max) : [];
    } catch (e) { return []; }
  }
  function write() {
    try { localStorage.setItem(key, JSON.stringify(list)); } catch (e) {}
  }
  function find(id) {
    var i;
    for (i = 0; i < list.length; i += 1) if (String(list[i].id) === String(id)) return i;
    return -1;
  }
  function render() {
    var html = "", i, row;
    if (!panel || !items) return;
    count.textContent = list.length + "/" + max;
    openBtn.disabled = list.length < 2;
    for (i = 0; i < list.length; i += 1) {
      row = list[i];
      html += '<div class="su-compare-item"><a href="' + esc(row.url) + '">' + esc(row.title) + '</a>' +
        '<button type="button" data-su-compare-remove="' + esc(row.id) + '" aria-label="Remove ' + esc(row.title) + '">✕</button></div>';
    }
    items.innerHTML = html || '<p class="su-compare-empty">' + esc(I.empty || "Select at least two posts to compare.") + '</p>';
    document.querySelectorAll("[data-su-compare]").forEach(function (button) {
      var on = find(button.getAttribute("data-id")) !== -1;
      button.setAttribute("aria-pressed", on ? "true" : "false");
      button.classList.toggle("is-added", on);
      var label = button.querySelector("[data-su-compare-label]");
      if (label) label.textContent = on ? (I.added || "Added") : (I.compare || "Compare");
    });
  }
  function show(on) {
    if (!panel) return;
    panel.hidden = !on;
    if (on) panel.classList.add("is-open"); else panel.classList.remove("is-open");
  }
  function modal() {
    if (list.length < 2) { window.alert(I.empty || "Select at least two posts to compare."); return; }
    var old = document.getElementById("su-compare-modal");
    if (old) old.remove();
    var html = '<div class="su-compare-modal" id="su-compare-modal" role="dialog" aria-modal="true" aria-labelledby="su-compare-title">' +
      '<div class="su-compare-card"><div class="su-compare-head"><h2 id="su-compare-title">Compare selected posts</h2><button type="button" data-su-compare-modal-close aria-label="Close">✕</button></div>' +
      '<div class="su-compare-table-wrap"><table class="su-compare-table"><thead><tr><th>Post</th><th>Category</th><th>Deadline</th><th>Links</th></tr></thead><tbody>';
    list.forEach(function (row) {
      var apply = row.apply ? ' · <a href="' + esc(row.apply) + '" target="_blank" rel="noopener noreferrer">Official apply</a>' : '';
      html += '<tr><th scope="row">' + esc(row.title) + '</th><td>' + esc(row.cat || "—") + '</td><td>' + esc(row.date || "Not announced") + '</td><td><a href="' + esc(row.url) + '">Read post →</a>' + apply + '</td></tr>';
    });
    html += '</tbody></table></div><p class="su-compare-note">Compare only the information shown in each article. Confirm dates, fees and eligibility in the official notification.</p></div></div>';
    document.body.insertAdjacentHTML("beforeend", html);
    var node = document.getElementById("su-compare-modal");
    var close = node.querySelector("[data-su-compare-modal-close]");
    close.focus();
    close.addEventListener("click", function () { node.remove(); });
    node.addEventListener("click", function (event) { if (event.target === node) node.remove(); });
    node.addEventListener("keydown", function (event) {
      if (event.key === "Escape") { event.preventDefault(); node.remove(); }
    });
  }
  function add(id, button) {
    var i = find(id);
    if (i !== -1) { list.splice(i, 1); }
    else {
      if (list.length >= max) { window.alert(I.limit || "Compare up to three posts."); return; }
      list.push({id: id, title: button.getAttribute("data-title") || "Post", url: button.getAttribute("data-url") || "", cat: button.getAttribute("data-cat") || "", date: button.getAttribute("data-date") || "", apply: button.getAttribute("data-apply") || ""});
    }
    write(); render(); show(list.length > 0);
  }
  function icsEscape(value) { return String(value || "").replace(/[\\;,\n]/g, function (c) { return c === "\n" ? "\\n" : "\\" + c; }); }
  function reminder(button) {
    var date = button.getAttribute("data-date") || "";
    if (!/^20\d{2}-\d{2}-\d{2}$/.test(date)) { window.alert(I.noDate || "No confirmed date is available."); return; }
    var ymd = date.replace(/-/g, "");
    var next = new Date(date + "T00:00:00Z");
    next.setUTCDate(next.getUTCDate() + 1);
    var endYmd = next.toISOString().slice(0, 10).replace(/-/g, "");
    var title = icsEscape(button.getAttribute("data-title") || "StudentUp deadline");
    var url = icsEscape(button.getAttribute("data-url") || window.location.href);
    var body = "Confirm the official notification before acting.\\n" + url;
    var ics = "BEGIN:VCALENDAR\r\nVERSION:2.0\r\nPRODID:-//StudentUp//Deadline Reminder//EN\r\nBEGIN:VEVENT\r\nUID:studentup-" + ymd + "-" + Date.now() + "@studentup.in\r\nDTSTAMP:" + new Date().toISOString().replace(/[-:]/g, "").replace(/\.\d{3}Z$/, "Z") + "\r\nDTSTART;VALUE=DATE:" + ymd + "\r\nDTEND;VALUE=DATE:" + endYmd + "\r\nSUMMARY:" + title + "\r\nDESCRIPTION:" + icsEscape(body) + "\r\nURL:" + url + "\r\nEND:VEVENT\r\nEND:VCALENDAR\r\n";
    var blob = new Blob([ics], {type: "text/calendar;charset=utf-8"});
    var link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "studentup-deadline-" + ymd + ".ics"; link.click();
    setTimeout(function () { URL.revokeObjectURL(link.href); }, 1000);
    button.setAttribute("data-reminded", "true");
    window.alert(I.reminder || "Reminder file downloaded. Add it to your calendar.");
  }
  document.addEventListener("click", function (event) {
    var target = event.target.closest ? event.target : null;
    var compare = target && target.closest("[data-su-compare]");
    var remove = target && target.closest("[data-su-compare-remove]");
    var reminderBtn = target && target.closest("[data-su-reminder]");
    if (compare) { event.preventDefault(); add(compare.getAttribute("data-id"), compare); return; }
    if (remove) { event.preventDefault(); add(remove.getAttribute("data-su-compare-remove"), {getAttribute: function (name) { return name === "data-id" ? remove.getAttribute("data-su-compare-remove") : ""; }}); return; }
    if (reminderBtn) { event.preventDefault(); reminder(reminderBtn); return; }
    if (target && target.closest("[data-su-print]")) { event.preventDefault(); window.print(); return; }
    if (target && target.closest("[data-su-compare-open]")) { event.preventDefault(); modal(); return; }
    if (target && target.closest("[data-su-compare-close]")) { event.preventDefault(); show(false); return; }
    if (target && target.closest("[data-su-compare-clear]")) { event.preventDefault(); list = []; write(); render(); show(false); }
  });
  // v198: home smart-search results lo compare buttons dynamic ga inject avutayi
  // (studentup-smart.js `studentup:compare-refresh` dispatch chestundi) —
  // appudu rail state ni malli render cheyyandi. Click handling delegate ayyindi,
  // so aa buttons ki extra wiring avasaram ledu.
  document.addEventListener("studentup:compare-refresh", function () { list = read(); render(); });
  list = read(); render();

  /* v165: Age & Eligibility Calculator Handler */
  (function initAgeCalc() {
    var btn = document.getElementById("su-calc-age-btn");
    if (!btn) return;

    btn.addEventListener("click", function () {
      var dobVal = document.getElementById("su-dob").value;
      var cutoffVal = document.getElementById("su-cutoff").value;
      var catRelax = parseInt(document.getElementById("su-cat").value, 10) || 0;
      var minAge = parseInt(btn.getAttribute("data-min"), 10) || 18;
      var baseMaxAge = parseInt(btn.getAttribute("data-max"), 10) || 44;
      var maxAllowed = baseMaxAge + catRelax;

      if (!dobVal || !cutoffVal) {
        alert("Please enter Date of Birth and Cut-off Date.");
        return;
      }

      var dob = new Date(dobVal);
      var cutoff = new Date(cutoffVal);

      if (dob >= cutoff) {
        alert("Date of Birth must be before Cut-off Date.");
        return;
      }

      var y = cutoff.getFullYear() - dob.getFullYear();
      var m = cutoff.getMonth() - dob.getMonth();
      var d = cutoff.getDate() - dob.getDate();

      if (d < 0) {
        m -= 1;
        var prevMonthLast = new Date(cutoff.getFullYear(), cutoff.getMonth(), 0).getDate();
        d += prevMonthLast;
      }
      if (m < 0) {
        y -= 1;
        m += 12;
      }

      var exactStr = y + " Years, " + m + " Months, " + d + " Days (" + y + " yrs)";
      var resBox = document.getElementById("su-age-result");
      var exactAgeEl = document.getElementById("su-exact-age");
      var maxAllowedEl = document.getElementById("su-max-allowed");
      var statusEl = document.getElementById("su-elig-status");
      var noteEl = document.getElementById("su-elig-note");

      exactAgeEl.textContent = exactStr;
      maxAllowedEl.textContent = maxAllowed + " Years (Base " + baseMaxAge + " + Relaxation " + catRelax + ")";

      var isEligible = (y >= minAge) && (y < maxAllowed || (y === maxAllowed && m === 0 && d === 0));

      if (isEligible) {
        statusEl.textContent = "Eligible";
        statusEl.className = "su-age-status su-elig-yes";
        noteEl.innerHTML = "Congratulations! Your age is within the eligible limit (" + minAge + " - " + maxAllowed + " years). Check official qualification criteria to apply.";
      } else {
        if (y < minAge) {
          statusEl.textContent = "Underage";
          statusEl.className = "su-age-status su-elig-no";
          noteEl.innerHTML = "Minimum age required is " + minAge + " years. As of the cut-off date, your age is " + y + " years.";
        } else {
          statusEl.textContent = "Over Age";
          statusEl.className = "su-age-status su-elig-no";
          noteEl.innerHTML = "Maximum age limit with relaxation is " + maxAllowed + " years. You exceed the upper age limit.";
        }
      }

      resBox.style.display = "block";
    });
  })();

  /* v166: Font Resizer Toolbar */
  (function initFontSizer() {
    var stored = localStorage.getItem("su_font_size") || "normal";
    function applyFont(size) {
      document.body.classList.remove("su-font-small", "su-font-large");
      if (size === "small") document.body.classList.add("su-font-small");
      if (size === "large") document.body.classList.add("su-font-large");
      document.querySelectorAll("[data-su-font]").forEach(function (btn) {
        btn.classList.toggle("is-active", btn.getAttribute("data-su-font") === size);
      });
      try { localStorage.setItem("su_font_size", size); } catch (e) {}
    }
    applyFont(stored);
    document.addEventListener("click", function (e) {
      var btn = e.target.closest && e.target.closest("[data-su-font]");
      if (btn) {
        e.preventDefault();
        applyFont(btn.getAttribute("data-su-font"));
      }
    });
  })();

  /* v167: Fee & Concession Calculator Handler */
  (function initFeeCalc() {
    var btn = document.getElementById("su-calc-fee-btn");
    if (!btn) return;

    btn.addEventListener("click", function () {
      var cat = document.getElementById("su-fee-cat").value;
      var proc = parseInt(document.getElementById("su-base-proc").value, 10) || 0;
      var exam = parseInt(document.getElementById("su-base-exam").value, 10) || 0;
      var finalProc = proc;
      var finalExam = exam;
      var note = "";

      if (cat === "sc_st") {
        finalExam = 0;
        note = "SC / ST candidates get 100% Exam Fee Exemption. Only processing fee is applicable.";
      } else if (cat === "pwd") {
        finalProc = 0;
        finalExam = 0;
        note = "PwD / Differently Abled candidates are 100% exempt from both processing and examination fees.";
      } else if (cat === "women") {
        finalExam = 0;
        note = "Female candidates receive exam fee concession as per state government rules.";
      } else if (cat === "esm") {
        finalExam = 0;
        note = "Ex-Servicemen are entitled to exam fee exemption.";
      } else {
        note = "OC / General / BC candidates must pay the full application and exam fee via the online portal.";
      }

      var total = finalProc + finalExam;
      document.getElementById("su-res-proc").textContent = "₹" + finalProc;
      document.getElementById("su-res-exam").textContent = finalExam === 0 ? "₹0 (Exempted)" : "₹" + finalExam;
      document.getElementById("su-res-total").textContent = "₹" + total;
      document.getElementById("su-fee-note").innerHTML = note;
      document.getElementById("su-fee-result").style.display = "block";
    });
  })();

  /* v167: Syllabus & Study Progress Tracker */
  (function initSyllabusTracker() {
    var wrap = document.getElementById("syllabus-tracker");
    if (!wrap) return;

    var postId = wrap.getAttribute("data-post-id") || "global";
    var storeKey = "su_syl_progress_" + postId;
    var chks = wrap.querySelectorAll(".su-syl-chk");
    var bar = document.getElementById("su-syl-bar");
    var countEl = document.getElementById("su-syl-count");
    var pctEl = document.getElementById("su-syl-percent");
    var resetBtn = document.getElementById("su-syl-reset");

    function getSaved() {
      try { return JSON.parse(localStorage.getItem(storeKey) || "{}"); } catch (e) { return {}; }
    }
    function save(data) {
      try { localStorage.setItem(storeKey, JSON.stringify(data)); } catch (e) {}
    }

    function updateUI() {
      var saved = getSaved();
      var done = 0;
      chks.forEach(function (chk) {
        var tid = chk.getAttribute("data-tid");
        var isDone = !!saved[tid];
        chk.checked = isDone;
        var item = chk.closest(".su-syl-item");
        if (item) item.classList.toggle("is-done", isDone);
        if (isDone) done++;
      });
      var total = chks.length || 1;
      var pct = Math.round((done / total) * 100);
      if (bar) bar.style.width = pct + "%";
      if (countEl) countEl.textContent = done + " / " + total + " Completed";
      if (pctEl) pctEl.textContent = pct + "%";
    }

    chks.forEach(function (chk) {
      chk.addEventListener("change", function () {
        var saved = getSaved();
        var tid = chk.getAttribute("data-tid");
        saved[tid] = chk.checked;
        save(saved);
        updateUI();
      });
    });

    if (resetBtn) {
      resetBtn.addEventListener("click", function () {
        if (confirm("Do you want to reset your syllabus progress?")) {
          save({});
          updateUI();
        }
      });
    }

    updateUI();
  })();

  /* v167: 1-Click WhatsApp Status Card Canvas Generator */
  (function initStatusCardGenerator() {
    var box = document.getElementById("su-status-box");
    var btn = document.getElementById("su-gen-status-btn");
    var canvas = document.getElementById("su-status-canvas");
    if (!box || !btn || !canvas) return;

    btn.addEventListener("click", function () {
      btn.textContent = "Generating status image…";
      btn.disabled = true;

      var ctx = canvas.getContext("2d");
      var w = 1080;
      var h = 1920;

      var grad = ctx.createLinearGradient(0, 0, w, h);
      grad.addColorStop(0, "#0b1528");
      grad.addColorStop(0.5, "#0f2e62");
      grad.addColorStop(1, "#162235");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, w, h);

      ctx.fillStyle = "#22c55e";
      ctx.beginPath();
      ctx.arc(100, 140, 16, 0, Math.PI * 2);
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 56px system-ui, sans-serif";
      ctx.fillText("StudentUp.in", 136, 156);

      ctx.fillStyle = "#38bdf8";
      ctx.font = "600 36px system-ui, sans-serif";
      ctx.fillText("Telangana & AP Job Alerts", 100, 230);

      ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
      if (ctx.roundRect) {
        ctx.roundRect(80, 320, 920, 1200, 40);
      } else {
        ctx.rect(80, 320, 920, 1200);
      }
      ctx.fill();

      ctx.fillStyle = "#ec4899";
      if (ctx.roundRect) {
        ctx.roundRect(140, 380, 450, 64, 32);
      } else {
        ctx.rect(140, 380, 450, 64);
      }
      ctx.fill();
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 32px system-ui, sans-serif";
      ctx.fillText("🔥 LATEST NOTIFICATION", 165, 424);

      var title = box.getAttribute("data-title") || "Government Job Notification";
      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 54px system-ui, sans-serif";
      
      var words = title.split(" ");
      var line = "";
      var y = 540;
      for (var i = 0; i < words.length; i++) {
        var testLine = line + words[i] + " ";
        if (ctx.measureText(testLine).width > 800 && i > 0) {
          ctx.fillText(line, 140, y);
          line = words[i] + " ";
          y += 74;
        } else {
          line = testLine;
        }
      }
      ctx.fillText(line, 140, y);

      var facts = [
        { icon: "💼", label: "Vacancies", val: box.getAttribute("data-vacancies") },
        { icon: "🎓", label: "Qualification", val: box.getAttribute("data-qual") },
        { icon: "⏰", label: "Last Date", val: box.getAttribute("data-last-date") }
      ];

      var fy = y + 80;
      for (var j = 0; j < facts.length; j++) {
        ctx.fillStyle = "rgba(255, 255, 255, 0.12)";
        if (ctx.roundRect) {
          ctx.roundRect(140, fy, 800, 110, 20);
        } else {
          ctx.rect(140, fy, 800, 110);
        }
        ctx.fill();

        ctx.font = "44px system-ui, sans-serif";
        ctx.fillText(facts[j].icon, 170, fy + 72);

        ctx.fillStyle = "#94a3b8";
        ctx.font = "600 28px system-ui, sans-serif";
        ctx.fillText(facts[j].label + ":", 240, fy + 44);

        ctx.fillStyle = "#38bdf8";
        ctx.font = "bold 38px system-ui, sans-serif";
        ctx.fillText(facts[j].val, 240, fy + 90);

        fy += 135;
      }

      ctx.fillStyle = "#22c55e";
      if (ctx.roundRect) {
        ctx.roundRect(140, 1600, 800, 130, 65);
      } else {
        ctx.rect(140, 1600, 800, 130);
      }
      ctx.fill();

      ctx.fillStyle = "#ffffff";
      ctx.font = "bold 44px system-ui, sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("Official Details & Apply 👉 studentup.in", 540, 1680);
      ctx.textAlign = "left";

      setTimeout(function () {
        var link = document.createElement("a");
        link.download = "studentup-job-status.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
        btn.textContent = "Status Image Downloaded";
        btn.disabled = false;
        setTimeout(function () {
          btn.textContent = "Download Status Image";
        }, 4000);
      }, 500);
    });
  })();

  /* v168: Admit Card & Hall Ticket Helper Handler */
  (function initAdmitCardHelper() {
    var select = document.getElementById("su-admit-select");
    var link = document.getElementById("su-admit-link");
    var reqText = document.getElementById("su-admit-req-text");
    if (!select || !link || !reqText) return;

    select.addEventListener("change", function () {
      var opt = select.options[select.selectedIndex];
      var url = opt.getAttribute("data-url") || "#";
      var req = opt.getAttribute("data-req") || "";
      link.href = url;
      reqText.textContent = req;
    });
  })();

  /* v168: Exam Score & Negative Marking Calculator Handler */
  (function initScoreCalc() {
    var btn = document.getElementById("su-calc-score-btn");
    if (!btn) return;

    btn.addEventListener("click", function () {
      var correct = parseFloat(document.getElementById("su-score-correct").value) || 0;
      var wrong = parseFloat(document.getElementById("su-score-wrong").value) || 0;
      var posRate = parseFloat(document.getElementById("su-score-pos").value) || 1.0;
      var negRate = parseFloat(document.getElementById("su-score-neg").value) || 0.25;

      var posMarks = correct * posRate;
      var negDeduction = wrong * (posRate * negRate);
      var netScore = Math.max(0, posMarks - negDeduction);
      var totalQ = correct + wrong;
      var accuracy = totalQ > 0 ? Math.round((correct / totalQ) * 100) : 0;

      document.getElementById("su-res-pos-marks").textContent = "+" + posMarks.toFixed(2);
      document.getElementById("su-res-neg-marks").textContent = "-" + negDeduction.toFixed(2);
      document.getElementById("su-res-final-score").textContent = netScore.toFixed(2) + " Marks";

      var note = "Your Accuracy Rate: <strong>" + accuracy + "%</strong>. ";
      if (accuracy >= 75) {
        note += "Excellent Accuracy! High chance of clearing the cutoff.";
      } else if (accuracy >= 55) {
        note += "Good attempt! Reducing negative marks will improve your overall rank.";
      } else {
        note += "Marks lost in negative scoring. Focus on high-confidence questions and reduce guessing.";
      }

      document.getElementById("su-score-note").innerHTML = note;
      document.getElementById("su-score-result").style.display = "block";
    });
  })();

  /* v168: Fresher Resume & Bio-Data Generator Handler */
  (function initResumeMaker() {
    var btn = document.getElementById("su-gen-resume-btn");
    var preview = document.getElementById("su-resume-preview");
    if (!btn || !preview) return;

    btn.addEventListener("click", function () {
      var name = document.getElementById("su-res-name").value.trim() || "Full Name";
      var phone = document.getElementById("su-res-phone").value.trim() || "9876543210";
      var qual = document.getElementById("su-res-qual").value;
      var skills = document.getElementById("su-res-skills").value.trim() || "MS Office, Typing, Basics";

      document.getElementById("su-rp-name").textContent = name;
      document.getElementById("su-rp-contact").textContent = "Phone: " + phone + " | Qualification: " + qual;
      document.getElementById("su-rp-qual-text").textContent = qual + " Pass (from recognized University / Board)";
      document.getElementById("su-rp-skills-text").textContent = skills;

      preview.style.display = "block";
      btn.textContent = "Resume Ready! See preview below";
    });
  })();

  /* v165: Web Speech API Telugu Audio Reader */
  (function initAudioReader() {
    var box = document.getElementById("su-audio-box");
    if (!box || !("speechSynthesis" in window)) {
      if (box && !("speechSynthesis" in window)) box.style.display = "none";
      return;
    }

    var btn = document.getElementById("su-audio-btn");
    var label = document.getElementById("su-audio-label");
    var icon = document.getElementById("su-audio-icon");
    var waves = document.getElementById("su-audio-waves");
    var ctrls = document.getElementById("su-audio-controls");
    var stopBtn = document.getElementById("su-audio-stop");
    var speedBtn = document.getElementById("su-audio-speed-btn");

    var speechText = box.getAttribute("data-speech") || "";
    var utterance = null;
    var isPlaying = false;
    var isPaused = false;
    var speed = 1.0;
    var speeds = [1.0, 1.25, 0.9];
    var speedIdx = 0;

    function resetUI() {
      isPlaying = false;
      isPaused = false;
      if (label) label.textContent = "Listen to Article";
      if (icon) icon.innerHTML = I.speaker;
      if (waves) waves.style.display = "none";
      if (ctrls) ctrls.style.display = "none";
    }

    btn.addEventListener("click", function () {
      if (!isPlaying) {
        window.speechSynthesis.cancel();
        utterance = new SpeechSynthesisUtterance(speechText);
        utterance.rate = speed;
        utterance.pitch = 1.0;

        var voices = window.speechSynthesis.getVoices();
        for (var i = 0; i < voices.length; i++) {
          if (voices[i].lang.indexOf("te") === 0 || voices[i].lang.indexOf("te-IN") === 0) {
            utterance.voice = voices[i];
            break;
          }
        }

        utterance.onend = function () { resetUI(); };
        utterance.onerror = function () { resetUI(); };

        window.speechSynthesis.speak(utterance);
        isPlaying = true;
        isPaused = false;
        label.textContent = "Pause";
        icon.innerHTML = I.pause;
        waves.style.display = "inline-flex";
        ctrls.style.display = "flex";
      } else if (isPlaying && !isPaused) {
        window.speechSynthesis.pause();
        isPaused = true;
        label.textContent = "Resume";
        icon.innerHTML = I.play;
        waves.style.display = "none";
      } else if (isPlaying && isPaused) {
        window.speechSynthesis.resume();
        isPaused = false;
        label.textContent = "Pause";
        icon.innerHTML = I.pause;
        waves.style.display = "inline-flex";
      }
    });

    if (stopBtn) {
      stopBtn.addEventListener("click", function () {
        window.speechSynthesis.cancel();
        resetUI();
      });
    }

    if (speedBtn) {
      speedBtn.addEventListener("click", function () {
        speedIdx = (speedIdx + 1) % speeds.length;
        speed = speeds[speedIdx];
        speedBtn.textContent = speed + "x";
        if (isPlaying && utterance) {
          window.speechSynthesis.cancel();
          isPlaying = false;
          btn.click();
        }
      });
    }
  })();
})();
