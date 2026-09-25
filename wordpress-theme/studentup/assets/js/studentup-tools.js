/* v120: local-only reader utilities — compare, calendar reminder and print/PDF. */
(function () {
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
      '<div class="su-compare-table-wrap"><table class="su-compare-table"><thead><tr><th>Post</th><th>Category</th><th>Open</th></tr></thead><tbody>';
    list.forEach(function (row) {
      html += '<tr><th scope="row">' + esc(row.title) + '</th><td>' + esc(row.cat || "—") + '</td><td><a href="' + esc(row.url) + '">Read post →</a></td></tr>';
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
      list.push({id: id, title: button.getAttribute("data-title") || "Post", url: button.getAttribute("data-url") || "", cat: button.getAttribute("data-cat") || ""});
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
  list = read(); render();
})();
