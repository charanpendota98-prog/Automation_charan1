/* StudentUp SAVED — reader bookmarks (v92 · theme 1.9.3)
 * Enti chestundi:
 *   1) Post save / un-save (🔖 button) — localStorage lo mattrame (DB ledu, cookie ledu)
 *   2) Saved panel (rail tab → slide-out) + /saved/ page grid — rendu okate store nunchi
 *   3) Count badges sync ([data-su-saved-count]) + aria-pressed (a11y)
 *   4) Reading history ("recently read") — saved panel kinda chupistundi
 *
 * Design rules:
 *   · Progressive enhancement — JS lekapoyina site baaguntundi (server markup intact)
 *   · localStorage block aithe (private mode / disabled) → okka soft note, crash ledu
 *   · XSS-safe — anni strings textContent tho (innerHTML lo user/title text ledu)
 *   · Vanilla only · no library · no external request
 */
(function () {
  "use strict";

  var D = window.STUDENTUP_SAVED || {};
  var I18N = D.i18n || {};
  var MAX = parseInt(D.max, 10) || 60;
  var KEY = D.store || "studentup_saved_v1";
  var RKEY = D.recent || "studentup_recent_v1";
  var ok = true;                       /* storage usable aa? */

  /* ---------- storage (every access guarded) ---------- */
  function read(key) {
    if (!ok) { return []; }
    try {
      var raw = window.localStorage.getItem(key);
      var val = raw ? JSON.parse(raw) : [];
      return Object.prototype.toString.call(val) === "[object Array]" ? val : [];
    } catch (e) { return []; }
  }
  function write(key, val) {
    if (!ok) { return false; }
    try {
      window.localStorage.setItem(key, JSON.stringify(val));
      return true;
    } catch (e) { ok = false; return false; }
  }
  function probe() {
    try {
      window.localStorage.setItem("su_probe", "1");
      window.localStorage.removeItem("su_probe");
    } catch (e) { ok = false; }
  }

  function saved() { return read(KEY); }
  function recent() { return read(RKEY); }

  function isSaved(id) {
    var list = saved(), want = String(id), i;
    for (i = 0; i < list.length; i++) {
      if (String(list[i].id) === want) { return true; }
    }
    return false;
  }

  /* ---------- toast (soft feedback, no alert) ---------- */
  var toastT = null;
  function toast(msg) {
    if (!msg) { return; }
    var el = document.getElementById("su-saved-toast");
    if (!el) {
      el = document.createElement("div");
      el.id = "su-saved-toast";
      el.className = "su-saved-toast";
      el.setAttribute("role", "status");
      el.setAttribute("aria-live", "polite");
      document.body.appendChild(el);
    }
    el.textContent = msg;
    el.classList.add("on");
    clearTimeout(toastT);
    toastT = setTimeout(function () { el.classList.remove("on"); }, 2600);
  }

  /* ---------- counts + button state ---------- */
  function syncCounts() {
    var n = saved().length, nodes = document.querySelectorAll("[data-su-saved-count]"), i;
    for (i = 0; i < nodes.length; i++) {
      nodes[i].textContent = String(n);
      if (nodes[i].hasAttribute("data-su-saved-count") &&
          nodes[i].classList.contains("su-saved-count")) {
        nodes[i].hidden = n === 0;
      }
    }
  }

  function syncButtons() {
    var btns = document.querySelectorAll("[data-su-save]"), i, b, on, txt;
    for (i = 0; i < btns.length; i++) {
      b = btns[i];
      on = isSaved(b.getAttribute("data-id"));
      b.setAttribute("aria-pressed", on ? "true" : "false");
      b.classList.toggle("on", on);
      txt = b.querySelector(".su-save-txt");
      if (txt) { txt.textContent = on ? (I18N.saved || "Saved") : (I18N.save || "Save"); }
    }
  }

  /* ---------- one safe card builder (textContent only) ---------- */
  function item(row) {
    var a = document.createElement("a");
    a.className = "su-saved-item";
    a.href = row.url || "#";

    var t = document.createElement("span");
    t.className = "su-saved-title";
    t.textContent = row.title || "";

    var m = document.createElement("span");
    m.className = "su-saved-meta";
    m.textContent = row.cat || "";

    a.appendChild(t);
    a.appendChild(m);

    var del = document.createElement("button");
    del.type = "button";
    del.className = "su-saved-del";
    del.setAttribute("data-su-remove", String(row.id));
    del.setAttribute("aria-label", I18N.removed || "Remove");
    del.textContent = "✕";

    var wrap = document.createElement("div");
    wrap.className = "su-saved-row";
    wrap.appendChild(a);
    wrap.appendChild(del);
    return wrap;
  }

  function renderPanel() {
    var body = document.querySelector("[data-su-saved-body]");
    if (!body) { return; }
    var list = saved();
    while (body.firstChild) { body.removeChild(body.firstChild); }

    if (!list.length) {
      var p = document.createElement("p");
      p.className = "su-saved-empty";
      p.textContent = I18N.empty || "No saved posts yet.";
      body.appendChild(p);
    } else {
      var box = document.createElement("div");
      box.className = "su-saved-list";
      var ordered = list.slice().reverse(), i;
      for (i = 0; i < ordered.length; i++) { box.appendChild(item(ordered[i])); }
      body.appendChild(box);
    }

    var rec = recent();
    if (rec.length) {
      var sub = document.createElement("div");
      sub.className = "su-saved-recent";
      var h = document.createElement("div");
      h.className = "su-saved-sub";
      h.textContent = I18N.recent || "Recently read";
      sub.appendChild(h);
      var r = rec.slice(0, 5);
      for (var j = 0; j < r.length; j++) { sub.appendChild(item(r[j])); }
      body.appendChild(sub);
    }
  }

  function renderPage() {
    var host = document.querySelector("[data-su-saved-page]");
    if (!host) { return; }
    var list = saved();
    while (host.firstChild) { host.removeChild(host.firstChild); }
    if (!list.length) {
      var p = document.createElement("p");
      p.className = "su-saved-empty";
      p.textContent = I18N.empty || "No saved posts yet.";
      host.appendChild(p);
      return;
    }
    var grid = document.createElement("div");
    grid.className = "su-saved-grid";
    var ordered = list.slice().reverse(), i;
    for (i = 0; i < ordered.length; i++) { grid.appendChild(item(ordered[i])); }
    host.appendChild(grid);
  }

  function renderAll() { syncCounts(); syncButtons(); renderPanel(); renderPage(); }

  /* ---------- toggle ---------- */
  function toggle(btn) {
    var id = btn.getAttribute("data-id");
    if (!id) { return; }
    var list = saved(), want = String(id), i, found = -1;
    for (i = 0; i < list.length; i++) {
      if (String(list[i].id) === want) { found = i; break; }
    }
    if (found > -1) {
      list.splice(found, 1);
      write(KEY, list);
      toast(I18N.removed || "Removed");
    } else {
      list.push({
        id: id,
        title: btn.getAttribute("data-title") || "",
        url: btn.getAttribute("data-url") || "",
        cat: btn.getAttribute("data-cat") || "",
        ts: Date.now()
      });
      while (list.length > MAX) { list.shift(); }   /* FIFO cap — storage bloat ledu */
      write(KEY, list);
      toast(ok ? (I18N.savedmsg || "Saved") : (I18N.nomore || ""));
    }
    renderAll();
  }

  function removeById(id) {
    var list = saved(), out = [], i, want = String(id);
    for (i = 0; i < list.length; i++) {
      if (String(list[i].id) !== want) { out.push(list[i]); }
    }
    write(KEY, out);
    renderAll();
  }

  /* ---------- reading history ---------- */
  function pushRecent() {
    var el = document.querySelector("article.article, .article-content");
    if (!el || !document.body.classList.contains("single")) { return; }
    var h1 = document.querySelector(".article-head h1") || document.querySelector("h1");
    var id = (document.body.className.match(/postid-(\d+)/) || [])[1];
    if (!id || !h1) { return; }
    var list = recent(), out = [{
      id: id, title: h1.textContent || "",
      url: window.location.href, cat: "", ts: Date.now()
    }], i;
    for (i = 0; i < list.length; i++) {
      if (String(list[i].id) !== String(id)) { out.push(list[i]); }
    }
    write(RKEY, out.slice(0, 20));
  }

  /* ---------- panel open/close ---------- */
  function panel(on) {
    var p = document.getElementById("su-saved-panel"),
        tab = document.getElementById("su-saved-tab");
    if (!p) { return; }
    if (on) { renderPanel(); }
    p.hidden = !on;
    if (tab) { tab.setAttribute("aria-expanded", on ? "true" : "false"); }
    document.body.classList.toggle("su-saved-open", !!on);
  }

  function wire() {
    document.addEventListener("click", function (e) {
      var t = e.target;
      if (!t || !t.closest) { return; }

      var btn = t.closest("[data-su-save]");
      if (btn) { e.preventDefault(); toggle(btn); return; }

      var del = t.closest("[data-su-remove]");
      if (del) { e.preventDefault(); removeById(del.getAttribute("data-su-remove")); return; }

      if (t.closest("[data-su-saved-open]")) {
        e.preventDefault();
        /* mobile panel nunchi open chesthe — mundu aa menu ni close cheyyali
         * (lekapote rendu panels okesaari overlap avutayi). studentup.js
         * `#menubtn` ni wire chesindi, anduke adi click chesi toggle chestunnamu. */
        if (t.closest(".mpanel")) {
          var mb = document.getElementById("menubtn");
          if (mb && mb.getAttribute("aria-expanded") === "true") { mb.click(); }
        }
        var p = document.getElementById("su-saved-panel");
        panel(p ? p.hidden : true);
        return;
      }
      if (t.closest("#su-saved-close")) { panel(false); return; }

      if (t.closest("#su-saved-clear")) {
        e.preventDefault();
        if (window.confirm(I18N.confirm || "Remove all?")) {
          write(KEY, []);
          renderAll();
          toast(I18N.cleared || "Cleared");
        }
        return;
      }

      /* outside click closes */
      var open = document.getElementById("su-saved-panel");
      if (open && !open.hidden &&
          !t.closest("#su-saved-panel") && !t.closest("[data-su-saved-open]")) {
        panel(false);
      }
    });

    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape") { panel(false); }
    });
  }

  /* ---------- init ---------- */
  function init() {
    probe();
    if (document.body) { pushRecent(); }
    renderAll();
    wire();
    if (!ok && I18N.nomore) { toast(I18N.nomore); }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
